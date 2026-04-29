import requests
import os
import csv
import time
from dotenv import load_dotenv
from datetime import datetime
import pandas as pd

# **Load API Key from .env File**
load_dotenv(dotenv_path="config/.env")
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

# **API Endpoint**
SEARCH_URL = "https://api.twitter.com/2/tweets/search/all"

# **Set Query Parameters**
# 2018 start and end time
# START_TIME = "2018-01-01T00:00:00.000Z"  
# END_TIME = "2018-12-31T23:59:59.999Z"

# 2013-2017 start and end time
START_TIME = "2013-01-01T00:00:00.000Z"  
END_TIME = "2017-12-31T23:59:59.999Z"

# **Set output file name dynamically based on date range**
begin_time = START_TIME[:10].replace("-", "_")
end_time = END_TIME[:10].replace("-", "_")
OUTPUT_CSV = f"data/raw/query_results_{begin_time}-{end_time}.csv"

# **Set API Rate Limits**
MAX_REQUESTS_PER_15_MIN = 300  # 300 requests per 15 minutes
TIME_WINDOW = 15 * 60  # 15 minutes in seconds

# **Global counters**
total_tweets_saved = 0
total_requests_made = 0
window_start_time = time.time()

MAX_TWEETS_PER_QUERY = None
MAX_RESULTS_PER_REQUEST = 500

QUERIES = {
    # Query 1: Structured birth announcements (Explicit, well-formed statements) (with pictures)
    1: '("welcome to the world baby" OR ("life update" "baby") OR "introducing baby" OR "our little one has arrived" OR "our new baby" OR "meet our baby" OR "our family just got bigger" OR "we had a baby" OR "our bundle of joy" OR "our baby is here" OR "we had our baby") -has:links -has:videos -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -"welcome to the world of" -"born again" -"chromosome" -"i was born" -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle -congrats -congratulations -"i liked a @youtube video"',

    # Query 2: Option 1 without pictures
    2: '("welcome to the world baby" OR ("life update" "baby") OR "introducing baby" OR "our little one has arrived" OR "our new baby" OR "meet our baby" OR "our family just got bigger" OR "we had a baby" OR "our bundle of joy" OR "our baby is here" OR "we had our baby") -has:media -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -"welcome to the world of" -"born again" -"chromosome" -"i was born" -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle -congrats -congratulations -"i liked a @youtube video"',
    
    # Query 3: Somewhat broad search (with pictures)
    3: '(("born" "wife" "baby") OR ("born after" "labor" "hours") OR ("born" "pounds" "ounces") OR ("born" "lbs" "oz") OR ("mom and baby are") OR ("born" "c-section") OR ("say hello to baby") OR ("say hi to baby") OR ("born at" "AM") OR ("born at" "PM") OR ("born" "this morning") OR ("born at" "this morning") OR ("born at" "afternoon")) has:images -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle -congrats -congratulations -"i liked a @youtube video"',

    # Query 4: Somewhat broad search (without pictures)
    4: '(("born" "wife" "baby") OR ("born after" "labor" "hours") OR ("born" "pounds" "ounces") OR ("born" "lbs" "oz") OR ("mom and baby are") OR ("born" "c-section") OR ("say hello to baby") OR ("say hi to baby") OR ("born at" "AM") OR ("born at" "PM") OR ("born" "this morning") OR ("born at" "this morning") OR ("born at" "afternoon")) -has:media -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle -congrats -congratulations -"i liked a @youtube video"',
     
    # Query 5: Family-centered birth phrases (with pictures)
    5: '(("had my baby" "today") OR ("i gave birth" "ago") OR ("i gave birth" "today") OR ("i gave birth" "yesterday") OR ("i gave birth" "last night") OR "meet your baby brother" OR "meet your baby sister" OR "was born last night" OR "was born a few hours ago" OR "we are officially parents") has:images -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle -congrats -congratulations -"i liked a @youtube video"',

    # Query 6: Family-centered birth phrases (without pictures)
    6: '(("had my baby" "today") OR ("i gave birth" "ago") OR ("i gave birth" "today") OR ("i gave birth" "yesterday") OR ("i gave birth" "last night") OR "meet your baby brother" OR "meet your baby sister" OR "was born last night" OR "was born a few hours ago" OR "we are officially parents") -has:media -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle -congrats -congratulations -"i liked a @youtube video"',

    # Query 7: Broadish search with pictures
    7: '("welcomed our baby" OR ("i became a mother" "today") OR ("i became a father" "today") OR ("went into labor" "ago") OR "delivered naturally" OR "we had a baby girl" OR "we had a baby boy" OR "welcoming our newest blessing" OR "we became parents today" OR "baby finally arrived") has:images -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle -congrats -congratulations -"i liked a @youtube video"',

    # Query 8: Broadish search without pictures
    8: '("welcomed our baby" OR ("i became a mother" "today") OR ("i became a father" "today") OR ("went into labor" "ago") OR "delivered naturally" OR "we had a baby girl" OR "we had a baby boy" OR "welcoming our newest blessing" OR "we became parents today" OR "baby finally arrived") -has:media -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle -congrats -congratulations -"i liked a @youtube video"',
    
    # Query 9: permutations of "i had a baby" with pictures
    9: '(("i had a baby" "ago") OR ("i had a baby" "today") OR ("i had a baby" "last night") OR ("i had a baby" "yesterday") OR ("i had a baby" "this morning") OR ("arrived" "baby" "wife") OR ("arrived" "baby" "husband")) has:images -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle -congrats -congratulations -"i liked a @youtube video"',
    
    # Query 10: permutations of "i had a baby" without pictures
    10: '(("i had a baby" "ago") OR ("i had a baby" "today") OR ("i had a baby" "last night") OR ("i had a baby" "yesterday") OR ("i had a baby" "this morning") OR ("arrived" "baby" "wife") OR ("arrived" "baby" "husband")) -has:media -is:retweet -is:quote -is:reply lang:en -puppy -cat -kitten -dog -dream -niece -nephew -granddaughter -grandchild -grandson -aunt -uncle -congrats -congratulations -"i liked a @youtube video"'
}

