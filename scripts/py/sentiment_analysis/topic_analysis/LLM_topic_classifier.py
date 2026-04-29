# LLM topic classifier

# Load Packages
import os
import json
import time
import pandas as pd
from openai import OpenAI
from tqdm import tqdm
 
# Configuration 
MODEL = "gpt-4o"
BATCH_SIZE = 25
TEMPERATURE = 0
SLEEP_TIME = 2          

# Setup 
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_handcode.csv"
output_path = "D:/TwitterBirth/data/sentiment_analysis/output/LLM_topic_classifier100.csv"

df = pd.read_csv(input_path)
all_tweets = df["text"].fillna("").astype(str).tolist()


# Define helper function (fix malformed json)
import re, json

def safe_json_loads(content):
    """Try to parse JSON output with minimal cleanup. Always returns a list."""
    # Clean common formatting artifacts 
    content = re.sub(r"^```(json)?", "", content.strip(), flags=re.I)
    content = re.sub(r"```$", "", content.strip())
    content = content.strip()

    # Remove stray trailing commas or extra characters after the JSON array
    content = re.sub(r",(\s*])", r"\1", content)
    content = re.sub(r"^[^{\[]+", "", content)  # drop leading junk
    content = re.sub(r"[^}\]]+$", "", content)  # drop trailing junk

    try:
        data = json.loads(content)
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            return [data]
        else:
            return [{"error": "Unexpected JSON type", "raw_output": content}]
    except json.JSONDecodeError as e:
        return [{"error": f"Invalid JSON: {e}", "raw_output": content}]


# Define classification function 
def classify_batch(tweets):
    joined = "\n".join([f"{i+1}. {t}" for i, t in enumerate(tweets)])
    prompt = f"""
    You are a tweet classifier. 
    Classify each tweet into one of the following mutually exclusive topics:

    1. "family" — mentions parents, children, siblings, relatives, family gatherings, home life, relationships within a family, or family-related events.
    2. "politics" — mentions political news, elections, parties, politicians, policies, laws, governments, international relations, or public debates about political or social issues.
    3. "other" — everything else not captured above.

    For each tweet, output a JSON object with:
    - "id": the tweet number
    - "classification": one of "family", "politics", or "other"
    - "reasoning": a brief (≤10 words) explanation of why you chose that label

    Return ONLY a valid JSON array — no extra text, no markdown, no code fences.

    Example format:
    [
      {{"id": 1, "classification": "family", "reasoning": "mentions parents"}},
      {{"id": 2, "classification": "politics", "reasoning": "about government policy"}},
      {{"id": 3, "classification": "other", "reasoning": "about sports"}}
    ]

    Tweets:
    {joined}
    """

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=TEMPERATURE,
    )

    content = response.choices[0].message.content.strip()
    results = safe_json_loads(content)
    return results


all_results = []

for i in tqdm(range(0, len(all_tweets), BATCH_SIZE)):
    batch = all_tweets[i:i+BATCH_SIZE]
    results = classify_batch(batch)
    # Attach global index so results map back to original rows
    for r in results:
        global_id = i + (r["id"] - 1)
        r["global_row"] = global_id

    all_results.extend(results)

    # Sleep to avoid rate limits
    time.sleep(SLEEP_TIME)



# Create output columns
df["classification"] = None
df["reasoning"] = None

for r in all_results:
    idx = r["global_row"]
    if 0 <= idx < len(df):
        df.at[idx, "classification"] = r.get("classification", None)
        df.at[idx, "reasoning"] = r.get("reasoning", None)


# ------------Save Output CSV--------------- #
df.to_csv(output_path, index=False)
print(f"\n✅ Classification complete. Saved to:\n{output_path}")