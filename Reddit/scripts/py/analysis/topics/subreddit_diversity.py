# Author: Hannah Lybbert
# Created: 2026-04-13
# Updated: 2026-04-13
# Purpose: Plot avg unique subreddits per active author per month relative to birth

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[5]
INPUT_PATH = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"
OUTPUT_DIR = ROOT / "Reddit/output/analysis/topics"

WINDOW_MIN = -18
WINDOW_MAX =  18

# ----------------------------------------------------------------
# Helper: mean and 95% CI of unique subreddits per active author
# Conditional on posting: no zero-fill — only author-months with
# observed activity enter the average for that month.
# ----------------------------------------------------------------
def compute_stats(df_subset, month_min, month_max):
    # For each author × month: count distinct subreddits posted to
    author_month = (
        df_subset
        .groupby(["author", "months_from_birth"])["subreddit"]
        .nunique()
        .reset_index()
        .rename(columns={"subreddit": "n_subreddits"})
    )
    # Restrict to window
    author_month = author_month[
        (author_month["months_from_birth"] >= month_min) &
        (author_month["months_from_birth"] <= month_max)
    ]
    # Average across active authors for each month (no zero-fill)
    stats = (
        author_month
        .groupby("months_from_birth")["n_subreddits"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    stats["se"]       = stats["std"] / np.sqrt(stats["count"])
    stats["ci_lower"] = stats["mean"] - 1.96 * stats["se"]
    stats["ci_upper"] = stats["mean"] + 1.96 * stats["se"]
    return stats

# ----------------------------------------------------------------
# Load data — restrict to full_18_pre == 1 sample
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH)
df = df[df["full_18_pre"] == 1].copy()
df = df[(df["months_from_birth"] >= WINDOW_MIN) & (df["months_from_birth"] <= WINDOW_MAX)].copy()

n_authors = df["author"].nunique()
print(f"Authors in sample (full_18_pre == 1): {n_authors:,}")

author_gender = df[["author", "female"]].drop_duplicates("author")
n_female = (author_gender["female"] == 1).sum()
n_male   = (author_gender["female"] == 0).sum()

# ----------------------------------------------------------------
# Figure 1: Overall
# ----------------------------------------------------------------
stats = compute_stats(df, WINDOW_MIN, WINDOW_MAX)

fig, ax = plt.subplots(figsize=(10, 5))
ax.errorbar(
    stats["months_from_birth"], stats["mean"],
    yerr=[stats["mean"] - stats["ci_lower"], stats["ci_upper"] - stats["mean"]],
    color="steelblue", linewidth=1.5, capsize=3, elinewidth=0.8, capthick=0.8
)
ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Months from Birth")
ax.set_ylabel("Avg Unique Subreddits per Month")
ax.set_title("Average Subreddit Diversity Around Birth")
ax.set_xlim(WINDOW_MIN, WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 2))
ax.annotate(
    f"N = {n_authors:,} authors",
    xy=(0.02, 0.97), xycoords="axes fraction", fontsize=9, color="gray", va="top"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "unique_subreddits.jpg", dpi=150)
plt.close()
print(f"Saved: {OUTPUT_DIR / 'unique_subreddits.jpg'}")

# ----------------------------------------------------------------
# Figure 2: By gender
# ----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5))
for gender, color, label in [(1, "red", "Female"), (0, "blue", "Male")]:
    df_g    = df[df["female"] == gender]
    stats_g = compute_stats(df_g, WINDOW_MIN, WINDOW_MAX)
    ax.errorbar(
        stats_g["months_from_birth"], stats_g["mean"],
        yerr=[stats_g["mean"] - stats_g["ci_lower"], stats_g["ci_upper"] - stats_g["mean"]],
        color=color, linewidth=1.5, capsize=3, elinewidth=0.8, capthick=0.8, label=label
    )

ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Months from Birth")
ax.set_ylabel("Avg Unique Subreddits per Month")
ax.set_title("Average Subreddit Diversity Around Birth by Gender")
ax.set_xlim(WINDOW_MIN, WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 2))
ax.legend(loc="upper right")
ax.annotate(
    f"N = {n_authors:,} authors ({n_female:,} female, {n_male:,} male)",
    xy=(0.02, 0.97), xycoords="axes fraction", fontsize=9, color="gray", va="top"
)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "unique_subreddits_gender.jpg", dpi=150)
plt.close()
print(f"Saved: {OUTPUT_DIR / 'unique_subreddits_gender.jpg'}")

