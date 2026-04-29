# Author: Hannah Lybbert
# Created: 02/25/2026
# Updated: 02/25/2026
# Purpose: Optimized birth detection — token-aware parallel batches, auto-retry, resume, cost tracking

import os
import openai
import pandas as pd
import json
import time
import re
from dotenv import load_dotenv

# ── Setup ──────────────────────────────────────────────────────────────────────
os.chdir("D:/TwitterBirth")
load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# File paths
# INPUT_PATH  = "Reddit/data/intermediate/cleaned_raw/reddit_cleaned_2006_to_2018.csv"
INPUT_PATH = "Reddit/data/intermediate/cleaned_raw/test_samples/reddit_test_100_sample.csv"
# OUTPUT_PATH = "Reddit/data/LLM/birth_detection.csv"
OUTPUT_PATH = "Reddit/data/LLM/test_samples/birth_detection_100.csv"

# Tuning constants
MAX_REQUESTS_PER_BATCH  = 1500
TOKENS_PER_PROMPT       = 500        # estimated input tokens per request
BATCH_TOKEN_QUEUE_LIMIT = 1_800_000  # Tier 1 cap is 2M — stay 10% below
MAX_RETRIES             = 2
POLL_INTERVAL           = 60         # seconds between polling cycles

# gpt-4o-mini batch API pricing — verify at platform.openai.com/pricing
# Batch API gives 50% discount on standard rates
INPUT_COST_PER_TOKEN  = 0.075 / 1_000_000   # $0.075 per 1M input tokens
OUTPUT_COST_PER_TOKEN = 0.300 / 1_000_000   # $0.30 per 1M output tokens

# Persistence paths
STATE_PATH    = "Reddit/data/json/batch_state_birth2.json"
COST_LOG_PATH = "Reddit/data/json/cost_log_birth.json"

# ── Load data ──────────────────────────────────────────────────────────────────
df = pd.read_csv(INPUT_PATH, encoding="utf-8", low_memory=False)
assert "id" in df.columns, "id column must exist in input data"
assert df["id"].notna().all(), "id column must not have missing values"
df["id"] = df["id"].astype(str)


# ── Helpers ────────────────────────────────────────────────────────────────────
def sanitize_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = text.replace('\x00', '').replace('\r', ' ').replace('\n', ' ')
    if len(text) > 2000:
        text = text[:2000]
    return text.strip()


def load_state():
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    return {}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_PATH), exist_ok=True)
    with open(STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


def load_cost_log():
    if os.path.exists(COST_LOG_PATH):
        with open(COST_LOG_PATH) as f:
            return json.load(f)
    return {"total_input_tokens": 0, "total_output_tokens": 0, "total_cost_usd": 0.0, "runs": []}


def save_cost_log(log):
    os.makedirs(os.path.dirname(COST_LOG_PATH), exist_ok=True)
    with open(COST_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


# ── JSONL creation ─────────────────────────────────────────────────────────────
def get_birth_prompt(post_id, title, selftext):
    title    = title    or ""
    selftext = selftext or ""
    return {
        "custom_id": str(post_id),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Classify a Reddit post on two tasks:\n\n"

                        "TASK 1 — BIRTH FLAG\n"
                        "Did the author post within 14 days (before or after) of having a baby?\n"
                        "VALID subjects: the author ('I am 39 weeks pregnant', 'I'm 4 days postpartum') "
                        "or their spouse/partner ('my wife is 38 weeks pregnant', 'my husband and I just had our baby').\n"
                        "INVALID: any other person — sister, mother, friend, nephew, etc.\n"
                        "Timing must be PRESENT TENSE ('I am', 'my wife is'), not past ('I was', 'she was').\n"
                        "Calculate days_from_birth (birth = 40 weeks):\n"
                        "- 'X weeks pregnant' → (X−40)×7  |  'X+Y' → ((X−40)×7)−Y\n"
                        "- 'X days postpartum/pp' → X  |  'X weeks postpartum' → X×7\n"
                        "- 'baby is X days/weeks old' → X or X×7\n"
                        "Flag as 1 only if −14 ≤ days_from_birth ≤ 14.\n\n"

                        "TASK 2 — POSTER GENDER (p_female, p_male, each 0-100, summing to 100)\n"
                        "Strong female signals: author is pregnant/postpartum, gave birth, is breastfeeding/nursing, "
                        "refers to self as mom/mother/mum, mentions her husband/boyfriend.\n"
                        "Strong male signals: author's wife/girlfriend is pregnant or postpartum, "
                        "author refers to self as dad/father, says 'I will become a father'.\n"
                        "Weaker signals: 'my partner' (ambiguous — use other cues); "
                        "note 'my wife' could indicate a same-sex female couple.\n"
                        "If no gender cues exist: p_female=50, p_male=50.\n\n"

                        "Respond on exactly five lines:\n"
                        "Line 1: birth_flag (1=within window, 0=not, -99=uncertain)\n"
                        "Line 2: days_from_birth (integer, or -999 if N/A)\n"
                        "Line 3: confidence (0-100)\n"
                        "Line 4: p_female (0-100)\n"
                        "Line 5: p_male (0-100)"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Title: {title}\n\n"
                        f"Post: {selftext}\n\n"
                        "[birth_flag]\n[days_from_birth]\n[confidence]\n[p_female]\n[p_male]"
                    )
                }
            ]
        }
    }


