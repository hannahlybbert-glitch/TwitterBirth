import requests
import os
import csv
from dotenv import load_dotenv
import pandas as pd
import sys
import time


# make new file that loads in the hand-coded file and get the tweets from those users for the week

# Load environment variables
load_dotenv(dotenv_path="config/.env")

# Retrieve the bearer token
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

# Toggle test mode ON/OFF
TEST_MODE = False  # Set to True for testing (10 tweets), False for full dataset

# Set tweet limits based on test mode
TWEETS_PER_REQUEST = 10 if TEST_MODE else 100  # Adjust between 10-100
TWEETS_PER_ACCOUNT = 10 if TEST_MODE else None  # Adjust for total tweets per account

# Rate limit settings
REQUEST_LIMIT = 60  # 60 requests per 15 minutes
TIME_WINDOW = 15 * 60  
REQUESTS_MADE = 0  # Track API requests
START_TIME_WINDOW = time.time()  # Track when rate limit window starts

# Start and end date for file naming
begin_date = "2025_02_17"
end_date = "2025_02_24"

# File Paths
HAND_CODED = f"data/testing/hand_coded{begin_date}-{end_date}.csv"
OUTPUT_CSV = (
    "data/testing/tweet_types_test.csv" if TEST_MODE 
    else f"data/testing/tweet_types_{begin_date}-{end_date}.csv"
)

# **Load User Data**
if not os.path.exists(HAND_CODED):
    print(f"Error: File '{HAND_CODED}' not found. Ensure it is in the correct directory.")
    sys.exit(1)

df = pd.read_csv(HAND_CODED, encoding="utf-8")
df = df[df["birth_announcement"] == 1]

# Ensure required columns exist
required_columns = ["author_id", "tweet_count", "days_account"]
if not all(col in df.columns for col in required_columns):
    print(f"Error: CSV must contain columns {required_columns}")
    sys.exit(1)

# **Subset for Testing Mode**
USER_IDS = df["author_id"].astype(str).tolist()
USER_IDS = USER_IDS[:8] if TEST_MODE else USER_IDS  # Limit for testing

# **Twitter API Endpoints**
SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"

# **API Headers**
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}


def handle_rate_limit():
    """Handles Twitter API rate limits by pausing if necessary."""
    global REQUESTS_MADE, START_TIME_WINDOW

    REQUESTS_MADE += 1  # Increment request count
    elapsed_time = time.time() - START_TIME_WINDOW

    if REQUESTS_MADE >= REQUEST_LIMIT:
        if elapsed_time < TIME_WINDOW:
            sleep_time = TIME_WINDOW - elapsed_time
            print(f"⚠️ Rate limit approaching. Sleeping for {sleep_time:.2f} seconds...")
            time.sleep(sleep_time + 1)
        # Reset counter
        REQUESTS_MADE = 0
        START_TIME_WINDOW = time.time()


def make_request(url, params=None):
    """Makes a request to the Twitter API with rate limit handling."""
    while True:
        handle_rate_limit()  # Check rate limit before sending request
        response = requests.get(url, headers=HEADERS, params=params)

        if response.status_code == 429:
            print("⚠️ Rate limit exceeded. Sleeping and retrying...")
            time.sleep(60)  # Sleep for a minute before retrying
            continue  # Retry request

        return response


def get_tweets(user_id):
    """Fetches tweets from a user's timeline using the Recent Search API."""
    query = f"from:{user_id} -is:retweet -is:reply"
    params = {
        "query": query,
        "max_results": TWEETS_PER_REQUEST,
        "tweet.fields": "created_at,text,public_metrics,referenced_tweets"
    }

    all_tweets = []
    next_token = None
    retries = 0
    max_retries = 3  # Maximum retries for temporary errors

    while True:
        if next_token:
            params["next_token"] = next_token

        response = make_request(SEARCH_URL, params)

        if response.status_code == 503:
            if retries < max_retries:
                retries += 1
                wait_time = 30  # Wait 30 seconds before retrying
                print(f"⚠️ Service Unavailable (503). Retrying {retries}/{max_retries} in {wait_time} seconds...")
                time.sleep(wait_time)
                continue  # Retry the request
            else:
                print(f"❌ Max retries reached for user {user_id}. Skipping...")
                return []  # Return empty list if retries failed

        if response.status_code != 200:
            print(f"Error fetching tweets for user {user_id}: {response.status_code}, {response.text}")
            return []  # Ensure the function always returns a valid result

        data = response.json()
        tweets = data.get("data", [])
        all_tweets.extend(tweets)

        print(f"Fetched {len(tweets)} tweets for user {user_id}, Total: {len(all_tweets)}")

        # Stop if we reach the total tweets limit per user
        if TWEETS_PER_ACCOUNT is not None and len(all_tweets) >= TWEETS_PER_ACCOUNT:
            break

        # Check for next page of results
        next_token = data.get("meta", {}).get("next_token")
        if not next_token:
            print(f"No more tweets available for user {user_id}.")
            break

        # Respect Twitter API rate limits
        time.sleep(1)

    return all_tweets[:TWEETS_PER_ACCOUNT] if TWEETS_PER_ACCOUNT else all_tweets



