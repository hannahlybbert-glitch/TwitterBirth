# Author: Hannah Lybbert
# Created: 2026-03-20
# Updated: 2026-04-09
# Purpose: Plot average posts per month (levels) relative to birth; requires full_18_pre or one_year_pre AND posted_after_birth

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[5]
INPUT_PATH = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"
OUTPUT_DIR = ROOT / "Reddit/output/analysis/volume"

WINDOW_MIN = -18
WINDOW_MAX =  18

# ----------------------------------------------------------------
# Helper: mean and 95% CI of posts per author per month
# Mirrors Stata: collapse (mean) (sd) (count), by(months_from_birth)
#                gen se = sd / sqrt(n)
#                gen ci_lower/upper = mean +/- 1.96 * se
# ----------------------------------------------------------------
def compute_stats(df_subset, authors, month_min, month_max):
    author_month = (
        df_subset.groupby(["author", "months_from_birth"])["id"]
        .count()
        .reset_index()
        .rename(columns={"id": "posts"})
    )
    months = range(month_min, month_max + 1)
    grid = pd.MultiIndex.from_product([authors, months], names=["author", "months_from_birth"])
    full = (
        pd.DataFrame(index=grid)
        .reset_index()
        .merge(author_month, on=["author", "months_from_birth"], how="left")
        .fillna({"posts": 0})
    )
    stats = full.groupby("months_from_birth")["posts"].agg(["mean", "std", "count"]).reset_index()
    stats["se"]       = stats["std"] / np.sqrt(stats["count"])
    stats["ci_lower"] = stats["mean"] - 1.96 * stats["se"]
    stats["ci_upper"] = stats["mean"] + 1.96 * stats["se"]
    return stats

# ----------------------------------------------------------------
# Load and filter to full_18_pre sample
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH)
df = df[df["full_18_pre"] == 1].copy()

n_authors = df["author"].nunique()
print(f"Authors in sample (full_18_pre == 1): {n_authors:,}")

# Gender already assigned in build_analysis_ready_file.py
author_gender = df[["author", "female"]].drop_duplicates("author")
n_female = (author_gender["female"] == 1).sum()
n_male   = (author_gender["female"] == 0).sum()

# ----------------------------------------------------------------
# Restrict to window
# ----------------------------------------------------------------
df = df[(df["months_from_birth"] >= WINDOW_MIN) & (df["months_from_birth"] <= WINDOW_MAX)]

# ----------------------------------------------------------------
# Figure 1: Overall
# ----------------------------------------------------------------
stats = compute_stats(df, df["author"].unique(), WINDOW_MIN, WINDOW_MAX)

fig, ax = plt.subplots(figsize=(10, 5))
ax.errorbar(stats["months_from_birth"], stats["mean"],
            yerr=[stats["mean"] - stats["ci_lower"], stats["ci_upper"] - stats["mean"]],
            color="steelblue", linewidth=1.5, capsize=3, elinewidth=0.8, capthick=0.8)
ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Months from Birth")
ax.set_ylabel("Avg Posts per Month")
ax.set_title("Average Reddit Posting Volume Around Birth")
ax.set_xlim(WINDOW_MIN, WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 2))
ax.annotate(f"N = {n_authors:,} authors",
            xy=(0.02, 0.97), xycoords="axes fraction", fontsize=9, color="gray", va="top")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "avg_posts_month.jpg", dpi=150)
plt.close()
print(f"Saved to {OUTPUT_DIR / 'avg_posts_month.jpg'}")

# ----------------------------------------------------------------
# Figure 2: By gender
# ----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5))
for gender, color, label in [(1, "red", "Female"), (0, "blue", "Male")]:
    df_g    = df[df["female"] == gender]
    stats_g = compute_stats(df_g, df_g["author"].unique(), WINDOW_MIN, WINDOW_MAX)
    ax.errorbar(stats_g["months_from_birth"], stats_g["mean"],
                yerr=[stats_g["mean"] - stats_g["ci_lower"], stats_g["ci_upper"] - stats_g["mean"]],
                color=color, linewidth=1.5, capsize=3, elinewidth=0.8, capthick=0.8, label=label)

ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Months from Birth")
ax.set_ylabel("Avg Posts per Month")
ax.set_title("Average Reddit Posting Volume Around Birth by Gender")
ax.set_xlim(WINDOW_MIN, WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 2))
ax.legend(loc="upper right")
ax.annotate(f"N = {n_authors:,} authors ({n_female:,} female, {n_male:,} male)",
            xy=(0.02, 0.97), xycoords="axes fraction", fontsize=9, color="gray", va="top")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "avg_posts_month_gender.jpg", dpi=150)
