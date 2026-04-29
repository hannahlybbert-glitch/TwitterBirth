# Author: Hannah Lybbert
# Created: 2026-03-25
# Updated: 2026-03-25
# Purpose: Build author x relative-month panel with post counts (zeros for months with no posts)

import pandas as pd
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[5]
INPUT_PATH = ROOT / "Reddit/data/final/treatment_control_births_posts.csv"
OUTPUT_DIR = ROOT / "Reddit/data/intermediate/diff_n_diff"
OUTPUT     = OUTPUT_DIR / "author_month_panel.csv"

WINDOW_MIN = -18
WINDOW_MAX =  18

# ----------------------------------------------------------------
# Load and filter
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH, low_memory=False)
df = df[df["full_18_pre"] == 1].copy()
print(f"Loaded {len(df):,} rows | {df['author'].nunique():,} authors")

df["date_birth"] = pd.to_datetime(df["date_birth"], format="mixed")

# ----------------------------------------------------------------
# Author-level metadata
# ----------------------------------------------------------------
author_meta = (
    df.drop_duplicates("author")
    [["author", "treated", "date_birth", "female"]]
    .set_index("author")
)

# ----------------------------------------------------------------
# Aggregate to author x relative month
# ----------------------------------------------------------------
post_counts = (
    df.groupby(["author", "months_from_birth"])
    .size()
    .reset_index(name="post_count")
)

# ----------------------------------------------------------------
# Build full grid: every author x every month in window
# ----------------------------------------------------------------
months = list(range(WINDOW_MIN, WINDOW_MAX + 1))
grid   = pd.MultiIndex.from_product(
    [author_meta.index.tolist(), months],
    names=["author", "months_from_birth"]
)
panel = pd.DataFrame(index=grid).reset_index()

# Merge post counts (fill zero for months with no posts)
panel = panel.merge(post_counts, on=["author", "months_from_birth"], how="left")
panel["post_count"] = panel["post_count"].fillna(0).astype(int)

# Merge author metadata
panel = panel.merge(author_meta.reset_index(), on="author", how="left")

# ----------------------------------------------------------------
# Calendar month ID (YYYYMM) for time fixed effects
# Approximate: date_birth + months_from_birth * 30 days
# ----------------------------------------------------------------
panel["cal_date"]     = panel["date_birth"] + pd.to_timedelta(panel["months_from_birth"] * 30, unit="D")
panel["cal_month_id"] = panel["cal_date"].dt.year * 100 + panel["cal_date"].dt.month

# ----------------------------------------------------------------
# Save
# ----------------------------------------------------------------
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
panel.to_csv(OUTPUT, index=False)

n_treat   = (author_meta["treated"] == 1).sum()
n_control = (author_meta["treated"] == 0).sum()
print(f"\nPanel built: {len(panel):,} rows ({panel['author'].nunique():,} authors x {len(months)} months)")
print(f"  Treated authors:  {n_treat:,}")
print(f"  Control authors:  {n_control:,}")
print(f"  Zero-post months: {(panel['post_count'] == 0).sum():,} ({100*(panel['post_count']==0).mean():.1f}%)")
print(f"Saved to {OUTPUT}")
