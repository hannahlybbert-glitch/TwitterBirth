# Author: Hannah Lybbert
# Created: 2026-07-01
# Purpose: LLM classification of anniversary seed tweets — filter to personal anniversary posts
#          near the date of the couple's anniversary (not third-party or retweeted content).
#          Output feeds into get_user_profiles.py (only classified positives are profiled).

import os
import sys
import openai
import pandas as pd
import json
import time
import re
import glob
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# --- Config ---
TEST_MODE   = True
FILTER_NAME = "anniversary"

_base_seed  = f"ControlGroup/data/1_seed_tweets/{FILTER_NAME}"
INPUT_PATH  = f"{_base_seed}/test/candidate_pool_CLEAN.csv" if TEST_MODE else f"{_base_seed}/candidate_pool_CLEAN.csv"

_base_out   = "ControlGroup/data/LLM/seed_tweets/test" if TEST_MODE else "ControlGroup/data/LLM/seed_tweets"
OUTPUT_PATH = f"{_base_out}/anniversary_tweets_classified_test.csv" if TEST_MODE else f"{_base_out}/anniversary_tweets_classified.csv"

_json_dir   = "ControlGroup/data/LLM/json"

# Constants
TOKENS_PER_PROMPT      = 500
ENQUEUED_TOKEN_LIMIT   = 100_000_000
MAX_REQUESTS_PER_BATCH = int(ENQUEUED_TOKEN_LIMIT * 0.98 // TOKENS_PER_PROMPT)
MAX_RETRIES            = 2
MAX_CHARS              = 1000

# Load input
df = pd.read_csv(INPUT_PATH)
assert "tweet_id" in df.columns, "tweet_id column must exist in input data"
assert df["tweet_id"].notna().all(), "tweet_id must not have missing values"
df["tweet_id"] = df["tweet_id"].astype(str)


############################# HELPER FUNCTIONS #############################

def clear_old_batches(task_name):
    jsonl_files = glob.glob(f"{_json_dir}/batch_requests_{task_name}_*.jsonl")
    for file in jsonl_files:
        os.remove(file)

    batch_ids_path = f"{_json_dir}/batch_ids_{task_name}.json"
    if os.path.exists(batch_ids_path):
        os.remove(batch_ids_path)

    print(f"Cleared {len(jsonl_files)} old batch files and batch IDs for task: {task_name}")


def sanitize_text(text):
    if pd.isna(text):
        return ""
    text = str(text)
    text = text.replace('\x00', '').replace('\r', ' ').replace('\n', ' ')
    if len(text) > MAX_CHARS:
        half = MAX_CHARS // 2
        text = text[:half] + " ... " + text[-half:]
    return text.strip()


def create_jsonl_files(task_name, prompt_function, input_columns):
    os.makedirs(_json_dir, exist_ok=True)
    clear_old_batches(task_name)
    batch_index = 0

    for start in range(0, len(df), MAX_REQUESTS_PER_BATCH):
        batch_df       = df.iloc[start:start + MAX_REQUESTS_PER_BATCH].copy()
        jsonl_filename = f"{_json_dir}/batch_requests_{task_name}_batch_{batch_index}.jsonl"

        with open(jsonl_filename, "w", encoding="utf-8") as f:
            for _, row in batch_df.iterrows():
                text_val = sanitize_text(row.get("text", ""))
                if not text_val:
                    continue
                input_data = {col: sanitize_text(row.get(col, "")) for col in input_columns}
                prompt = prompt_function(row["tweet_id"], **input_data)
                f.write(json.dumps(prompt, ensure_ascii=False) + "\n")

        print(f"Created JSONL: {jsonl_filename} ({len(batch_df)} requests)")
        batch_index += 1


############################# PROMPT #############################

def get_anniversary_prompt(tweet_id, text):
    text = text or ""

    return {
        "custom_id": str(tweet_id),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Classify this tweet: is the author celebrating their own romantic "
                        "(wedding or dating) anniversary right now (today) or clearly within "
                        "1 month of the post?\n\n"

                        "Use verb tense and timing as signals: present/present-continuous tense "
                        "describing the anniversary happening or being spent now = Flag 1. "
                        "If a specific date/timeframe is given (e.g. \"in 18 days\", \"next week\", "
                        "\"on the 12th\") and it falls within 1 month, treat as Flag 1 even if future "
                        "tense. If timing is vague (\"weekend\", \"soon\", \"can't wait\") with no "
                        "stated date, or the date is more than 1 month away, treat as Flag 0.\n\n"

                        "Flag 1 examples:\n"
                        "- \"Happy anniversary [partner]!\"\n"
                        "- \"Date with babe for our anniversary\"\n"
                        "- \"25 years with my beautiful wife!\"\n"
                        "- \"Our anniversary is in 18 days\" (specific date, within 1 month)\n\n"

                        "Flag 0 examples:\n"
                        "- \"So excited for our anniversary weekend\" (vague timing)\n"
                        "- \"No idea what to get my husband/bf for our anniversary\" or \"Booked reservation for our anniversary\" (planning)\n"
                        "- \"This is my anniversary present to us\" (ambiguous timing, gift-focused)\n"
                        "- \"Our anniversary is in 3 months\" (specific date, beyond 1 month)\n"
                        "- Third party, business, or non-romantic anniversary\n"
                        "- Manual quoted-retweet pattern (\"@user: ...\")\n\n"

                        "When uncertain, flag 0.\n\n"

                        "Respond on exactly two lines:\n"
                        "1: anniversary_flag (1 or 0)\n"
                        "2: confidence (0–100)"
                    )
                },
                # {
                #     "role": "system",
                #     "content": (
                #         "Classify this tweet: is the author marking their own romantic (wedding or dating) anniversary?\n\n"

                #         "Flag 1 if:\n"
                #         "- Author celebrates their own anniversary with their partner\n"
                #         "  Examples: (\"happy anniversary [partner]\", \"our anniversary\", \"X years married/together\")\n\n"

                #         "Flag 0 if:\n"
                #         "- Subject is a third party (friend, family, business, event, show, etc.)\n"
                #         "- Non-romantic anniversary (job, business, show, etc.)\n"
                #         "- Manual quoted-retweet pattern (\"@user: ...\")\n"
                #         "- More than ~1 month from the anniversary date\n\n"

                #         "Respond on exactly two lines:\n"
                #         "1: anniversary_flag (1 or 0)\n"
                #         "2: confidence (0–100)"
                #     )
                # },
                {
                    "role": "user",
                    "content": (
                        f"Tweet: {text}\n\n"
                        "[anniversary_flag]\n"
                        "[confidence]"
                    )
                }
            ]
        }
    }


