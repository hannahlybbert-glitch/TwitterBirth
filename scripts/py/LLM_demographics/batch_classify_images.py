import pandas as pd
import os
import openai
import time
import json
from dotenv import load_dotenv
import sys
import glob

# Set working directory
os.chdir("E:/TwitterBirth")

# Load API Key
load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Date range for filenames
begin_date = "2013_01_01"
end_date = "2017_12_31"

# Load Data
file_path = f"data/raw/classified_text_GPT4_{begin_date}-{end_date}.csv"
if not os.path.exists(file_path):
    print(f"Error: File '{file_path}' not found.")
    sys.exit(1)

original_df = pd.read_csv(file_path, encoding="utf-8")

# Keep only tweets with pictures that are already classified as birth announcements
pics_df = original_df[(original_df["has_picture"] == 1) & (original_df["text_classification"] == 1)].copy()
pics_df = pics_df[["query_id", "tweet_id", "media_url"]]

if pics_df.empty:
    print("Error: No tweets with pictures found. Exiting.")
    sys.exit(1)

# Token Limits
TOKENS_PER_REQUEST = 230
ENQUEUED_TOKEN_LIMIT = 40_000_000
MAX_TWEETS_PER_BATCH = min(ENQUEUED_TOKEN_LIMIT // TOKENS_PER_REQUEST, 50_000)
# MAX_TWEETS_PER_BATCH = 1000
# MAX_TWEETS_PER_BATCH = 5

# Define file paths
output_filename = f"data/raw/classified_images_{begin_date}-{end_date}.csv"
hand_code_path = f"data/raw/hand_coding/to_hand_code_{begin_date}-{end_date}.csv"


def clear_old_image_batches():
    """Deletes all previous batch JSONL files for image classification."""
    jsonl_files = glob.glob("data/json/batch_image_requests_*.jsonl")  # Finds all batch JSONL files
    for file in jsonl_files:
        os.remove(file)  # Deletes the file
    print(f"✅ Cleared {len(jsonl_files)} old image batch JSONL files.")

    

def create_jsonl_files():
    """Clears old batches, then splits `pics_df` into multiple batches and creates JSONL files."""
    clear_old_image_batches()  # ✅ Clear JSONL files before creating new ones

    batch_index = 0  # Track batch number

    for start in range(0, len(pics_df), MAX_TWEETS_PER_BATCH):
        batch_df = pics_df.iloc[start:start + MAX_TWEETS_PER_BATCH].copy()
        batch_df["tweet_id"] = batch_df["tweet_id"].astype(str)  # Ensure `tweet_id` is a string

        jsonl_filename = f"data/json/batch_image_requests_{begin_date}-{end_date}_batch_{batch_index}.jsonl"

        with open(jsonl_filename, "w", encoding="utf-8") as f:
            for _, row in batch_df.iterrows():
                data = {
                    "custom_id": str(row["tweet_id"]),
                    "method": "POST",
                    "url": "/v1/chat/completions",
                    "body": {
                        "model": "gpt-4-turbo",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": (
                                        "Does this image likely represent a real-life birth announcement?"
                                        "\nCriteria for '1' (Yes):"
                                        "\n- A newborn baby (real, not animated) is clearly visible."
                                        "\n- A mother in a hospital bed, appearing to have recently given birth."
                                        "\n- A father or family member holding what appears to be a newborn."
                                        "\n- A hospital setting with clear birth-related context (e.g., a bassinet, baby wristbands, medical staff)."
                                        "\n\nCriteria for '0' (No):"
                                        "\n- The image is animated, AI-generated, or a cartoon."
                                        "\n- There are no humans visible, or the image contains unrelated objects."
                                        "\n- The image does not have any clear birth-related elements."
                                        "\n\nThink step by step and analyze the image carefully before responding."
                                        "\nRespond ONLY with '1' (Birth Announcement) or '0' (Not Birth Announcement)."
                                    )},
                                    {"type": "image_url", "image_url": {"url": row["media_url"], "detail": "low"}}
                                ]
                            }
                        ]
                    }
                }
                f.write(json.dumps(data, ensure_ascii=False) + "\n")


        print(f"✅ JSONL file created: {jsonl_filename} with {len(batch_df)} requests.")
        batch_index += 1  # Move to next batch


