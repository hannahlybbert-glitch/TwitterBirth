import os
import openai
import pandas as pd
import time
import json
from dotenv import load_dotenv
import sys

# Set working directory
os.chdir("/Users/rorylawson/Desktop/TwitterBirth")

# Load API Key
load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Date range for filenames
begin_date = "2018_01_01"
end_date = "2018_12_31"

# Load Data
file_path = f"data/raw/classified_text_{begin_date}-{end_date}.csv"
if not os.path.exists(file_path):
    print(f"Error: File '{file_path}' not found.")
    sys.exit(1)

original_df = pd.read_csv(file_path, encoding="utf-8")

# Keep only tweets with pictures that are already classified as birth announcements
pics_df = original_df[(original_df["has_picture"] == 1) & (original_df["text_classification"] == 1)].copy()
pics_df = pics_df[["query_id", "tweet_id", "media_url"]].dropna(subset=["media_url"])

if pics_df.empty:
    print("Error: No tweets with pictures found. Exiting.")
    sys.exit(1)

# ✅ Step 1: Create JSONL File for OpenAI Batch Processing
def create_jsonl_file(filename=f"data/json/batch_image_requests_{begin_date}-{end_date}.jsonl"):
    """Creates a JSONL file for OpenAI's Batch API for image classification."""
    with open(filename, "w", encoding="utf-8") as f:
        for _, row in pics_df.iterrows():
            data = {
                "custom_id": str(row["tweet_id"]),
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": "gpt-4-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "Determine if this image represents a birth announcement. "
                                       "Respond with '1' if it does, '0' otherwise."
                        },
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": "Analyze the image and determine if it likely represents a birth announcement."},
                                {"type": "image_url", "image_url": {"url": row["media_url"], "detail": "low"}}
                            ]
                        }
                    ]
                }
            }
            f.write(json.dumps(data, ensure_ascii=False) + "\n")
    
    print(f"JSONL file created with {len(pics_df)} requests.")

# ✅ Step 2: Submit Batch Job
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
        print(e)
        return None

# ✅ Step 3: Monitor Batch Job
def check_batch_status(batch_id):
    """Checks the status of the batch job until completion."""
    if not batch_id:
        print("No batch ID provided.")
        return

    while True:
        try:
            job_status = client.batches.retrieve(batch_id)
            status = job_status.status
            print(f"Batch Status: {status}")

            if status in ["completed", "failed", "cancelled"]:
                print(f"Batch job {batch_id} ended with status: {status}")
                break

            time.sleep(300)  # Check status every 300 seconds (5 minutes)
        except Exception as e:
            print(e)
            break

# ✅ Step 4: Retrieve and Process Batch Results
def retrieve_batch_results(batch_id):
    """Retrieves batch classification results from OpenAI and returns JSONL content as a list of dictionaries."""
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
        
        # Fetch results from OpenAI's Files API
        file_response = client.files.content(output_file_id)
        results = file_response.text.splitlines()  # List of JSON strings

        classifications = []
        for line in results:
            response = json.loads(line)
            custom_id = response.get("custom_id")
            response_data = response.get("response", {})
            status_code = response_data.get("status_code")

            if status_code == 200:
                body = response_data.get("body", {})
                choices = body.get("choices", [])
                classification_text = choices[0]["message"]["content"].strip() if choices else None
                classification = 1 if classification_text == "1" else 0
            else:
                classification = None  

            classifications.append({"tweet_id": str(custom_id), "pic_classification": classification})  # Ensure string format

        return pd.DataFrame(classifications)

    except Exception as e:
        print(f"Error retrieving batch results: {e}")
        return None

# ✅ Step 5: Merge and Save Results
def merge_and_save_results(classified_df, output_filename):
    """Merges classification results with original DataFrame and saves the final CSV."""
    if classified_df is None or classified_df.empty:
        print("No classified data available to merge.")
        return

    try:
        # Ensure `tweet_id` is string in both DataFrames for accurate merging
        original_df["tweet_id"] = original_df["tweet_id"].astype(str)
        classified_df["tweet_id"] = classified_df["tweet_id"].astype(str)

        # Merge on `tweet_id`
        merged_df = original_df.merge(classified_df, on="tweet_id", how="left")

        # Save the merged results
        merged_df.to_csv(output_filename, index=False, encoding="utf-8")

        print(f"Merged classification results successfully saved to {output_filename}")

    except Exception as e:
        print(f"Error merging and saving results: {e}")

