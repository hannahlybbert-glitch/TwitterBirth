# Author: Hannah Lybbert
# Created: 2026-03-25
# Updated: 2026-04-10
# Purpose: Plot average posts per month relative to birth for treatment vs control (placebo)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[5]
INPUT_PATH = ROOT / "Reddit/data/final/treatment_control_births_posts.csv"
OUTPUT_DIR = ROOT / "Reddit/output/analysis/volume/placebo"

WINDOW_MIN = -18
WINDOW_MAX =  18

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH)
print(f"Loaded {len(df):,} rows | {df['author'].nunique():,} unique authors")

# ----------------------------------------------------------------
# full_18_pre & posted_after_birth sample
# ----------------------------------------------------------------
df3 = df[df["full_18_pre"] == 1].copy()
df3 = df3[(df3["months_from_birth"] >= WINDOW_MIN) & (df3["months_from_birth"] <= WINDOW_MAX)]

n_treat   = df3[df3["treated"] == 1]["author"].nunique()
n_control = df3[df3["treated"] == 0]["author"].nunique()
print(f"\nfull_18_pre sample — treated: {n_treat:,}  control: {n_control:,}")

fig, ax = plt.subplots(figsize=(10, 5))
for treated, color, label, n in [(1, "steelblue", "Treatment", n_treat),
                                  (0, "coral",     "Control",   n_control)]:
    ppm = (
        df3[df3["treated"] == treated]
        .groupby("months_from_birth")["id"]
        .count()
        .div(n)
        .reset_index()
        .rename(columns={"id": "avg_posts"})
    )
    ax.plot(ppm["months_from_birth"], ppm["avg_posts"],
            color=color, linewidth=1.5, label=f"{label} (n={n:,})")

ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Months from Birth")
ax.set_ylabel("Avg Posts per Month")
ax.set_title("Average Reddit Posting Volume Around Birth — Treatment vs Control\n(≥18 months pre-birth, posted after birth)")
ax.set_xlim(WINDOW_MIN, WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 2))
ax.legend(loc="upper right")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "avg_posts_month_placebo.jpg", dpi=150)
plt.close()
print(f"Saved to {OUTPUT_DIR / 'avg_posts_month_placebo.jpg'}")

# ----------------------------------------------------------------
# Log(+1) volume figure — treatment vs control
# ----------------------------------------------------------------
def compute_l_stats(df_subset, authors, month_min, month_max):
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
    full["l_posts"] = np.log(full["posts"] + 1)
    stats = full.groupby("months_from_birth")["l_posts"].agg(["mean", "std", "count"]).reset_index()
    stats["se"]       = stats["std"] / np.sqrt(stats["count"])
    stats["ci_lower"] = stats["mean"] - 1.96 * stats["se"]
    stats["ci_upper"] = stats["mean"] + 1.96 * stats["se"]
    return stats

fig, ax = plt.subplots(figsize=(10, 5))
for treated, color, label, n in [(1, "steelblue", "Treatment", n_treat),
                                  (0, "coral",     "Control",   n_control)]:
    grp    = df3[df3["treated"] == treated]
    stats  = compute_l_stats(grp, grp["author"].unique(), WINDOW_MIN, WINDOW_MAX)
    ax.plot(stats["months_from_birth"], stats["mean"],
            color=color, linewidth=1.5, label=f"{label} (n={n:,})")

ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Months from Birth")
ax.set_ylabel("Log(Avg Posts per Month + 1)")
ax.set_title("Log Average Reddit Posting Volume Around Birth — Treatment vs Control\n(≥18 months pre-birth)")
ax.set_xlim(WINDOW_MIN, WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 2))
ax.legend(loc="upper right")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "l_avg_posts_month_placebo.jpg", dpi=150)
plt.close()
print(f"Saved to {OUTPUT_DIR / 'l_avg_posts_month_placebo.jpg'}")

# ----------------------------------------------------------------
# one_year_pre sample
# ----------------------------------------------------------------
WINDOW_MIN_1YR = -12

df1 = df[df["one_year_pre"] == 1].copy()
df1 = df1[(df1["months_from_birth"] >= WINDOW_MIN_1YR) & (df1["months_from_birth"] <= WINDOW_MAX)]

n_treat_1yr   = df1[df1["treated"] == 1]["author"].nunique()
n_control_1yr = df1[df1["treated"] == 0]["author"].nunique()
print(f"\none_year_pre sample — treated: {n_treat_1yr:,}  control: {n_control_1yr:,}")

fig, ax = plt.subplots(figsize=(10, 5))
for treated, color, label, n in [(1, "steelblue", "Treatment", n_treat_1yr),
                                  (0, "coral",     "Control",   n_control_1yr)]:
    ppm = (
        df1[df1["treated"] == treated]
        .groupby("months_from_birth")["id"]
        .count()
        .div(n)
        .reset_index()
        .rename(columns={"id": "avg_posts"})
    )
    ax.plot(ppm["months_from_birth"], ppm["avg_posts"],
            color=color, linewidth=1.5, label=f"{label} (n={n:,})")

ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Months from Birth")
ax.set_ylabel("Avg Posts per Month")
ax.set_title("Average Reddit Posting Volume Around Birth — Treatment vs Control\n(≥12 months pre-birth, posted after birth)")
ax.set_xlim(WINDOW_MIN_1YR, WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN_1YR, WINDOW_MAX + 1, 2))
ax.legend(loc="upper right")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "avg_posts_month_placebo_1yr_pre.jpg", dpi=150)
plt.close()
print(f"Saved to {OUTPUT_DIR / 'avg_posts_month_placebo_1yr_pre.jpg'}")
