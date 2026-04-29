# Author: Hannah Lybbert
# Created: 2026-04-09
# Updated: 2026-04-09
# Purpose: Run VADER sentiment analysis on Reddit text_analysis file; outputs sentiment scores

import pandas as pd
import swifter
swifter.config.progress_bar = True
from pathlib import Path
from vader_sentiment_logic import get_sentiment_scores

ROOT        = Path(__file__).resolve().parents[5]
INPUT_10K   = ROOT / "Reddit/data/final/text/text_analysis_births_posts_10k.csv"
INPUT_FULL  = ROOT / "Reddit/data/final/text/text_analysis_births_posts.csv"
OUTPUT_DIR  = ROOT / "Reddit/data/NLP/sentiment"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SCORE_COLS  = ["neg", "neu", "pos", "compound", "overall"]
CHUNK_SIZE  = 50_000

# ----------------------------------------------------------------
# Toggle: set TEST = True to run on 10k sample, False for full run
# ----------------------------------------------------------------
TEST = False

input_path  = INPUT_10K  if TEST else INPUT_FULL
output_path = OUTPUT_DIR / ("vader_sentiment_10k.csv" if TEST else "vader_sentiment_FULL.csv")

# ----------------------------------------------------------------
# 10k sample: load all at once, use swifter for parallelized apply
# ----------------------------------------------------------------
if TEST:
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df):,} rows for test run")

    df[SCORE_COLS] = df["text"].swifter.apply(
        lambda x: pd.Series(get_sentiment_scores(x))
    )

    df[["neg", "neu", "pos", "compound"]] = df[["neg", "neu", "pos", "compound"]].astype("float32")
    df["overall"] = df["overall"].astype("category")

    df.to_csv(output_path, index=False)
    print(f"\nDone. Saved {len(df):,} rows to {output_path}")

# ----------------------------------------------------------------
# Full run: chunked processing to keep memory manageable at 3.4M rows
# ----------------------------------------------------------------
else:
    print(f"Starting full run (chunk size: {CHUNK_SIZE:,})")
    reader    = pd.read_csv(input_path, chunksize=CHUNK_SIZE)
    total_rows = 0

    for i, chunk in enumerate(reader):
        chunk[SCORE_COLS] = chunk["text"].apply(
            lambda x: pd.Series(get_sentiment_scores(x))
        )
        chunk[["neg", "neu", "pos", "compound"]] = chunk[["neg", "neu", "pos", "compound"]].astype("float32")
        chunk["overall"] = chunk["overall"].astype("category")

        chunk.to_csv(output_path, mode="a", index=False, header=(i == 0))
        total_rows += len(chunk)

        if (i + 1) % 10 == 0:
            print(f"  Processed {total_rows:,} rows...")

    print(f"\nDone. Saved {total_rows:,} rows to {output_path}")
