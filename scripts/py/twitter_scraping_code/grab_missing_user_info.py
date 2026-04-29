import requests
import csv
import time
from dotenv import load_dotenv
import os
import pandas as pd
from dateutil.relativedelta import relativedelta
from datetime import datetime

###################################################
### THIS SCRIPT SHOULD ONLY BE RAN ON 2018 DATA ###
###################################################

# **Load API Key from .env File**
load_dotenv(dotenv_path="config/.env")
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
USER_LOOKUP_URL = "https://api.twitter.com/2/users"

# Set file paths
original_csv = "data/raw/user_info_missing_bio_2018.csv"  # Final sample of handles from 2018
updated_csv = "data/raw/user_info_2018.csv"

# **Rate Limit Settings**
REQUEST_LIMIT = 900  # Max 900 requests per 15 minutes
TIME_WINDOW = 15 * 60  # 15 minutes in seconds
MAX_USERS_PER_REQUEST = 100  # Max 100 users per request
REQUESTS_MADE = 0
WINDOW_START_TIME = time.time()

# # **Load user IDs from your dataset**
# def load_user_ids(filename):
#     """Extract unique user IDs from an existing CSV file."""
#     user_ids = set()
#     with open(filename, "r", encoding="utf-8") as file:
#         reader = csv.DictReader(file)
#         for row in reader:
#             if row.get("author_id"):
#                 user_ids.add(row["author_id"])
#     return list(user_ids)


def load_user_ids(filename):
    """Extract unique user IDs, keeping the earliest timestamp per user."""
    df = pd.read_csv(filename, usecols=["author_id", "created_at"])

    # Ensure 'created_at' is in datetime format
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")

    # Drop rows with missing timestamps
    df = df.dropna(subset=["created_at"])

    # Keep only the earliest created_at per author_id
    df = df.sort_values(by=["created_at"]).drop_duplicates(subset=["author_id"], keep="first")

    # Return a list of unique author IDs
    return df["author_id"].astype(str).tolist()



# **Rate Limit Handling**
def manage_rate_limit():
    """Ensures we do not exceed Twitter API rate limits."""
    global REQUESTS_MADE, WINDOW_START_TIME

    elapsed_time = time.time() - WINDOW_START_TIME

    if REQUESTS_MADE >= REQUEST_LIMIT:
        if elapsed_time < TIME_WINDOW:
            wait_time = TIME_WINDOW - elapsed_time
            print(f"Rate limit reached! Sleeping for {wait_time:.2f} seconds...")
            time.sleep(wait_time)

        REQUESTS_MADE = 0  # Reset counter after waiting
        WINDOW_START_TIME = time.time()  # Reset the 15-minute window

# **Fetch user data from Twitter API**
def fetch_user_data(user_ids):
    """Fetches user metadata (bio, follower count) from the Twitter API."""
    global REQUESTS_MADE

    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    user_data = {}

    # Process in batches of 100
    for i in range(0, len(user_ids), MAX_USERS_PER_REQUEST):
        batch = user_ids[i:i + MAX_USERS_PER_REQUEST]
        params = {
            "ids": ",".join(batch),
            "user.fields": "id,username,name,created_at,description,public_metrics"
        }

        # Handle rate limits
        manage_rate_limit()

        response = requests.get(USER_LOOKUP_URL, headers=headers, params=params)
        REQUESTS_MADE += 1  # Track API requests

        if response.status_code == 200:
            data = response.json().get("data", [])
            for user in data:
                user_data[user["id"]] = {
                    "username": user.get("username", ""),
                    "name": user.get("name", ""),
                    "description": user.get("description", ""),
                    "followers_count": user.get("public_metrics", {}).get("followers_count", "")
                }
        else:
            print(f"Error fetching batch: {response.status_code}, {response.text}")

        time.sleep(1)  # Ensures we don’t send too many requests at once

    return user_data

def reorder_columns(df):
    """Moves 'description' and 'followers_count' right after 'user_created_at'."""
    if "user_created_at" in df.columns:
        user_created_index = df.columns.get_loc("user_created_at")

        # Move "description" right after "user_created_at"
        if "description" in df.columns:
            col = df.pop("description")
            df.insert(user_created_index + 1, "description", col)

        # Move "followers_count" right after "description"
        if "followers_count" in df.columns:
            col = df.pop("followers_count")
            df.insert(user_created_index + 2, "followers_count", col)

    return df

# **Save updated user data to a new CSV file**
def save_updated_user_data(original_file, output_file, user_data):
    """Merges new user data into the original dataset, filters birth announcements, and reorders columns."""
    
    # Load original dataset into Pandas
    df = pd.read_csv(original_file)

    # Keep only rows where birth_announcement == 1
    if "birth_announcement" in df.columns:
        df = df[df["birth_announcement"] == 1]

    # Merge user metadata
    df["description"] = df["author_id"].map(lambda x: user_data.get(str(x), {}).get("description", ""))
    df["followers_count"] = df["author_id"].map(lambda x: user_data.get(str(x), {}).get("followers_count", ""))

    # Reorder columns
    df = reorder_columns(df)
    
    # Save back to CSV
    df.to_csv(output_file, index=False, encoding = "utf-8")

# Main Execution
print("Extracting unique user IDs...")
user_ids = load_user_ids(original_csv)

print(f"Fetching metadata for {len(user_ids)} users...")
user_data = fetch_user_data(user_ids)

print("Merging user data with tweets and saving...")
save_updated_user_data(original_csv, updated_csv, user_data)

print(f"User data successfully added! Output saved as: {updated_csv}")





