# Author: Hannah Lybbert
# Created: 05/18/2026
# Purpose: Test pull from X API with search/all/ endpoint

import os
import requests
from dotenv import load_dotenv

load_dotenv()

headers = {"Authorization": f"Bearer {os.getenv('X_API_BEARER_TOKEN')}"}

params = {
    "query": "bagel -is:retweet lang:en",
    "max_results": 10,
    "tweet.fields": "author_id,created_at,public_metrics",
    "sort_order": "recency",
}

response = requests.get(
    "https://api.twitter.com/2/tweets/search/all",
    headers=headers,
    params=params
)

print(response.status_code)
print(response.json())