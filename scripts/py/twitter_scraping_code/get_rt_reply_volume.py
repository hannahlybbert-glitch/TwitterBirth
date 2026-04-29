import requests
import os
import csv
import time
import pandas as pd
from dotenv import load_dotenv
from dateutil.relativedelta import relativedelta
from tqdm import tqdm
import urllib3
from datetime import timedelta

# Load environment variables
load_dotenv(dotenv_path="config/.env")
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

if not BEARER_TOKEN:
    print("Bearer token not found! Please set it in your .env file or export it in your terminal.")
    exit()

# API Endpoint
TWEET_COUNTS_URL = "https://api.twitter.com/2/tweets/counts/all"

# Set year
year = "2013_2017"

# File paths
INPUT_CSV = f"data/raw/hand_coding/{year}/hand_coded_master_{year}.csv"
OUTPUT_CSV = f"data/raw/retweet_reply_volume_by_user_{year}.csv"

# ORIGINAL_VOLUME_CSV = f"data/raw/tweet_volume_by_user_{year}.csv"

# Load in hand coded data
df = pd.read_csv(INPUT_CSV, encoding="utf-8")
# Keep only if it is a birth announcement 
df = df[df["birth_announcement"] == 1]

# fill in missing values with 0 for "days_from"
df["days_from"] = df["days_from"].fillna(0)

# Convert post date
df["created_at_dt"] = pd.to_datetime(df["created_at"])

# subtract days_from for birth announcements that are not same day as actual birth
df["date_birth_dt"] = df["created_at_dt"] + pd.to_timedelta(df["days_from"], unit="D")

# Save birth date as a string (needed for unique_id and output)
df["date_birth"] = df["date_birth_dt"].dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

# Create a unique ID per birth (author_id + date of birth)
df["author_id"] = df["author_id"].astype(str).str.strip()
df["unique_id"] = df["author_id"] + "_" + df["date_birth"]

# Check for existing processed unique_id values
if os.path.exists(OUTPUT_CSV):
    existing_df = pd.read_csv(OUTPUT_CSV, encoding="utf-8", usecols=["unique_id"])
    processed_user_ids = set(existing_df["unique_id"].astype(str))
else:
    processed_user_ids = set()


if "author_id" not in df.columns or "user_created_at" not in df.columns or "created_at" not in df.columns:
    print("Error: CSV must contain 'author_id', 'user_created_at', and 'created_at' columns.")
    exit()

# convert account creation date
df["user_created_at_dt"] = pd.to_datetime(df["user_created_at"])


# Compute time window using timedelta (546 days before and after)
df["begin_date_dt"] = df["date_birth_dt"] - timedelta(days=546)
df["end_date_dt"] = df["date_birth_dt"] + timedelta(days=546)

# # Compute time window using lambda + apply **** This was used for 2018 data - but changed to the above for 2013-2017 ***
# df["begin_date_dt"] = df.apply(lambda row: row["date_birth_dt"] - relativedelta(years=1, months=6), axis=1)
# df["end_date_dt"] = df.apply(lambda row: row["date_birth_dt"] + relativedelta(years=1, months=6), axis=1)

# Adjust `begin_date` to be the account creation date if necessary
df["begin_date_dt"] = df.apply(lambda row: max(row["begin_date_dt"], row["user_created_at_dt"]), axis=1)

# Convert dates to Twitter API format
df["begin_date"] = df["begin_date_dt"].dt.strftime("%Y-%m-%dT00:00:00.000Z")
df["end_date"] = df["end_date_dt"].dt.strftime("%Y-%m-%dT23:59:59.999Z")


# Extract all unique birth events
unique_births = df[["unique_id", "author_id", "begin_date", "end_date"]].drop_duplicates()

# Randomize and filter out already processed unique_ids
new_births = unique_births.sample(frac=1, random_state=2061).reset_index(drop=True)
new_births = new_births[~new_births["unique_id"].isin(processed_user_ids)].reset_index(drop=True)


