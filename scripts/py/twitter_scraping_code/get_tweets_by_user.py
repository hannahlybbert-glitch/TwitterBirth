import requests
import csv
import time
import pandas as pd
from dotenv import load_dotenv
import os
from dateutil.relativedelta import relativedelta

os.chdir("E:/TwitterBirth")

# Load environment variables
load_dotenv(dotenv_path="config/.env")
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

if not BEARER_TOKEN:
    print("Bearer token not found! Please set it in your .env file or export it in your terminal.")
    exit()

# Twitter API Endpoint
TWEET_SEARCH_URL = "https://api.twitter.com/2/tweets/search/all"


# Headers for API requests
HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}",
    "User-Agent": "v2TweetSearchPython"
}

# Input file that has daily count of original and quote tweets by user during 3 year sample period
COUNTS_CSV = "data/raw/tweet_volume_by_user_2013_2017.csv"
# Define output CSV file
OUTPUT_CSV = "data/raw/tweets_by_user_2013_2017.csv"

# Check for already processed users
if os.path.exists(OUTPUT_CSV) and os.path.getsize(OUTPUT_CSV) > 0:
    try:
        existing_df = pd.read_csv(OUTPUT_CSV, encoding="utf-8", usecols=["author_id"])
        processed_user_ids = set(existing_df["author_id"].astype(str))
    except ValueError:
        print("Output file exists but doesn't contain 'author_id' column. Proceeding with empty processed list.")
        processed_user_ids = set()
else:
    processed_user_ids = set()


QUOTA_EXCEEDED = False

# set the remaining monthly quota of tweets (or just the max number of tweets we want to pull)
quota = 1906

# Load user data
df = pd.read_csv(COUNTS_CSV, encoding="utf-8")

# Parse date of birth
df["date_birth_dt"] = pd.to_datetime(df["date_birth"])

# Add helper column to count how many days of tweet volume data we have
df["days_volume_data"] = 1

# Aggregate daily tweet data to the unique birth event level
collapsed_df = df.drop(columns=["date"]).groupby(
    ["unique_id", "author_id", "user_created_at", "date_birth", "begin_date", "end_date"],
    as_index=False
).agg({
    "tweet_count": "sum",
    "days_volume_data": "sum"
})

# Convert dates for filtering
collapsed_df["date_birth_dt"] = pd.to_datetime(collapsed_df["date_birth"])
collapsed_df["begin_date_dt"] = pd.to_datetime(collapsed_df["begin_date"])

# Calculate number of pre-period days
collapsed_df["days_pre_period"] = (collapsed_df["date_birth_dt"] - collapsed_df["begin_date_dt"]).dt.days

# Filter to users with full pre-period and at least 50 tweets
collapsed_df = collapsed_df[
    (collapsed_df["days_pre_period"] >= 546) &
    (collapsed_df["tweet_count"] >= 50)
]

# Keep only the earliest birth per user
collapsed_df = collapsed_df.sort_values("unique_id").drop_duplicates(subset="author_id", keep="first")

# Sort by tweet count (ascending) to prioritize lower-volume users
collapsed_df = collapsed_df.sort_values(by="tweet_count", ascending=True)

# Apply tweet quota
collapsed_df["cumsum"] = collapsed_df["tweet_count"].cumsum()
collapsed_df = collapsed_df[collapsed_df["cumsum"] <= quota]

# # Get datetime vars for user_created_at and date_birth
collapsed_df["date_birth_dt"] = pd.to_datetime(collapsed_df["date_birth"])
# collapsed_df["user_created_at_dt"] = pd.to_datetime(collapsed_df["user_created_at"])


if "unique_id" not in collapsed_df.columns or "author_id" not in collapsed_df.columns or "begin_date" not in collapsed_df.columns or "end_date" not in collapsed_df.columns:
    print("Error: CSV must contain 'unique_id', 'author_id', 'begin_date', 'end_date', columns.")
    exit()

print(collapsed_df[["unique_id", "author_id", "tweet_count", "cumsum"]])

# Get unique user IDs
# make sure that author_id is a string
# collapsed_df["author_id"] = collapsed_df["author_id"].iloc[0:1].astype(str)
# USER_IDS = collapsed_df["author_id"].astype(str).unique().tolist()

