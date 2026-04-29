# Load in user file
# Use chagpt api to classify gender based on name. 
# If unclear, say so. 
# Then use profile picture to get gender. 
# Then use description to get gender. 
# Hand-code gender when there are contradictions
# Get occupation from description

import os
import openai
import pandas as pd
import re
import sys
import json
import time
from tqdm import tqdm
from dotenv import load_dotenv
from datetime import datetime
import html
import emoji
import unicodedata
import glob

os.chdir("E:/TwitterBirth")
# Load API Key
load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Constants
TOKENS_PER_TWEET = 100 # placeholder
ENQUEUED_TOKEN_LIMIT = 40_000_000
MAX_TWEETS_PER_BATCH = ENQUEUED_TOKEN_LIMIT // TOKENS_PER_TWEET
# toggle this to either 2018 or 2013_2017
YEAR = 2018

# File paths
INPUT_PATH = f"data/raw/user_info_{YEAR}.csv"
OUTPUT_PATH = f"data/raw/user_info_with_demographics_{YEAR}.csv" 

# 
df = pd.read_csv(INPUT_PATH, encoding="utf-8")
df = df.iloc[0:20] # test on first 20 observations


def get_race_prompt(user_id, profile_image_url):
    profile_image_url = profile_image_url or ""

    return {
        "custom_id": str(user_id),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a visual classification assistant. Your task is to determine the likely race or ethnicity "
                        "of a person based ONLY on their profile image.\n\n"
                        "Use the following codes:\n"
                        "- 1 = Black\n- 2 = White\n- 3 = Asian\n- 4 = Hispanic\n- 5 = Other\n- -99 = Uncertain\n\n"
                        "Only return -99 if the image is not of a person or is too unclear to classify."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Here is the profile image. Classify the person's race visually."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": profile_image_url,
                                "detail": "auto"
                            }
                        }
                    ]
                }
            ]
        }
    }


def clear_old_batches():
    """Deletes all previous batch JSONL files before running new batch processing."""
    jsonl_files = glob.glob("data/json/batch_requests_*.jsonl") # Finds all batch JSONL files
    for file in jsonl_files:
        os.remove(file) # Deletes file
    print(f"Cleared {len(jsonl_files)} old batch JSONL files.")

def create_jsonl_files():
    """Clears old batches, then splits `df` into multiple batches and creates JSONL files."""
    clear_old_batches()
    batch_index = 0

    for start in range(0, len(df), MAX_TWEETS_PER_BATCH):
        batch_df = df.iloc[start:start + MAX_TWEETS_PER_BATCH].copy()
        batch_df["author_id"] = batch_df["author_id"].astype(str)

        jsonl_filename = f"data/json/batch_requests_demographics_batch_{batch_index}.jsonl"
        with open(jsonl_filename, 'w', encoding="utf-8") as f:
            for _, row in batch_df.iterrows():
                json_entry = get_race_prompt(
                    row["author_id"],
                    row.get("profile_image_url", "")
                )
                f.write(json.dumps(json_entry, ensure_ascii=False) + "\n")

        print(f"✅ JSONL file created: {jsonl_filename} with {len(batch_df)} requests.")
        batch_index += 1


def submit_batch_job(jsonl_filename):
    try:
        file_upload = client.files.create(file=open(jsonl_filename, "rb"), purpose = "batch")
        file_id = file_upload.id
        response = client.batches.create(input_file_id=file_id, endpoint="/v1/chat/completions", completion_window="24h")
        return response.id
    except Exception as e:
        print(f"Error submitting batch job: {e}")
        return None

def check_batch_status(batch_id):
    if not batch_id:
        print("No batch ID provided")
        return None

    while True:
        try:
            job_status = client.batches.retrieve(batch_id)
            status = job_status.status
            print(f"Batch Status: {status}")

            if status in ["completed", "failed", "cancelled"]:
                print(f"Batch job {batch_id} ended with status: {status}")
                return status

            time.sleep(60)
        except Exception as e:
            print(e)
            return None

def retrieve_and_process_race_results(batch_id):
    if not batch_id:
        return None

    try:
        batch_info = client.batches.retrieve(batch_id)
        output_file_id = batch_info.output_file_id
        if not output_file_id:
            return None

        file_response = client.files.content(output_file_id)
        results = file_response.text

        classifications = []
        for line in results.splitlines():
            response = json.loads(line)
            author_id = str(response.get("custom_id"))
            response_data = response.get("response", {})
            status_code = response_data.get("status_code")

            race = -99
            if status_code == 200:
                body = response_data.get("body", {})
                content = body.get("choices", [])[0]["message"]["content"].strip() if body.get("choices") else ""
                match = re.search(r"\b-?1\b|\b[2-5]\b", content)
                if match:
                    race = int(match.group(0))

            classifications.append({"author_id": author_id, "race": race})

        return pd.DataFrame(classifications)

    except Exception as e:
        print(f"Error: {e}")
        return None

    

def run_batches():
    batch_index = 0
    all_results = []

    while True:
        jsonl_filename = f"data/json/batch_requests_demographics_batch_{batch_index}.jsonl"
        if not os.path.exists(jsonl_filename):
            print("✅ All batches submitted and processed.")
            break

        batch_id = submit_batch_job(jsonl_filename)
        if batch_id:
            status = check_batch_status(batch_id)
            if status == "completed":
                result_df = retrieve_and_process_race_results(batch_id)
                if result_df is not None:
                    all_results.append(result_df)

        batch_index += 1

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        final_df["author_id"] = final_df["author_id"].astype(str)
        df["author_id"] = df["author_id"].astype(str)
        merged = df.merge(final_df, on="author_id", how="left")
        merged.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
        print(f"✅ Final output saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    start_time = time.time()
    create_jsonl_files()
    run_batches()
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"{elapsed_time} seconds elapsed")



# get occupation and number of child 