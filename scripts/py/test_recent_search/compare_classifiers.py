# import os
# import openai
# import pandas as pd
# import re
# import sys
# import json
# import time
# from tqdm import tqdm
# from dotenv import load_dotenv
# from datetime import datetime
# import html
# import emoji
# import requests
# import unicodedata

# # Load API Key
# load_dotenv(dotenv_path="config/.env")
# client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # Set file paths
# begin_date = "2018_01_01"
# end_date = "2018_12_31"
# file_path = f"data/raw/query_results_{begin_date}-{end_date}.csv"

# if not os.path.exists(file_path):
#     print(f"Error: File '{file_path}' not found. Ensure it is in the correct directory.")
#     sys.exit(1)

# # Load CSV File
# original_df = pd.read_csv(file_path, encoding="utf-8").iloc[0:10]

# def truncate_text(text, max_chars=200):
#     """Truncates text to a maximum character length, adding '…' if trimmed."""
#     return text[:max_chars].strip() + ("…" if len(text) > max_chars else "")

# # Keep only these baby-related emojis
# KEEP_EMOJIS = {"👶", "🍼", "👼"}

# def remove_unwanted_emojis(text):
#     """Removes all emojis except for baby face, baby bottle, and baby angel."""
#     return "".join(char if char in KEEP_EMOJIS or not emoji.is_emoji(char) else " " for char in text)

# def preprocess_text(text, max_chars=200):
#     """Preprocess tweet text to remove unnecessary characters and reduce token usage."""
#     text = str(text).strip()
    
#     # Convert &amp; -> &, etc.
#     text = html.unescape(text)

#     # Normalize Unicode (e.g., curly quotes to standard ASCII)
#     text = unicodedata.normalize("NFKC", text)

#     # Remove non-ASCII characters (curly quotes, dashes, etc.)
#     text = text.encode("ascii", "ignore").decode()

#     # Remove links and mentions
#     text = re.sub(r"http\S+|www\S+|@\S+", "", text)

#     # Keep only relevant baby-related emojis, remove others
#     text = remove_unwanted_emojis(text)

#     # Remove extra spaces
#     text = re.sub(r"\s+", " ", text).strip()

#     # Truncate tweet to reduce token usage
#     return truncate_text(text, max_chars)



# def get_chain_of_thought_prompt(tweet_id, text):
#     """Generates a JSONL entry for batch processing with structured Chain of Thought reasoning."""
#     return {
#         "custom_id": str(tweet_id),  # Track request using tweet_id
#         "method": "POST",
#         "url": "/v1/chat/completions",
#         "body": {
#             "model": "gpt-4-turbo",
#             "messages": [
#                 {
#                     "role": "system",
#                     "content": (
#                         "Classify whether a tweet is a birth announcement using the following criteria:\n"
#                         "- If it explicitly announces a birth (within ~1 week), mentions birth details (name, date, weight), "
#                         "or references a child's milestone within ~1 year, classify as '1'.\n"
#                         "- If it congratulates someone else, comes from a business, refers to animals, or lacks birth references, classify as '0'.\n"
#                         "Think step by step before answering."
#                     ),
#                 },
#                 {
#                     "role": "user",
#                     "content": f"Tweet: {text}\n\nFinal Answer: Respond ONLY with '1' (Birth Announcement) or '0' (Not Birth Announcement).",
#                 },
#             ],
#         },
#     }


# def create_jsonl_file(df, filename="data/json/batch_requests.jsonl"):
#     """Creates a JSONL file for OpenAI's Batch API using chain-of-thought classification."""
#     with open(filename, "w", encoding="utf-8") as f:
#         for _, row in df.iterrows():
#             json_entry = get_chain_of_thought_prompt(row["tweet_id"], row["text"])
#             f.write(json.dumps(json_entry, ensure_ascii=False) + "\n")

#     print(f"JSONL file created with {len(df)} requests.")


# def submit_batch_job(jsonl_filename):
#     """Uploads the JSONL file to OpenAI and submits a batch job."""
#     try:
#         # Step 1: Upload the JSONL file
#         file_upload = client.files.create(
#             file=open(jsonl_filename, "rb"),
#             purpose="batch"
#         )
#         file_id = file_upload.id  # Retrieve the file ID from response
#         print(f"📂 File uploaded successfully. File ID: {file_id}")