collapsed_df = collapsed_df[collapsed_df["author_id"].notna()]
collapsed_df["author_id"] = collapsed_df["author_id"].astype(str)
USER_IDS = collapsed_df["author_id"].unique().tolist()


# print(USER_IDS)
# print(f"Already processed {processed_user_ids}")

new_user_ids = [user_id for user_id in USER_IDS if user_id not in processed_user_ids]

# print(new_user_ids)
# new_user_ids = new_user_ids
# print(f"About to process {new_user_ids}")

print(f"Total users in dataset: {len(USER_IDS)}")
print(f"Users already processed: {len(processed_user_ids)}")
print(f"Users left to process: {len(new_user_ids)}")

# Fields to collect
TWEET_FIELDS = "id,text,created_at,public_metrics,entities,attachments,referenced_tweets"
EXPANSIONS = "attachments.media_keys"
MEDIA_FIELDS = "media_key,type,url"

def fetch_tweets(user_id, start_time, end_time):
    """Fetches tweets from a user, extracting URLs, media, and tweet type."""
    query = f'from:{user_id} -is:retweet -is:reply'
    
    query_params = {
        "query": query,
        "tweet.fields": TWEET_FIELDS,
        "expansions": EXPANSIONS,
        "media.fields": MEDIA_FIELDS,
        "start_time": start_time,
        "end_time": end_time,
        "max_results": 500
    }

    all_tweets = []
    next_token = None  
    total_tweets_fetched = 0

    while True:
        if next_token:
            query_params["next_token"] = next_token

        print(f"Fetching tweets for {user_id}...")  
        response = requests.get(TWEET_SEARCH_URL, headers=HEADERS, params=query_params)

        if response.status_code == 200:
            json_response = response.json()
            tweets = json_response.get("data", [])

            if not tweets:
                print(f"API returned empty data for {user_id}. Full response: {json_response}")
                
                # Save a row indicating no data found for this user
                save_to_csv([{
                    "author_id": user_id,
                    "tweet_id": "No Data",
                    "created_at": "",
                    "text": "",
                    "like_count": "",
                    "retweet_count": "",
                    "reply_count": "",
                    "quote_count": "",
                    "tweet_type": "",
                    "tweet_url": "",
                    "embedded_urls": "",
                    "media_urls": ""
                }], OUTPUT_CSV)

                return []  # Stop processing this user

            # if not tweets:
            #     print(f"API returned empty data for {user_id}. Full response:")
            #     print(json_response)  # DEBUG: Print API response if empty
            #     break

            media_dict = {m["media_key"]: m.get("url", "") for m in json_response.get("includes", {}).get("media", [])}

            num_tweets_fetched = len(tweets)
            total_tweets_fetched += num_tweets_fetched
            print(f"   🔹 Fetched {num_tweets_fetched} tweets in this request. Total so far: {total_tweets_fetched}")

            for tweet in tweets:
                tweet_url = f"https://twitter.com/i/web/status/{tweet['id']}"  

                # urls = tweet.get("entities", {}).get("urls", [])
                # embedded_urls = "; ".join(
                #     [url["expanded_url"] for url in urls if "expanded_url" in url and not url["expanded_url"].startswith("https://twitter.com/")]
                # ) if urls else ""
                embedded_urls = ""

                media_keys = tweet.get("attachments", {}).get("media_keys", [])
                media_urls = "; ".join([media_dict[key] for key in media_keys if key in media_dict]) if media_keys else ""

                # tweet_type = "original"  # Default to original
                # if "referenced_tweets" in tweet:
                #     for ref in tweet["referenced_tweets"]:
                #         if ref.get("type") == "quoted":
                #             tweet_type = "quote"
                #             break
                tweet_type = "original"
                if any(ref.get("type") == "quoted" for ref in tweet.get("referenced_tweets", [])):
                    tweet_type = "quote"


                tweet_data = {
                    "author_id": user_id,
                    "tweet_id": tweet["id"],
                    "created_at": tweet["created_at"],
                    "text": tweet["text"],
                    "like_count": tweet["public_metrics"].get("like_count", 0),
                    "retweet_count": tweet["public_metrics"].get("retweet_count", 0),
                    "reply_count": tweet["public_metrics"].get("reply_count", 0),
                    "quote_count": tweet["public_metrics"].get("quote_count", 0),
                    "tweet_type": tweet_type,
                    "tweet_url": tweet_url,
                    "embedded_urls": embedded_urls,
                    "media_urls": media_urls
                }

                all_tweets.append(tweet_data)

            next_token = json_response.get("meta", {}).get("next_token")
            if not next_token:
                break  

        elif response.status_code == 429:
            print(f"Rate limit hit! Sleeping for 15 minutes...")
            time.sleep(15 * 60)

        elif response.status_code == 403:
            json_response = response.json()
            error_messages = [err["message"] for err in json_response.get("errors", [])]

            if any("Exceeded your monthly tweet cap" in msg for msg in error_messages):
                print(f"Monthly quota exceeded! Saving current data before stopping.")
                global QUOTA_EXCEEDED
                QUOTA_EXCEEDED = True
                return all_tweets  # Return what we have before stopping further requests

        else:
            print(f"Error fetching tweets for {user_id}: {response.status_code}, {response.text}")
            break  

    print(f"Finished fetching {total_tweets_fetched} tweets for {user_id}")
    return all_tweets