# **Authentication**
def bearer_oauth(r):
    """Method required by bearer token authentication."""
    r.headers["Authorization"] = f"Bearer {BEARER_TOKEN}"
    r.headers["User-Agent"] = "v2FullArchiveSearchPython"
    return r

# **Handle API Rate Limits**
def manage_rate_limit():
    """Manages Twitter API rate limits (300 requests per 15 minutes)."""
    global total_requests_made, window_start_time

    elapsed_time = time.time() - window_start_time

    if total_requests_made >= 300:  # Pro API limit
        if elapsed_time < TIME_WINDOW:
            wait_time = TIME_WINDOW - elapsed_time
            print(f"Rate limit reached! Sleeping for {wait_time:.2f} seconds...")
            time.sleep(wait_time)
        
        total_requests_made = 0  # Reset counter after waiting
        window_start_time = time.time()  # Reset 15-minute window

    time.sleep(1)  # Enforce max 1 request per second


# **Connect to API**
def connect_to_endpoint(url, params):
    """Connect to the Twitter API endpoint and return JSON response."""
    global total_requests_made, window_start_time

    while True:
        manage_rate_limit()  # Ensure rate limit is respected

        response = requests.get(url, auth=bearer_oauth, params=params)
        total_requests_made += 1  # Track API requests

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            return response.json()

        elif response.status_code == 400:
            print(f"API Error 400: {response.text}")
            return None  # Don't exit, just move to the next query

        elif response.status_code == 429:
            print(f"Rate limit hit! Sleeping for 15 minutes...")
            time.sleep(15 * 60)  # 15-minute wait
            total_requests_made = 0  # Reset counter
            window_start_time = time.time()
            continue  # Retry after sleeping

        elif response.status_code in [401, 403, 503]:
            print(f"API Error {response.status_code}: Retrying in 60 seconds...")
            time.sleep(60)
            continue  # Retry

        else:
            print(f"Unexpected API Error {response.status_code}: {response.text}")
            return None  # Skip to next query



