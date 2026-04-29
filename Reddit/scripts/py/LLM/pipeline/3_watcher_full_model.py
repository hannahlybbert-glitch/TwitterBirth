# Author: Hannah Lybbert
# Created: 2026-03-26
# Updated: 2026-03-28
# Purpose: Poll staging/ every 2 hours for new positives files; run each through GPT-4o sequentially

import os
import time
import openai
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from pipeline_utils import run_batch_pipeline

ROOT        = Path(__file__).resolve().parents[5]
STAGING_DIR = ROOT / "Reddit/data/LLM/pipeline/staging"
FULL_DIR    = ROOT / "Reddit/data/LLM/pipeline/full_output"
JSON_DIR    = ROOT / "Reddit/data/json/pipeline"

MODEL                  = "gpt-4o"
TOKENS_PER_PROMPT      = 1800
ENQUEUED_TOKEN_LIMIT   = 50_000_000   # tier 3 limit for gpt-4o
MAX_REQUESTS_PER_BATCH = int(ENQUEUED_TOKEN_LIMIT * 0.99 // TOKENS_PER_PROMPT)

POLL_INTERVAL_HOURS    = 1
POLL_INTERVAL_SECONDS  = POLL_INTERVAL_HOURS * 3600

# ----------------------------------------------------------------
# Setup
# ----------------------------------------------------------------
load_dotenv(dotenv_path=str(ROOT / "config/.env"))
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

FULL_DIR.mkdir(parents=True, exist_ok=True)

print(f"Watcher started. Polling every {POLL_INTERVAL_HOURS} hour(s) for new staging files...")
print(f"Staging dir:     {STAGING_DIR}")
print(f"Full output dir: {FULL_DIR}\n")

# ----------------------------------------------------------------
# Poll loop
# ----------------------------------------------------------------
while True:
    staging_files = sorted(STAGING_DIR.glob("*_positives.csv"))

    pending = [
        f for f in staging_files
        if not (FULL_DIR / f.name.replace("_positives.csv", "_full_results.csv")).exists()
    ]

    if not pending:
        print(f"[Watcher] No new files found. Sleeping {POLL_INTERVAL_HOURS}h...")
    else:
        print(f"[Watcher] Found {len(pending)} new file(s) to process: {[f.name for f in pending]}")

        # Process sequentially — one at a time, wait for each to finish
        for staging_path in pending:
            batch_name = staging_path.stem.replace("_positives", "")   # e.g. "batch_01"
            full_out   = FULL_DIR / f"{batch_name}_full_results.csv"

            print(f"\n[{batch_name}] Loading positives ({staging_path.name})...")
            df = pd.read_csv(staging_path)
            df["id"] = df["id"].astype(str)
            print(f"[{batch_name}] {len(df):,} rows — running through {MODEL}...")

            task_name = f"full_{batch_name}"
            results   = run_batch_pipeline(
                client                 = client,
                df                     = df,
                task_name              = task_name,
                model                  = MODEL,
                max_requests_per_batch = MAX_REQUESTS_PER_BATCH,
                json_dir               = JSON_DIR,
            )

            results.to_csv(full_out, index=False)
            print(f"[{batch_name}] Full results saved → {full_out.name} ({len(results):,} rows)")

        print(f"\n[Watcher] All pending files processed. Sleeping {POLL_INTERVAL_HOURS}h...")

    time.sleep(POLL_INTERVAL_SECONDS)