# ✅ Create Hand-Code File
def create_hand_code_file():
    """Creates a file with tweets that passed classification OR need manual review due to failed API requests."""
    df = pd.read_csv(output_filename, encoding="utf-8")

    # Select tweets where classification is 1 OR where classification failed (-99)
    hand_code = df[
        (df["pic_classification"] == 1) | 
        (df["pic_classification"] == -99) |  # Include failed classifications
        ((df["text_classification"] == 1) & (df["has_picture"] == 0))
    ]

    # Ensure classification column is a string
    df["pic_classification"] = df["pic_classification"].astype(str) 

    # Save manually reviewable tweets
    hand_code.to_csv(hand_code_path, encoding="utf-8", index=False)

    print(len(hand_code), "tweets made it through classification or need manual review")
    print(f"✅ Tweets saved to: {hand_code_path}")


# ✅ Step 3: Submit Batch Job
def submit_batch_job(jsonl_filename):
    """Uploads the JSONL file and submits a batch job to OpenAI."""
    try:
        file_upload = client.files.create(
            file=open(jsonl_filename, "rb"),
            purpose="batch"
        )
        file_id = file_upload.id
        print(f"File uploaded. File ID: {file_id}")

        response = client.batches.create(
            input_file_id=file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h"
        )

        batch_id = response.id
        print(f"Batch job submitted. Batch ID: {batch_id}")
        return batch_id

    except Exception as e:
        print(f"Error submitting batch job: {e}")
        return None


# ✅ Monitor Batch Job Status
def check_batch_status(batch_id, max_wait_time=1800):
    """Checks the batch job status until completion or timeout."""
    if not batch_id:
        print("No batch ID provided.")
        return None

    start_time = time.time()

    while True:
        try:
            job_status = client.batches.retrieve(batch_id)
            status = job_status.status
            print(f"Batch Status: {status}")

            if status in ["completed", "failed", "cancelled"]:
                print(f"Batch job {batch_id} ended with status: {status}")
                return status  

            elapsed_time = time.time() - start_time
            if elapsed_time > max_wait_time:
                print(f"⏳ Timeout: Exiting status check after {max_wait_time / 60} minutes.")
                return "timeout"

            time.sleep(60)  

        except Exception as e:
            print(f"Error checking batch status: {e}")
            return None


# ✅ Retrieve and Merge Batch Results
def retrieve_and_process_batch_results(batch_id):
    """Retrieves batch classification results, processes successful and failed requests, and returns a DataFrame."""
    if not batch_id:
        print("No batch ID provided.")
        return None

    try:
        batch_info = client.batches.retrieve(batch_id)
        output_file_id = batch_info.output_file_id
        error_file_id = batch_info.error_file_id  # Get error file if exists

        if not output_file_id and not error_file_id:
            print(f"No output or error files found for batch {batch_id}.")
            return None

        classifications = []

        # ✅ Process Successful Classifications
        if output_file_id:
            print(f"Retrieving successful batch results from File ID: {output_file_id}")
            file_response = client.files.content(output_file_id)
            results = file_response.text

            for line in results.splitlines():
                response = json.loads(line)
                tweet_id = str(response.get("custom_id"))  # Ensure tweet_id is a string
                response_data = response.get("response", {})
                status_code = response_data.get("status_code")

                if status_code == 200:
                    body = response_data.get("body", {})
                    choices = body.get("choices", [])
                    classification_text = choices[0]["message"]["content"].strip() if choices else None
                    classification = int(classification_text) if classification_text in ["1", "0"] else -99  # Handle bad outputs
                else:
                    classification = -99  # Assign -99 to failed cases

                classifications.append({"tweet_id": tweet_id, "pic_classification": classification})

        # ✅ Process Failed Requests (Errors)
        if error_file_id:
            print(f"Retrieving failed batch requests from File ID: {error_file_id}")
            error_response = client.files.content(error_file_id)
            error_results = error_response.text

            for line in error_results.splitlines():
                response = json.loads(line)
                tweet_id = str(response.get("custom_id"))  # Ensure tweet_id is a string
                classifications.append({"tweet_id": tweet_id, "pic_classification": -99})  # Mark failed requests as -99

        # ✅ Convert to DataFrame and return classification results **ONLY**
        classified_df = pd.DataFrame(classifications)
        classified_df["tweet_id"] = classified_df["tweet_id"].astype(str)  # Ensure tweet_id is a string

        print(f"✅ Processed batch {batch_id} with {len(classified_df)} rows (including errors).")
        return classified_df  # ✅ Return both successful and failed classifications

    except Exception as e:
        print(f"Error retrieving and processing batch results: {e}")
        return None


