# Author: Hannah Lybbert
# Created: 2026-05-07
# Updated: 2026-05-07
# Purpose: Phase 1 — collect 40k seed tweets from unique users via weighted time-window sampling

import sys
import os

# Add script directory to path so sampling_function can be imported after os.chdir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

os.chdir("D:/TwitterBirth")

import json
import time
import pandas as pd
from dotenv import load_dotenv
from sampling_function import draw_sample

# --- Config ---
load_dotenv(dotenv_path="config/.env")
BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")

HOUR_WEIGHTS_CSV = "data/ControlGroup/treatment_distributions/hour_weights.csv"
WEEK_LIST_CSV    = "data/ControlGroup/treatment_distributions/week_list.csv"
OUTPUT_DIR       = "data/ControlGroup/seed_tweets"
CHECKPOINT_CSV   = f"{OUTPUT_DIR}/candidate_pool.csv"
PROGRESS_FILE    = f"{OUTPUT_DIR}/progress.json"

TOTAL_TARGET     = 40_000
CHECKPOINT_EVERY = 10     # save progress every N weeks
SLEEP_BETWEEN    = 1.0    # seconds between API calls

TEST_MODE        = True   # set False for full run

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Load inputs ---
hour_weights = pd.read_csv(HOUR_WEIGHTS_CSV)
week_list    = pd.read_csv(WEEK_LIST_CSV).reset_index(drop=True)

if TEST_MODE:
    week_list    = week_list[week_list["week_start"].str.startswith("2013-01")].reset_index(drop=True)
    TOTAL_TARGET = 50

# --- Resume from checkpoint if exists ---
if os.path.exists(CHECKPOINT_CSV) and os.path.exists(PROGRESS_FILE):
    print("Checkpoint found — resuming from last save...")
    pool_df        = pd.read_csv(CHECKPOINT_CSV, dtype=str)
    candidate_pool = pool_df.set_index("author_id").to_dict("index")
    with open(PROGRESS_FILE) as f:
        progress = json.load(f)
    start_idx = progress["last_completed_week_idx"] + 1
    print(f"  Loaded {len(candidate_pool):,} users — resuming at week index {start_idx}")
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
        tweets = draw_sample(week_start, target_n, hour_weights, BEARER_TOKEN)
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