#         # Step 2: Submit batch job using the uploaded file
#         response = client.batches.create(
#             input_file_id=file_id,
#             endpoint="/v1/chat/completions",
#             completion_window = "24h"
#         )

#         batch_id = response.id  # Retrieve batch ID
#         print(f"🚀 Batch job submitted! Batch ID: {batch_id}")
#         return batch_id

#     except Exception as e:
#         print(f"❌ Error submitting batch job: {e}")
#         return None

# def check_batch_status(batch_id):
#     """Checks the status of the batch job until it completes or is cancelled."""
#     if not batch_id:
#         print("No batch ID provided.")
#         return

#     while True:
#         try:
#             job_status = client.batches.retrieve(batch_id)
#             status = job_status.status
#             print(f"Batch Status: {status}")

#             if status in ["completed", "failed", "cancelled"]:  # Stop checking if cancelled
#                 print(f"Batch job {batch_id} ended with status: {status}")
#                 break

#             time.sleep(30)  # Wait before checking again
#         except Exception as e:
#             print(e)
#             break


# def retrieve_batch_results(batch_id):
#     """Retrieves batch classification results from OpenAI and returns the JSONL content."""
#     if not batch_id:
#         print("No batch ID provided.")
#         return None

#     try:
#         batch_info = client.batches.retrieve(batch_id)
#         output_file_id = batch_info.output_file_id

#         if not output_file_id:
#             print(f"No output file found for batch {batch_id}.")
#             return None

#         print(f"Retrieving batch results from File ID: {output_file_id}")
        
#         # Fetch results from OpenAI's Files API
#         file_response = client.files.content(output_file_id)
#         results = file_response.text  # Each line is a separate JSON object

#         return results

#     except Exception as e:
#         print(f"Error retrieving batch results: {e}")
#         return None


# def save_batch_results_jsonl(batch_id, jsonl_output_filename):
#     """Saves batch classification results as a JSONL file."""
#     results = retrieve_batch_results(batch_id)
#     if results is None:
#         return None

#     try:
#         with open(jsonl_output_filename, "w", encoding="utf-8") as f:
#             for line in results.splitlines():
#                 f.write(line + "\n")

#         print(f"Batch results successfully saved to {jsonl_output_filename}")
#         return jsonl_output_filename  # Return the file path

#     except Exception as e:
#         print(f"Error saving batch results to JSONL: {e}")
#         return None


# def convert_jsonl_to_dataframe(jsonl_filename):
#     """Reads a JSONL file and converts batch classification results into a DataFrame."""
#     try:
#         classifications = []

#         with open(jsonl_filename, "r", encoding="utf-8") as f:
#             for line in f:
#                 response = json.loads(line)
#                 tweet_id = response.get("custom_id")
#                 response_data = response.get("response", {})
#                 status_code = response_data.get("status_code")

#                 if status_code == 200:
#                     body = response_data.get("body", {})
#                     choices = body.get("choices", [])
#                     classification_text = choices[0]["message"]["content"].strip() if choices else None
#                     classification = 1 if classification_text == "1" else 0
#                 else:
#                     classification = None  

#                 classifications.append({"tweet_id": str(tweet_id), "text_classification": classification})

#         classified_df = pd.DataFrame(classifications)

#         # Ensure tweet_id is string type
#         classified_df["tweet_id"] = classified_df["tweet_id"].astype(str)

#         return classified_df

#     except Exception as e:
#         print(f"Error processing batch results into DataFrame: {e}")
#         return None


# def merge_and_save_results(original_df, classified_df, output_filename):
#     """Merges classification results with the original DataFrame and saves the final CSV."""
#     if classified_df is None or classified_df.empty:
#         print("No classified data available to merge.")
#         return

#     try:
#         # Ensure `tweet_id` is string in both DataFrames for accurate merging
#         original_df["tweet_id"] = original_df["tweet_id"].astype(str)
#         classified_df["tweet_id"] = classified_df["tweet_id"].astype(str)

#         # Merge on `tweet_id`
#         merged_df = original_df.merge(classified_df, on="tweet_id", how="left")

#         # Save the merged results
#         merged_df.to_csv(output_filename, index=False, encoding="utf-8")

