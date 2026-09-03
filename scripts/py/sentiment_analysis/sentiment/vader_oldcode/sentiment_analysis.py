#!/usr/bin/env python3

# from transformers import pipeline
# classifier = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment")
# print(classifier("I love this new phone!"))


# import os
# import re
# import html
# import unicodedata
# import pandas as pd
# from tqdm import tqdm
# from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
# from multiprocessing import Pool, cpu_count, set_start_method

# # ----------------- Config -----------------
# INPUT_FILE = "data/raw/tweets_by_user_2018.csv"
# OUTPUT_FILE = "data/raw/tweet_sentiment_2018_parallel.csv"
# MAX_CHARS = 300
# BATCH_SIZE = 32           # Hugging Face pipeline batch size
# CHUNK_SIZE = 1000         # Number of tweets per parallel job
# NUM_WORKERS = cpu_count()

# # Suppress warnings from transformers
# from transformers import logging
# logging.set_verbosity_error()

# # ----------------- Preprocessing -----------------
# def preprocess_text(text, max_chars=MAX_CHARS):
#     text = str(text).strip()
#     text = html.unescape(text)
#     text = unicodedata.normalize("NFKC", text)
#     text = re.sub(r"https?://\S+|www\.\S+", "", text)
#     text = re.sub(r"\s+", " ", text).strip()
#     return text[:max_chars] + ("…" if len(text) > max_chars else "")

# # ----------------- Global pipeline (loaded inside each worker) -----------------
# def init_pipeline():
#     global classifier, label_map
#     model_name = "cardiffnlp/twitter-roberta-base-sentiment"
#     tokenizer = AutoTokenizer.from_pretrained(model_name)
#     model = AutoModelForSequenceClassification.from_pretrained(model_name)
#     classifier = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer, batch_size=BATCH_SIZE, truncation=False)
#     label_map = {"LABEL_0": -1, "LABEL_1": 0, "LABEL_2": 1}

# # ----------------- Worker -----------------
# def analyze_batch(batch_texts):
#     results = classifier(batch_texts)
#     return [(label_map.get(r["label"], None), r["score"]) for r in results]

# # ----------------- Main -----------------
# if __name__ == "__main__":
#     try:
#         set_start_method("spawn")  # safer on some OS setups (especially Windows)
#     except RuntimeError:
#         pass

#     # Load data
#     if not os.path.exists(INPUT_FILE):
#         raise FileNotFoundError(f"File not found: {INPUT_FILE}")

#     df = pd.read_csv(INPUT_FILE)
#     df.drop_duplicates(subset="tweet_id", inplace=True)
#     df["processed_text"] = df["text"].apply(preprocess_text)
#     texts = df["processed_text"].tolist()

#     print(f"🔍 Running sentiment on {len(texts)} tweets using {NUM_WORKERS} cores...")

#     # Split into chunks for parallel jobs
#     chunks = [texts[i:i + CHUNK_SIZE] for i in range(0, len(texts), CHUNK_SIZE)]

#     # Run in parallel
#     with Pool(processes=NUM_WORKERS, initializer=init_pipeline) as pool:
#         all_results = list(tqdm(pool.imap(analyze_batch, chunks), total=len(chunks)))

#     # Flatten results
#     flat_results = [item for sublist in all_results for item in sublist]
#     sentiments, confidences = zip(*flat_results)

#     # Add to DataFrame and save
#     df["sentiment"] = sentiments
#     df["confidence"] = confidences
#     df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")

#     print(f"✅ Done! Results saved to {OUTPUT_FILE}")


import os
import re
import html
import unicodedata
import pandas as pd
from tqdm import tqdm
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

# ----------------- Configuration -----------------
INPUT_FILE = "data/raw/tweets_by_user_2018.csv"
OUTPUT_FILE = "data/raw/tweet_sentiment_2018.csv"
MAX_CHARS = 300  # Truncate long tweets for speed

# ----------------- Preprocessing -----------------
def preprocess_text(text, max_chars=MAX_CHARS):
    text = str(text).strip()
    text = html.unescape(text)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"https?://\S+|www\.\S+", "", text)  # Remove links
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars] + ("…" if len(text) > max_chars else "")

# ----------------- Load Data -----------------
if not os.path.exists(INPUT_FILE):
    raise FileNotFoundError(f"File not found: {INPUT_FILE}")

df = pd.read_csv(INPUT_FILE)
df = df.iloc[0:10000]
df.drop_duplicates(subset="tweet_id", inplace=True)
df["processed_text"] = df["text"].apply(preprocess_text)

# ----------------- Load Model -----------------
print("🔄 Loading sentiment model...")
model_name = "cardiffnlp/twitter-roberta-base-sentiment"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSequenceClassification.from_pretrained(model_name)
classifier = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)

