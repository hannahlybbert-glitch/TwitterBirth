# Includes a "test mode" which allows to test 10 tweets - otherwise gets 100 tweets
import requests
import os
import csv
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re
import pandas as pd

# Load environment variables
load_dotenv(dotenv_path="config/.env")

# Retrieve the bearer token
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

# Toggle test mode ON/OFF
TEST_MODE = True  # Set to True for testing (10 tweets), False for full dataset

# Set tweet limits based on test mode
MAX_TWEETS = 10 if TEST_MODE else None  # this will set the max tweets per query
TWEETS_PER_REQUEST = 10 if TEST_MODE else 100 # needs to be between 10 and 100

# Rate limit settings
REQUEST_LIMIT = 60  # 60 requests per 15 minutes
TIME_WINDOW = 15 * 60  

# Optional start and end times
# START_TIME = "2025-02-15T00:00:00Z"  
# END_TIME = "2025-02-15T23:59:59Z"  
START_TIME = None
END_TIME = None


# If START_TIME is None, default to 7 days ago (Recent Search API behavior)
if START_TIME is None:
    begin_timestamp = (datetime.utcnow() - timedelta(days=7)).strftime("%Y%m%dT%H%M%SZ")
else:
    begin_timestamp = START_TIME.replace(":", "").replace("-", "")

# start date for filepath    
begin_date = (datetime.utcnow() - timedelta(days=7)).strftime("%Y_%m_%d")

# If END_TIME is None, default to the current time (Recent Search API behavior)
if END_TIME is None:
    end_timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
else:
    end_timestamp = END_TIME.replace(":", "").replace("-", "")

# end date for filepath
end_date = datetime.utcnow().strftime("%Y_%m_%d")

# print(f"In file we have: {begin_timestamp} and {end_timestamp}, in filename we have: {begin_date} and {end_date}")

# Define the OUTPUT_CSV file path
OUTPUT_CSV = (
    "data/testing/query_test.csv" if TEST_MODE 
    else f"data/testing/query_results_{begin_date}-{end_date}.csv"
)

# print(OUTPUT_CSV)

# Output CSV file (uses correct file names)
# OUTPUT_CSV = "data/testing/birthtweets_test.csv" if TEST_MODE else "data/testing/brithtweets_.csv"


# two hour period from 1:00pm until 3pm
# START_TIME = "2025-02-06T13:00:00Z"
# END_TIME = "2025-02-06T15:00:00Z"


# Narrow searches - run these for the entire week
QUERIES = {
    # Query 1: Structured birth announcements (Explicit, well-formed statements) (with pictures)
    1: '("welcome to the world baby" OR ("life update" "baby") OR "introducing baby" OR "our little one has arrived" OR "our new baby" OR "meet our baby" OR "our family just got bigger" OR "we had a baby" OR "our bundle of joy" OR "our baby is here" OR "we had our baby") has:images -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -"welcome to the world of" -"born again" -"chromosome" -"i was born" -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle',

    # Query 2: Option 1 without pictures
    2: '("welcome to the world baby" OR ("life update" "baby") OR "introducing baby" OR "our little one has arrived" OR "our new baby" OR "meet our baby" OR "our family just got bigger" OR "we had a baby" OR "our bundle of joy" OR "our baby is here" OR "we had our baby") -has:media -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -"welcome to the world of" -"born again" -"chromosome" -"i was born" -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle',
    
    # Query 3: Somewhat broad search (with pictures)
    3: '(("born" "wife" "baby") OR ("born after" "labor" "hours") OR ("born" "pounds" "ounces") OR ("born" "lbs" "oz") OR ("mom and baby are") OR ("born" "c-section") OR ("say hello to baby") OR ("say hi to baby") OR ("born at" "AM") OR ("born at" "PM") OR ("born" "this morning") OR ("born at" "this morning") OR ("born at" "afternoon")) has:images -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle',

    # Query 4: Somewhat broad search (without pictures)
    4: '(("born" "wife" "baby") OR ("born after" "labor" "hours") OR ("born" "pounds" "ounces") OR ("born" "lbs" "oz") OR ("mom and baby are") OR ("born" "c-section") OR ("say hello to baby") OR ("say hi to baby") OR ("born at" "AM") OR ("born at" "PM") OR ("born" "this morning") OR ("born at" "this morning") OR ("born at" "afternoon")) -has:media -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle',
     
    # Query 5: Family-centered birth phrases (with pictures)
    5: '(("had my baby" "today") OR ("i gave birth" "ago") OR ("i gave birth" "today") OR ("i gave birth" "yesterday") OR ("i gave birth" "last night") OR "meet your baby brother" OR "meet your baby sister" OR "was born last night" OR "was born a few hours ago" OR "we are officially parents") has:images -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle',

    # Query 6: Family-centered birth phrases (without pictures)
    6: '(("had my baby" "today") OR ("i gave birth" "ago") OR ("i gave birth" "today") OR ("i gave birth" "yesterday") OR ("i gave birth" "last night") OR "meet your baby brother" OR "meet your baby sister" OR "was born last night" OR "was born a few hours ago" OR "we are officially parents") -has:media -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle',

    # Query 7: Broadish search with pictures
    7: '("welcomed our baby" OR ("i became a mother" "today") OR ("i became a father" "today") OR ("went into labor" "ago") OR "delivered naturally" OR "we had a baby girl" OR "we had a baby boy" OR "welcoming our newest blessing" OR "we became parents today" OR "baby finally arrived") has:images -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle',

    # Query 8: Broadish search without pictures
    8: '("welcomed our baby" OR ("i became a mother" "today") OR ("i became a father" "today") OR ("went into labor" "ago") OR "delivered naturally" OR "we had a baby girl" OR "we had a baby boy" OR "welcoming our newest blessing" OR "we became parents today" OR "baby finally arrived") -has:media -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle',
    
    # Query 9: permutations of "i had a baby" with pictures
    9: '(("i had a baby" "ago") OR ("i had a baby" "today") OR ("i had a baby" "last night") OR ("i had a baby" "yesterday") OR ("i had a baby" "this morning") OR ("arrived" "baby" "wife") OR ("arrived" "baby" "husband")) has:images -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle',
    
    # Query 10: permutations of "i had a baby" without pictures
    10: '(("i had a baby" "ago") OR ("i had a baby" "today") OR ("i had a baby" "last night") OR ("i had a baby" "yesterday") OR ("i had a baby" "this morning") OR ("arrived" "baby" "wife") OR ("arrived" "baby" "husband")) -has:media -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle'
}