#         print(f"Merged classification results successfully saved to {output_filename}")

#     except Exception as e:
#         print(f"Error merging and saving results: {e}")




# if __name__ == "__main__":
#     jsonl_filename = f"data/json/batch_requests_{begin_date}-{end_date}.jsonl"
#     jsonl_output_filename = f"data/json/batch_results_{begin_date}-{end_date}.jsonl"
#     output_filename = f"data/raw/classified_text_{begin_date}-{end_date}.csv"

#     # Step 1: Submit batch job
#     batch_id = submit_batch_job(jsonl_filename)

#     # Step 2: Monitor batch job status
#     check_batch_status(batch_id)

#     # Step 3: Save batch results to JSONL
#     jsonl_file = save_batch_results_jsonl(batch_id, jsonl_output_filename)

#     if jsonl_file:
#         # Step 4: Convert JSONL to DataFrame
#         classified_df = convert_jsonl_to_dataframe(jsonl_file)

#         if classified_df is not None:
#             # Step 5: Merge and save results
#             merge_and_save_results(original_df, classified_df, output_filename)

























# import os
# import openai
# import pandas as pd
# import re
# import sys
# import json
# import time
# from tqdm import tqdm
# from dotenv import load_dotenv
# from datetime import datetime
# import html
# import emoji
# import unicodedata
# import requests

# # Load API Key
# load_dotenv(dotenv_path="config/.env")
# client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # Set file paths
# begin_date = "2018_01_01"
# end_date = "2018_12_31"
# file_path = f"data/raw/query_results_{begin_date}-{end_date}.csv"

# if not os.path.exists(file_path):
#     print(f"Error: File '{file_path}' not found. Ensure it is in the correct directory.")
#     sys.exit(1)

# # Load CSV File
# original_df = pd.read_csv(file_path, encoding="utf-8").iloc[0:10]

# def truncate_text(text, max_chars=200):
#     """Truncates text to a maximum character length, adding '…' if trimmed."""
#     return text[:max_chars].strip() + ("…" if len(text) > max_chars else "")

# # Keep only these baby-related emojis
# KEEP_EMOJIS = {"👶", "🍼", "👼"}

# def remove_unwanted_emojis(text):
#     """Removes all emojis except for baby face, baby bottle, and baby angel."""
#     return "".join(char if char in KEEP_EMOJIS or not emoji.is_emoji(char) else " " for char in text)

# def preprocess_text(text, max_chars=200):
#     """Preprocess tweet text to remove unnecessary characters and reduce token usage."""
#     text = str(text).strip()
    
#     # Convert &amp; -> &, etc.
#     text = html.unescape(text)

#     # Normalize Unicode (e.g., curly quotes to standard ASCII)
#     text = unicodedata.normalize("NFKC", text)

#     # Remove non-ASCII characters (curly quotes, dashes, etc.)
#     text = text.encode("ascii", "ignore").decode()

#     # Remove links and mentions
#     text = re.sub(r"http\S+|www\S+|@\S+", "", text)

#     # Keep only relevant baby-related emojis, remove others
#     text = remove_unwanted_emojis(text)

#     # Remove extra spaces
#     text = re.sub(r"\s+", " ", text).strip()

#     # Truncate tweet to reduce token usage
#     return truncate_text(text, max_chars)



# def create_jsonl_file(df, filename=f"data/json/batch_requests_{begin_date}-{end_date}.jsonl"):
#     """Creates a JSONL file for OpenAI's Batch API with a concise prompt and numerical classification output."""
#     with open(filename, "w", encoding="utf-8") as f:
#         for _, row in df.iterrows():
#             processed_tweet = preprocess_text(row["text"], max_chars=200)

#             data = {
#                 "custom_id": str(row["tweet_id"]),
#                 "method": "POST",
#                 "url": "/v1/chat/completions",
#                 "body": {
#                     "model": "gpt-4-turbo",
#                     "messages": [
#                         {
#                             "role": "system",
#                             "content": (
#                                 "Classify if this tweet announces a birth. "
#                                 "If it explicitly states a birth, mentions birth details (name, date, weight), or strongly implies a recent birth, respond with '1'. "
#                                 "Otherwise, respond with '0'."
#                             ),
#                         },
#                         {"role": "user", "content": processed_tweet},
#                     ]
#                 }
#             }