# ----------------- Map Labels -----------------
label_map = {
    "LABEL_0": -1,  # Negative
    "LABEL_1": 0,   # Neutral
    "LABEL_2": 1    # Positive
}

# ----------------- Run Sentiment Analysis -----------------
print(f"🔍 Running sentiment classification on {len(df)} tweets...")
sentiments = []
confidence_scores = []

for text in tqdm(df["processed_text"], desc="Classifying"):
    result = classifier(text)[0]
    label = result["label"]
    score = result["score"]
    
    sentiments.append(label_map.get(label, None))
    confidence_scores.append(score)

df["sentiment"] = sentiments
df["confidence"] = confidence_scores

# ----------------- Save Output -----------------
df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
print(f"Sentiment results saved to: {OUTPUT_FILE}")



# # load in tweets by user file
# # get a sentiment score for each tweet and save output

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
# import glob
# import tiktoken

# os.chdir("E:/TwitterBirth")
# # Load API Key
# load_dotenv(dotenv_path="config/.env")
# client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# INPUT_FILE = f"data/raw/tweets_by_user_2018.csv"
# OUTPUT_FILE = f"data/raw/tweet_sentiment_2018.csv"

# if not os.path.exists(INPUT_FILE):
#     print(f"Error: File '{INPUT_FILE}' not found. Ensure it is in the correct directory.")
#     sys.exit(1)

# MODEL_NUM = 4

# df = pd.read_csv(INPUT_FILE, encoding="utf-8")
# df = df.iloc[1000:1100]
# print(f"Started with {len(df)} tweets in file")

# ENQUEUED_TOKEN_LIMIT = 40_000_000
# MAX_TWEETS_PER_BATCH = 1000

# # Choose model name for token encoding
# MODEL_NAME = "gpt-4" if MODEL_NUM == 4 else "gpt-3.5-turbo"
# # encoding = tiktoken.encoding_for_model(MODEL_NAME)

# def preprocess_text(text, max_chars=300):
#     text = str(text).strip()
#     text = html.unescape(text)
#     text = unicodedata.normalize("NFKC", text)
#     text = re.sub(r"https?://\S+|www\.\S+", "", text)  # Remove links
#     text = re.sub(r"\s+", " ", text).strip()
#     return text[:max_chars] + ("…" if len(text) > max_chars else "")

# # def estimate_tokens(tweet_text):
# #     system_msg = (
# #         "You are a sentiment analysis assistant. Analyze the following tweet and classify its sentiment as follows:\n"
# #         "0: Negative, 1: Neutral, 2: Positive.\nRespond with only the corresponding number."
# #     )
# #     user_msg = f"Tweet: {tweet_text}\n\nSentiment:"
# #     return len(encoding.encode(system_msg)) + len(encoding.encode(user_msg)) + 4  # 4 = formatting overhead


# # # Preprocess and estimate token usage
# # df["processed_text"] = df["text"].apply(preprocess_text)
# # df["token_estimate"] = df["processed_text"].apply(estimate_tokens)

# # # Quick peek
# # # print(df[["text", "processed_text", "token_estimate"]].head())

# df["processed_text"] = df["text"].apply(preprocess_text)

# # ----- ChatGPT Batch Prompt Generation -----
# def get_sentiment_prompt(tweet_id, processed_text, model):
#     """
#     Create a JSON entry for a tweet for the batch call.
#     The system prompt instructs ChatGPT to analyze tweet sentiment:
#       - 0: Negative
#       - 1: Neutral
#       - 2: Positive
#     """
#     model_name = "gpt-3.5-turbo" if model == 3.5 else "gpt-4-turbo"
#     return {
#         "custom_id": str(tweet_id),
#         "method": "POST",
#         "url": "/v1/chat/completions",
#         "body": {
#             "model": model_name,
#             "messages": [
#                 {
#                     "role": "system",
#                     "content": (
#                         "You are a sentiment analysis assistant. Analyze the following tweet and classify its sentiment as follows:\n"
#                         "-1: Negative, 0: Neutral, 1: Positive.\n"
#                         "Respond with only the corresponding number."
#                     )
#                 },
#                 {
#                     "role": "user",
#                     "content": f"Tweet: {processed_text}\n\nSentiment:",
#                 }
#             ]
#         },
#     }

# def clear_old_batches():
#     """Removes old JSONL batch files before creating new ones."""
#     jsonl_files = glob.glob("data/json/sentiment_batch_requests_*.jsonl")
#     for file in jsonl_files:
#         os.remove(file)
#     print(f"Cleared {len(jsonl_files)} old batch JSONL files.")

