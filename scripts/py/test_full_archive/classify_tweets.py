import os
import openai
import pandas as pd
import re
import sys
import emoji
from tqdm import tqdm
from dotenv import load_dotenv
from collections import Counter
import time
import json

# Load API Key
load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

begin_date = "2018_06_01"
end_date = "2018_06_30"

# Ensure file exists
file_path = f"data/raw/query_results_{begin_date}-{end_date}.csv"
if not os.path.exists(file_path):
    print(f"Error: File '{file_path}' not found. Make sure it is in the correct directory.")
    sys.exit(1)

original_df = pd.read_csv(file_path, encoding="utf-8").iloc[:200] # - only do the 1st thousand tweets
df = original_df[["query_id","tweet_id","text"]].copy()

# Check if DataFrame is empty
if df.empty:
    print("Error: The CSV file is empty. Exiting.")
    sys.exit(1)

# Check for correct column name
expected_column = "text"
if expected_column not in df.columns:
    print(f"Error: Column '{expected_column}' not found. Available columns: {df.columns.tolist()}")
    sys.exit(1)

# Enable tqdm progress tracking
tqdm.pandas()

# Rate limit settings
TOKEN_LIMIT_PER_MINUTE = 40000
REQUEST_LIMIT_PER_MINUTE = 5000
TOKEN_LIMIT_PER_DAY = 1350000

# Track API usage
rate_limit_tracker = "data/rate_limit_tracker.json"
if os.path.exists(rate_limit_tracker):
    with open(rate_limit_tracker, "r") as f:
        rate_limit_data = json.load(f)
else:
    rate_limit_data = {"requests_made": 0, "tokens_used": 0, "daily_tokens_used": 0, "last_run_date": ""}

requests_made = rate_limit_data.get("requests_made", 0)
tokens_used = rate_limit_data.get("tokens_used", 0)
daily_tokens_used = rate_limit_data.get("daily_tokens_used", 0)
last_run_date = rate_limit_data.get("last_run_date", "")

# Reset daily counter if it's a new day
today = time.strftime("%Y-%m-%d")
if today != last_run_date:
    daily_tokens_used = 0
    last_run_date = today

# Preprocess text (keeping all emojis)
def preprocess_text(text):
    text = str(text).strip()
    text = re.sub(r"http\S+|www\S+|@\S+", "", text)  # Remove links and mentions
    text = re.sub(r"[^a-zA-Z0-9\s.,!?'/:-\U0001F600-\U0001F64F]", "", text)  # Keep all emojis
    text = re.sub(r"\s+", " ", text).strip()  # Remove extra spaces
    return text.lower()

# Chain of Thought (CoT) Reasoning Prompt with Emoji Interpretation
def get_chain_of_thought_prompt(text):
    return f"""
You are an expert classifier tasked with determining if a tweet is a birth announcement.

A tweet should be classified as a birth announcement if it meets ANY of the following criteria:
✔ Explicitly announces the recent birth of the tweeter's own child (within approximately one week).
✔ Mentions the child's birth date, birth time, baby's name, weight, or birth-related emojis (👶, 🍼) in a personal context.
✔ Clearly references their child's age in terms of a milestone closely tied to birth (e.g., "[baby name] turned 6 months today!" or "Happy 1st birthday to my baby!"), provided the referenced birth occurred within approximately the last 1 year.

A tweet is NOT a birth announcement if it meets ANY of the following criteria:
❌ Congratulates someone else on their baby's birth (e.g., friend, sibling, relative).
❌ Is posted by a business, organization, or brand account.
❌ Refers to the birth of an animal or pet.
❌ Refers clearly to a child's birth that occurred more than approximately 1 year ago.
❌ Contains no explicit or implicit references to childbirth.

---

### Tweet to classify:
{text}

Think step by step. Based on the criteria above, is this tweet a birth announcement?

**Final Answer:** Respond with ONLY "1" (Birth Announcement) or "0" (Not a Birth Announcement).
"""

# Handle rate limits
def handle_rate_limit():
    global requests_made, tokens_used, daily_tokens_used
    
    if requests_made >= REQUEST_LIMIT_PER_MINUTE or tokens_used >= TOKEN_LIMIT_PER_MINUTE:
        time.sleep(60)  # Pause for 60 seconds if rate limit reached
        requests_made = 0
        tokens_used = 0
    
    if daily_tokens_used >= TOKEN_LIMIT_PER_DAY:
        print("🚨 Daily token limit reached! Stopping classification.")
        sys.exit(1)

# Classification function without majority voting
def classify_tweet(text):
    global requests_made, tokens_used, daily_tokens_used

    if not text or len(text.split()) < 3:
        return "0"  # Assume "Not a Birth Announcement" for very short tweets

    handle_rate_limit()
    prompt = get_chain_of_thought_prompt(text)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        answer = response.choices[0].message.content.strip()
        match = re.findall(r"\b(1|0)\b", answer)
        
        # Update rate-limit counters
        requests_made += 1
        tokens_used += response.usage.total_tokens
        daily_tokens_used += response.usage.total_tokens
        
        # Save rate limit state
        rate_limit_data.update({"requests_made": requests_made, "tokens_used": tokens_used, "daily_tokens_used": daily_tokens_used, "last_run_date": today})
        with open(rate_limit_tracker, "w") as f:
            json.dump(rate_limit_data, f)
        
        return match[-1] if match else "Error"
    
    except openai.RateLimitError as e:
        print(f"Quota exceeded error: {e}. Stopping classification.")
        sys.exit(1)
    
    except openai.OpenAIError as e:
        print(f"Error: {e}. Retrying...")
        time.sleep(2)
        return "Error"

# Apply classification with progress tracking
start_time = time.time()
df["processed_text"] = df["text"].progress_apply(preprocess_text)
df["text_classification"] = df["processed_text"].progress_apply(classify_tweet)

# Merge back in with original df
df = df.drop(columns=["text"])
merged_df = pd.merge(df, original_df, on=['query_id', 'tweet_id'], how='inner')

# Save results
merged_df.to_csv(f"data/classified_text_{begin_date}-{end_date}.csv", index=False, encoding="utf-8")

print(f"✅ Classification complete. Results saved to 'classified_text_{begin_date}-{end_date}.csv'.")
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Classification completed in {elapsed_time:.2f} seconds, using {tokens_used}.")