############################# BATCH PROCESSING #############################

def submit_batch_job(jsonl_filename):
    try:
        file_upload = client.files.create(file=open(jsonl_filename, "rb"), purpose="batch")
        file_id     = file_upload.id
        response    = client.batches.create(
            input_file_id=file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        return response.id
    except Exception as e:
        print(f"Error submitting batch job for {jsonl_filename}: {e}")
        return None


def check_batch_status(batch_id, task_name):
    while True:
        try:
            job_status = client.batches.retrieve(batch_id)
            status     = job_status.status
            print(f"[{task_name}] Batch {batch_id} status: {status}")
            if status in ["completed", "failed", "cancelled"]:
                return status
            time.sleep(30)
        except Exception as e:
            print(f"Error checking status: {e}")
            return None


def parse_anniversary_result(batch_id):
    try:
        batch_info     = client.batches.retrieve(batch_id)
        output_file_id = batch_info.output_file_id
        if not output_file_id:
            print(f"No output file for batch {batch_id}")
            return None

        file_response = client.files.content(output_file_id)
        results       = file_response.text

        parsed = []

        for line in results.splitlines():
            response  = json.loads(line)
            tweet_id  = str(response.get("custom_id"))
            content   = response.get("response", {}).get("body", {}).get("choices", [])[0]["message"]["content"].strip()

            lines      = content.splitlines()
            flag_match = re.search(r":\s*(-?\d+)", lines[0]) if len(lines) > 0 else None
            conf_match = re.search(r":\s*(\d+)",   lines[1]) if len(lines) > 1 else None

            parsed.append({
                "tweet_id":         tweet_id,
                "anniversary_flag": int(flag_match.group(1)) if flag_match else -99,
                "confidence":       int(conf_match.group(1)) if conf_match else 0,
            })

        return pd.DataFrame(parsed)

    except Exception as e:
        print(f"Error parsing anniversary results: {e}")
        return None


def load_batch_ids(path):
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}