# def create_jsonl_files():
#     """
#     Splits the tweet DataFrame into batches (based on estimated token limits) 
#     and writes each batch to a JSONL file for batch processing.
#     """
#     clear_old_batches()
#     batch_index = 0
#     for start in range(0, len(df), MAX_TWEETS_PER_BATCH):
#         batch_df = df.iloc[start:start + MAX_TWEETS_PER_BATCH].copy()
#         batch_df["tweet_id"] = batch_df["tweet_id"].astype(str)
#         jsonl_filename = f"data/json/sentiment_batch_requests_batch_{batch_index}.jsonl"
#         with open(jsonl_filename, "w", encoding="utf-8") as f:
#             for _, row in batch_df.iterrows():
#                 prompt = get_sentiment_prompt(row["tweet_id"], row["processed_text"], MODEL_NUM)
#                 f.write(json.dumps(prompt, ensure_ascii=False) + "\n")
#         print(f"Created JSONL file: {jsonl_filename} with {len(batch_df)} tweets.")
#         batch_index += 1    

# # ----- Batch Job Submission & Processing -----
# def submit_batch_job(jsonl_filename):
#     """Uploads the JSONL file to OpenAI and creates a batch job."""
#     try:
#         file_upload = client.files.create(file=open(jsonl_filename, "rb"), purpose="batch")
#         file_id = file_upload.id
#         response = client.batches.create(input_file_id=file_id, endpoint="/v1/chat/completions", completion_window="24h")
#         return response.id
#     except Exception as e:
#         print(f"Error submitting batch job for {jsonl_filename}: {e}")
#         return None
    
# def check_batch_status(batch_id):
#     """Polls the batch job until it completes (or fails/cancels)."""
#     while True:
#         try:
#             job_status = client.batches.retrieve(batch_id)
#             status = job_status.status
#             print(f"Batch {batch_id} status: {status}")
#             if status in ["completed", "failed", "cancelled"]:
#                 return status
#             time.sleep(30)  # Wait before checking again
#         except Exception as e:
#             print(f"Error checking status for batch {batch_id}: {e}")
#             return None
        
# def retrieve_and_process_batch_results(batch_id):
#     """
#     Once a batch is complete, retrieve its results, parse the response for sentiment,
#     and convert the results to a DataFrame.
#     """
#     try:
#         batch_info = client.batches.retrieve(batch_id)
#         output_file_id = batch_info.output_file_id
#         if not output_file_id:
#             print(f"No output file for batch {batch_id}.")
#             return None
#         file_response = client.files.content(output_file_id)
#         results = file_response.text
#         classifications = []
#         for line in results.splitlines():
#             response = json.loads(line)
#             tweet_id = str(response.get("custom_id"))
#             response_data = response.get("response", {})
#             status_code = response_data.get("status_code")
#             sentiment = None
#             if status_code == 200:
#                 body = response_data.get("body", {})
#                 choices = body.get("choices", [])
#                 sentiment_raw = choices[0]["message"]["content"].strip() if choices else None
#                 # Only accept valid numeric labels
#                 match = re.search(r"\b-1\b|\b0\b|\b1\b", sentiment_raw or "")
#                 if match:
#                     sentiment = int(match.group(0))
#                 else:
#                     print(f"⚠️ Unexpected sentiment output for tweet {tweet_id}: {sentiment_raw}")   
#             classifications.append({"tweet_id": tweet_id, "sentiment": sentiment})
#         return pd.DataFrame(classifications)
#     except Exception as e:
#         print(f"Error retrieving results for batch {batch_id}: {e}")
#         return None
    
                
# def process_batches():
#     """
#     Iterates over each JSONL batch file, submits the batch job,
#     waits for completion, and aggregates the results.
#     Finally, merges classification results with the original DataFrame and writes to CSV.
#     """
#     batch_index = 0
#     all_results = []
#     while True:
#         jsonl_filename = f"data/json/sentiment_batch_requests_batch_{batch_index}.jsonl"
#         if not os.path.exists(jsonl_filename):
#             print("All batches processed.")
#             break
#         batch_id = submit_batch_job(jsonl_filename)
#         if batch_id:
#             status = check_batch_status(batch_id)
#             if status == "completed":
#                 result_df = retrieve_and_process_batch_results(batch_id)
#                 if result_df is not None:
#                     all_results.append(result_df)
#         batch_index += 1

#     if all_results:
#         final_results = pd.concat(all_results, ignore_index=True)
#         final_results["tweet_id"] = final_results["tweet_id"].astype(str)
#         df["tweet_id"] = df["tweet_id"].astype(str)
#         merged_df = df.merge(final_results, on="tweet_id", how="left")
#         merged_df.to_csv(OUTPUT_FILE, index=False, encoding="utf-8")
#         print(f"Final classified results saved to {OUTPUT_FILE}")

# # ----- Main Execution -----
# if __name__ == "__main__":
#     start_time = time.time()
#     create_jsonl_files()
#     process_batches()
#     elapsed = time.time() - start_time
#     print(f"Elapsed time: {elapsed:.2f} seconds")        