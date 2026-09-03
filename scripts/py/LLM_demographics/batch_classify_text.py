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

# Set file paths
begin_date = "2013_01_01"
end_date = "2017_12_31"

file_path = f"data/raw/query_results_{begin_date}-{end_date}.csv"


if not os.path.exists(file_path):
    print(f"Error: File '{file_path}' not found. Ensure it is in the correct directory.")
    sys.exit(1)

MODEL_NUM = 4

# Load CSV File and Drop Duplicate tweet_id Entries 
# original_df = pd.read_csv(file_path, encoding="utf-8").iloc[17635:17665].drop_duplicates(subset="tweet_id").copy()
original_df = pd.read_csv(file_path, encoding="utf-8")
print(f"Started with {len(original_df)} tweets in file")

original_df = original_df.drop_duplicates(subset="tweet_id").copy()
print(f"Removed duplicate tweets. Remaining tweets: {len(original_df)}")

original_df = original_df[~original_df["text"].str.contains("I liked a @YouTube video", case=False, na=False)]
print(f"Removed YouTube auto-tweets. Remaining tweets: {len(original_df)}")


# Token Limits - these will differ depending on which model is used
TOKENS_PER_TWEET = 150 if MODEL_NUM == 3.5 else 240
# Enqeued token limit depends on which model we use
# ENQUEUED_TOKEN_LIMIT = 20_000_000 if MODEL_NUM == 3.5 else 1_350_000
ENQUEUED_TOKEN_LIMIT = 40_000_000
MAX_TWEETS_PER_BATCH = min(ENQUEUED_TOKEN_LIMIT // TOKENS_PER_TWEET, 50_000)


# Define emojis to keep
KEEP_EMOJIS = {"👶", "🍼", "👼"}

def remove_unwanted_emojis(text):
    """Removes all emojis except for baby face, baby bottle, and baby angel."""
    return "".join(char if char in KEEP_EMOJIS or not emoji.is_emoji(char) else " " for char in text)

def preprocess_text(text, max_chars=200):
    """Preprocess tweet text to remove links, hashtags, mentions, and unwanted emojis."""
    text = str(text).strip()

    # Convert HTML entities (&amp; -> &, etc.)
    text = html.unescape(text)

    # Normalize Unicode (e.g., curly quotes to standard ASCII)
    text = unicodedata.normalize("NFKC", text)

    # Remove links (shortened & full URLs)
    text = re.sub(r"https?://\S+|www\.\S+", "", text)

    # Remove mentions (@usernames)
    text = re.sub(r"@\w+", "", text)

    # Remove hashtags (#word)
    text = re.sub(r"#\w+", "", text)

    # Remove unwanted emojis (keep only 👶 🍼 👼)
    text = remove_unwanted_emojis(text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    # Truncate tweet to reduce token usage
    return text[:max_chars].strip() + ("…" if len(text) > max_chars else "")

# Apply preprocessing
original_df["processed_text"] = original_df["text"].apply(preprocess_text)

# print(original_df["processed_text"])

def get_chain_of_thought_prompt(tweet_id, processed_text, model):
    """Generates a JSONL entry for batch processing with structured Chain of Thought reasoning."""

    model_name = "gpt-3.5-turbo" if model == 3.5 else "gpt-4-turbo"  # Ensures correct model naming
    return {
        "custom_id": str(tweet_id),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": model_name,
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


def clear_old_batches():
    """Deletes all previous batch JSONL files before running new batch processing."""
    jsonl_files = glob.glob("data/json/batch_requests_*.jsonl")  # Finds all batch JSONL files
    for file in jsonl_files:
        os.remove(file)  # Deletes the file
    print(f"✅ Cleared {len(jsonl_files)} old batch JSONL files.")

def create_jsonl_files():
    """Clears old batches, then splits `original_df` into multiple batches and creates JSONL files."""
    clear_old_batches()  # ✅ Clear JSONL files before creating new ones
    
    batch_index = 0  # Track batch number

    for start in range(0, len(original_df), MAX_TWEETS_PER_BATCH):
        batch_df = original_df.iloc[start:start + MAX_TWEETS_PER_BATCH].copy()
        batch_df["tweet_id"] = batch_df["tweet_id"].astype(str)  # Ensure `tweet_id` is a string

        jsonl_filename = f"data/json/batch_requests_{begin_date}-{end_date}_batch_{batch_index}.jsonl"

        with open(jsonl_filename, "w", encoding="utf-8") as f:
            for _, row in batch_df.iterrows():
                json_entry = get_chain_of_thought_prompt(row["tweet_id"], row["processed_text"], MODEL_NUM)
                f.write(json.dumps(json_entry, ensure_ascii=False) + "\n")

        print(f"✅ JSONL file created: {jsonl_filename} with {len(batch_df)} requests.")
        batch_index += 1  # Move to next batch



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

            time.sleep(60)
        except Exception as e:
            print(e)
            return None

def retrieve_and_process_batch_results(batch_id):
    """Retrieves batch classification results and returns a DataFrame without modifying `original_df`."""
    if not batch_id:
        print("No batch ID provided.")
        return None

    try:
        batch_info = client.batches.retrieve(batch_id)
        output_file_id = batch_info.output_file_id  

        if not output_file_id:
            print(f"No output file found for batch {batch_id}.")
            return None

        print(f"Retrieving batch results from File ID: {output_file_id}")
        file_response = client.files.content(output_file_id)
        results = file_response.text  

        classifications = []
        for line in results.splitlines():
            response = json.loads(line)
            tweet_id = str(response.get("custom_id"))  # Ensure tweet_id is a string
            response_data = response.get("response", {})
            status_code = response_data.get("status_code")

            if status_code == 200:
                body = response_data.get("body", {})
                choices = body.get("choices", [])
                classification_text = choices[0]["message"]["content"].strip() if choices else None
                classification = 1 if classification_text == "1" else 0
            else:
                classification = None  

            classifications.append({"tweet_id": tweet_id, "text_classification": classification})

        # Convert to DataFrame
        classified_df = pd.DataFrame(classifications)
        classified_df["tweet_id"] = classified_df["tweet_id"].astype(str)  # Ensure tweet_id is string

        # sort by author_id and date

        print(f"✅ Processed batch {batch_id} with {len(classified_df)} rows.")
        return classified_df  # ✅ Only return classification results

    except Exception as e:
        print(f"Error retrieving and processing batch results: {e}")
        return None

def run_batches():
    """Processes multiple batch requests sequentially and merges results into a single CSV."""
    batch_index = 0
    all_results = []  # List to store DataFrame results from each batch

    while True:
        jsonl_filename = f"data/json/batch_requests_{begin_date}-{end_date}_batch_{batch_index}.jsonl"

        if not os.path.exists(jsonl_filename):
            print("✅ All batches processed.")
            break  # No more batches left

        # Step 2: Submit batch job
        batch_id = submit_batch_job(jsonl_filename)

        if batch_id:
            status = check_batch_status(batch_id)

            if status == "completed":
                # Step 4: Retrieve, process, and collect results
                batch_results = retrieve_and_process_batch_results(batch_id)

                if batch_results is not None:
                    all_results.append(batch_results)  # Store batch results

        batch_index += 1  # Move to next batch

    # ✅ Merge all batch results together
    if all_results:
        final_classified_df = pd.concat(all_results, ignore_index=True)

        # Ensure tweet_id is a string before merging
        final_classified_df["tweet_id"] = final_classified_df["tweet_id"].astype(str)
        original_df["tweet_id"] = original_df["tweet_id"].astype(str)

        # ✅ Corrected: Merge with original_df to preserve all tweets
        merged_df = original_df.merge(final_classified_df, on="tweet_id", how="left")

        # Save final merged results
        final_output_filename = f"data/raw/classified_text_{begin_date}-{end_date}.csv"
        merged_df.to_csv(final_output_filename, index=False, encoding="utf-8")

        print(f"✅ Final merged classification results saved to {final_output_filename}")



if __name__ == "__main__":
    start_time = time.time()
    create_jsonl_files()
    # run_batches()
    # end_time = time.time()
    # elapsed_time = end_time - start_time
    # print(f"{elapsed_time} seconds elapsed")
    