# **Save Data to CSV**
def save_to_csv(data, users, media, query_id,filename):
    """Save tweet and user data to a CSV file."""
    csv_headers = [
        "query_id", "author_id", "username", "name", "tweet_id", "created_at", "text", "media_url",
        "has_picture", "tweet_url", "profile_image_url", "like_count", "retweet_count",
        "reply_count", "quote_count", "user_created_at", "description", "following_count", "followers_count",
        "tweet_count", "verified", "verified_type", "start_time", "end_time"
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
                    media_url = media_item.get("url", media_item.get("preview_image_url"))
                    break  # Only grab the first available media

            writer.writerow([
                query_id, 
                tweet.get("author_id"), 
                user.get("username"), 
                user.get("name"),
                tweet.get("id"), 
                tweet.get("created_at"), 
                tweet.get("text"), 
                media_url,
                "1" if "attachments" in tweet and "media_keys" in tweet["attachments"] else "0",
                f"https://x.com/{user.get('username')}/status/{tweet.get('id')}" if user.get("username") else "NA",
                profile_image_url, 
                tweet["public_metrics"].get("like_count", 0),
                tweet["public_metrics"].get("retweet_count", 0),
                tweet["public_metrics"].get("reply_count", 0),
                tweet["public_metrics"].get("quote_count", 0),
                user.get("created_at"), 
                user.get("description"),
                user.get("public_metrics", {}).get("following_count", 0),
                user.get("public_metrics", {}).get("followers_count", 0),
                user.get("public_metrics", {}).get("tweet_count", 0), 
                user.get("verified", False),
                user.get("verified_type"), 
                START_TIME, 
                END_TIME
            ])

    print(f"Saved {len(data)} tweets for query {query_id}!")

# **Run Queries**
def run_query(query_id, query_text):
    """Fetch and save tweets while respecting limits on tweets per query."""
    total_tweets = 0
    next_token = None

    print(f"\nRunning Query {query_id} (Max tweets: {MAX_TWEETS_PER_QUERY})...")

    while MAX_TWEETS_PER_QUERY is None or total_tweets < MAX_TWEETS_PER_QUERY:
        # If unlimited, always request 500 tweets per batch
        max_results = 500 if MAX_TWEETS_PER_QUERY is None else max(10, min(500, MAX_TWEETS_PER_QUERY - total_tweets))

        query_params = {
            'query': query_text,
            'tweet.fields': 'author_id,created_at,text,lang,public_metrics,attachments',
            'user.fields': 'username,created_at,description,public_metrics,url,verified,verified_type,profile_image_url,name',
            'media.fields': 'media_key,type,url,preview_image_url',
            'expansions': 'author_id,attachments.media_keys',
            'max_results': max_results,
            'start_time': START_TIME,
            'end_time': END_TIME
        }

        if next_token:
            query_params['next_token'] = next_token

        json_response = connect_to_endpoint(SEARCH_URL, query_params)
        if not json_response or "data" not in json_response:
            print(f"No more tweets found")
            break

        # Save tweets to CSV
        save_to_csv(json_response["data"], 
                    json_response.get("includes", {}).get("users", []), 
                    json_response.get("includes", {}).get("media", []), 
                    query_id, OUTPUT_CSV)

        total_tweets += len(json_response["data"])
        print(f"Query {query_id}: Collected {total_tweets}/{MAX_TWEETS_PER_QUERY} tweets")

        next_token = json_response.get("meta", {}).get("next_token")
        if not next_token:
            print(f"No more pages available.")
            break

    print(f"Query {query_id} complete. Total tweets retrieved: {total_tweets}")
    print(f"Total requests so far {total_requests_made}")


# **Main Function**
def main():
    start_time = time.time()

    for query_id, query_text in QUERIES.items():
        run_query(query_id, query_text)

    df = pd.read_csv(OUTPUT_CSV)
    total_tweets_pulled = len(df)

    elapsed_time = time.time() - start_time
    print(f"\nFinished. Pulled {total_tweets_pulled} tweets with {total_requests_made} requests made.")
    print(f"Time Elapsed: {elapsed_time:.2f} seconds")
    print(f"Output saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()

