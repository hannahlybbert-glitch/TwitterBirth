# Author: Hannah Lybbert
# Created: 2026-03-26
# Updated: 2026-03-26
# Purpose: Split 2.3M parquet into 10 evenly-sized batch parquets for the mini → full pipeline

import pandas as pd
import numpy as np
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[5]
INPUT_PATH = ROOT / "Reddit/data/intermediate/cleaned_raw/reddit_parenting_2_3M_sample.parquet"
BATCH_DIR  = ROOT / "Reddit/data/LLM/pipeline/batches"

N_BATCHES  = 10

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
print(f"Loading {INPUT_PATH.name}...")
df = pd.read_parquet(INPUT_PATH)
print(f"  Loaded {len(df):,} rows")

# ----------------------------------------------------------------
# Split into N_BATCHES evenly-sized chunks
# ----------------------------------------------------------------
BATCH_DIR.mkdir(parents=True, exist_ok=True)

batch_dfs = np.array_split(df, N_BATCHES)

for i, batch in enumerate(batch_dfs, start=1):
    batch = batch.reset_index(drop=True)
    out   = BATCH_DIR / f"batch_{i:02d}.parquet"
    batch.to_parquet(out, index=False)
    print(f"  Batch {i:02d}: {len(batch):,} rows → {out.name}")

print(f"\nDone. {N_BATCHES} batch files saved to {BATCH_DIR}")