def create_jsonl_files():
    """Create JSONL batch files for the full dataset. Skips files that already exist (resume-safe)."""
    os.makedirs("Reddit/data/json", exist_ok=True)
    file_map    = {}   # batch_index -> jsonl_filename
    batch_index = 0

    for start in range(0, len(df), MAX_REQUESTS_PER_BATCH):
        batch_df       = df.iloc[start:start + MAX_REQUESTS_PER_BATCH].copy()
        jsonl_filename = f"Reddit/data/json/batch_requests_birth2_batch_{batch_index}.jsonl"
        file_map[batch_index] = jsonl_filename

        if os.path.exists(jsonl_filename):
            print(f"JSONL already exists, skipping: {jsonl_filename}")
            batch_index += 1
            continue

        requests_written = 0
        with open(jsonl_filename, "w", encoding="utf-8") as f:
            for _, row in batch_df.iterrows():
                title_val    = sanitize_text(row.get("title",    ""))
                selftext_val = sanitize_text(row.get("selftext", ""))
                if not title_val and not selftext_val:
                    continue
                prompt = get_birth_prompt(row["id"], title_val, selftext_val)
                f.write(json.dumps(prompt, ensure_ascii=False) + "\n")
                requests_written += 1

        print(f"Created JSONL: {jsonl_filename} ({requests_written} requests)")
        batch_index += 1

    print(f"Total JSONL batches prepared: {batch_index}")
    return file_map