# Process Batches & Merge into One CSV
def run_batches():
    """Processes multiple batch requests sequentially and merges results into a single CSV."""
    batch_index = 0
    all_results = []  # Store DataFrames for final merge

    while True:
        jsonl_filename = f"data/json/batch_image_requests_{begin_date}-{end_date}_batch_{batch_index}.jsonl"

        if not os.path.exists(jsonl_filename):
            print("✅ All batches processed.")
            break  # No more batches left

        batch_id = submit_batch_job(jsonl_filename)

        if batch_id:
            status = check_batch_status(batch_id)

            if status == "completed":
                batch_results = retrieve_and_process_batch_results(batch_id)
                if batch_results is not None:
                    all_results.append(batch_results)

        batch_index += 1  

    # ✅ Append all batch results into a single DataFrame
    if all_results:
        final_classified_df = pd.concat(all_results, ignore_index=True)

        # ✅ Ensure tweet_id is a string before merging
        final_classified_df["tweet_id"] = final_classified_df["tweet_id"].astype(str)
        original_df["tweet_id"] = original_df["tweet_id"].astype(str)

    
        # ✅ Merge all classification results with original_df **AFTER all batches are processed**
        merged_df = original_df.merge(final_classified_df, on="tweet_id", how="left")

        # Save final merged results
        final_output_filename = f"data/raw/classified_images_{begin_date}-{end_date}.csv"
        merged_df.to_csv(final_output_filename, index=False, encoding="utf-8")

        print(f"✅ Final merged classification results saved to {final_output_filename}")

    # ✅ Create hand-code file after merging
    create_hand_code_file()


# ✅ Step 6: Run Batch Process
if __name__ == "__main__":
    start_time = time.time()
    create_jsonl_files()
    run_batches()
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"⏳ Total run time: {elapsed_time} seconds")




























# import pandas as pd
# import os
# import openai
# import time
# import json
# from dotenv import load_dotenv
# import sys
# import glob

# # Set working directory
# os.chdir("E:/TwitterBirth")

# # Load API Key
# load_dotenv(dotenv_path="config/.env")
# client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # Date range for filenames
# begin_date = "2018_01_01"
# end_date = "2018_12_31"

# # Load Data
# file_path = f"data/raw/classified_text_GPT4_{begin_date}-{end_date}.csv"
# if not os.path.exists(file_path):
#     print(f"Error: File '{file_path}' not found.")
#     sys.exit(1)

# original_df = pd.read_csv(file_path, encoding="utf-8")

# # Keep only tweets with pictures that are already classified as birth announcements
# pics_df = original_df[(original_df["has_picture"] == 1) & (original_df["text_classification"] == 1)].copy()
# pics_df = pics_df[["query_id", "tweet_id", "media_url"]]

# if pics_df.empty:
#     print("Error: No tweets with pictures found. Exiting.")
#     sys.exit(1)

# # Token Limits
# TOKENS_PER_REQUEST = 700
# ENQUEUED_TOKEN_LIMIT = 1_350_000
# MAX_TWEETS_PER_BATCH = 1000
# # MAX_TWEETS_PER_BATCH = 5

# # Define file paths
# output_filename = f"data/raw/classified_images_{begin_date}-{end_date}.csv"
# hand_code_path = f"data/raw/to_hand_code_{begin_date}-{end_date}.csv"


# def clear_old_image_batches():
#     """Deletes all previous batch JSONL files for image classification."""
#     jsonl_files = glob.glob("data/json/batch_image_requests_*.jsonl")  # Finds all batch JSONL files
#     for file in jsonl_files:
#         os.remove(file)  # Deletes the file
#     print(f"✅ Cleared {len(jsonl_files)} old image batch JSONL files.")

