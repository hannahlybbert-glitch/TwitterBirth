import pandas as pd
from itertools import combinations
import os

begin_date = "2025_02_17"
end_date = "2025_02_24"

# Set working directory (temporary change for this script)
os.chdir("/Users/rorylawson/Desktop/TwitterBirth")

# Verify it's set correctly
print(f"Current Working Directory: {os.getcwd()}")

# File paths (update as needed)
TWEETS_CSV = f"data/testing/query_results_{begin_date}-{end_date}.csv" # CSV containing the original set of tweets
CODED_CSV = f"data/testing/hand_coded_{begin_date}-{end_date}.csv"  # CSV containing tweets with a "text" column
PHRASE_CSV = f"data/testing/query_phrases_{begin_date}-{end_date}.csv"  # CSV containing phrases with "query_id" and "phrase" columns
OUTPUT_CSV = f"data/testing/phrase_matches_{begin_date}-{end_date}.csv"  # Output file with counts

# Load CSV files
tweets_df = pd.read_csv(TWEETS_CSV, encoding = "utf-8")
coded_df = pd.read_csv(CODED_CSV, encoding="utf-8")
phrases_df = pd.read_csv(PHRASE_CSV, encoding="utf-8")

# Merge birth_announcement from coded_df into tweets_df
tweets_df = tweets_df.merge(
    coded_df[['tweet_id', 'birth_announcement']], 
    on='tweet_id', 
    how='left'
)

# Replace NaN values with 0 (assuming missing tweets are non-birth announcements)
tweets_df['birth_announcement'] = tweets_df['birth_announcement'].fillna(0).astype(int)


# # Set the "birth announcements" column
# tweets_df["birth_announcement"] = tweets_df["loose"]

# print(tweets_df.columns)

# Ensure necessary columns exist
if "text" not in tweets_df.columns or "birth_announcement" not in coded_df.columns or "query_id" not in coded_df.columns or "has_picture" not in coded_df.columns:
    raise ValueError("Tweet CSV must contain 'text', 'birth_announcement', 'query_id', and 'has_picture' columns.")

# Function to match phrases while handling AND logic
def match_phrase(tweet, phrase):
    phrase_parts = phrase.split(" AND ")  # Split on AND logic
    return all(part.lower() in tweet.lower() for part in phrase_parts)

# Count occurrences
match_counts = []

for _, row in phrases_df.iterrows():
    phrase = row["phrase"]
    query_ids = list(map(int, str(row["query_id"]).split(",")))  # Convert query_id to list of integers
    
    matched_tweets = tweets_df[tweets_df["text"].apply(lambda x: match_phrase(str(x), phrase))]
    
    # Separate analysis for tweets with and without images
    matched_tweets_with_pics = matched_tweets[matched_tweets["has_picture"] == 1]
    matched_tweets_no_pics = matched_tweets[matched_tweets["has_picture"] == 0]
    
    # Compute stats for tweets with pictures
    n_matches_with_pics = len(matched_tweets_with_pics)
    birth_announcement_matches_with_pics = matched_tweets_with_pics[matched_tweets_with_pics["birth_announcement"] == 1].shape[0]
    hit_rate_with_pics = (birth_announcement_matches_with_pics / n_matches_with_pics * 100) if n_matches_with_pics > 0 else 0
    
    # Compute stats for tweets without pictures
    n_matches_no_pics = len(matched_tweets_no_pics)
    birth_announcement_matches_no_pics = matched_tweets_no_pics[matched_tweets_no_pics["birth_announcement"] == 1].shape[0]
    hit_rate_no_pics = (birth_announcement_matches_no_pics / n_matches_no_pics * 100) if n_matches_no_pics > 0 else 0
    
    # Append results
    match_counts.append({
        "query_id": ",".join(map(str, sorted(query_ids))),
        "phrase": phrase,
        "n_matches_with_pics": n_matches_with_pics,
        "birth_announcement_matches_with_pics": birth_announcement_matches_with_pics,
        "hit_rate_with_pics": round(hit_rate_with_pics, 2),
        "n_matches_no_pics": n_matches_no_pics,
        "birth_announcement_matches_no_pics": birth_announcement_matches_no_pics,
        "hit_rate_no_pics": round(hit_rate_no_pics, 2),
    })

# Convert results to DataFrame
output_df = pd.DataFrame(match_counts)

# Save results
output_df.to_csv(OUTPUT_CSV, index=False, encoding="utf-8")

print(f"Phrase matching completed. Results saved to {OUTPUT_CSV}.")




