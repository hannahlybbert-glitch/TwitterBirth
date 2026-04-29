# Author: Hannah Lybbert
# Created: 2026-03-30
# Updated: 2026-03-30
# Purpose: Recover title/selftext columns for staging positives files that were saved without text.
#          Run this for any batch processed by script 2 before the fix (batches 1-6).
#          Also deletes the empty full_results files so script 3 will reprocess them.

import pandas as pd
from pathlib import Path

ROOT        = Path(__file__).resolve().parents[5]
staging_dir = ROOT / "Reddit/data/LLM/pipeline/staging"
batches_dir = ROOT / "Reddit/data/LLM/pipeline/batches"
output_dir  = ROOT / "Reddit/data/LLM/pipeline/full_output"

BATCHES_TO_RECOVER = range(1, 6)  # batches 1-6

for i in BATCHES_TO_RECOVER:
    batch        = f"batch_{i:02d}"
    staging_file = staging_dir / f"{batch}_positives.csv"
    results_file = output_dir  / f"{batch}_full_results.csv"
    parquet_file = batches_dir / f"{batch}.parquet"

    if not staging_file.exists():
        print(f"[{batch}] No staging file found — skipping.")
        continue

    # Check if text is already present
    cols = pd.read_csv(staging_file, nrows=0).columns.tolist()
    if "title" in cols and "selftext" in cols:
        print(f"[{batch}] Already has text columns — skipping.")
        continue

    print(f"\n[{batch}] Joining text columns...")
    parquet = pd.read_parquet(parquet_file)[["id", "title", "selftext"]]
    parquet["id"] = parquet["id"].astype(str)

    positives = pd.read_csv(staging_file)
    positives["id"] = positives["id"].astype(str)
    positives = positives.merge(parquet, on="id", how="left")
    positives.to_csv(staging_file, index=False)
    print(f"  Saved {len(positives):,} rows with columns: {list(positives.columns)}")

    # Delete empty results file so watcher reprocesses it
    if results_file.exists():
        results_file.unlink()
        print(f"  Deleted {results_file.name}")

print("\nRecovery complete.")