# def create_jsonl_files():
#     """Clears old batches, then splits `pics_df` into multiple batches and creates JSONL files."""
#     clear_old_image_batches()  # ✅ Clear JSONL files before creating new ones

#     batch_index = 0  # Track batch number

#     for start in range(0, len(pics_df), MAX_TWEETS_PER_BATCH):
#         batch_df = pics_df.iloc[start:start + MAX_TWEETS_PER_BATCH].copy()
#         batch_df["tweet_id"] = batch_df["tweet_id"].astype(str)  # Ensure `tweet_id` is a string

#         jsonl_filename = f"data/json/batch_image_requests_{begin_date}-{end_date}_batch_{batch_index}.jsonl"

#         with open(jsonl_filename, "w", encoding="utf-8") as f:
#             for _, row in batch_df.iterrows():
#                 data = {
#                     "custom_id": str(row["tweet_id"]),
#                     "method": "POST",
#                     "url": "/v1/chat/completions",
#                     "body": {
#                         "model": "gpt-4-turbo",
#                         "messages": [
#                             {
#                                 "role": "user",
#                                 "content": [
#                                     {"type": "text", "text": (
#                                         "Does this image likely represent a real-life birth announcement?"
#                                         "\nCriteria for '1' (Yes):"
#                                         "\n- A newborn baby (real, not animated) is clearly visible."
#                                         "\n- A mother in a hospital bed, appearing to have recently given birth."
#                                         "\n- A father or family member holding what appears to be a newborn."
#                                         "\n- A hospital setting with clear birth-related context (e.g., a bassinet, baby wristbands, medical staff)."
#                                         "\n\nCriteria for '0' (No):"
#                                         "\n- The image is animated, AI-generated, or a cartoon."
#                                         "\n- There are no humans visible, or the image contains unrelated objects."
#                                         "\n- The image does not have any clear birth-related elements."
#                                         "\n\nThink step by step and analyze the image carefully before responding."
#                                         "\nRespond ONLY with '1' (Birth Announcement) or '0' (Not Birth Announcement)."
#                                     )},
#                                     {"type": "image_url", "image_url": {"url": row["media_url"], "detail": "low"}}
#                                 ]
#                             }
#                         ]
#                     }
#                 }
#                 f.write(json.dumps(data, ensure_ascii=False) + "\n")


#         print(f"✅ JSONL file created: {jsonl_filename} with {len(batch_df)} requests.")
#         batch_index += 1  # Move to next batch


# # ✅ Step 2: Process Batches & Merge into One CSV
# def process_batches():
#     """Processes multiple batch requests sequentially and merges results into a single CSV."""
#     batch_index = 0
#     all_results = []  # Store DataFrames for final merge

#     while True:
#         jsonl_filename = f"data/json/batch_image_requests_{begin_date}-{end_date}_batch_{batch_index}.jsonl"

#         if not os.path.exists(jsonl_filename):
#             print("✅ All batches processed.")
#             break  # No more batches left

#         batch_id = submit_batch_job(jsonl_filename)

#         if batch_id:
#             status = check_batch_status(batch_id)

#             if status == "completed":
#                 batch_results = retrieve_and_process_batch_results(batch_id)
#                 if batch_results is not None:
#                     all_results.append(batch_results)

#         batch_index += 1  

#     # ✅ Append all batch results into a single DataFrame
#     if all_results:
#         final_classified_df = pd.concat(all_results, ignore_index=True)

#         # ✅ Ensure tweet_id is a string before merging
#         final_classified_df["tweet_id"] = final_classified_df["tweet_id"].astype(str)
#         original_df["tweet_id"] = original_df["tweet_id"].astype(str)

#         # ✅ Merge all classification results with original_df **AFTER all batches are processed**
#         merged_df = original_df.merge(final_classified_df, on="tweet_id", how="left")

#         # Save final merged results
#         final_output_filename = f"data/raw/classified_images_{begin_date}-{end_date}.csv"
#         merged_df.to_csv(final_output_filename, index=False, encoding="utf-8")

#         print(f"✅ Final merged classification results saved to {final_output_filename}")

#     # ✅ Create hand-code file after merging
#     create_hand_code_file()

