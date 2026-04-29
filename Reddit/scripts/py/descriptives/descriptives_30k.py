# Author: Hannah Lybbert
# Created: 2026-03-23
# Updated: 2026-03-23
# Purpose: Summary stats and histogram on birth posts (birth_post == 1) from the 30k sample

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[4]
INPUT_PATH = ROOT / "Reddit/data/final/reddit_30k_births_and_posts.csv"
OUTPUT_DIR = ROOT / "Reddit/output/descriptives"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------
# Load and filter to birth posts
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH)
births = df[df["birth_post"] == 1].copy()
print(f"Loaded {len(df):,} total rows | {len(births):,} birth posts (birth_post == 1)")

# ----------------------------------------------------------------
# days_from_birth
# ----------------------------------------------------------------
print("\n--- days_from_birth (birth posts only) ---")
print(births["days_from_birth"].describe(percentiles=[.1, .25, .5, .75, .9]).round(1).to_string())

# ----------------------------------------------------------------
# confidence
# ----------------------------------------------------------------
print("\n--- confidence (birth posts only) ---")
print(births["confidence"].describe(percentiles=[.1, .25, .5, .75, .9]).round(3).to_string())

# ----------------------------------------------------------------
# Gender breakdown (p_female / p_male)
# ----------------------------------------------------------------
print("\n--- Gender breakdown (birth posts only) ---")
print(f"  Mean p_female: {births['p_female'].mean():.3f}")
print(f"  Mean p_male:   {births['p_male'].mean():.3f}")
print(f"  Likely female (p_female > 0.5): {(births['p_female'] > 0.5).sum():,} ({(births['p_female'] > 0.5).mean()*100:.1f}%)")
print(f"  Likely male   (p_male   > 0.5): {(births['p_male']   > 0.5).sum():,} ({(births['p_male']   > 0.5).mean()*100:.1f}%)")

# ----------------------------------------------------------------
# Top subreddits
# ----------------------------------------------------------------
print("\n--- Top 10 subreddits (birth posts only) ---")
print(births["subreddit"].value_counts().head(10).to_string())

# ----------------------------------------------------------------
# Post score
# ----------------------------------------------------------------
print("\n--- score (birth posts only) ---")
print(births["score"].describe(percentiles=[.25, .5, .75, .9]).round(1).to_string())

# ----------------------------------------------------------------
# Histograms
# ----------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# days_from_birth
axes[0, 0].hist(births["days_from_birth"].dropna(), bins=40, edgecolor="white", color="steelblue")
axes[0, 0].axvline(0, color="black", linestyle="--", linewidth=1)
axes[0, 0].set_title("Days from Birth (birth posts only)")
axes[0, 0].set_xlabel("Days from Birth")
axes[0, 0].set_ylabel("Number of Posts")

# confidence
axes[0, 1].hist(births["confidence"].dropna(), bins=30, edgecolor="white", color="steelblue")
axes[0, 1].set_title("Model Confidence (birth posts only)")
axes[0, 1].set_xlabel("Confidence")
axes[0, 1].set_ylabel("Number of Posts")

# p_female
axes[1, 0].hist(births["p_female"].dropna(), bins=30, edgecolor="white", color="mediumpurple")
axes[1, 0].axvline(0.5, color="black", linestyle="--", linewidth=1)
axes[1, 0].set_title("P(Female) (birth posts only)")
axes[1, 0].set_xlabel("p_female")
axes[1, 0].set_ylabel("Number of Posts")

# score
axes[1, 1].hist(births["score"].dropna().clip(upper=births["score"].quantile(0.95)), bins=30, edgecolor="white", color="steelblue")
axes[1, 1].set_title("Post Score — clipped at 95th pct (birth posts only)")
axes[1, 1].set_xlabel("Score")
axes[1, 1].set_ylabel("Number of Posts")

plt.suptitle("30k Sample — Birth Post Descriptives", fontsize=14, fontweight="bold")
plt.tight_layout()
out_path = OUTPUT_DIR / "descriptives_30k_births.jpg"
plt.savefig(out_path, dpi=150)
plt.close()
print(f"\nHistogram saved to {out_path}")
