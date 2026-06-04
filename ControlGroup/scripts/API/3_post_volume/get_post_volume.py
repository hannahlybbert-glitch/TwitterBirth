# Author: Hannah Lybbert
# Created: 2026-06-04
# Purpose: Phase 3 — pull daily post volume for filtered users,
#          18 months before and after each user's seed tweet date

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

import json
import time
import requests
import pandas as pd
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv

# --- Config ---
load_dotenv(dotenv_path="config/.env")
BEARER_TOKEN = os.getenv("X_API_BEARER_TOKEN")

SLEEP_BETWEEN    = 0.5   # seconds between each API call
CHECKPOINT_EVERY = 10    # users between progress saves

TEST_MODE = True   # set False for full run

if TEST_MODE:
    INPUT_CSV  = "ControlGroup/data/user_profiles/test/profiles_filtered.csv"
    OUTPUT_DIR = "ControlGroup/data/post_volume/test"
else:
    INPUT_CSV  = "ControlGroup/data/user_profiles/profiles_filtered.csv"
    OUTPUT_DIR = "ControlGroup/data/post_volume"

TEMP_CSV      = f"{OUTPUT_DIR}/post_volume_temp.csv"
OUTPUT_CSV    = f"{OUTPUT_DIR}/post_volume.csv"       # test mode final output
OUTPUT_PARQUET = f"{OUTPUT_DIR}/post_volume.parquet"  # full mode final output
PROGRESS_FILE = f"{OUTPUT_DIR}/progress.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)

COUNTS_URL = "https://api.twitter.com/2/tweets/counts/all"

# --- Load inputs ---
users_df = pd.read_csv(INPUT_CSV, dtype=str)
users_df["seed_tweet_date"] = pd.to_datetime(users_df["seed_tweet_date"], utc=True)
users_df = users_df[["author_id", "seed_tweet_date"]].drop_duplicates(subset="author_id")
print(f"Loaded {len(users_df):,} filtered users")

# --- Resume from checkpoint ---
completed_ids = set()
if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE) as f:
        completed_ids = set(json.load(f).get("completed_author_ids", []))
    print(f"Checkpoint found — {len(completed_ids):,} users already complete, skipping")

remaining = users_df[~users_df["author_id"].isin(completed_ids)]
print(f"Remaining: {len(remaining):,} users to pull")

# --- Helpers ---
def paginate_counts(query, start_time, end_time, bearer_token, max_retries=5):
    """Fetch all daily count buckets for a query+window, paging through next_token."""
    params = {
        "query":       query,
        "start_time":  start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time":    end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "granularity": "day",
    }
    headers = {"Authorization": f"Bearer {bearer_token}"}
    rows = []

    while True:
        for attempt in range(max_retries):
            response = requests.get(COUNTS_URL, params=params, headers=headers)
            if response.status_code == 200:
                break
            if response.status_code == 429:
                reset_ts = response.headers.get("x-rate-limit-reset")
                wait = max(int(reset_ts) - int(time.time()) + 5, 5) if reset_ts else 60 * (2 ** attempt)
                print(f"    Rate limited. Waiting {wait}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait)
            else:
                response.raise_for_status()
        else:
            response.raise_for_status()

        data = response.json()
        for bucket in data.get("data", []):
            rows.append({
                "date":  bucket["start"][:10],   # YYYY-MM-DD
                "count": bucket["tweet_count"],
            })

        next_token = data.get("meta", {}).get("next_token")
        if not next_token:
            break
        params["next_token"] = next_token
        time.sleep(SLEEP_BETWEEN)

    return rows

def flush_to_temp(rows):
    chunk = pd.concat(rows, ignore_index=True)
    write_header = not os.path.exists(TEMP_CSV)
    chunk.to_csv(TEMP_CSV, mode="a", header=write_header, index=False)

def save_progress(completed_ids):
    with open(PROGRESS_FILE, "w") as f:
        json.dump({"completed_author_ids": list(completed_ids)}, f)

# --- Main pull loop ---
buffer = []
users_since_checkpoint = 0

for _, user_row in remaining.iterrows():
    author_id = user_row["author_id"]
    seed_dt   = user_row["seed_tweet_date"]

    start_time = seed_dt - relativedelta(months=18)
    end_time   = seed_dt + relativedelta(months=18)

    print(f"[{author_id}]  seed={seed_dt.date()}  window: {start_time.date()} → {end_time.date()}")

    try:
        counts_a = paginate_counts(
            f"from:{author_id} -is:retweet -is:reply",
            start_time, end_time, BEARER_TOKEN
        )
        time.sleep(SLEEP_BETWEEN)

        counts_b = paginate_counts(
            f"from:{author_id} (is:retweet OR is:reply)",
            start_time, end_time, BEARER_TOKEN
        )
    except Exception as e:
        print(f"  ERROR: {e} — skipping {author_id}")
        time.sleep(SLEEP_BETWEEN)
        continue

    df_a = pd.DataFrame(counts_a) if counts_a else pd.DataFrame(columns=["date", "count"])
    df_b = pd.DataFrame(counts_b) if counts_b else pd.DataFrame(columns=["date", "count"])

    df_a = df_a.rename(columns={"count": "original_quote_count"})
    df_b = df_b.rename(columns={"count": "retweet_reply_count"})

    user_df = df_a.merge(df_b, on="date", how="outer").fillna(0)
    user_df["author_id"] = author_id
    user_df = user_df[["author_id", "date", "original_quote_count", "retweet_reply_count"]]

    buffer.append(user_df)
    completed_ids.add(author_id)
    users_since_checkpoint += 1

    print(f"  {len(user_df)} days pulled")

    if users_since_checkpoint >= CHECKPOINT_EVERY:
        flush_to_temp(buffer)
        save_progress(completed_ids)
        print(f"  Checkpoint saved — {len(completed_ids):,} users complete")
        buffer = []
        users_since_checkpoint = 0

    time.sleep(SLEEP_BETWEEN)

# --- Final flush ---
if buffer:
    flush_to_temp(buffer)

save_progress(completed_ids)
print(f"\nAll users pulled. {len(completed_ids):,} total complete.")

# --- Finalize output ---
if TEST_MODE:
    os.rename(TEMP_CSV, OUTPUT_CSV)
    print(f"Output saved to {OUTPUT_CSV}")
else:
    print("Converting temp CSV to parquet...")
    import pyarrow as pa
    import pyarrow.parquet as pq

    writer = None
    for chunk in pd.read_csv(TEMP_CSV, chunksize=500_000):
        table = pa.Table.from_pandas(chunk, preserve_index=False)
        if writer is None:
            writer = pq.ParquetWriter(OUTPUT_PARQUET, table.schema)
        writer.write_table(table)
    if writer:
        writer.close()

    os.remove(TEMP_CSV)
    print(f"Output saved to {OUTPUT_PARQUET}")
