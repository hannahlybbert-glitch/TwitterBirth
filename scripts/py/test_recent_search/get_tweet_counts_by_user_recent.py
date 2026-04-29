# Gets each tweet type and runs in batches of 5 (to respect basic tier rate limits of 5 requests per 5 minutes)
import requests
import os
import csv
import time
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv(dotenv_path="config/.env")

# Retrieve the bearer token
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

if not BEARER_TOKEN:
    print("Bearer token not found! Please set it in your .env file or export it in your terminal.")
    exit()

# API Endpoint
TWEET_COUNTS_URL = "https://api.twitter.com/2/tweets/counts/recent"

begin_date = "2025_02_17"
end_date = "2025_02_24"

BEGIN_TIME = "2025-02-17T00:00:00Z"
END_TIME = "2025-02-24T00:00:00Z"

# Headers for API requests
HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "User-Agent": "v2TweetCountsPython"
}

# Rate limit settings
REQUEST_LIMIT = 5  # 5 requests per 15 minutes
TIME_WINDOW = 15 * 60  # 15 minutes in seconds

# File Paths
INPUT_CSV = f"data/testing/hand_coded_{begin_date}-{end_date}.csv"  # Input file containing user_ids
OUTPUT_CSV = f"data/testing/tweet_counts_{begin_date}-{end_date}.csv"  # Output file for tweet counts

# Load User Data
df = pd.read_csv(INPUT_CSV, encoding="utf-8")
if "author_id" not in df.columns:
    print("Error: CSV must contain an 'author_id' column.")
    exit()

USER_IDS = df["author_id"].astype(str).tolist()[0:10]


def get_tweet_counts(user_id):
    """Fetches the number of original tweets in the last 7 days for a given user."""
    query_params = {
        "query": f"from:{user_id} -is:retweet -is:reply -is:quote",
        "granularity": "day",
        "start_time": BEGIN_TIME,
        "end_time": END_TIME
    }

    response = requests.get(TWEET_COUNTS_URL, headers=HEADERS, params=query_params)
    
    if response.status_code == 200:
        return response.json().get("data", [])
    elif response.status_code == 429:
        print(f"⚠️ Rate limit hit. Sleeping for {TIME_WINDOW} seconds...")
        time.sleep(TIME_WINDOW)
        return get_tweet_counts(user_id)  # Retry after sleeping
    else:
        print(f"Error fetching tweet counts for {user_id}: {response.status_code}, {response.text}")
        return None


def save_to_csv(data, user_id, filename):
    """Save tweet count data to CSV."""
    csv_headers = ["author_id", "date", "tweet_count"]

    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(csv_headers)

        if data:
            for entry in data:
                writer.writerow([user_id, entry["start"], entry["tweet_count"]])
        else:
            writer.writerow([user_id, "No Data", 0])


def main():
    print(f"Fetching tweet counts for {len(USER_IDS)} users...")

    for i in range(0, len(USER_IDS), REQUEST_LIMIT):  # Process in batches of 5
        batch = USER_IDS[i:i + REQUEST_LIMIT]
        for user_id in batch:
            tweet_counts = get_tweet_counts(user_id)
            save_to_csv(tweet_counts, user_id, OUTPUT_CSV)
            time.sleep(1)  # Respect 1 request per second limit
        
        if i + REQUEST_LIMIT < len(USER_IDS):
            print(f"Sleeping for {TIME_WINDOW} seconds to respect rate limits...")
            time.sleep(TIME_WINDOW)
    
    print("Finished fetching tweet counts.")


if __name__ == "__main__":
    main()

    