# # ✅ Create Hand-Code File
# def create_hand_code_file():
#     """Creates a file with tweets that passed classification or need manual review due to missing classification."""
#     df = pd.read_csv(output_filename, encoding="utf-8")

#     # Ensure classification column is properly formatted
#     df["pic_classification"] = df["pic_classification"].fillna("MISSING").astype(str)  # Mark missing classifications

#     # Select tweets where classification is 1 OR where classification failed (MISSING)
#     hand_code = df[
#         (df["pic_classification"] == "1") | 
#         (df["pic_classification"] == "MISSING") |
#         ((df["text_classification"] == 1) & (df["has_picture"] == 0))
#     ]

#     # Save manually reviewable tweets
#     hand_code.to_csv(hand_code_path, encoding="utf-8", index=False)

#     print(len(hand_code), "tweets made it through classification or need manual review")
#     print(f"✅ Tweets saved to: {hand_code_path}")



# # ✅ Step 3: Submit Batch Job
# def submit_batch_job(jsonl_filename):
#     """Uploads the JSONL file and submits a batch job to OpenAI."""
#     try:
#         file_upload = client.files.create(
#             file=open(jsonl_filename, "rb"),
#             purpose="batch"
#         )
#         file_id = file_upload.id
#         print(f"File uploaded. File ID: {file_id}")

#         response = client.batches.create(
#             input_file_id=file_id,
#             endpoint="/v1/chat/completions",
#             completion_window="24h"
#         )

#         batch_id = response.id
#         print(f"Batch job submitted. Batch ID: {batch_id}")
#         return batch_id

#     except Exception as e:
#         print(f"Error submitting batch job: {e}")
#         return None


# # ✅ Step 4: Monitor Batch Job Status
# def check_batch_status(batch_id, max_wait_time=1800):
#     """Checks the batch job status until completion or timeout."""
#     if not batch_id:
#         print("No batch ID provided.")
#         return None

#     start_time = time.time()

#     while True:
#         try:
#             job_status = client.batches.retrieve(batch_id)
#             status = job_status.status
#             print(f"Batch Status: {status}")

#             if status in ["completed", "failed", "cancelled"]:
#                 print(f"Batch job {batch_id} ended with status: {status}")
#                 return status  

#             elapsed_time = time.time() - start_time
#             if elapsed_time > max_wait_time:
#                 print(f"⏳ Timeout: Exiting status check after {max_wait_time / 60} minutes.")
#                 return "timeout"

#             time.sleep(30)  

#         except Exception as e:
#             print(f"Error checking batch status: {e}")
#             return None


# # ✅ Step 5: Retrieve and Merge Batch Results
# def retrieve_and_process_batch_results(batch_id):
#     """Retrieves batch classification results and returns a DataFrame without modifying `original_df`."""
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
#         file_response = client.files.content(output_file_id)
#         results = file_response.text  

#         classifications = []
#         for line in results.splitlines():
#             response = json.loads(line)
#             tweet_id = str(response.get("custom_id"))  # Ensure tweet_id is a string
#             response_data = response.get("response", {})
#             status_code = response_data.get("status_code")

#             if status_code == 200:
#                 body = response_data.get("body", {})
#                 choices = body.get("choices", [])
#                 classification_text = choices[0]["message"]["content"].strip() if choices else None
#                 classification = classification_text if classification_text in ["1", "0"] else None

#             else:
#                 classification = None  

#             classifications.append({"tweet_id": tweet_id, "pic_classification": classification})

#         # ✅ Convert to DataFrame and return classification results **ONLY**
#         classified_df = pd.DataFrame(classifications)
#         classified_df["tweet_id"] = classified_df["tweet_id"].astype(str)  # Ensure tweet_id is a string

#         print(f"✅ Processed batch {batch_id} with {len(classified_df)} rows.")
#         return classified_df  # ✅ Return only classification results

#     except Exception as e:
#         print(f"Error retrieving and processing batch results: {e}")
#         return None


# # ✅ Step 6: Run Batch Process
# if __name__ == "__main__":
#     start_time = time.time()
#     create_jsonl_files()
#     process_batches()
#     end_time = time.time()
#     elapsed_time = end_time - start_time
#     print(f"⏳ Total run time: {elapsed_time} seconds")






