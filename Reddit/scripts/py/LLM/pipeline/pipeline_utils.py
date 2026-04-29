# Author: Hannah Lybbert
# Created: 2026-03-26
# Updated: 2026-03-26
# Purpose: Shared API helper functions for 2-stage GPT-4o-mini → GPT-4o birth detection pipeline

import os
import json
import time
import re
import glob
import pandas as pd
from pathlib import Path

MAX_CHARS = 3000

SYSTEM_PROMPT = (
    "Classify a Reddit post on two tasks:\n\n"

    "TASK 1 — BIRTH FLAG\n"
    "Did the author post within 21 days before or after birth?\n\n"

    "VALID subjects: the author or their spouse/partner only.\n"
    "INVALID: any other person — sister, mother, friend, aunt, etc.\n\n"

    "STRICT RULE:\n"
    "Only flag 1 if there is CLEAR and EXPLICIT timing evidence placing the post between:\n"
    "- 36+ weeks pregnant\n"
    "- OR 0–21 days postpartum\n"
    "Do NOT guess or infer timing.\n\n"

    "TIMING SIGNALS (use only these):\n\n"

    "Pregnancy:\n"
    "- 'X weeks pregnant' → only if X ≥ 36\n"
    "- 'X+Y weeks' means X weeks and Y days (e.g., 39+2 = 39 weeks 2 days)\n\n"

    "Postpartum:\n"
    "- Y days postpartum / pp\n"
    "- X weeks postpartum\n"
    "- baby is Y days or X weeks old\n\n"

    "days_from_birth rules:\n"
    "- X weeks pregnant → (X−40)*7\n"
    "- X+Y weeks → ((X−40)*7) − Y\n"
    "- Y postpartum days → Y\n"
    "- X postpartum weeks → X*7\n"
    "- baby is Y days old → Y\n"
    "- baby is X weeks old → X*7\n\n"

    "Flag 1 only if −21 ≤ days_from_birth ≤ 21.\n\n"

    "IMPORTANT OUT-OF-WINDOW RULES:\n"
    "If timing explicitly indicates the baby is older than 21 days, return 0.\n\n"

    "Examples of OUTSIDE the window:\n"
    "- X months postpartum\n"
    "- X month old baby\n"
    "- X years old\n"
    "- toddler, infant, older baby\n"
    "- example. 8 months pp\n"
    "These are NOT within the birth window.\n\n"

    "Do NOT convert months to weeks or days.\n"
    "If months are mentioned, assume timing is outside the window unless days or weeks are explicitly given.\n"
    "If postpartum timing is greater than 2 weeks, return 0 even if strong birth indicators are present.\n\n"

    "Other STRONG birth indicators:\n"
    "- Water breaking or active labor or contractions where delivery is imminent\n"
    "- Birth story or recent delivery\n"
    "- NICU or preterm birth when birth clearly just occurred\n\n"

    "If pregnancy is mentioned but weeks < 36 → return 0.\n"
    "If no birth or pregnancy content, or if timing is out of birth window → return 0.\n\n"

    "Before answering, briefly reason internally:\n"
    "1. Who is the subject?\n"
    "2. Is there explicit timing?\n"
    "3. Is timing within the window?\n\n"

    "TASK 2 — POSTER GENDER\n"
    "Return probabilities (0–100 each, sum = 100).\n\n"

    "Strong female:\n"
    "- Pregnant, postpartum, gave birth, in labor, contractions, breastfeeding, nursing\n"
    "- Becoming a mother or mom\n\n"

    "Strong male:\n"
    "- Becoming a father or dad\n"
    "- Wife/girlfriend pregnant or postpartum\n\n"

    "If no signals → 50/50.\n\n"

    "Respond on exactly five lines:\n"
    "1: birth_flag (1, 0, or -99)\n"
    "2: days_from_birth (integer or -999)\n"
    "3: confidence (0–100)\n"
    "4: p_female\n"
    "5: p_male"
)


def sanitize_text(text):
    if pd.isna(text):
        return ""
    text = str(text).replace('\x00', '').replace('\r', ' ').replace('\n', ' ').strip()
    if len(text) > MAX_CHARS:
        half = MAX_CHARS // 2
        text = text[:half] + " ... " + text[-half:]
    return text


def get_birth_prompt(post_id, title, selftext, model):
    return {
        "custom_id": str(post_id),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": (
                        f"Title: {title}\n\n"
                        f"Post: {selftext}\n\n"
                        "[birth_flag]\n"
                        "[days_from_birth]\n"
                        "[confidence]\n"
                        "[p_female]\n"
                        "[p_male]"
                    )
                }
            ]
        }
    }


def clear_old_batches(task_name, json_dir):
    jsonl_files = glob.glob(str(json_dir / f"batch_requests_{task_name}_*.jsonl"))
    for f in jsonl_files:
        os.remove(f)
    batch_ids_path = json_dir / f"batch_ids_{task_name}.json"
    if batch_ids_path.exists():
        batch_ids_path.unlink()
    print(f"Cleared {len(jsonl_files)} old JSONL files for task: {task_name}")


def create_jsonl_files(df, task_name, model, max_requests_per_batch, json_dir):
    json_dir.mkdir(parents=True, exist_ok=True)
    clear_old_batches(task_name, json_dir)
    batch_index = 0

    for start in range(0, len(df), max_requests_per_batch):
        batch_df       = df.iloc[start:start + max_requests_per_batch].copy()
        jsonl_filename = json_dir / f"batch_requests_{task_name}_batch_{batch_index}.jsonl"

        with open(jsonl_filename, "w", encoding="utf-8") as f:
            for _, row in batch_df.iterrows():
                title_val    = sanitize_text(row.get("title",    ""))
                selftext_val = sanitize_text(row.get("selftext", ""))
                if not title_val and not selftext_val:
                    continue
                prompt = get_birth_prompt(row["id"], title_val, selftext_val, model)
                f.write(json.dumps(prompt, ensure_ascii=False) + "\n")

        print(f"  Created JSONL: {jsonl_filename.name} ({len(batch_df):,} requests)")
        batch_index += 1