plt.close()
print(f"Saved to {OUTPUT_DIR / 'avg_posts_month_gender.jpg'}")

# ----------------------------------------------------------------
# Figures 3 & 4: one_year_pre == 1 sample
# ----------------------------------------------------------------
WINDOW_MIN_1YR = -12

df1 = pd.read_csv(INPUT_PATH)
df1 = df1[df1["one_year_pre"] == 1].copy()

n_authors_1yr = df1["author"].nunique()
print(f"\nAuthors in sample (one_year_pre == 1): {n_authors_1yr:,}")

author_gender_1yr = df1[["author", "female"]].drop_duplicates("author")
n_female_1yr = (author_gender_1yr["female"] == 1).sum()
n_male_1yr   = (author_gender_1yr["female"] == 0).sum()

df1 = df1[(df1["months_from_birth"] >= WINDOW_MIN_1YR) & (df1["months_from_birth"] <= WINDOW_MAX)]

# Figure 3: Overall — one_year_pre
stats_1yr = compute_stats(df1, df1["author"].unique(), WINDOW_MIN_1YR, WINDOW_MAX)

fig, ax = plt.subplots(figsize=(10, 5))
ax.errorbar(stats_1yr["months_from_birth"], stats_1yr["mean"],
            yerr=[stats_1yr["mean"] - stats_1yr["ci_lower"], stats_1yr["ci_upper"] - stats_1yr["mean"]],
            color="steelblue", linewidth=1.5, capsize=3, elinewidth=0.8, capthick=0.8)
ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Months from Birth")
ax.set_ylabel("Avg Posts per Month")
ax.set_title("Average Reddit Posting Volume Around Birth (1-Year Pre Sample)")
ax.set_xlim(WINDOW_MIN_1YR, WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN_1YR, WINDOW_MAX + 1, 2))
ax.annotate(f"N = {n_authors_1yr:,} authors",
            xy=(0.02, 0.97), xycoords="axes fraction", fontsize=9, color="gray", va="top")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "avg_posts_month_1yr_pre.jpg", dpi=150)
plt.close()
print(f"Saved to {OUTPUT_DIR / 'avg_posts_month_1yr_pre.jpg'}")

# Figure 4: By gender — one_year_pre
fig, ax = plt.subplots(figsize=(10, 5))
for gender, color, label in [(1, "red", "Female"), (0, "blue", "Male")]:
    df1_g    = df1[df1["female"] == gender]
    stats_1g = compute_stats(df1_g, df1_g["author"].unique(), WINDOW_MIN_1YR, WINDOW_MAX)
    ax.errorbar(stats_1g["months_from_birth"], stats_1g["mean"],
                yerr=[stats_1g["mean"] - stats_1g["ci_lower"], stats_1g["ci_upper"] - stats_1g["mean"]],
                color=color, linewidth=1.5, capsize=3, elinewidth=0.8, capthick=0.8, label=label)

ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Months from Birth")
ax.set_ylabel("Avg Posts per Month")
ax.set_title("Average Reddit Posting Volume Around Birth by Gender (1-Year Pre Sample)")
ax.set_xlim(WINDOW_MIN_1YR, WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN_1YR, WINDOW_MAX + 1, 2))
ax.legend(loc="upper right")
ax.annotate(f"N = {n_authors_1yr:,} authors ({n_female_1yr:,} female, {n_male_1yr:,} male)",
            xy=(0.02, 0.97), xycoords="axes fraction", fontsize=9, color="gray", va="top")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "avg_posts_month_gender_1yr_pre.jpg", dpi=150)
plt.close()
print(f"Saved to {OUTPUT_DIR / 'avg_posts_month_gender_1yr_pre.jpg'}")