print(f"Total birth events in dataset: {len(unique_births)}")
print(f"Birth events already processed: {len(processed_user_ids)}")
print(f"Birth events left to process: {len(new_births)}")

# print(df[df["author_id"] == "126664098"][["unique_id", "date_birth", "begin_date", "end_date"]])


def get_tweet_counts(user_id, start_time, end_time):
    """Fetches daily retweets and reply tweet counts for a user within the given time range."""
    query_params = {
        "query": f'from:{user_id} (is:retweet OR is:reply)',
        "granularity": "day",
        "start_time": start_time,
        "end_time": end_time
    }

    all_tweet_counts = []
    next_token = None

    while True:
        try:
            if next_token:
                query_params["next_token"] = next_token

            response = requests.get(TWEET_COUNTS_URL, headers={"Authorization": f"Bearer {BEARER_TOKEN}"}, params=query_params)

            if response.status_code == 200:
                json_response = response.json()
                all_tweet_counts.extend(json_response.get("data", []))
                next_token = json_response.get("meta", {}).get("next_token")
                if not next_token:
                    break  # No more data

            elif response.status_code == 429:  # Rate limit hit
                print(f"Rate limit reached! Sleeping for 15 minutes...")
                time.sleep(15 * 60)  # 15-minute sleep

            else:
                print(f"Error fetching tweet counts for {user_id}: {response.status_code}, {response.text}")
                break  # Stop retrying for other errors

        except urllib3.exceptions.ProtocolError as e:
            if "10054" in str(e):  # Specific ConnectionResetError
                print(f"Critical connection error detected: {e}")
                print("Breaking execution immediately due to ConnectionResetError 10054.")
                exit(1)  # Immediately terminate script

            else:
                print(f"Other ProtocolError encountered: {e}")
                break  # Stop retrying for other protocol errors

        except requests.exceptions.RequestException as e:
            print(f"General request error for {user_id}: {e}")
            break  # Stop retrying for other request errors

    return all_tweet_counts



def save_to_csv(data, unique_id, filename):
   """Save tweet count data to CSV, including account creation and birth dates."""
   csv_headers = [
        "unique_id",
        "author_id",
        "user_created_at",
        "date_birth",
        "begin_date",
        "end_date",
        "date",
        "rt_reply_count"
    ]
   file_exists = os.path.isfile(filename)
   
   with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)

        if not file_exists:
            writer.writerow(csv_headers)  # Write headers if file does not exist

        user_row = df[df["unique_id"] == unique_id]
        if user_row.empty:
            return

        user_id = user_row["author_id"].values[0]
        user_created_at = user_row["user_created_at"].values[0]
        date_birth = user_row["date_birth"].values[0]
        begin_date = user_row["begin_date"].values[0]
        end_date = user_row["end_date"].values[0]

        if data:
            for entry in data:
                writer.writerow([unique_id,
                                 user_id, 
                                 user_created_at, 
                                 date_birth, 
                                 begin_date, 
                                 end_date, 
                                 entry["start"], 
                                 entry["tweet_count"]])
        else:
            writer.writerow([unique_id,
                             user_id, 
                             user_created_at, 
                             date_birth, 
                             begin_date, 
                             end_date, 
                             "No Data", 
                             0])

def main():
    """Fetches tweet counts for new users only and appends results."""
    if new_births.empty:
        print("No new birth events to process. Exiting.")
        return

    print(f"Fetching tweet counts for {len(new_births)} new birth events...")

    # Initialize progress bar
    for _, row in tqdm(new_births.iterrows(), total=len(new_births), desc="Processing Events", unit="event"):
        unique_id = row["unique_id"]
        user_id = row["author_id"]
        start_time = row["begin_date"]
        end_time = row["end_date"]

        tweet_counts = get_tweet_counts(user_id, start_time, end_time)
        save_to_csv(tweet_counts, unique_id, OUTPUT_CSV)

    print(f"Finished fetching tweet counts. Results appended to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()