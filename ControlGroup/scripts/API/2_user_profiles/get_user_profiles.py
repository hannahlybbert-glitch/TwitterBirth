# Author: Hannah Lybbert
# Created: 2026-06-04
# Purpose: Phase 2 — pull user profiles for seed tweet authors and apply filters

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

import json
import time
import requests
import pandas as pd
from datetime import date
from dotenv import load_dotenv

# --- Config ---
load_dotenv(dotenv_path="config/.env")
BEARER_TOKEN = os.getenv("X_API_BEARER_TOKEN")

BATCH_SIZE        = 100
CHECKPOINT_EVERY  = 10           # batches between saves
SLEEP_BETWEEN     = 1.0          # seconds between API calls

FILTER_B_REF_DATE = date.today()   # reference date for account age (date script is run)
FILTER_B_CUTOFF   = 403            # max avg weekly tweets

FILTER_NAME = "anniversary"   # must match the value used in get_seed_tweets.py; set "" for default pull

TEST_MODE = True   # set False for full run

_base_seed     = "ControlGroup/data/LLM/seed_tweets"
_base_profiles = "ControlGroup/data/user_profiles"
if FILTER_NAME:
    _base_profiles = f"{_base_profiles}/{FILTER_NAME}"

if TEST_MODE:
    INPUT_CSV  = f"{_base_seed}/test/anniversaries_extracted_test.csv"
    OUTPUT_DIR = f"{_base_profiles}/test"
else:
    INPUT_CSV  = f"{_base_seed}/anniversaries_extracted.csv"
    OUTPUT_DIR = _base_profiles

RAW_CSV       = f"{OUTPUT_DIR}/profiles_raw.csv"
FILTERED_CSV  = f"{OUTPUT_DIR}/profiles_filtered.csv"
PROGRESS_FILE = f"{OUTPUT_DIR}/progress.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Load inputs ---
pool_df = pd.read_csv(INPUT_CSV, dtype=str)
pool_df = pool_df.rename(columns={"created_at": "seed_tweet_date"})
pool_df = pool_df.drop_duplicates(subset="author_id")
author_ids = pool_df["author_id"].tolist()
seed_date_lookup = pool_df.set_index("author_id")["seed_tweet_date"].to_dict()

batches = [author_ids[i : i + BATCH_SIZE] for i in range(0, len(author_ids), BATCH_SIZE)]
print(f"Loaded {len(author_ids):,} unique authors → {len(batches)} batch(es)")

# --- Resume from checkpoint ---
pulled_rows = []
start_batch = 0

if os.path.exists(RAW_CSV) and os.path.exists(PROGRESS_FILE):
    try:
        pulled_rows = pd.read_csv(RAW_CSV, dtype=str).to_dict("records")
        with open(PROGRESS_FILE) as f:
            progress = json.load(f)
        start_batch = progress["last_completed_batch_idx"] + 1
        print(f"Checkpoint found — {len(pulled_rows):,} users already pulled, resuming at batch {start_batch}")
    except (pd.errors.EmptyDataError, KeyError, ValueError):
        print("Checkpoint invalid — starting fresh.")

# --- Helpers ---
USERS_URL = "https://api.twitter.com/2/users"

def fetch_users_batch(ids, bearer_token, max_retries=5):
    params  = {
        "ids":          ",".join(ids),
        "user.fields":  "username,description,created_at,public_metrics,verified",
    }
    headers = {"Authorization": f"Bearer {bearer_token}"}

    for attempt in range(max_retries):
        response = requests.get(USERS_URL, params=params, headers=headers)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 429:
            reset_ts = response.headers.get("x-rate-limit-reset")
            wait = max(int(reset_ts) - int(time.time()) + 5, 5) if reset_ts else 60 * (2 ** attempt)
            print(f"  Rate limited. Waiting {wait}s (attempt {attempt + 1}/{max_retries})...")
            time.sleep(wait)
        else:
            response.raise_for_status()

    response.raise_for_status()

def save_checkpoint(rows, batch_idx):
    pd.DataFrame(rows).to_csv(RAW_CSV, index=False)
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"last_completed_batch_idx": batch_idx}, f)
    print(f"  Checkpoint saved — {len(rows):,} users through batch {batch_idx}")

