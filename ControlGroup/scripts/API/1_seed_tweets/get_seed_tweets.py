# Author: Hannah Lybbert
# Created: 2026-05-07
# Updated: 2026-05-07
# Purpose: Phase 1 — collect 40k seed tweets from unique users via weighted time-window sampling

import sys
import os

# Add script directory to path so sampling_function can be imported after os.chdir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

import json
import time
import pandas as pd
from dotenv import load_dotenv
from sampling_function import draw_sample

# --- Config ---
load_dotenv(dotenv_path="config/.env")
BEARER_TOKEN = os.getenv("X_API_BEARER_TOKEN")

HOUR_WEIGHTS_CSV = "ControlGroup/data/treatment_distributions/hour_weights.csv"
WEEK_LIST_CSV    = "ControlGroup/data/treatment_distributions/week_list.csv"

# FILTER_NAME      = "animal"   # set "" for the default (no-filter) pull
# QUERY            = "cat OR kitten OR dog OR puppy OR hamster OR rabbit  -is:retweet -is:reply lang:en"

# FILTER_NAME      = "relationships"   # set "" for the default (no-filter) pull
# QUERY            = "my mom OR my dad OR my sister OR my brother OR my boyfriend OR my girlfriend OR friend -is:retweet -is:reply lang:en"

FILTER_NAME      = "events"   # set "" for the default (no-filter) pull
QUERY            = "breakfast OR brunch OR dinner OR concert OR party OR vacation OR conference OR meeting -is:retweet -is:reply lang:en"

FILTER_NAME      = "celebrations"   # set "" for the default (no-filter) pull
QUERY            = '"happy birthday" OR "happy anniversary" OR birthday OR anniversary OR congratulations OR graduation OR graduated OR retirement OR wedding OR married -is:retweet -is:reply lang:en'


TOTAL_TARGET     = 40_000
TEST_TARGET      = 10    # used only in test mode
CHECKPOINT_EVERY = 10     # save progress every N weeks
SLEEP_BETWEEN    = 1.0    # seconds between API calls

TEST_MODE        = True   # set False for full run

_base_dir  = "ControlGroup/data/seed_tweets"
if FILTER_NAME:
    _base_dir = f"{_base_dir}/{FILTER_NAME}"
OUTPUT_DIR     = f"{_base_dir}/test" if TEST_MODE else _base_dir
CHECKPOINT_CSV = f"{OUTPUT_DIR}/candidate_pool.csv"
PROGRESS_FILE  = f"{OUTPUT_DIR}/progress.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Load inputs ---
hour_weights = pd.read_csv(HOUR_WEIGHTS_CSV)
week_list    = pd.read_csv(WEEK_LIST_CSV).reset_index(drop=True)

if TEST_MODE:
    TOTAL_TARGET = TEST_TARGET
    n_test_weeks = max(10, TOTAL_TARGET // 40)
    week_list    = week_list.head(n_test_weeks).reset_index(drop=True)

# --- Resume from checkpoint if exists (skipped in test mode) ---
if not TEST_MODE and os.path.exists(CHECKPOINT_CSV) and os.path.exists(PROGRESS_FILE):
    try:
        pool_df        = pd.read_csv(CHECKPOINT_CSV, dtype=str)
        candidate_pool = pool_df.set_index("author_id").to_dict("index")
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)
        start_idx = progress["last_completed_week_idx"] + 1
        print(f"Checkpoint found — resuming with {len(candidate_pool):,} users at week index {start_idx}")
    except (pd.errors.EmptyDataError, KeyError, ValueError):
        print("Checkpoint files found but empty or invalid — starting fresh.")
        candidate_pool = {}
        start_idx      = 0
else:
    candidate_pool = {}
    start_idx      = 0

# --- Checkpoint helper ---
def save_checkpoint(pool, week_idx):
    rows = [{"author_id": aid, **vals} for aid, vals in pool.items()]
    pd.DataFrame(rows).to_csv(CHECKPOINT_CSV, index=False)
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"last_completed_week_idx": week_idx}, f)
    print(f"  Checkpoint saved — {len(pool):,} users through week index {week_idx}")

# --- Main collection loop ---
last_idx = start_idx

for idx, row in week_list.iloc[start_idx:].iterrows():
    if len(candidate_pool) >= TOTAL_TARGET:
        print(f"Reached {TOTAL_TARGET:,} unique users. Stopping.")
        break

    week_start = row["week_start"]
    target_n   = int(row["target_n"])
    print(f"[Week {idx + 1}/{len(week_list)}]  {week_start}  target_n={target_n}  pool={len(candidate_pool):,}")

    try:
        tweets = draw_sample(week_start, target_n, hour_weights, BEARER_TOKEN, query=QUERY)
    except Exception as e:
        print(f"  ERROR: {e} — skipping week {week_start}")
        last_idx = idx
        time.sleep(SLEEP_BETWEEN)
        continue

    new_users = 0
    for tweet in tweets:
        if tweet["author_id"] not in candidate_pool:
            candidate_pool[tweet["author_id"]] = {
                "tweet_id":   tweet["tweet_id"],
                "created_at": tweet["created_at"],
                "week_start": week_start,
                "text":       tweet["text"],
                "like_count": tweet.get("public_metrics", {}).get("like_count"),
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
