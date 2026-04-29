# Author: Hannah Lybbert
# Created: 2026-03-20
# Updated: 2026-03-20
# Purpose: Descriptive histograms of author sample coverage in months relative to birth

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[4]
INPUT_PATH = ROOT / "Reddit/data/final/reddit_30k_births_and_posts.csv"
OUTPUT_DIR = ROOT / "Reddit/output/descriptives"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH)
print(f"Loaded {len(df):,} rows, {df['author'].nunique():,} unique authors")

# ----------------------------------------------------------------
# Compute min and max months_from_birth per author
# ----------------------------------------------------------------
author_coverage = df.groupby("author")["months_from_birth"].agg(
    start_month="min",
    end_month="max"
).reset_index()

authors_15mo_pre  = (author_coverage["start_month"] <= -15).sum()
authors_18mo_pre  = (author_coverage["start_month"] <= -18).sum()
authors_18mo_post = (author_coverage["end_month"]   >= 18).sum()

print(f"\nSample coverage (months_from_birth):")
print(f"  Avg start month:                  {author_coverage['start_month'].mean():.1f}")
print(f"  Avg end month:                    {author_coverage['end_month'].mean():.1f}")
print(f"  Authors with >= 15 months pre:    {authors_15mo_pre:,}")
print(f"  Authors with >= 18 months pre:    {authors_18mo_pre:,}")
print(f"  Authors with >= 18 months post:   {authors_18mo_post:,}")

# ----------------------------------------------------------------
# Histogram: distribution of start months (most negative months_from_birth)
# ----------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].hist(author_coverage["start_month"], bins=30, edgecolor="white", color="steelblue")
axes[0].axvline(0, color="black", linestyle="--", linewidth=1)
axes[0].set_title("Distribution of Author Start Month\n(min months_from_birth per author)")
axes[0].set_xlabel("Months from Birth")
axes[0].set_ylabel("Number of Authors")

# ----------------------------------------------------------------
# Histogram: distribution of end months (most positive months_from_birth)
# ----------------------------------------------------------------
axes[1].hist(author_coverage["end_month"], bins=30, edgecolor="white", color="steelblue")
axes[1].axvline(0, color="black", linestyle="--", linewidth=1)
axes[1].set_title("Distribution of Author End Month\n(max months_from_birth per author)")
axes[1].set_xlabel("Months from Birth")
axes[1].set_ylabel("Number of Authors")

plt.tight_layout()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
plt.savefig(OUTPUT_DIR / "sample_coverage_months.jpg", dpi=150)
plt.close()
print(f"\nSaved to {OUTPUT_DIR / 'sample_coverage_months.jpg'}")