def save_to_csv(data, filename, unique_id=None):
    """Saves tweet data to CSV, including unique_id if provided."""
    csv_headers = [
        "unique_id", "author_id", "tweet_id", "created_at", "text",
        "like_count", "retweet_count", "reply_count", "quote_count",
        "tweet_type", "tweet_url", "embedded_urls", "media_urls"
    ]

    file_exists = os.path.isfile(filename) and os.path.getsize(filename) > 0

    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)

        if not file_exists:
            writer.writerow(csv_headers)

        for tweet in data:
            writer.writerow([
                unique_id or tweet.get("unique_id", ""),
                tweet["author_id"],
                tweet["tweet_id"],
                tweet["created_at"],
                tweet["text"],
                tweet["like_count"],
                tweet["retweet_count"],
                tweet["reply_count"],
                tweet["quote_count"],
                tweet["tweet_type"],
                tweet["tweet_url"],
                tweet["embedded_urls"],
                tweet["media_urls"]
            ])

    print(f"Saved {len(data)} tweets")




# def save_to_csv(data, filename):
#     """Saves tweet data to CSV, ensuring all fields match fetch_tweets."""
#     csv_headers = [
#         "author_id", "tweet_id", "created_at", "text",
#         "like_count", "retweet_count", "reply_count", "quote_count",
#         "tweet_type", "tweet_url", "embedded_urls", "media_urls"
#     ]

#     file_exists = os.path.isfile(filename) and os.path.getsize(filename) > 0

#     with open(filename, mode="a", newline="", encoding="utf-8") as file:
#         writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_MINIMAL)

#         if not file_exists:
#             writer.writerow(csv_headers)  # Write headers only if file is new

#         for tweet in data:
#             writer.writerow([
#                 tweet["author_id"], tweet["tweet_id"], tweet["created_at"], tweet["text"],
#                 tweet["like_count"], tweet["retweet_count"], tweet["reply_count"], tweet["quote_count"],
#                 tweet["tweet_type"], tweet["tweet_url"], tweet["embedded_urls"], tweet["media_urls"]
#             ])

#     print(f"Saved {len(data)} tweets")


def main():
    """Fetch tweets for new users only and stop execution if quota is exceeded."""
    global QUOTA_EXCEEDED
    QUOTA_EXCEEDED = False  # Initialize quota tracking

    if not new_user_ids:
        print("No new users to process. Exiting.")
        return

    print(f"Fetching tweets for {len(new_user_ids)} new users...")

    for user_id in new_user_ids:
        if QUOTA_EXCEEDED:
            print("Quota exceeded. Stopping script.")
            break  # Stop processing further users

        user_row = collapsed_df[collapsed_df["author_id"] == user_id]
        if user_row.empty:
            continue

        start_time, end_time = user_row["begin_date"].values[0], user_row["end_date"].values[0]

        unique_id = user_row["unique_id"].values[0]
        tweets = fetch_tweets(user_id, start_time, end_time)
        if tweets:
            save_to_csv(tweets, OUTPUT_CSV, unique_id=unique_id)

        if QUOTA_EXCEEDED:
            print("Quota exceeded. Exiting script after saving data.")
            break  # Stop the loop after saving what we have

        time.sleep(1)  # Respect rate limits

    print(f"Finished fetching user tweets. Results saved to {OUTPUT_CSV}")

if __name__ == "__main__":
    main()
    