def submit_batch_job(client, jsonl_filename):
    try:
        file_upload = client.files.create(file=open(jsonl_filename, "rb"), purpose="batch")
        response    = client.batches.create(
            input_file_id=file_upload.id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        return response.id
    except Exception as e:
        print(f"Error submitting batch job for {jsonl_filename}: {e}")
        return None


def check_batch_status(client, batch_id, task_name):
    while True:
        try:
            job_status = client.batches.retrieve(batch_id)
            status     = job_status.status
            print(f"  [{task_name}] Batch {batch_id} status: {status}")
            if status in ["completed", "failed", "cancelled"]:
                return status
            time.sleep(30)
        except Exception as e:
            print(f"  Error checking status: {e}")
            return None


def parse_birth_result(client, batch_id):
    try:
        batch_info     = client.batches.retrieve(batch_id)
        output_file_id = batch_info.output_file_id
        if not output_file_id:
            print(f"  No output file for batch {batch_id}")
            return None

        results = client.files.content(output_file_id).text
        parsed  = []

        for line in results.splitlines():
            response = json.loads(line)
            post_id  = str(response.get("custom_id"))
            content  = response.get("response", {}).get("body", {}).get("choices", [])[0]["message"]["content"].strip()
            lines    = content.splitlines()

            flag_match = re.search(r":\s*(-?\d+)", lines[0]) if len(lines) > 0 else None
            days_match = re.search(r":\s*(-?\d+)", lines[1]) if len(lines) > 1 else None
            conf_match = re.search(r":\s*(\d+)",   lines[2]) if len(lines) > 2 else None
            fem_match  = re.search(r":\s*(\d+)",   lines[3]) if len(lines) > 3 else None
            mal_match  = re.search(r":\s*(\d+)",   lines[4]) if len(lines) > 4 else None

            parsed.append({
                "id":              post_id,
                "birth_flag":      int(flag_match.group(1)) if flag_match else -99,
                "days_from_birth": int(days_match.group(1)) if days_match else -999,
                "confidence":      int(conf_match.group(1)) if conf_match else 0,
                "p_female":        int(fem_match.group(1))  if fem_match  else 50,
                "p_male":          int(mal_match.group(1))  if mal_match  else 50,
            })

        return pd.DataFrame(parsed)

    except Exception as e:
        print(f"  Error parsing results: {e}")
        return None


def load_batch_ids(path):
    if path.exists():
        with open(path, "r") as f:
            return json.load(f)
    return {}


def save_batch_id(path, batch_index, batch_id):
    ids = load_batch_ids(path)
    ids[str(batch_index)] = batch_id
    with open(path, "w") as f:
        json.dump(ids, f, indent=2)


def run_batch_pipeline(client, df, task_name, model, max_requests_per_batch, json_dir, max_retries=2):
    """
    Full pipeline: create JSONL → submit batches → wait → parse results.
    Returns a DataFrame of all results with columns:
    id, birth_flag, days_from_birth, confidence, p_female, p_male
    """
    create_jsonl_files(df, task_name, model, max_requests_per_batch, json_dir)

    batch_ids_path = json_dir / f"batch_ids_{task_name}.json"
    existing_ids   = load_batch_ids(batch_ids_path)
    all_results    = []
    batch_index    = 0

    while True:
        jsonl_filename = json_dir / f"batch_requests_{task_name}_batch_{batch_index}.jsonl"
        if not jsonl_filename.exists():
            break

        if str(batch_index) in existing_ids:
            batch_id = existing_ids[str(batch_index)]
            print(f"  Resuming API batch {batch_index} with existing ID {batch_id}")
        else:
            print(f"  Submitting API batch {batch_index}...")
            batch_id = submit_batch_job(client, jsonl_filename)
            if batch_id:
                save_batch_id(batch_ids_path, batch_index, batch_id)

        if batch_id:
            retries = 0
            while retries <= max_retries:
                status = check_batch_status(client, batch_id, task_name)
                if status == "completed":
                    result_df = parse_birth_result(client, batch_id)
                    if result_df is not None:
                        all_results.append(result_df)
                    break
                elif status == "failed":
                    retries += 1
                    if retries <= max_retries:
                        print(f"  Batch failed — retrying ({retries}/{max_retries})...")
                        batch_id = submit_batch_job(client, jsonl_filename)
                        if batch_id:
                            save_batch_id(batch_ids_path, batch_index, batch_id)
                    else:
                        print(f"  Batch failed after {max_retries} retries — skipping.")
                    break
                else:
                    break

        batch_index += 1

    if all_results:
        final_df    = pd.concat(all_results, ignore_index=True)
        final_df["id"] = final_df["id"].astype(str)
        # Fill any missing rows
        df_out      = df[["id"]].copy().astype(str)
        df_out      = df_out.merge(final_df, on="id", how="left")
        df_out["birth_flag"]      = df_out["birth_flag"].fillna(-99).astype(int)
        df_out["days_from_birth"] = df_out["days_from_birth"].fillna(-999).astype(int)
        df_out["confidence"]      = df_out["confidence"].fillna(0).astype(int)
        df_out["p_female"]        = df_out["p_female"].fillna(50).astype(int)
        df_out["p_male"]          = df_out["p_male"].fillna(50).astype(int)
        return df_out
    else:
        return pd.DataFrame(columns=["id", "birth_flag", "days_from_birth", "confidence", "p_female", "p_male"])
