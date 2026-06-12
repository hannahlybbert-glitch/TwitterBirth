# Author: Hannah Lybbert
# Created: 2026-06-12
# Purpose: Collect seed tweets matching the anniversary query via per-week fixed sampling (2013-2018)

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

import json
import time
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

# --- Config ---
load_dotenv(dotenv_path="config/.env")
BEARER_TOKEN = os.getenv("X_API_BEARER_TOKEN")

FILTER_NAME = "anniversary"
QUERY = (
    # Anniversary terms
    '(("our wedding anniversary" OR "our anniversary" OR "my anniversary" '
    'OR "years we\'ve been married" '
    'OR "years ago we got married" OR "years ago i got married" '
    'OR "since we got married") '

    # Happy anniversary to spouse
    'OR ("happy anniversary" ("husband" OR "wife" OR "hubby" '
    'OR "wifey" OR "babe" OR "my love" OR "partner"))) '

    # Exclusions
    '-"congrats to" -"congratulations to" '
    '-"their anniversary" -"his anniversary" -"her anniversary" '
    '-"parents" -"mom" -"dad" -"mum" -"grandma" -"grandpa" -"grandparents" '
    '-"brother" -"sister" -"cousin" -"aunt" -"uncle" '
    '-"her hubby" -"her husband" -"his wifey" -"his wife" '

    # Exclusions from observed false positives
    '-"#WeAlmostDatedBut"'
    '-"RT @" '
    '-"shop" -"buy" -"order" -"discount" -"sale" -"gift idea"'
    '-"I liked a @YouTube video" '

    '-is:retweet -is:reply lang:en'
)

START_DATE      = datetime(2013, 1, 1, tzinfo=timezone.utc)
END_DATE        = datetime(2019, 1, 1, tzinfo=timezone.utc)  # exclusive
TWEETS_PER_WEEK = 150    # max tweets pulled per week (~39k total across 2013-2018)

CHECKPOINT_EVERY = 10    # save progress every N weeks
SLEEP_BETWEEN    = 1.0   # seconds between API calls

TEST_MODE   = True
TEST_WEEKS  = 3          # number of weeks to fetch in test mode

_base_dir      = f"ControlGroup/data/seed_tweets/{FILTER_NAME}"
OUTPUT_DIR     = f"{_base_dir}/test" if TEST_MODE else _base_dir
CHECKPOINT_CSV = f"{OUTPUT_DIR}/candidate_pool.csv"
PROGRESS_FILE  = f"{OUTPUT_DIR}/progress.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)

SEARCH_URL = "https://api.twitter.com/2/tweets/search/all"

# --- Build week list ---
weeks = []
week_start = START_DATE
while week_start < END_DATE:
    week_end = min(week_start + timedelta(days=7), END_DATE)
    weeks.append((week_start, week_end))
    week_start += timedelta(days=7)


def get_with_backoff(params, max_retries=5):
    headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
    for attempt in range(max_retries):
        response = requests.get(SEARCH_URL, params=params, headers=headers)
        if response.status_code == 200:
            return response
        if response.status_code == 429:
            reset_ts = response.headers.get("x-rate-limit-reset")
            wait = max(int(reset_ts) - int(time.time()) + 5, 5) if reset_ts else 60 * (2 ** attempt)
            print(f"  Rate limited. Waiting {wait}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(wait)
        else:
            response.raise_for_status()
    response.raise_for_status()


def save_checkpoint(pool, week_idx):
    rows = [{"author_id": aid, **vals} for aid, vals in pool.items()]
    pd.DataFrame(rows).to_csv(CHECKPOINT_CSV, index=False)
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"last_completed_week_idx": week_idx}, f)
    print(f"  Checkpoint saved — {len(pool):,} users through week index {week_idx}")


# --- Resume from checkpoint ---
candidate_pool = {}
start_idx = 0

if not TEST_MODE and os.path.exists(CHECKPOINT_CSV) and os.path.exists(PROGRESS_FILE):
    try:
        pool_df = pd.read_csv(CHECKPOINT_CSV, dtype=str)
        candidate_pool = pool_df.set_index("author_id").to_dict("index")
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)
        start_idx = progress["last_completed_week_idx"] + 1
        print(f"Checkpoint found — resuming with {len(candidate_pool):,} users at week index {start_idx}")
    except (pd.errors.EmptyDataError, KeyError, ValueError):
        print("Checkpoint files found but invalid — starting fresh.")

# --- Main collection loop ---
target_weeks = weeks[:TEST_WEEKS] if TEST_MODE else weeks
last_idx = start_idx

for idx, (w_start, w_end) in enumerate(target_weeks[start_idx:], start=start_idx):
    print(f"[Week {idx + 1}/{len(target_weeks)}]  {w_start.date()}  pool={len(candidate_pool):,}")

    params = {
        "query":        QUERY,
        "start_time":   w_start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time":     w_end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "max_results":  TWEETS_PER_WEEK,
        "tweet.fields": "author_id,created_at,text,public_metrics",
        "sort_order":   "recency",
    }

    try:
        response = get_with_backoff(params)
    except Exception as e:
        print(f"  ERROR: {e} — skipping week {w_start.date()}")
        last_idx = idx
        time.sleep(SLEEP_BETWEEN)
        continue

    tweets = response.json().get("data", [])
    new_users = 0
    for t in tweets:
        if t["author_id"] not in candidate_pool:
            candidate_pool[t["author_id"]] = {
                "tweet_id":   t["id"],
                "created_at": t["created_at"],
                "week_start": str(w_start.date()),
                "text":       t["text"],
                "like_count": t.get("public_metrics", {}).get("like_count"),
            }
            new_users += 1

    print(f"  +{new_users} new users  (pool now {len(candidate_pool):,})")
    last_idx = idx

    if (idx + 1) % CHECKPOINT_EVERY == 0:
        save_checkpoint(candidate_pool, idx)

    time.sleep(SLEEP_BETWEEN)

# --- Final save ---
save_checkpoint(candidate_pool, last_idx)
print(f"\nDone. Final pool: {len(candidate_pool):,} unique users saved to {CHECKPOINT_CSV}")
