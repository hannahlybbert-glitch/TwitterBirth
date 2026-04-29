# Author: Hannah Lybbert
# Created: 2026-03-27
# Updated: 2026-04-02
# Purpose: Descriptive stats on the placebo sample (placebo_births_and_posts.csv + reddit_placebo_cleaned.csv)

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT          = Path(__file__).resolve().parents[4]
INPUT_PATH    = ROOT / "Reddit/data/intermediate/births_and_posts/placebo_births_and_posts.csv"
INPUT_CLEANED  = ROOT / "Reddit/data/intermediate/cleaned_raw/reddit_placebo_cleaned.csv"
INPUT_STACKED  = ROOT / "Reddit/data/final/treatment_control_births_posts.csv"
OUTPUT_DIR    = ROOT / "Reddit/output/descriptives"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df_cleaned = pd.read_csv(INPUT_CLEANED, low_memory=False)
df_cleaned["created_utc"] = pd.to_datetime(df_cleaned["created_utc"], unit="s")
print(f"--- reddit_placebo_cleaned.csv date range ---")
print(f"  Min created_utc: {df_cleaned['created_utc'].min()}")
print(f"  Max created_utc: {df_cleaned['created_utc'].max()}")
print()

df     = pd.read_csv(INPUT_PATH, low_memory=False)
births = df[df["birth_post"] == 1].copy()
print(f"Loaded {len(df):,} total rows | {df['author'].nunique():,} unique authors | {len(births):,} birth posts")

# ----------------------------------------------------------------
# days_from (drawn from real birth-post timing distribution)
# ----------------------------------------------------------------
days = births["days_from"].dropna()
print(f"\n--- days_from (placebo birth posts) ---")
print(f"  Mean:   {days.mean():.1f}")
print(f"  Median: {days.median():.1f}")
print(f"  Min:    {days.min():.1f}")
print(f"  Max:    {days.max():.1f}")
print(days.describe(percentiles=[.1, .25, .5, .75, .9]).round(1).to_string())

# ----------------------------------------------------------------
# days_from distribution — deciles + shape
# ----------------------------------------------------------------
deciles = days.quantile([i/10 for i in range(0, 11)])
print(f"\n--- days_from deciles ---")
for q, v in deciles.items():
    print(f"  {int(q*100):3d}th pct: {v:.1f}")
print(f"\n  Negative days_from (post before birth): {(days < 0).sum():,} ({(days < 0).mean()*100:.1f}%)")
print(f"  Zero days_from (same day):              {(days == 0).sum():,} ({(days == 0).mean()*100:.1f}%)")
print(f"  Positive days_from (post after birth):  {(days > 0).sum():,} ({(days > 0).mean()*100:.1f}%)")

# ----------------------------------------------------------------
# Sample coverage: author-level
# ----------------------------------------------------------------
author_stats = df.groupby("author").agg(
    total_posts      = ("id", "count"),
    pre_birth_posts  = ("post", lambda x: (x == 0).sum()),
    post_birth_posts = ("post", lambda x: (x == 1).sum()),
    weeks_in_sample  = ("weeks_from_birth", lambda x: x.max() - x.min()),
).reset_index()

print(f"\n--- Author-level coverage ---")
print(f"  Avg posts per author:            {author_stats['total_posts'].mean():.1f}")
print(f"  Avg pre-birth posts per author:  {author_stats['pre_birth_posts'].mean():.1f}")
print(f"  Avg post-birth posts per author: {author_stats['post_birth_posts'].mean():.1f}")
print(f"  Avg weeks in sample per author:  {author_stats['weeks_in_sample'].mean():.1f}")

# ----------------------------------------------------------------
# Sample restriction flags
# ----------------------------------------------------------------
print(f"\n--- Sample restriction flags ---")
one_year  = df.groupby("author")["one_year_pre"].first()
full_18   = df.groupby("author")["full_18_pre"].first()
full_post = df.groupby("author")["full_18_post"].first()
print(f"  Authors with >= 12 months pre-birth  (one_year_pre): {one_year.sum():,} ({one_year.mean()*100:.1f}%)")
print(f"  Authors with >= 18 months pre-birth  (full_18_pre):  {full_18.sum():,} ({full_18.mean()*100:.1f}%)")
print(f"  Authors with >= 18 months post-birth (full_18_post): {full_post.sum():,} ({full_post.mean()*100:.1f}%)")

# ----------------------------------------------------------------
# Top subreddits (all posts)
# ----------------------------------------------------------------
# print(f"\n--- Subreddits with > 50 posts ---")
# sub_counts = df["subreddit"].value_counts()
# print(sub_counts[sub_counts > 50].to_string())

# ----------------------------------------------------------------
# Histograms (2x2)
# ----------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# days_from (placebo birth posts)
axes[0, 0].hist(days, bins=40, edgecolor="white", color="steelblue")
axes[0, 0].axvline(0, color="black", linestyle="--", linewidth=1)
axes[0, 0].set_title("Days from Birth to Birth Post — drawn from real distribution\n(placebo birth posts only)")
axes[0, 0].set_xlabel("days_from")
axes[0, 0].set_ylabel("Number of Authors")

# weeks_from_birth distribution (all posts)
axes[0, 1].hist(df["weeks_from_birth"].dropna(), bins=60, edgecolor="white", color="steelblue")
axes[0, 1].axvline(0, color="black", linestyle="--", linewidth=1)
axes[0, 1].set_title("Weeks from Placebo Birth (all posts)")
axes[0, 1].set_xlabel("Weeks from Birth")
axes[0, 1].set_ylabel("Number of Posts")