if not BEARER_TOKEN:
    print("Bearer token not found! Please set it in your .env file or export it in your terminal.")
    exit()

print(f"Bearer token loaded successfully. TEST_MODE: {TEST_MODE}")

search_url = "https://api.twitter.com/2/tweets/search/recent"

def bearer_oauth(r):
    """Method required by bearer token authentication."""
    r.headers["Authorization"] = f"Bearer {BEARER_TOKEN}"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    return r

def connect_to_endpoint(url, params):
    """Connect to the Twitter API endpoint with the provided URL and parameters."""
    while True:
        response = requests.get(url, auth=bearer_oauth, params=params)
        print(f"Status Code: {response.status_code}")

        if response.status_code == 429:
            reset_time = int(response.headers.get("x-rate-limit-reset", time.time() + TIME_WINDOW))
            wait_time = max(1, reset_time - int(time.time()))
            print(f"Rate limit hit. Sleeping for {wait_time} seconds...")
            time.sleep(wait_time + 1)
        elif response.status_code != 200:
            raise Exception(response.status_code, response.text)
        else:
            return response.json()
        

def save_to_csv(data, users, media, query_id, filename=OUTPUT_CSV):
    """Save tweet and user data to a CSV file, optimizing by directly accessing values."""
    
    csv_headers = [
        "query_id", "author_id", "username", "tweet_id", "created_at", "text", "media_url", 
        "has_picture", "tweet_url", "profile_image_url", "like_count", "retweet_count", 
        "reply_count", "quote_count", "user_created_at", "following_count", "tweet_count", 
        "verified", "verified_type", "start_time", "end_time"
    ]

    file_exists = os.path.isfile(filename)
    with open(filename, mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(csv_headers)

        user_map = {user["id"]: user for user in users}
        media_map = {m["media_key"]: m for m in media} if media else {}


        for tweet in data:
            user = user_map.get(tweet["author_id"], {})
            media_url = ""
            profile_image_url = user.get("profile_image_url", "").replace("_normal", "_400x400")

            if "attachments" in tweet and "media_keys" in tweet["attachments"]:
                for media_key in tweet["attachments"]["media_keys"]:
                    media_item = media_map.get(media_key, {})
                    media_url = media_item.get("url", media_item.get("preview_image_url", "NA"))
                    break  # Only grab the first available media

            writer.writerow([
                query_id,
                tweet.get("author_id"),
                user.get("username"),
                tweet.get("id"),
                tweet.get("created_at"),
                tweet.get("text"),
                media_url,
                "1" if "attachments" in tweet and "media_keys" in tweet["attachments"] else "0",
                f"https://x.com/{user.get('username')}/status/{tweet.get('id')}" if user.get("username") else "NA",
                profile_image_url,  # Profile Image URL
                tweet["public_metrics"].get("like_count"),
                tweet["public_metrics"].get("retweet_count"),
                tweet["public_metrics"].get("reply_count"),
                tweet["public_metrics"].get("quote_count"),
                user.get("created_at"),
                user.get("public_metrics", {}).get("following_count"),
                user.get("public_metrics", {}).get("tweet_count"),
                user.get("verified"),
                user.get("verified_type"),  
                START_TIME,
                END_TIME
            ])
    
    print(f"Filtered tweets saved to {filename} for query {query_id}!")



def run_query(query_id, query_text):
    """Runs an individual query and saves results to CSV, handling pagination."""
    total_tweets = 0
    next_token = None

    while MAX_TWEETS is None or total_tweets < MAX_TWEETS:
        query_params = {
            'query': query_text,
            'tweet.fields': 'author_id,created_at,text,lang,public_metrics,attachments',
            'user.fields': 'username,created_at,description,public_metrics,url,verified,verified_type,profile_image_url',
            'media.fields': 'media_key,type,url,preview_image_url',
            'expansions': 'author_id,attachments.media_keys',
            'max_results': TWEETS_PER_REQUEST
        }

        if START_TIME:
            query_params['start_time'] = START_TIME
        if END_TIME:
            query_params['end_time'] = END_TIME
        if next_token:
            query_params['next_token'] = next_token

        json_response = connect_to_endpoint(search_url, query_params)
        tweets = json_response.get("data", [])
        users = json_response.get("includes", {}).get("users", [])
        media = json_response.get("includes", {}).get("media", [])


        save_to_csv(tweets, users, media, query_id, OUTPUT_CSV)
        total_tweets += len(tweets)

        print(f"Query {query_id}: Retrieved {len(tweets)} tweets, Total: {total_tweets}/{MAX_TWEETS}")

        # **Fixed Condition**
        if (MAX_TWEETS is not None and total_tweets >= MAX_TWEETS) or not json_response.get("meta", {}).get("next_token"):
            break  # Stop if max tweets reached or no more pages

        next_token = json_response["meta"]["next_token"]


def generate_query_phrases_csv(queries, phrases_filepath=f"data/testing/query_phrases_{begin_date}-{end_date}.csv"):
    """
    Extracts phrases from Twitter queries while respecting OR and AND logic.
    Saves them to a CSV file with 'query_id' and 'phrase' columns.

    Parameters:
        queries (dict): Dictionary of query_id to query string.
        phrases_filepath (str): Path to save the CSV file.
    """
    phrase_dict = {}

    for query_id, query in queries.items():
        # Step 1: Extract content inside the first outer parentheses (ignore everything else)
        match = re.search(r'\((.*)\)', query)
        if not match:
            continue  # Skip if no valid phrases found

        phrase_group = match.group(1)  # Capture only the phrases

        # Step 2: Split phrases using OR logic
        or_split_phrases = re.split(r'\s+OR\s+', phrase_group)

        for phrase in or_split_phrases:
            phrase = phrase.strip()

            # Step 3: Handle compound phrases (phrases inside parentheses)
            if phrase.startswith("(") and phrase.endswith(")"):
                words = re.findall(r'"([^"]+)"', phrase)  # Extract words within quotes
                cleaned_phrase = " AND ".join(words)  # Join words with AND
            else:
                # Extract non-compound phrases by removing quotes
                cleaned_phrase = phrase.replace('"', '')

            # Store phrases under their respective query IDs
            if cleaned_phrase:
                if cleaned_phrase in phrase_dict:
                    phrase_dict[cleaned_phrase].add(query_id)
                else:
                    phrase_dict[cleaned_phrase] = {query_id}

    # Convert to a list of dictionaries for DataFrame
    phrase_list = [{"query_id": ",".join(map(str, sorted(query_ids))), "phrase": phrase}
                   for phrase, query_ids in phrase_dict.items()]

    # Save to CSV
    phrases_df = pd.DataFrame(phrase_list)
    phrases_df.to_csv(phrases_filepath, index=False, encoding="utf-8")

    print(f"Query phrases saved to {phrases_filepath}.")

def main():
    print(f"Generating query_phrases.csv...")
    generate_query_phrases_csv(QUERIES)  # Call the function to generate query_phrases.csv

    print(f"Connecting to the Twitter API... (TEST_MODE: {TEST_MODE})")

    # Clear existing file if it exists
    if os.path.exists(OUTPUT_CSV):
        os.remove(OUTPUT_CSV)

    for query_id, query_text in QUERIES.items():
        run_query(query_id, query_text)

    print(f"Finished fetching tweets for all queries.")

if __name__ == "__main__":
    main()