#             f.write(json.dumps(data, ensure_ascii=False) + "\n")

#     print(f"JSONL file created with {len(df)} requests.")



# def submit_batch_job(jsonl_filename):
#     """Uploads the JSONL file to OpenAI and submits a batch job."""
#     try:
#         # Step 1: Upload the JSONL file
#         file_upload = client.files.create(
#             file=open(jsonl_filename, "rb"),
#             purpose="batch"
#         )
#         file_id = file_upload.id  # Retrieve the file ID from response
#         print(f"📂 File uploaded successfully. File ID: {file_id}")

#         # Step 2: Submit batch job using the uploaded file
#         response = client.batches.create(
#             input_file_id=file_id,
#             endpoint="/v1/chat/completions",
#             completion_window = "24h"
#         )

#         batch_id = response.id  # Retrieve batch ID
#         print(f"🚀 Batch job submitted! Batch ID: {batch_id}")
#         return batch_id

#     except Exception as e:
#         print(f"❌ Error submitting batch job: {e}")
#         return None

# def check_batch_status(batch_id):
#     """Checks the status of the batch job until it completes or is cancelled."""
#     if not batch_id:
#         print("No batch ID provided.")
#         return

#     while True:
#         try:
#             job_status = client.batches.retrieve(batch_id)
#             status = job_status.status
#             print(f"Batch Status: {status}")

#             if status in ["completed", "failed", "cancelled"]:  # Stop checking if cancelled
#                 print(f"Batch job {batch_id} ended with status: {status}")
#                 break

#             time.sleep(30)  # Wait before checking again
#         except Exception as e:
#             print(e)
#             break


# def download_batch_results(batch_id, original_df, output_filename):
#     """Downloads and merges batch classification results."""
#     if not batch_id:
#         print("No batch ID provided.")
#         return

#     try:
#         batch_info = client.batches.retrieve(batch_id)
#         output_file_id = batch_info.output_file_id  
#         if not output_file_id:
#             print(f"No output file found for batch {batch_id}")
#             return

#         print(f"Downloading results from File ID: {output_file_id}")

#         file_response = client.files.content(output_file_id)  
#         results = file_response.text  

#         classifications = []
#         for line in results.splitlines():
#             response = json.loads(line)
#             custom_id = response.get("custom_id")
#             response_data = response.get("response", {})
#             status_code = response_data.get("status_code")

#             if status_code == 200:
#                 body = response_data.get("body", {})
#                 choices = body.get("choices", [])

#                 if choices and "message" in choices[0]:
#                     classification_text = choices[0]["message"]["content"].strip()
#                     classification = 1 if classification_text == "1" else 0
#                 else:
#                     classification = None
#             else:
#                 classification = None  

#             classifications.append({"tweet_id": str(custom_id), "pic_classification": classification})

#         # Convert classifications DataFrame tweet_id to string
#         classified_df = pd.DataFrame(classifications)
#         classified_df["tweet_id"] = classified_df["tweet_id"].astype(str)

#         # Convert original DataFrame tweet_id to string before merging
#         original_df["tweet_id"] = original_df["tweet_id"].astype(str)

#         # Merge and save results
#         merged_df = original_df.merge(classified_df, on="tweet_id", how="left")
#         merged_df.to_csv(output_filename, index=False)

#         print(f"Merged classification results saved to {output_filename}")

#     except Exception as e:
#         print(e)



# if __name__ == "__main__":
#     # Load tweets from CSV
#     tweets_df = original_df[["query_id", "tweet_id", "text"]].copy()
    
#     # Define filenames
#     jsonl_filename = f"data/json/batch_requests_{begin_date}-{end_date}.jsonl"
#     output_filename = f"data/raw/classified_tweets_{begin_date}-{end_date}.csv"

#     # Step 1: Create JSONL file
#     create_jsonl_file(tweets_df, jsonl_filename)

#     # Step 2: Submit batch job and get batch ID
#     batch_id = submit_batch_job(jsonl_filename)

#     # Step 3: Monitor job status
#     check_batch_status(batch_id)

#     # Step 4: Download and merge results
#     download_batch_results(batch_id, tweets_df, output_filename)

