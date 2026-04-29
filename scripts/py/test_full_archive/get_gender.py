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
OUTPUT_PATH = f"data/raw/user_info_with_demographics{YEAR}.csv" 

# 
df = pd.read_csv(INPUT_PATH, encoding="utf-8")
df = df.iloc[0:20] # test on first 20 observations


# # debugging prompt
# def get_gender_prompt(user_id, name, username, description, profile_image_url):
#     name = name or ""
#     username = username or ""
#     description = description or ""
#     profile_image_url = profile_image_url or ""

#     return {
#         "custom_id": str(user_id),
#         "method": "POST",
#         "url": "/v1/chat/completions",
#         "body": {
#             "model": "gpt-4-turbo",
#             "messages": [
#                 {
#                     "role": "system",
#                     "content": (
#                         "Determine the likely gender of a Twitter user "
#                         "based on their name, username, profile description, and profile image. Explain your reasoning for each piece of information, "
#                         "then give a final classification."
#                     )
#                 },
#                 {
#                     "role": "user",
#                     "content": [
#                         {
#                             "type": "text",
#                             "text": (
#                                 f"User info:\n"
#                                 f"- Name: {name}\n"
#                                 f"- Username: {username}\n"
#                                 f"- Description: {description}\n\n"
#                                 "Instructions:\n"
#                                 "1. Explain whether and how the **name** is associated with a specific gender.\n"
#                                 "2. Explain whether the **username** gives any clues about gender.\n"
#                                 "3. Explain if the **description** contains any gendered words or references.\n"
#                                 "4. Examine the **profile image** only if it appears to show a real human face. If it's a cartoon, logo, or unrelated image, state that you are ignoring it. Otherwise, explain what gender cues you find.\n\n"
#                                 "After explaining your reasoning, respond with one of the following:\n"
#                                 "- 1 → Likely Female\n"
#                                 "- 0 → Likely Male\n"
#                                 "- -99 → Gender is uncertain or cannot be determined\n\n"
#                                 "Final answer (number only):"
#                             )
#                         },
#                         {
#                             "type": "image_url",
#                             "image_url": {
#                                 "url": profile_image_url,
#                                 "detail": "low"
#                             }
#                         }
#                     ]
#                 }
#             ]
#         }
#     }



# prompt for getting gender using name, description, and profile image
def get_gender_prompt(user_id, name, username, description, profile_image_url):
    name = name or ""
    username = username or ""
    description = description or ""
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
                        "Determine the likely gender of a Twitter user "
                        "based on their name, username, profile description, and profile image. "
                        "Use cautious, evidence-based reasoning."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"User information:\n"
                                f"- Name: {name}\n"
                                f"- Username: {username}\n"
                                f"- Description: {description}\n\n"
                                "Instructions:\n"
                                "1. If the name is clearly associated with a specific gender (e.g., Angela, John), use that as your primary signal.\n"
                                "2. Use the description and username for secondary clues (e.g., pronouns, 'mom', 'husband').\n"
                                "3. Examine the profile image **only if it clearly shows a real human face**. Ignore logos, cartoons, pets, or vague photos.\n"
                                "4. If the image is ambiguous, blurry, indirect, or only shows clothing or context (e.g., a person from behind), do NOT override the textual cues.\n"
                                "5. If the name and description suggest one gender and the image is unclear or weak, stick with the name/description.\n"
                                "6. If all signals are unclear, return `-99`.\n\n"
                                "Respond with only ONE of the following:\n"
                                "- 1 → Likely Female\n"
                                "- 0 → Likely Male\n"
                                "- -99 → Gender is uncertain or cannot be determined\n\n"
                                "Final answer (number only):"
                            )
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
    """Clears old batches, then splits `original_df` into multiple batches and creates JSONL files."""
    clear_old_batches()  # ✅ Clear JSONL files before creating new ones
    
    batch_index = 0 # track batch number

    for start in range(0, len(df), MAX_TWEETS_PER_BATCH):
        batch_df = df.iloc[start:start + MAX_TWEETS_PER_BATCH].copy()
        batch_df["author_id"] = batch_df["author_id"].astype(str) # Make sure that the `author_id` is a string

        jsonl_filename = f"data/json/batch_requests_gender_batch_{batch_index}.jsonl"

        with open(jsonl_filename, 'w', encoding = "utf-8") as f:
            for _, row in batch_df.iterrows():
                json_entry = get_gender_prompt(row["author_id"], row["name"], row["username"], row["description"], row["profile_image_url"])
                f.write(json.dumps(json_entry, ensure_ascii=False) + "\n")
        
        print(f"✅ JSONL file created: {jsonl_filename} with {len(batch_df)} requests.")
        batch_index += 1  # Move to next batch

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

def retrieve_and_process_gender_results(batch_id):
    """Retrieves batch gender classification results and returns a DataFrame with author_id and female variable."""

    if not batch_id:
        print("❌ No batch ID provided.")
        return None

    try:
        # Step 1: Retrieve batch info
        batch_info = client.batches.retrieve(batch_id)
        output_file_id = batch_info.output_file_id

        if not output_file_id:
            print(f"⚠️ No output file found for batch {batch_id}.")
            return None

        print(f"📥 Retrieving batch results from File ID: {output_file_id}")
        file_response = client.files.content(output_file_id)
        results = file_response.text

        # Step 2: Parse results
        classifications = []
        for line in results.splitlines():
            response = json.loads(line)
            author_id = str(response.get("custom_id"))  # Handle user_id or author_id
            response_data = response.get("response", {})
            status_code = response_data.get("status_code")

            gender_code = -99  # Default: uncertain
            if status_code == 200:
                body = response_data.get("body", {})
                choices = body.get("choices", [])
                content = choices[0]["message"]["content"].strip() if choices else None

                # Extract gender code from final answer
                match = re.search(r"\b-?1\b|\b0\b", content or "")
                if match:
                    gender_code = int(match.group(0))

            classifications.append({"author_id": author_id, "female": gender_code})

        # Step 3: Convert to DataFrame
        gender_df = pd.DataFrame(classifications)
        gender_df["author_id"] = gender_df["author_id"].astype(str)

        print(f"✅ Processed batch {batch_id} with {len(gender_df)} gender labels.")
        return gender_df

    except Exception as e:
        print(f"❌ Error retrieving gender results for batch {batch_id}: {e}")
        return None
    

def run_batches():
    batch_index = 0
    all_results = []

    while True:
        jsonl_filename = f"data/json/batch_requests_gender_batch_{batch_index}.jsonl"
        if not os.path.exists(jsonl_filename):
            print("✅ All batches submitted and processed.")
            break

        batch_id = submit_batch_job(jsonl_filename)
        if batch_id:
            status = check_batch_status(batch_id)
            if status == "completed":
                gender_df = retrieve_and_process_gender_results(batch_id)
                if gender_df is not None:
                    all_results.append(gender_df)

        batch_index += 1

    # Save combined output
    if all_results:
        result_df = pd.concat(all_results, ignore_index=True)
        result_df["author_id"] = result_df["author_id"].astype(str)
        df["author_id"] = df["author_id"].astype(str)
        merged = df.merge(result_df, on="author_id", how="left")
        merged.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
        print(f"✅ Final output saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    start_time = time.time()
    create_jsonl_files()
    run_batches()
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"{elapsed_time} seconds elapsed")