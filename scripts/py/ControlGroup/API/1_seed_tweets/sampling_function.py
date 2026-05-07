# Author: Hannah Lybbert
# Created: 2026-05-07
# Updated: 2026-05-07
# Purpose: Draw a weighted random 1-hour tweet sample for a given week via X API full-archive search

import time
import requests
from datetime import datetime, timedelta, timezone

SEARCH_URL    = "https://api.twitter.com/2/tweets/search/all"
MAX_RESULTS_CAP = 500


def draw_sample(week_start, target_n, hour_weights, bearer_token):
    """
    Draw up to target_n tweets from a weighted random 1-hour window within the given week.

    Args:
        week_start   : str "YYYY-MM-DD" — the Monday that starts the week (UTC)
        target_n     : int — how many tweets to request (capped at MAX_RESULTS_CAP)
        hour_weights : DataFrame with columns [dow, hod, share]  (dow: 0=Mon … 6=Sun)
        bearer_token : str

    Returns:
        list of dicts {tweet_id, author_id, created_at}
    """
    bucket     = hour_weights.sample(n=1, weights="share").iloc[0]
    dow        = int(bucket["dow"])
    hod        = int(bucket["hod"])

    week_dt    = datetime.strptime(week_start, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    start_time = week_dt + timedelta(days=dow, hours=hod)
    end_time   = start_time + timedelta(hours=1)

    params = {
        "query":       "-is:retweet -is:reply lang:en",
        "start_time":  start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time":    end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "max_results": min(target_n, MAX_RESULTS_CAP),
        "tweet.fields": "author_id,created_at",
        "sort_order":  "recency",
    }
    headers = {"Authorization": f"Bearer {bearer_token}"}

    response = _get_with_backoff(SEARCH_URL, params, headers)
    tweets   = response.json().get("data", [])

    return [
        {
            "tweet_id":   t["id"],
            "author_id":  t["author_id"],
            "created_at": t["created_at"],
        }
        for t in tweets
    ]


def _get_with_backoff(url, params, headers, max_retries=5):
    """GET request with exponential backoff on 429 rate-limit responses."""
    for attempt in range(max_retries):
        response = requests.get(url, params=params, headers=headers)

        if response.status_code == 200:
            return response

        if response.status_code == 429:
            reset_ts = response.headers.get("x-rate-limit-reset")
            if reset_ts:
                wait = max(int(reset_ts) - int(time.time()) + 5, 5)
            else:
                wait = 60 * (2 ** attempt)
            print(f"  Rate limited. Waiting {wait}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(wait)
        else:
            response.raise_for_status()

    response.raise_for_status()
