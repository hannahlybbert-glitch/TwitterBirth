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

# Load API Key
load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Set file paths
begin_date = "2018_06_01"
end_date = "2018_06_30"
file_path = f"data/raw/query_results_{begin_date}-{end_date}.csv"

if not os.path.exists(file_path):
    print(f"Error: File '{file_path}' not found. Ensure it is in the correct directory.")
    sys.exit(1)

# Load CSV File
original_df = pd.read_csv(file_path, encoding="utf-8").iloc[200:245]

def truncate_text(text, max_chars=200):
    """Truncates text to a maximum character length, adding '…' if trimmed."""
    return text[:max_chars].strip() + ("…" if len(text) > max_chars else "")

# Keep only these baby-related emojis
KEEP_EMOJIS = {"👶", "🍼", "👼"}

def remove_unwanted_emojis(text):
    """Removes all emojis except for baby face, baby bottle, and baby angel."""
    return "".join(char if char in KEEP_EMOJIS or not emoji.is_emoji(char) else " " for char in text)

def preprocess_text(text, max_chars=200):
    """Preprocess tweet text to remove unnecessary characters and reduce token usage."""
    text = str(text).strip()
    
    # Convert &amp; -> &, etc.
    text = html.unescape(text)

    # Normalize Unicode (e.g., curly quotes to standard ASCII)
    text = unicodedata.normalize("NFKC", text)

    # Remove non-ASCII characters (curly quotes, dashes, etc.)
    text = text.encode("ascii", "ignore").decode()

    # Remove links and mentions
    text = re.sub(r"http\S+|www\S+|@\S+", "", text)

    # Keep only relevant baby-related emojis, remove others
    text = remove_unwanted_emojis(text)

    # Remove extra spaces
    text = re.sub(r"\s+", " ", text).strip()

    # Truncate tweet to reduce token usage
    return truncate_text(text, max_chars)


def create_jsonl_file(df, filename=f"data/json/batch_requests_{begin_date}-{end_date}.jsonl"):
    """Creates a JSONL file for OpenAI's Batch API processing, including custom_id for mapping."""
    with open(filename, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            processed_tweet = preprocess_text(row["text"], max_chars=200)  # Preprocess and truncate

            data = {
                "model": "gpt-4-turbo",
                "messages": [
                    {"role": "system", "content": "Classify if this tweet is a birth announcement."},
                    {"role": "user", "content": processed_tweet}
                ],
                "temperature": 0,
                "custom_id": str(row["tweet_id"])  # Store tweet_id as custom_id for mapping
            }

            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    print(f"✅ JSONL file created with {len(df)} requests.")

batch_input_file = client.files.create(
    file = open(f"data/json/batch_requests_{begin_date}-{end_date}.jsonl", "rb"),
    purpose = "batch"
)

# print(batch_input_file)

# create batch

batch_input_file_id = batch_input_file.id
client.batches.create(
    input_file_id = batch_input_file_id,
    endpoint = "/v1/chat/completions",
    completion_window = "24h",
    metadata = {
        "description": "test run"
    }
)

# check the status of the batch
batch = client.batches.retrieve("batch_abc123")
print(batch)


# retreieve results
file_response = client.files.content("file-xyz123")
print(file_response.text)