def save_to_csv(tweets, filename, user_id, tweet_count, days_account):
    """Ensures every user is recorded, even if they have zero tweets. Prevents misalignment in the CSV file."""
    csv_headers = [
        "author_id", "tweet_id", "tweet_url", "created_at", "text",
        "like_count", "retweet_count", "reply_count", "quote_count", "tweet_count", "days_account"
    ]

    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="", encoding="utf-8-sig") as file:
        writer = csv.writer(file)

        # Write headers only if the file is new
        if not file_exists:
            writer.writerow(csv_headers)

        if len(tweets) == 0:
            # **Ensure correct column alignment even when no tweets exist**
            writer.writerow([user_id, "", "", "", "", "", "", "", "", tweet_count, days_account])
            print(f"✅ User {user_id} had no tweets. Metadata recorded.")
        else:
            for tweet in tweets:
                tweet_id = tweet.get("id", "")
                tweet_url = f"https://x.com/i/web/status/{tweet_id}"  # No username involved

                writer.writerow([
                    user_id, tweet_id, tweet_url, tweet.get("created_at", ""), tweet.get("text", ""),
                    tweet["public_metrics"].get("like_count", 0),
                    tweet["public_metrics"].get("retweet_count", 0),
                    tweet["public_metrics"].get("reply_count", 0),
                    tweet["public_metrics"].get("quote_count", 0),
                    tweet_count, days_account
                ])
    print(f"✅ User {user_id} saved. Tweets Fetched: {len(tweets)}")


start_time = time.time()
# **Main Execution**
for index, row in df.iterrows():
    user_id = str(row["author_id"])
    save_to_csv(get_tweets(user_id), OUTPUT_CSV, user_id, row["tweet_count"], row["days_account"])
end_time = time.time()

elapsed_time = end_time - start_time
print(f"⏳ {elapsed_time:.2f} seconds elapsed")


# import requests
# import os
# import csv
# from dotenv import load_dotenv
# import pandas as pd
# import sys
# import time
# from datetime import datetime, timedelta

# # Load environment variables
# load_dotenv(dotenv_path="config/.env")

# # Retrieve the bearer token
# BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

# # Toggle test mode ON/OFF
# TEST_MODE = True  # Set to True for testing (10 tweets), False for full dataset

# # Set tweet limits based on test mode
# TWEETS_PER_REQUEST = 10 if TEST_MODE else 100  # Adjust between 10-100
# TWEETS_PER_ACCOUNT = 10 if TEST_MODE else 300  # Adjust for total tweets per account

# # Rate limit settings
# REQUEST_LIMIT = 300  # Twitter allows 300 requests per 15 minutes
# TIME_WINDOW = 15 * 60  # 15 minutes in seconds
# REQUESTS_MADE = 0  # Track API requests
# START_TIME_WINDOW = time.time()  # Track when rate limit window starts

# # Define start and end times (defaults to last 7 days)
# START_TIME = None
# END_TIME = None

# if START_TIME is None:
#     START_TIME = (datetime.utcnow() - timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
# if END_TIME is None:
#     END_TIME = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

# # Start and end date for file naming
# begin_date = "2025_02_11"
# end_date = "2025_02_18"

# # File Paths
# USER_CSV = "data/testing/handles_final_2025_02_11-2025_02_18.csv"
# OUTPUT_CSV = (
#     "data/testing/tweet_types_test.csv" if TEST_MODE 
#     else f"data/testing/tweet_types_{begin_date}-{end_date}.csv"
# )

# # **Load User Data**
# if not os.path.exists(USER_CSV):
#     print(f"Error: File '{USER_CSV}' not found. Ensure it is in the correct directory.")
#     sys.exit(1)

# df = pd.read_csv(USER_CSV, encoding="utf-8")

# # Ensure required columns exist
# required_columns = ["author_id", "tweet_count", "days_account"]
# if not all(col in df.columns for col in required_columns):
#     print(f"Error: CSV must contain columns {required_columns}")
#     sys.exit(1)

# # **Subset for Testing Mode**
# USER_IDS = df["author_id"].astype(str).tolist()

# # **Twitter API Endpoints**
# USER_LOOKUP_URL = "https://api.twitter.com/2/users/{}?user.fields=username"
# SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"

# # **API Headers**
# HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}


# def handle_rate_limit():
#     """Handles Twitter API rate limits by pausing if necessary."""
#     global REQUESTS_MADE, START_TIME_WINDOW

#     REQUESTS_MADE += 1  # Increment request count
#     elapsed_time = time.time() - START_TIME_WINDOW

#     if REQUESTS_MADE >= REQUEST_LIMIT:
#         if elapsed_time < TIME_WINDOW:
#             sleep_time = TIME_WINDOW - elapsed_time
#             print(f"⚠️ Rate limit approaching. Sleeping for {sleep_time:.2f} seconds...")
#             time.sleep(sleep_time + 1)
#         # Reset counter
#         REQUESTS_MADE = 0
#         START_TIME_WINDOW = time.time()