# --- Main pull loop ---
for batch_idx, batch in enumerate(batches[start_batch:], start=start_batch):
    print(f"[Batch {batch_idx + 1}/{len(batches)}]  {len(batch)} authors")

    try:
        data = fetch_users_batch(batch, BEARER_TOKEN)
    except Exception as e:
        print(f"  ERROR: {e} — skipping batch {batch_idx}")
        time.sleep(SLEEP_BETWEEN)
        continue

    returned_ids = set()

    for user in data.get("data", []):
        uid     = user["id"]
        metrics = user.get("public_metrics", {})
        returned_ids.add(uid)
        pulled_rows.append({
            "author_id":          uid,
            "seed_tweet_date":    seed_date_lookup.get(uid),
            "username":           user.get("username"),
            "description":        user.get("description"),
            "account_created_at": user.get("created_at"),
            "followers_count":    metrics.get("followers_count"),
            "following_count":    metrics.get("following_count"),
            "tweet_count":        metrics.get("tweet_count"),
            "verified":           user.get("verified"),
            "not_found":          0,
        })

    for uid in batch:
        if uid not in returned_ids:
            pulled_rows.append({
                "author_id":          uid,
                "seed_tweet_date":    seed_date_lookup.get(uid),
                "username":           None,
                "description":        None,
                "account_created_at": None,
                "followers_count":    None,
                "following_count":    None,
                "tweet_count":        None,
                "verified":           None,
                "not_found":          1,
            })

    if (batch_idx + 1) % CHECKPOINT_EVERY == 0:
        save_checkpoint(pulled_rows, batch_idx)

    time.sleep(SLEEP_BETWEEN)

# --- Save final raw (pre-filter) ---
save_checkpoint(pulled_rows, len(batches) - 1)

# --- Compute derived columns ---
df = pd.DataFrame(pulled_rows)

df["seed_tweet_date"]    = pd.to_datetime(df["seed_tweet_date"], utc=True, errors="coerce")
df["account_created_at"] = pd.to_datetime(df["account_created_at"], utc=True, errors="coerce")
df["tweet_count"]        = pd.to_numeric(df["tweet_count"], errors="coerce")

ref_date = pd.Timestamp(FILTER_B_REF_DATE, tz="UTC")

df["account_age_weeks"] = (ref_date - df["account_created_at"]).dt.days / 7
df["avg_weekly_tweets"] = df["tweet_count"] / df["account_age_weeks"]

# Filter A: account must exist >= 18 months before seed tweet date
# 18 months ≈ 548 days (18 × 30.44)
df["filter_a_pass"] = (
    df["account_created_at"].notna() &
    ((df["seed_tweet_date"] - df["account_created_at"]).dt.days >= 548)
).astype(int)

# Filter B: avg weekly tweets (as of April 2025) must be <= 403
df["filter_b_pass"] = (
    df["avg_weekly_tweets"].notna() &
    (df["avg_weekly_tweets"] <= FILTER_B_CUTOFF)
).astype(int)

# Re-save raw with all derived columns appended
df.to_csv(RAW_CSV, index=False)
print(f"\nRaw profiles (with filter flags) saved to {RAW_CSV}")

# --- Save filtered ---
filtered_df = df[
    (df["not_found"] == 0) &
    (df["filter_a_pass"] == 1) &
    (df["filter_b_pass"] == 1)
].copy()
filtered_df.to_csv(FILTERED_CSV, index=False)
print(f"Filtered profiles saved to {FILTERED_CSV}")

# --- Summary ---
n_total     = len(df)
n_not_found = (df["not_found"] == 1).sum()
n_found     = (df["not_found"] == 0).sum()
n_after_a   = ((df["not_found"] == 0) & (df["filter_a_pass"] == 1)).sum()
n_final     = len(filtered_df)

print(f"\nSummary:")
print(f"  Input authors:          {n_total:,}")
print(f"  Not found by API:       {n_not_found:,}")
print(f"  Pass Filter A (age):    {n_after_a:,}  (of {n_found:,} found)")
print(f"  Pass Filter A + B:      {n_final:,}")
