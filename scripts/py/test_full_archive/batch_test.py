import os
import openai
import pandas as pd
import re
import sys
import json
import time
from dotenv import load_dotenv
import html
import emoji
import unicodedata

# Load API Key
load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set test parameters
begin_date = "2018_01_01"
end_date = "2018_12_31"
file_path = f"data/raw/query_results_{begin_date}-{end_date}.csv"  # Test file

# Load CSV File and Drop Duplicate tweet_id Entries
original_df = pd.read_csv(file_path, encoding="utf-8").drop_duplicates(subset="tweet_id").copy().iloc[21600:21615]

# Slice first 10 rows for testing
# original_df = original_df.iloc[:10]

# Token Limits for Test
TOKENS_PER_REQUEST = 160  # Estimated per request
ENQUEUED_TOKEN_LIMIT = 1_350_000
MAX_TWEETS_PER_BATCH = 5  # ✅ Force two batches of 5 tweets each

# Define output paths
output_filename = "data/raw/test_classified_results.csv"

# Define emojis to keep
KEEP_EMOJIS = {"👶", "🍼", "👼"}

def remove_unwanted_emojis(text):
    """Removes all emojis except for baby face, baby bottle, and baby angel."""
    return "".join(char if char in KEEP_EMOJIS or not emoji.is_emoji(char) else " " for char in text)

def preprocess_text(text, max_chars=200):
    """Preprocess tweet text to remove links, hashtags, mentions, and unwanted emojis."""
    text = str(text).strip()
    text = html.unescape(text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"https?://\S+|www\.\S+", "", text)
    text = re.sub(r"@\w+", "", text)
    text = re.sub(r"#\w+", "", text)
    text = remove_unwanted_emojis(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars].strip() + ("…" if len(text) > max_chars else "")

# Apply preprocessing
original_df["processed_text"] = original_df["text"].apply(preprocess_text)

def get_chain_of_thought_prompt(tweet_id, processed_text):
    """Generates a JSONL entry for batch processing with structured Chain of Thought reasoning."""
    return {
        "custom_id": str(tweet_id),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-3.5-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Classify whether a tweet is a birth announcement using the following criteria:\n"
                        "- If it explicitly announces a birth (within ~1 week), mentions birth details (name, date, weight), "
                        "or references a child's milestone within ~1 year, classify as '1'.\n"
                        "- If it congratulates someone else, comes from a business, refers to animals, or lacks birth references, classify as '0'.\n"
                        "Think step by step before answering."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Tweet: {processed_text}\n\nFinal Answer: Respond ONLY with '1' (Birth Announcement) or '0' (Not Birth Announcement).",
                },
            ],
        },
    }

def create_jsonl_files():
    """Splits `original_df` into two batches of 5 tweets each and creates JSONL files."""
    batch_index = 0

    for start in range(0, len(original_df), MAX_TWEETS_PER_BATCH):
        batch_df = original_df.iloc[start:start + MAX_TWEETS_PER_BATCH]

        # Ensure tweet_id is a string
        batch_df["tweet_id"] = batch_df["tweet_id"].astype(str)

        # Define JSONL filename
        jsonl_filename = f"data/json/test_batch_{batch_index}.jsonl"

        # Write to JSONL file
        with open(jsonl_filename, "w", encoding="utf-8") as f:
            for _, row in batch_df.iterrows():
                json_entry = get_chain_of_thought_prompt(row["tweet_id"], row["processed_text"])
                f.write(json.dumps(json_entry, ensure_ascii=False) + "\n")

        print(f"✅ JSONL file created: {jsonl_filename} with {len(batch_df)} requests.")

        batch_index += 1  # Move to next batch

def process_batches():
    """Processes two test batch requests sequentially and merges results into a single CSV."""
    batch_index = 0
    all_results = []  # List to store DataFrame results from each batch

    while batch_index < 2:  # ✅ Only process two batches
        jsonl_filename = f"data/json/test_batch_{batch_index}.jsonl"

        if not os.path.exists(jsonl_filename):
            print("✅ All test batches processed.")
            break

        batch_id = submit_batch_job(jsonl_filename)

        if batch_id:
            status = check_batch_status(batch_id)

            if status == "completed":
                batch_results = retrieve_and_process_batch_results(batch_id)

                if batch_results is not None:
                    all_results.append(batch_results)

        batch_index += 1  # Move to next batch

    # Merge all batch results into a single DataFrame and save to CSV
    if all_results:
        final_classified_df = pd.concat(all_results, ignore_index=True)

        # Ensure tweet_id is a string before merging
        final_classified_df["tweet_id"] = final_classified_df["tweet_id"].astype(str)
        original_df["tweet_id"] = original_df["tweet_id"].astype(str)

        # Merge with original_df to preserve all tweets
        merged_df = original_df.merge(final_classified_df, on="tweet_id", how="left")

        # Save final merged results
        merged_df.to_csv(output_filename, index=False, encoding="utf-8")

        print(f"✅ Final merged classification results saved to {output_filename}")

def submit_batch_job(jsonl_filename):
    """Uploads the JSONL file to OpenAI and submits a batch job."""
    try:
        file_upload = client.files.create(file=open(jsonl_filename, "rb"), purpose="batch")
        file_id = file_upload.id  
        response = client.batches.create(input_file_id=file_id, endpoint="/v1/chat/completions", completion_window="24h")
        return response.id  
    except Exception as e:
        print(f"Error submitting batch job: {e}")
        return None

def check_batch_status(batch_id):
    """Checks the status of the batch job until it completes or is cancelled."""
    if not batch_id:
        print("No batch ID provided.")
        return None

    while True:
        try:
            job_status = client.batches.retrieve(batch_id)
            status = job_status.status
            print(f"Batch Status: {status}")

            if status in ["completed", "failed", "cancelled"]:
                print(f"Batch job {batch_id} ended with status: {status}")
                return status

            time.sleep(30)
        except Exception as e:
            print(e)
            return None

def retrieve_and_process_batch_results(batch_id):
    """Retrieves batch classification results and processes them into a DataFrame."""
    print(f"Retrieving batch results for {batch_id}...")

    batch_info = client.batches.retrieve(batch_id)
    output_file_id = batch_info.output_file_id  

    if not output_file_id:
        print(f"No output file found for batch {batch_id}.")
        return None

    file_response = client.files.content(output_file_id)
    results = file_response.text  

    classifications = []
    for line in results.splitlines():
        response = json.loads(line)
        tweet_id = str(response.get("custom_id"))
        classification = response.get("response", {}).get("body", {}).get("choices", [{}])[0].get("message", {}).get("content", "").strip()
        classification = 1 if classification == "1" else 0
        classifications.append({"tweet_id": tweet_id, "text_classification": classification})

    return pd.DataFrame(classifications)

if __name__ == "__main__":
    create_jsonl_files()  
    process_batches()
