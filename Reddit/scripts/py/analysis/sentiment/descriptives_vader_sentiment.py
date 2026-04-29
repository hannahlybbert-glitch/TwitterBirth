# Author: Hannah Lybbert
# Created: 2026-04-09
# Updated: 2026-04-09
# Purpose: Descriptive figures for VADER sentiment scores on Reddit

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

ROOT        = Path(__file__).resolve().parents[5]
INPUT_10K   = ROOT / "Reddit/data/NLP/sentiment/vader_sentiment_10k.csv"
INPUT_FULL  = ROOT / "Reddit/data/NLP/sentiment/vader_sentiment_FULL.csv"
OUTPUT_DIR  = ROOT / "Reddit/output/analysis/NLP/sentiment"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------
# Toggle: set TEST = True to run on 10k sample, False for full run
# ----------------------------------------------------------------
TEST = False

INPUT_PATH = INPUT_10K if TEST else INPUT_FULL
LABEL      = "10k"    if TEST else "FULL"

WINDOW_MIN = -18
WINDOW_MAX =  18

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH)
print(f"Loaded {len(df):,} rows | {df['author'].nunique():,} unique authors")

# ----------------------------------------------------------------
# Figure 1: Distributions of neg, neu, pos, compound (2x2 panel)
# ----------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(12, 8))

axes[0, 0].hist(df["neg"].dropna(),      bins=50, color="steelblue", edgecolor="white")
axes[0, 0].set_title("Negative Score Distribution")
axes[0, 0].set_xlabel("neg")
axes[0, 0].set_ylabel("Number of Posts")

axes[0, 1].hist(df["neu"].dropna(),      bins=50, color="steelblue", edgecolor="white")
axes[0, 1].set_title("Neutral Score Distribution")
axes[0, 1].set_xlabel("neu")
axes[0, 1].set_ylabel("Number of Posts")

axes[1, 0].hist(df["pos"].dropna(),      bins=50, color="steelblue", edgecolor="white")
axes[1, 0].set_title("Positive Score Distribution")
axes[1, 0].set_xlabel("pos")
axes[1, 0].set_ylabel("Number of Posts")

axes[1, 1].hist(df["compound"].dropna(), bins=50, color="steelblue", edgecolor="white")
axes[1, 1].axvline( 0.05, color="green", linestyle="--", linewidth=1, label="Positive threshold")
axes[1, 1].axvline(-0.05, color="red",   linestyle="--", linewidth=1, label="Negative threshold")
axes[1, 1].set_title("Compound Score Distribution")
axes[1, 1].set_xlabel("compound")
axes[1, 1].set_ylabel("Number of Posts")
axes[1, 1].legend(fontsize=8)

n_pos = (df["overall"] == "Positive").sum()
n_neg = (df["overall"] == "Negative").sum()
n_neu = (df["overall"] == "Neutral").sum()
n_tot = df["overall"].notna().sum()
print(f"\n--- Sentiment breakdown ---")
print(f"  Positive: {n_pos:,} ({n_pos/n_tot*100:.1f}%)")
print(f"  Neutral:  {n_neu:,} ({n_neu/n_tot*100:.1f}%)")
print(f"  Negative: {n_neg:,} ({n_neg/n_tot*100:.1f}%)")
print(f"  Mean compound:   {df['compound'].mean():.4f}")
print(f"  Median compound: {df['compound'].median():.4f}")

plt.suptitle(f"VADER Sentiment Score Distributions — {LABEL} Sample", fontsize=13, fontweight="bold")
plt.tight_layout()
out_dists = OUTPUT_DIR / f"sentiment_dists_{LABEL}.jpg"
plt.savefig(out_dists, dpi=150)
plt.close()
print(f"\nSaved: {out_dists}")

# ----------------------------------------------------------------
# Helper: author-month mean → collapse to month-level stats + 95% CI
# ----------------------------------------------------------------
def compute_sentiment_stats(df_win, score_col):
    author_month = (
        df_win.groupby(["author", "months_from_birth"])[score_col]
        .mean()
        .reset_index()
        .rename(columns={score_col: "score"})
    )
    stats = author_month.groupby("months_from_birth")["score"].agg(["mean", "std", "count"]).reset_index()
    stats["se"]       = stats["std"] / np.sqrt(stats["count"])
    stats["ci_lower"] = stats["mean"] - 1.96 * stats["se"]
    stats["ci_upper"] = stats["mean"] + 1.96 * stats["se"]
    return stats

# ----------------------------------------------------------------
# Figure 2: Time series — pos, neg, neu, compound (2x2 panel)
# Avg author-month score, averaged across authors per month
# ----------------------------------------------------------------
df_win = df[
    (df["months_from_birth"] >= WINDOW_MIN) &
    (df["months_from_birth"] <= WINDOW_MAX)
].copy()

n_authors = df_win["author"].nunique()

plot_specs = [
    ("pos",      "Avg Positive Score",  "steelblue",    (0, 0)),
    ("neg",      "Avg Negative Score",  "firebrick",    (0, 1)),
    ("neu",      "Avg Neutral Score",   "gray",         (1, 0)),
    ("compound", "Avg Compound Score",  "mediumpurple", (1, 1)),
]

fig, axes = plt.subplots(2, 2, figsize=(14, 9))

for score_col, ylabel, color, (r, c) in plot_specs:
    stats = compute_sentiment_stats(df_win.dropna(subset=[score_col]), score_col)
    ax = axes[r, c]
    ax.errorbar(stats["months_from_birth"], stats["mean"],
                yerr=[stats["mean"] - stats["ci_lower"], stats["ci_upper"] - stats["mean"]],
                color=color, linewidth=1.5, capsize=3, elinewidth=0.8, capthick=0.8)
    ax.axvline(0,   color="black", linestyle="--", linewidth=1)
    ax.axhline(0,   color="gray",  linestyle=":",  linewidth=0.8)
    ax.set_xlabel("Months from Birth")
    ax.set_ylabel(ylabel)
    ax.set_title(f"{ylabel} Around Birth")
    ax.set_xlim(WINDOW_MIN, WINDOW_MAX)
    ax.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 3))
    ax.annotate(f"N = {n_authors:,} authors",
                xy=(0.02, 0.97), xycoords="axes fraction", fontsize=8, color="gray", va="top")

plt.suptitle(f"VADER Sentiment Around Birth — {LABEL} Sample", fontsize=13, fontweight="bold")
plt.tight_layout()
out_ts = OUTPUT_DIR / f"avg_sentiment_month_{LABEL}.jpg"
plt.savefig(out_ts, dpi=150)
plt.close()
print(f"Saved: {out_ts}")
