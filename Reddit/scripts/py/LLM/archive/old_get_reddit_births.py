# Author: Hannah Lybbert
# Created: 02/20/2026
# Updated: 02/25/2026
# Purpose: Detect birth window posts in Reddit data using OpenAI batch API

import os
import openai
import pandas as pd
import json
import time
import re
import glob
from dotenv import load_dotenv

# Set working directory
os.chdir("D:/TwitterBirth")

# Load API key
load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# File paths
# INPUT_PATH  = "Reddit/data/intermediate/cleaned_raw/reddit_cleaned_2006_to_2018.csv"
INPUT_PATH  = "Reddit/data/intermediate/cleaned_raw/test_samples/reddit_test_100_sample.csv"
# OUTPUT_PATH = "Reddit/data/LLM/birth_detection.csv"
OUTPUT_PATH = "Reddit/data/LLM/test_samples/birth_detection_100_T3.csv"


# Constants
TOKENS_PER_PROMPT      = 500         # estimate for birth detection prompt
ENQUEUED_TOKEN_LIMIT   = 2_000_000   # depends on account tier and model used
MAX_REQUESTS_PER_BATCH = ENQUEUED_TOKEN_LIMIT // TOKENS_PER_PROMPT
MAX_RETRIES            = 2
MAX_CHARS              = 3000        # to keep prompts concise and avoid encoding issues

# Load DataFrame
df = pd.read_csv(INPUT_PATH, encoding="utf-8", low_memory=False)
# df = df.iloc[0:100].copy()  # for testing

assert "id" in df.columns, "id column must exist in input data"
assert df["id"].notna().all(), "id column must not have missing values"
df["id"] = df["id"].astype(str)


############################# HELPER FUNCTIONS #############################

def clear_old_batches(task_name):
    jsonl_files = glob.glob(f"Reddit/data/json/batch_requests_{task_name}_*.jsonl")
    for file in jsonl_files:
        os.remove(file)
    print(f"Cleared {len(jsonl_files)} old batch files for task: {task_name}")

def sanitize_text(text):
    """Clean text to avoid JSON encoding issues."""
    if pd.isna(text):
        return ""
    text = str(text)
    text = text.replace('\x00', '').replace('\r', ' ').replace('\n', ' ')
    # if len(text) > 2000:
    #     text = text[:2000]
    # return text.strip()
    if len(text) > MAX_CHARS:
        half = MAX_CHARS // 2
        text = text[:half] + " ... " + text[-half:]
    return text.strip()

def create_jsonl_files(task_name, prompt_function, input_columns):
    os.makedirs("Reddit/data/json", exist_ok=True)
    clear_old_batches(task_name)
    batch_index = 0

    for start in range(0, len(df), MAX_REQUESTS_PER_BATCH):
        batch_df       = df.iloc[start:start + MAX_REQUESTS_PER_BATCH].copy()
        jsonl_filename = f"Reddit/data/json/batch_requests_{task_name}_batch_{batch_index}.jsonl"

        with open(jsonl_filename, "w", encoding="utf-8") as f:
            for _, row in batch_df.iterrows():
                title_val    = sanitize_text(row.get("title",    ""))
                selftext_val = sanitize_text(row.get("selftext", ""))
                if not title_val and not selftext_val:
                    continue
                input_data = {col: sanitize_text(row.get(col, "")) for col in input_columns}
                prompt = prompt_function(row["id"], **input_data)
                f.write(json.dumps(prompt, ensure_ascii=False) + "\n")

        print(f"Created JSONL: {jsonl_filename} ({len(batch_df)} requests)")
        batch_index += 1


############################# PROMPT #############################

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


############################# BATCH PROCESSING #############################

# Submits batch job to OpenAI API
def submit_batch_job(jsonl_filename):
    try:
        file_upload = client.files.create(file=open(jsonl_filename, "rb"), purpose="batch")
        file_id = file_upload.id
        response = client.batches.create(
            input_file_id=file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )
        return response.id
    except Exception as e:
        print(f"Error submitting batch job for {jsonl_filename}: {e}")
        return None

# Checks the status of current batch every 30 seconds
def check_batch_status(batch_id, task_name):
    while True:
        try:
            job_status = client.batches.retrieve(batch_id)
            status = job_status.status
            print(f"[{task_name}] Batch {batch_id} status: {status}")
            if status in ["completed", "failed", "cancelled"]:
                return status
            time.sleep(30)
        except Exception as e:
            print(f"Error checking status: {e}")
            return None

# Retrieves birth detection results from OpenAI batch output
def parse_birth_result(batch_id):
    try:
        batch_info = client.batches.retrieve(batch_id)
        output_file_id = batch_info.output_file_id
        if not output_file_id:
            print(f"No output file for batch {batch_id}")
            return None

        file_response = client.files.content(output_file_id)
        results = file_response.text

        parsed = []
        for line in results.splitlines():
            response = json.loads(line)
            post_id  = str(response.get("custom_id"))
            content  = response.get("response", {}).get("body", {}).get("choices", [])[0]["message"]["content"].strip()
            lines    = content.splitlines()

            flag_match      = re.search(r"^(-?\d+)", lines[0]) if len(lines) > 0 else None
            days_match      = re.search(r"^(-?\d+)", lines[1]) if len(lines) > 1 else None
            conf_match      = re.search(r"^(\d+)",   lines[2]) if len(lines) > 2 else None
            fem_match       = re.search(r"^(\d+)",   lines[3]) if len(lines) > 3 else None
            mal_match       = re.search(r"^(\d+)",   lines[4]) if len(lines) > 4 else None

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
        print(f"Error parsing birth results: {e}")
        return None