# ----------------------------------------------------------------
# Helper: active author count per month
# ----------------------------------------------------------------
def compute_active_n(df_subset, month_min, month_max):
    active = (
        df_subset
        .groupby("months_from_birth")["author"]
        .nunique()
        .reset_index()
        .rename(columns={"author": "active_authors"})
    )
    active = active[
        (active["months_from_birth"] >= month_min) &
        (active["months_from_birth"] <= month_max)
    ]
    return active

# ----------------------------------------------------------------
# Figure 3: Overall — two panels (diversity + active N)
# ----------------------------------------------------------------
active = compute_active_n(df, WINDOW_MIN, WINDOW_MAX)

fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(10, 7), sharex=True,
                                      gridspec_kw={"height_ratios": [3, 1]})

ax_top.errorbar(
    stats["months_from_birth"], stats["mean"],
    yerr=[stats["mean"] - stats["ci_lower"], stats["ci_upper"] - stats["mean"]],
    color="steelblue", linewidth=1.5, capsize=3, elinewidth=0.8, capthick=0.8
)
ax_top.axvline(0, color="black", linestyle="--", linewidth=1)
ax_top.set_ylabel("Avg Unique Subreddits per Month")
ax_top.set_title("Average Subreddit Diversity Around Birth")
ax_top.set_xlim(WINDOW_MIN, WINDOW_MAX)
ax_top.annotate(
    f"N = {n_authors:,} authors",
    xy=(0.02, 0.97), xycoords="axes fraction", fontsize=9, color="gray", va="top"
)

ax_bot.bar(active["months_from_birth"], active["active_authors"],
           color="steelblue", alpha=0.6, width=0.8)
ax_bot.axvline(0, color="black", linestyle="--", linewidth=1)
ax_bot.set_xlabel("Months from Birth")
ax_bot.set_ylabel("Active Authors")
ax_bot.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 2))

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "unique_subreddits_with_n.jpg", dpi=150)
plt.close()
print(f"Saved: {OUTPUT_DIR / 'unique_subreddits_with_n.jpg'}")

# ----------------------------------------------------------------
# Figure 4: By gender — two panels (diversity + active N)
# ----------------------------------------------------------------
fig, (ax_top, ax_bot) = plt.subplots(2, 1, figsize=(10, 7), sharex=True,
                                      gridspec_kw={"height_ratios": [3, 1]})

for gender, color, label in [(1, "red", "Female"), (0, "blue", "Male")]:
    df_g    = df[df["female"] == gender]
    stats_g = compute_stats(df_g, WINDOW_MIN, WINDOW_MAX)
    active_g = compute_active_n(df_g, WINDOW_MIN, WINDOW_MAX)
    ax_top.errorbar(
        stats_g["months_from_birth"], stats_g["mean"],
        yerr=[stats_g["mean"] - stats_g["ci_lower"], stats_g["ci_upper"] - stats_g["mean"]],
        color=color, linewidth=1.5, capsize=3, elinewidth=0.8, capthick=0.8, label=label
    )
    ax_bot.plot(active_g["months_from_birth"], active_g["active_authors"],
                color=color, linewidth=1.2, label=label)

ax_top.axvline(0, color="black", linestyle="--", linewidth=1)
ax_top.set_ylabel("Avg Unique Subreddits per Month")
ax_top.set_title("Average Subreddit Diversity Around Birth by Gender")
ax_top.set_xlim(WINDOW_MIN, WINDOW_MAX)
ax_top.legend(loc="upper right")
ax_top.annotate(
    f"N = {n_authors:,} authors ({n_female:,} female, {n_male:,} male)",
    xy=(0.02, 0.97), xycoords="axes fraction", fontsize=9, color="gray", va="top"
)

ax_bot.axvline(0, color="black", linestyle="--", linewidth=1)
ax_bot.set_xlabel("Months from Birth")
ax_bot.set_ylabel("Active Authors")
ax_bot.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 2))
ax_bot.legend(loc="upper right")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "unique_subreddits_gender_with_n.jpg", dpi=150)
plt.close()
print(f"Saved: {OUTPUT_DIR / 'unique_subreddits_gender_with_n.jpg'}")