def save_batch_id(path, batch_index, batch_id):
    ids = load_batch_ids(path)
    ids[str(batch_index)] = batch_id
    with open(path, "w") as f:
        json.dump(ids, f, indent=2)
    print(f"Saved batch ID {batch_id} for batch index {batch_index}")


def submit_and_process_batches(task_name):
    batch_index    = 0
    all_results    = []
    batch_ids_path = f"{_json_dir}/batch_ids_{task_name}.json"
    existing_ids   = load_batch_ids(batch_ids_path)

    while True:
        jsonl_filename = f"{_json_dir}/batch_requests_{task_name}_batch_{batch_index}.jsonl"
        if not os.path.exists(jsonl_filename):
            break

        if str(batch_index) in existing_ids:
            batch_id = existing_ids[str(batch_index)]
            print(f"Resuming batch {batch_index} with existing ID {batch_id}")
        else:
            print(f"Submitting batch {batch_index}")
            batch_id = submit_batch_job(jsonl_filename)
            if batch_id:
                save_batch_id(batch_ids_path, batch_index, batch_id)

        if batch_id:
            retries = 0
            while retries <= MAX_RETRIES:
                status = check_batch_status(batch_id, task_name)
                if status == "completed":
                    result_df = parse_anniversary_result(batch_id)
                    if result_df is not None:
                        all_results.append(result_df)
                    break
                elif status == "failed":
                    retries += 1
                    if retries <= MAX_RETRIES:
                        print(f"Batch {batch_id} failed — retrying ({retries}/{MAX_RETRIES})...")
                        batch_id = submit_batch_job(jsonl_filename)
                        if batch_id:
                            save_batch_id(batch_ids_path, batch_index, batch_id)
                    else:
                        print(f"Batch {batch_id} failed after {MAX_RETRIES} retries — skipping.")
                    break
                else:
                    break

        batch_index += 1

    if all_results:
        final_df             = pd.concat(all_results, ignore_index=True)
        final_df["tweet_id"] = final_df["tweet_id"].astype(str)
        return final_df
    else:
        return pd.DataFrame(columns=["tweet_id", "anniversary_flag", "confidence"])


############################# MAIN #############################

def main():
    create_jsonl_files("anniversary", get_anniversary_prompt, ["text"])

    df_anniversary = submit_and_process_batches("anniversary")

    print(df_anniversary.head())
    print(df_anniversary["anniversary_flag"].value_counts(dropna=False))

    # Merge classification results back onto full input so all rows are represented
    df_all = df.copy()
    df_all = df_all.merge(df_anniversary[["tweet_id", "anniversary_flag", "confidence"]], on="tweet_id", how="left")
    df_all["anniversary_flag"] = df_all["anniversary_flag"].fillna(-99).astype(int)
    df_all["confidence"]       = df_all["confidence"].fillna(0).astype(int)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df_all.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"Results saved to: {OUTPUT_PATH}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total records: {len(df_all):,}")
    print(f"\nAnniversary flag predictions:")
    print(f"  - Personal anniversary (1):  {(df_all['anniversary_flag'] == 1).sum():,}")
    print(f"  - Not personal       (0):    {(df_all['anniversary_flag'] == 0).sum():,}")
    print(f"  - Uncertain          (-99):  {(df_all['anniversary_flag'] == -99).sum():,}")
    print(f"\nConfidence distribution:")
    print(f"  - No confidence (0):  {(df_all['confidence'] == 0).sum():,}")
    print(f"  - Low (1-39):         {((df_all['confidence'] >= 1)  & (df_all['confidence'] < 40)).sum():,}")
    print(f"  - Medium (40-89):     {((df_all['confidence'] >= 40) & (df_all['confidence'] < 90)).sum():,}")
    print(f"  - High (90-100):      {(df_all['confidence'] >= 90).sum():,}")


if __name__ == "__main__":
    main()