# posts per author
axes[1, 0].hist(
    author_stats["total_posts"].clip(upper=author_stats["total_posts"].quantile(0.95)),
    bins=40, edgecolor="white", color="steelblue"
)
axes[1, 0].set_title("Posts per Author — clipped at 95th pct")
axes[1, 0].set_xlabel("Total Posts")
axes[1, 0].set_ylabel("Number of Authors")

# pre vs post posts per author
axes[1, 1].hist(
    author_stats["pre_birth_posts"].clip(upper=author_stats["pre_birth_posts"].quantile(0.95)),
    bins=40, edgecolor="white", color="steelblue", alpha=0.6, label="Pre-birth"
)
axes[1, 1].hist(
    author_stats["post_birth_posts"].clip(upper=author_stats["post_birth_posts"].quantile(0.95)),
    bins=40, edgecolor="white", color="coral", alpha=0.6, label="Post-birth"
)
axes[1, 1].set_title("Pre vs Post-birth Posts per Author — clipped at 95th pct")
axes[1, 1].set_xlabel("Number of Posts")
axes[1, 1].set_ylabel("Number of Authors")
axes[1, 1].legend()

plt.suptitle("Placebo Sample — Descriptives", fontsize=14, fontweight="bold")
plt.tight_layout()
out_path = OUTPUT_DIR / "descriptives_placebo.jpg"
plt.savefig(out_path, dpi=150)
plt.close()
print(f"\nHistogram saved to {out_path}")

# ----------------------------------------------------------------
# Sample coverage
# ----------------------------------------------------------------
author_coverage = df.groupby("author")["months_from_birth"].agg(
    start_month="min",
    end_month="max"
).reset_index()

authors_15mo_pre  = (author_coverage["start_month"] <= -15).sum()
authors_18mo_pre  = (author_coverage["start_month"] <= -18).sum()
authors_18mo_post = (author_coverage["end_month"]   >= 18).sum()

print(f"\n--- Sample coverage (months_from_birth) ---")
print(f"  Avg start month:                  {author_coverage['start_month'].mean():.1f}")
print(f"  Avg end month:                    {author_coverage['end_month'].mean():.1f}")
print(f"  Authors with >= 15 months pre:    {authors_15mo_pre:,}")
print(f"  Authors with >= 18 months pre:    {authors_18mo_pre:,}")
print(f"  Authors with >= 18 months post:   {authors_18mo_post:,}")

fig, axes = plt.subplots(1, 2, figsize=(12, 5))

axes[0].hist(author_coverage["start_month"], bins=30, edgecolor="white", color="steelblue")
axes[0].axvline(0, color="black", linestyle="--", linewidth=1)
axes[0].set_title("Distribution of Author Start Month\n(min months_from_birth per author)")
axes[0].set_xlabel("Months from Placebo Birth")
axes[0].set_ylabel("Number of Authors")

axes[1].hist(author_coverage["end_month"], bins=30, edgecolor="white", color="steelblue")
axes[1].axvline(0, color="black", linestyle="--", linewidth=1)
axes[1].set_title("Distribution of Author End Month\n(max months_from_birth per author)")
axes[1].set_xlabel("Months from Placebo Birth")
axes[1].set_ylabel("Number of Authors")

plt.tight_layout()
out_path_coverage = OUTPUT_DIR / "sample_coverage_placebo.jpg"
plt.savefig(out_path_coverage, dpi=150)
plt.close()
print(f"Sample coverage figure saved to {out_path_coverage}")

# ----------------------------------------------------------------
# Distribution of assigned placebo birth dates
# ----------------------------------------------------------------
birth_dates = births["date_birth"].dropna()
birth_dates = pd.to_datetime(birth_dates)

fig, ax = plt.subplots(figsize=(12, 5))
ax.hist(birth_dates, bins=60, edgecolor="white", color="steelblue")
ax.set_title("Distribution of Assigned Placebo Birth Dates")
ax.set_xlabel("Placebo Date of Birth")
ax.set_ylabel("Number of Authors")
fig.autofmt_xdate()

plt.tight_layout()
out_path_births = OUTPUT_DIR / "date_birth_dist_placebo.jpg"
plt.savefig(out_path_births, dpi=150)
plt.close()
print(f"Birth date distribution saved to {out_path_births}")

# ----------------------------------------------------------------
# days_from comparison: treatment vs control, full_18_pre sample (sanity check)
# ----------------------------------------------------------------
stacked = pd.read_csv(INPUT_STACKED)
stacked_births = stacked[(stacked["birth_post"] == 1) & (stacked["full_18_pre"] == 1)].copy()

print(f"\n--- days_from comparison: treatment vs control (birth posts, full_18_pre == 1) ---")
for treated, label in [(1, "Treatment"), (0, "Control")]:
    days = stacked_births.loc[stacked_births["treated"] == treated, "days_from"].dropna()
    print(f"\n  {label} (n={len(days):,})")
    print(f"    Mean:   {days.mean():.2f}")
    print(f"    Median: {days.median():.2f}")
    print(f"    Min:    {days.min():.1f}")
    print(f"    Max:    {days.max():.1f}")
    print(days.describe(percentiles=[.1, .25, .5, .75, .9]).round(2).to_string())