# ✅ Run Batch Process
if __name__ == "__main__":
    start_time = time.time()
    jsonl_filename = f"data/json/batch_image_requests_{begin_date}-{end_date}.jsonl"
    output_filename = f"data/testing/classified_images_{begin_date}-{end_date}.csv"

    # Step 1: Create JSONL file
    create_jsonl_file(jsonl_filename)

    # Step 2: Submit batch job
    batch_id = submit_batch_job(jsonl_filename)

    # Step 3: Monitor batch status
    check_batch_status(batch_id)

    # Step 4: Retrieve and process results
    classified_df = retrieve_batch_results(batch_id)

    if classified_df is not None:
        # Step 5: Merge and save results
        merge_and_save_results(classified_df, output_filename)

    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Run time: {elapsed_time} seconds")












# import pandas as pd
# import os
# import openai
# import time
# from dotenv import load_dotenv
# from tqdm import tqdm
# import sys
# import time

# # Set working directory (temporary change for this script)
# os.chdir("/Users/rorylawson/Desktop/TwitterBirth")

# # Verify it's set correctly
# print(f"Current Working Directory: {os.getcwd()}")

# # Load API Key
# load_dotenv(dotenv_path="config/.env")  # ✅ Load only once
# client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # Date range for filenames
# begin_date = "2025_02_17"
# end_date = "2025_02_24"

# # Load Data
# file_path = f"data/raw/classified_text_{begin_date}-{end_date}.csv"
# if not os.path.exists(file_path):
#     print(f"Error: File '{file_path}' not found. Make sure it is in the correct directory.")
#     sys.exit(1)

# df = pd.read_csv(file_path, encoding="utf-8")

# # Keep only tweets with pictures
# # Filter only tweets that are classified as birth announcements and have pictures
# pics_df = df[(df["has_picture"] == 1) & (df["text_classification"] == 1)].copy()

# pics_df = pics_df[["query_id", "tweet_id", "media_url", "has_picture"]]

# # Check if DataFrame is empty
# if pics_df.empty:
#     print("Error: No tweets with pictures found. Exiting.")
#     sys.exit(1)

# # Ensure necessary columns exist
# required_columns = {"query_id", "tweet_id", "media_url", "has_picture"}
# if not required_columns.issubset(df.columns):
#     raise ValueError(f"Tweet CSV must contain columns: {required_columns}")

# # Enable tqdm progress tracking
# tqdm.pandas()

# # Function to classify an image
# def classify_image(image_url):
#     """Classifies an image using GPT-4V and returns 1 (birth announcement) or 0 (not a birth announcement)."""
#     try:
#         response = client.chat.completions.create(
#             model="gpt-4-turbo",
#             messages=[
#                 {"role": "system", "content": "You are an expert image classifier for identifying birth announcement images."},
#                 {"role": "user", "content": [
#                     {"type": "text", "text": "Does this image likely represent a birth announcement? Respond with '1' for Yes or '0' for No."},
#                     {"type": "image_url", "image_url": {"url": image_url, "detail": "low"}}  # ✅ Corrected structure
#                 ]}
#             ]
#         )

#         # Extract classification result
#         result = response.choices[0].message.content.strip()
        
#         # Ensure valid output (should be "1" or "0")
#         return "1" if result == "1" else "0"
    
#     except openai.RateLimitError as e:
#         print(f"Quota exceeded error: {e}. Stopping classification.")
#         raise  # Re-raise to stop further classification

#     except openai.OpenAIError as e:
#         print(f"❌ OpenAI API Error: {e}")
#         return "Error"  # Return error so we can debug failed classifications

# # Apply image classification with progress tracking
# start_time = time.time()
# print("🔍 Classifying images...")
# pics_df["pic_classification"] = pics_df["media_url"].progress_apply(classify_image)
# end_time = time.time()
# elapsed_time = end_time - start_time
# print(f"✅ Classification completed in {elapsed_time:.2f} seconds..")

# # Merge classification results back into the original DataFrame
# df = df.merge(pics_df[["tweet_id", "pic_classification"]], on="tweet_id", how="left")

# # Fill non-picture tweets with NA
# df["pic_classification"] = df["pic_classification"].apply(lambda x: x if pd.notna(x) else "NA")

# # Save results - this will just be for our records
# # the file itself likely will not be used unless we want to hand-check accuracy of image classifier
# record_file = f"data/testing/classified_pics_{begin_date}-{end_date}.csv"
# df.to_csv(record_file, index=False, encoding="utf-8")

# print(f"Classification results saved to: {record_file}")

# # Create the csv file that will be hand coded
# df = pd.read_csv(f"data/testing/classified_pics_{begin_date}-{end_date}.csv", encoding="utf-8")

# hand_code = df[(df["pic_classification"] == 1) | ((df["text_classification"] == 1) & (df["has_picture"] == 0)) ]

# output_path = f"data/testing/to_hand_code_{begin_date}-{end_date}.csv"
# hand_code.to_csv(output_path, encoding = "utf-8", index = False)

# print(len(hand_code), "tweets made it through classification")
# print(f"✅ Tweets saved to: {output_path}")