# def make_request(url, params=None):
#     """Makes a request to the Twitter API with rate limit handling."""
#     while True:
#         handle_rate_limit()  # Check rate limit before sending request
#         response = requests.get(url, headers=HEADERS, params=params)
        
#         if response.status_code == 429:
#             print("⚠️ Rate limit exceeded. Sleeping and retrying...")
#             time.sleep(60)  # Sleep for a minute before retrying
#             continue  # Retry request
        
#         return response


# def get_username(user_id):
#     """Fetch username using Twitter API."""
#     response = make_request(USER_LOOKUP_URL.format(user_id))
    
#     if response.status_code == 200:
#         return response.json()["data"].get("username", "unknown")
#     else:
#         print(f"Error getting username for {user_id}: {response.status_code}, {response.text}")
#         return "unknown"


# def get_tweets(user_id):
#     """Fetches tweets from a user's timeline using the Recent Search API."""
#     query = f"from:{user_id}"
#     params = {
#         "query": query,
#         "max_results": TWEETS_PER_REQUEST,
#         "tweet.fields": "created_at,text,public_metrics,referenced_tweets",
#         "start_time": START_TIME,
#         "end_time": END_TIME
#     }

#     all_tweets = []
#     next_token = None

#     while True:
#         if next_token:
#             params["next_token"] = next_token

#         response = make_request(SEARCH_URL, params)
#         if response.status_code != 200:
#             print(f"Error fetching tweets for user {user_id}: {response.status_code}, {response.text}")
#             return all_tweets  

#         data = response.json()
#         tweets = data.get("data", [])
#         all_tweets.extend(tweets)

#         print(f"Fetched {len(tweets)} tweets for user {user_id}, Total: {len(all_tweets)}")

#         # Stop if we reach the total tweets limit per user
#         if TWEETS_PER_ACCOUNT is not None and len(all_tweets) >= TWEETS_PER_ACCOUNT:
#             break

#         # Check for next page of results
#         next_token = data.get("meta", {}).get("next_token")
#         if not next_token:
#             print(f"No more tweets available for user {user_id}.")
#             break

#         # Respect Twitter API rate limits
#         time.sleep(1)

#     return all_tweets[:TWEETS_PER_ACCOUNT] if TWEETS_PER_ACCOUNT else all_tweets


# def classify_tweet(tweet):
#     """Classifies a tweet as an original tweet, retweet, quote tweet, or reply."""
#     referenced_tweets = tweet.get("referenced_tweets", [])

#     if not referenced_tweets:
#         return "Original Tweet"

#     for ref in referenced_tweets:
#         if ref["type"] == "retweeted":
#             return "Retweet"
#         elif ref["type"] == "quoted":
#             return "Quote Tweet"
#         elif ref["type"] == "replied_to":
#             return "Reply"

#     return "Unknown"


# def save_to_csv(tweets, filename, user_id, username, tweet_count, days_account):
#     """Ensures every user is recorded, even if they have zero tweets. Prevents misalignment in the CSV file."""
#     csv_headers = [
#         "author_id", "username", "tweet_id", "tweet_url", "created_at", "text", "tweet_type",
#         "like_count", "retweet_count", "reply_count", "quote_count", "tweet_count", "days_account"
#     ]

#     file_exists = os.path.isfile(filename)
#     with open(filename, mode="a", newline="", encoding="utf-8-sig") as file:
#         writer = csv.writer(file)

#         # Write headers only if the file is new
#         if not file_exists:
#             writer.writerow(csv_headers)

#         if len(tweets) == 0:
#             # If no tweets, write a metadata row ensuring username is present
#             writer.writerow([
#                 user_id, username, "", "", "", "", "", "", "", "", "", tweet_count, days_account
#             ])
#             print(f"✅ User {user_id} had no tweets in this period. Metadata recorded.")
#         else:
#             for tweet in tweets:
#                 tweet_id = tweet.get("id", "")
#                 tweet_url = f"https://x.com/{username}/status/{tweet_id}" if username else f"https://x.com/i/web/status/{tweet_id}"

#                 writer.writerow([
#                     user_id, username, tweet_id, tweet_url, tweet.get("created_at", ""), tweet.get("text", ""), classify_tweet(tweet),
#                     tweet["public_metrics"].get("like_count", 0),
#                     tweet["public_metrics"].get("retweet_count", 0),
#                     tweet["public_metrics"].get("reply_count", 0),
#                     tweet["public_metrics"].get("quote_count", 0),
#                     tweet_count, days_account
#                 ])

#     print(f"✅ User {user_id} saved. Tweets Fetched: {len(tweets)}")


# # **Main Execution**
# for index, row in df.iterrows():
#     user_id = str(row["author_id"])
#     username = get_username(user_id)
#     save_to_csv(get_tweets(user_id), OUTPUT_CSV, user_id, username, row["tweet_count"], row["days_account"])