BATCH_IDS_PATH = "Reddit/data/json/batch_ids_birth.json"

def load_batch_ids():
    if os.path.exists(BATCH_IDS_PATH):
        with open(BATCH_IDS_PATH, "r") as f:
            return json.load(f)
    return {}

def save_batch_id(batch_index, batch_id):
    ids = load_batch_ids()
    ids[str(batch_index)] = batch_id
    with open(BATCH_IDS_PATH, "w") as f:
        json.dump(ids, f, indent=2)
    print(f"Saved batch ID {batch_id} for batch index {batch_index}")

def submit_and_process_batches(task_name):
    batch_index  = 0
    all_results  = []
    existing_ids = load_batch_ids()

    while True:
        jsonl_filename = f"Reddit/data/json/batch_requests_{task_name}_batch_{batch_index}.jsonl"
        if not os.path.exists(jsonl_filename):
            break

        # Reuse existing batch ID if already submitted (avoids double-submission on resume)
        if str(batch_index) in existing_ids:
            batch_id = existing_ids[str(batch_index)]
            print(f"Resuming batch {batch_index} with existing ID {batch_id}")
        else:
            print(f"Submitting batch {batch_index}")
            batch_id = submit_batch_job(jsonl_filename)
            if batch_id:
                save_batch_id(batch_index, batch_id)

        if batch_id:
            retries = 0
            while retries <= MAX_RETRIES:
                status = check_batch_status(batch_id, task_name)
                if status == "completed":
                    result_df = parse_birth_result(batch_id)
                    if result_df is not None:
                        all_results.append(result_df)
                    break
                elif status == "failed":
                    retries += 1
                    if retries <= MAX_RETRIES:
                        print(f"Batch {batch_id} failed — retrying ({retries}/{MAX_RETRIES})...")
                        batch_id = submit_batch_job(jsonl_filename)
                        if batch_id:
                            save_batch_id(batch_index, batch_id)
                    else:
                        print(f"Batch {batch_id} failed after {MAX_RETRIES} retries — skipping.")
                    break
                else:
                    break

        batch_index += 1

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        final_df["id"] = final_df["id"].astype(str)
        return final_df
    else:
        return pd.DataFrame(columns=["id", "birth_flag", "days_from_birth", "confidence", "p_female", "p_male"])


# Run all of the functions
def main():
    # Create JSONL files
    create_jsonl_files("birth", get_birth_prompt, ["title", "selftext"])

    # Submit and process results
    df_birth = submit_and_process_batches("birth")

    # Merge back to original df so all rows are represented
    df_all = df[["id"]].copy()
    df_all = df_all.merge(df_birth, on="id", how="left")

    # Fill missing predictions (rows skipped due to empty content)
    df_all["birth_flag"]      = df_all["birth_flag"].fillna(-99).astype(int)
    df_all["days_from_birth"] = df_all["days_from_birth"].fillna(-999).astype(int)
    df_all["confidence"]      = df_all["confidence"].fillna(0).astype(int)
    df_all["p_female"]        = df_all["p_female"].fillna(50).astype(int)
    df_all["p_male"]          = df_all["p_male"].fillna(50).astype(int)

    # Save output
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df_all.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"Results saved to: {OUTPUT_PATH}")

    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total records: {len(df_all):,}")

    print(f"\nBirth flag predictions:")
    print(f"  - Within 14-day window (1):  {(df_all['birth_flag'] == 1).sum():,}")
    print(f"  - Outside window / none (0): {(df_all['birth_flag'] == 0).sum():,}")
    print(f"  - Uncertain (-99):           {(df_all['birth_flag'] == -99).sum():,}")

    flagged = df_all[df_all["birth_flag"] == 1]
    if len(flagged) > 0:
        print(f"\nDays from birth distribution (flagged posts only):")
        print(f"  - Prenatal  (< 0): {(flagged['days_from_birth'] < 0).sum():,}")
        print(f"  - Day of    (= 0): {(flagged['days_from_birth'] == 0).sum():,}")
        print(f"  - Postnatal (> 0): {(flagged['days_from_birth'] > 0).sum():,}")
        print(f"  - Mean days_from_birth: {flagged['days_from_birth'].mean():.1f}")

    print(f"\nConfidence distribution (all records):")
    print(f"  - No confidence (0): {(df_all['confidence'] == 0).sum():,}")
    print(f"  - Low (1-39):        {((df_all['confidence'] >= 1)  & (df_all['confidence'] < 40)).sum():,}")
    print(f"  - Medium (40-89):    {((df_all['confidence'] >= 40) & (df_all['confidence'] < 90)).sum():,}")
    print(f"  - High (90-100):     {(df_all['confidence'] >= 90).sum():,}")

    print(f"\nPoster gender distribution (all records):")
    print(f"  - Likely female (p_female > 50): {(df_all['p_female'] > 50).sum():,}")
    print(f"  - Likely male   (p_male   > 50): {(df_all['p_male']   > 50).sum():,}")
    print(f"  - Uncertain     (p_female = 50): {(df_all['p_female'] == 50).sum():,}")


if __name__ == "__main__":
    main()
