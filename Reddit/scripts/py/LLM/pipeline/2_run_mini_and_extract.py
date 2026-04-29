# Author: Hannah Lybbert
# Created: 2026-03-26
# Updated: 2026-03-28
# Purpose: Run each of the 10 batches through GPT-4o-mini sequentially; extract birth_flag==1 rows to staging

import os
import openai
import pandas as pd
from pathlib import Path
from dotenv import load_dotenv
from pipeline_utils import run_batch_pipeline

ROOT        = Path(__file__).resolve().parents[5]
BATCH_DIR   = ROOT / "Reddit/data/LLM/pipeline/batches"
MINI_DIR    = ROOT / "Reddit/data/LLM/pipeline/mini_output"
STAGING_DIR = ROOT / "Reddit/data/LLM/pipeline/staging"
JSON_DIR    = ROOT / "Reddit/data/json/pipeline"

MODEL                  = "gpt-4o-mini"
TOKENS_PER_PROMPT      = 1800
ENQUEUED_TOKEN_LIMIT   = 40_000_000   # tier 3 limit for gpt-4o-mini
MAX_REQUESTS_PER_BATCH = int(ENQUEUED_TOKEN_LIMIT * 0.99 // TOKENS_PER_PROMPT)

# ----------------------------------------------------------------
# Setup
# ----------------------------------------------------------------
load_dotenv(dotenv_path=str(ROOT / "config/.env"))
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MINI_DIR.mkdir(parents=True, exist_ok=True)
STAGING_DIR.mkdir(parents=True, exist_ok=True)

batch_files = sorted(BATCH_DIR.glob("batch_*.parquet"))
print(f"Found {len(batch_files)} batch files to process\n")

# ----------------------------------------------------------------
# Loop through each batch
# ----------------------------------------------------------------
for batch_path in batch_files:
    batch_name  = batch_path.stem                            # e.g. "batch_01"
    mini_out    = MINI_DIR    / f"{batch_name}_mini_results.csv"
    staging_out = STAGING_DIR / f"{batch_name}_positives.csv"

    # Skip if already fully processed
    if staging_out.exists():
        print(f"[{batch_name}] Already processed — skipping.")
        continue

    print(f"[{batch_name}] Loading batch ({batch_path.name})...")
    df = pd.read_parquet(batch_path)
    df["id"] = df["id"].astype(str)
    print(f"[{batch_name}] {len(df):,} rows — running through {MODEL}...")

    # Run through GPT-4o-mini
    task_name = f"mini_{batch_name}"
    results   = run_batch_pipeline(
        client               = client,
        df                   = df,
        task_name            = task_name,
        model                = MODEL,
        max_requests_per_batch = MAX_REQUESTS_PER_BATCH,
        json_dir             = JSON_DIR,
    )

    # Save full mini results
    results.to_csv(mini_out, index=False)
    print(f"[{batch_name}] Mini results saved → {mini_out.name} ({len(results):,} rows)")

    # Extract positives and save to staging (include original text for full model)
    positives = results[results["birth_flag"] == 1].copy()
    text_cols = [c for c in ["title", "selftext"] if c in df.columns]
    if text_cols:
        positives = positives.merge(df[["id"] + text_cols], on="id", how="left")
    positives.to_csv(staging_out, index=False)
    print(f"[{batch_name}] Positives saved → {staging_out.name} ({len(positives):,} rows)\n")

print("All batches complete.")