# ── Batch submission ───────────────────────────────────────────────────────────
def submit_batch(jsonl_filename):
    try:
        with open(jsonl_filename, "rb") as f:
            file_upload = client.files.create(file=f, purpose="batch")
        response = client.batches.create(
            input_file_id=file_upload.id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        return response.id
    except Exception as e:
        print(f"  Error submitting {jsonl_filename}: {e}")
        return None


def estimate_enqueued_tokens(state):
    """Estimate tokens currently in OpenAI's queue based on in-flight batches."""
    active_statuses = {"submitted", "queued", "in_progress", "validating"}
    active_count    = sum(1 for v in state.values() if v.get("status") in active_statuses)
    return active_count * MAX_REQUESTS_PER_BATCH * TOKENS_PER_PROMPT


# ── Result parsing ─────────────────────────────────────────────────────────────
def parse_batch_result(batch_id, track_tokens=True):
    """
    Download and parse a completed batch.

    Returns:
        (DataFrame, input_tokens, output_tokens)
        Token counts are 0 when track_tokens=False (used for resumed batches
        already counted in a prior run's cost log).
    """
    try:
        batch_info     = client.batches.retrieve(batch_id)
        output_file_id = batch_info.output_file_id
        if not output_file_id:
            print(f"  No output file for batch {batch_id}")
            return None, 0, 0

        file_response = client.files.content(output_file_id)
        results       = file_response.text
        parsed        = []
        input_tokens  = 0
        output_tokens = 0

        for line in results.splitlines():
            response = json.loads(line)
            post_id  = str(response.get("custom_id"))
            body     = response.get("response", {}).get("body", {})
            choices  = body.get("choices", [])
            usage    = body.get("usage", {})

            if track_tokens:
                input_tokens  += usage.get("prompt_tokens",     0)
                output_tokens += usage.get("completion_tokens", 0)

            if not choices:
                parsed.append({"id": post_id, "birth_flag": -99, "days_from_birth": -999,
                                "confidence": 0, "p_female": 50, "p_male": 50})
                continue

            content = choices[0]["message"]["content"].strip()
            lines   = content.splitlines()

            flag_match = re.search(r"^(-?\d+)", lines[0]) if len(lines) > 0 else None
            days_match = re.search(r"^(-?\d+)", lines[1]) if len(lines) > 1 else None
            conf_match = re.search(r"^(\d+)",   lines[2]) if len(lines) > 2 else None
            fem_match  = re.search(r"^(\d+)",   lines[3]) if len(lines) > 3 else None
            mal_match  = re.search(r"^(\d+)",   lines[4]) if len(lines) > 4 else None

            parsed.append({
                "id":              post_id,
                "birth_flag":      int(flag_match.group(1)) if flag_match else -99,
                "days_from_birth": int(days_match.group(1)) if days_match else -999,
                "confidence":      int(conf_match.group(1)) if conf_match else 0,
                "p_female":        int(fem_match.group(1))  if fem_match  else 50,
                "p_male":          int(mal_match.group(1))  if mal_match  else 50,
            })

        return pd.DataFrame(parsed), input_tokens, output_tokens

    except Exception as e:
        print(f"  Error parsing batch {batch_id}: {e}")
        return None, 0, 0


# ── Main loop ──────────────────────────────────────────────────────────────────
def main():
    run_start     = time.time()
    cost_log      = load_cost_log()
    total_in_tok  = 0
    total_out_tok = 0
    all_results   = []

    active_statuses = {"submitted", "queued", "in_progress", "validating"}

    # Step 1: Create JSONL files (skips existing files for resume safety)
    file_map    = create_jsonl_files()
    num_batches = len(file_map)

    # Step 2: Load or initialize state
    state = load_state()
    for idx in file_map:
        key = str(idx)
        if key not in state:
            state[key] = {
                "jsonl_file":       file_map[idx],
                "batch_id":         None,
                "status":           "pending_submission",
                "retries":          0,
                "result_collected": False,
            }
    save_state(state)

    # Step 3: Collect results from any batches already completed in a prior run
    already_done = [k for k, v in state.items()
                    if v["status"] == "completed" and v.get("result_collected", False)]
    if already_done:
        print(f"Resuming: collecting {len(already_done)} previously completed batch(es)...")
    for key in already_done:
        result_df, _, _ = parse_batch_result(state[key]["batch_id"], track_tokens=False)
        if result_df is not None:
            all_results.append(result_df)
            print(f"  Batch {key}: {len(result_df)} rows loaded from prior run")

    print(f"\nStarting token-aware submission loop ({num_batches} total batches)\n")

    # Step 4: Token-aware submission + polling loop
    while True:
        terminal    = {"completed", "abandoned"}
        not_done    = [k for k, v in state.items() if v["status"] not in terminal]
        if not not_done:
            print("All batches complete.")
            break

        # ── Poll all in-flight batches ─────────────────────────────────────────
        in_flight = [k for k, v in state.items() if v["status"] in active_statuses]
        for key in in_flight:
            info = state[key]
            try:
                job        = client.batches.retrieve(info["batch_id"])
                api_status = job.status
            except Exception as e:
                print(f"  Error polling batch {key}: {e}")
                continue

            if api_status in ("queued", "in_progress", "validating"):
                state[key]["status"] = api_status
                print(f"  Batch {key} ({info['batch_id']}): {api_status}")

            elif api_status == "completed":
                print(f"  Batch {key} completed — downloading results...")
                result_df, in_tok, out_tok = parse_batch_result(info["batch_id"], track_tokens=True)
                if result_df is not None:
                    all_results.append(result_df)
                    total_in_tok  += in_tok
                    total_out_tok += out_tok
                    state[key]["status"]           = "completed"
                    state[key]["result_collected"] = True
                    print(f"    {len(result_df)} rows | {in_tok:,} input / {out_tok:,} output tokens")
                else:
                    # Treat parse failure like a batch failure so it can be retried
                    state[key]["status"] = "failed"

            elif api_status in ("failed", "cancelled", "expired"):
                retries = info.get("retries", 0)
                if retries < MAX_RETRIES:
                    print(f"  Batch {key} {api_status} — retrying ({retries + 1}/{MAX_RETRIES})...")
                    new_id = submit_batch(info["jsonl_file"])
                    if new_id:
                        state[key]["batch_id"] = new_id
                        state[key]["status"]   = "submitted"
                        state[key]["retries"]  = retries + 1
                    else:
                        print(f"    Resubmission failed — will retry next cycle")
                else:
                    print(f"  Batch {key} abandoned after {MAX_RETRIES} retries.")
                    state[key]["status"] = "abandoned"

        save_state(state)

        # ── Submit pending batches within token budget ─────────────────────────
        enqueued_tokens = estimate_enqueued_tokens(state)
        pending         = [k for k, v in state.items() if v["status"] == "pending_submission"]

        for key in pending:
            tokens_this_batch = MAX_REQUESTS_PER_BATCH * TOKENS_PER_PROMPT
            if enqueued_tokens + tokens_this_batch > BATCH_TOKEN_QUEUE_LIMIT:
                print(f"  Token queue near limit ({enqueued_tokens:,} / {BATCH_TOKEN_QUEUE_LIMIT:,}) — holding submission")
                break

            print(f"  Submitting batch {key}: {state[key]['jsonl_file']}")
            batch_id = submit_batch(state[key]["jsonl_file"])
            if batch_id:
                state[key]["batch_id"] = batch_id
                state[key]["status"]   = "submitted"
                enqueued_tokens       += tokens_this_batch
                print(f"    Submitted as {batch_id} | enqueued tokens ~{enqueued_tokens:,}")
            else:
                print(f"    Submission failed for batch {key} — will retry next cycle")

        save_state(state)

        # ── Cost update ────────────────────────────────────────────────────────
        cost_so_far = (total_in_tok * INPUT_COST_PER_TOKEN) + (total_out_tok * OUTPUT_COST_PER_TOKEN)
        print(f"\n  Tokens this run: {total_in_tok:,} in / {total_out_tok:,} out | "
              f"Cost so far: ${cost_so_far:.4f}\n")

        # ── Sleep before next cycle ────────────────────────────────────────────
        still_active = any(v["status"] in active_statuses | {"pending_submission"}
                           for v in state.values())
        if still_active:
            print(f"  Sleeping {POLL_INTERVAL}s...\n")
            time.sleep(POLL_INTERVAL)

    # ── Compile and save results ───────────────────────────────────────────────
    if all_results:
        df_birth       = pd.concat(all_results, ignore_index=True)
        df_birth["id"] = df_birth["id"].astype(str)
    else:
        df_birth = pd.DataFrame(columns=["id", "birth_flag", "days_from_birth",
                                          "confidence", "p_female", "p_male"])

    df_all = df[["id"]].copy()
    df_all = df_all.merge(df_birth, on="id", how="left")
    df_all["birth_flag"]      = df_all["birth_flag"].fillna(-99).astype(int)
    df_all["days_from_birth"] = df_all["days_from_birth"].fillna(-999).astype(int)
    df_all["confidence"]      = df_all["confidence"].fillna(0).astype(int)
    df_all["p_female"]        = df_all["p_female"].fillna(50).astype(int)
    df_all["p_male"]          = df_all["p_male"].fillna(50).astype(int)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df_all.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"\nResults saved to: {OUTPUT_PATH}")

    # ── Update cost log ────────────────────────────────────────────────────────
    run_cost = (total_in_tok * INPUT_COST_PER_TOKEN) + (total_out_tok * OUTPUT_COST_PER_TOKEN)
    cost_log["total_input_tokens"]  += total_in_tok
    cost_log["total_output_tokens"] += total_out_tok
    cost_log["total_cost_usd"]      += run_cost
    cost_log["runs"].append({
        "timestamp":     time.strftime("%Y-%m-%d %H:%M:%S"),
        "input_tokens":  total_in_tok,
        "output_tokens": total_out_tok,
        "cost_usd":      round(run_cost, 6),
        "runtime_s":     round(time.time() - run_start, 1),
    })
    save_cost_log(cost_log)

    # ── Summary ────────────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total records:              {len(df_all):,}")
    print(f"Input tokens (this run):    {total_in_tok:,}")
    print(f"Output tokens (this run):   {total_out_tok:,}")
    print(f"Cost (this run):            ${run_cost:.4f}")
    print(f"Cumulative cost (all runs): ${cost_log['total_cost_usd']:.4f}")

    print(f"\nBirth flag predictions:")
    print(f"  Within 14-day window (1):  {(df_all['birth_flag'] == 1).sum():,}")
    print(f"  Outside window / none (0): {(df_all['birth_flag'] == 0).sum():,}")
    print(f"  Uncertain (-99):           {(df_all['birth_flag'] == -99).sum():,}")

    flagged = df_all[df_all["birth_flag"] == 1]
    if len(flagged) > 0:
        print(f"\nDays from birth (flagged posts only):")
        print(f"  Prenatal  (< 0): {(flagged['days_from_birth'] < 0).sum():,}")
        print(f"  Day of    (= 0): {(flagged['days_from_birth'] == 0).sum():,}")
        print(f"  Postnatal (> 0): {(flagged['days_from_birth'] > 0).sum():,}")
        print(f"  Mean days_from_birth: {flagged['days_from_birth'].mean():.1f}")

    print(f"\nConfidence distribution:")
    print(f"  No confidence (0): {(df_all['confidence'] == 0).sum():,}")
    print(f"  Low (1-39):        {((df_all['confidence'] >= 1)  & (df_all['confidence'] < 40)).sum():,}")
    print(f"  Medium (40-89):    {((df_all['confidence'] >= 40) & (df_all['confidence'] < 90)).sum():,}")
    print(f"  High (90-100):     {(df_all['confidence'] >= 90).sum():,}")

    print(f"\nPoster gender distribution:")
    print(f"  Likely female (p_female > 50): {(df_all['p_female'] > 50).sum():,}")
    print(f"  Likely male   (p_male   > 50): {(df_all['p_male']   > 50).sum():,}")
    print(f"  Uncertain     (p_female = 50): {(df_all['p_female'] == 50).sum():,}")


if __name__ == "__main__":
    main()
