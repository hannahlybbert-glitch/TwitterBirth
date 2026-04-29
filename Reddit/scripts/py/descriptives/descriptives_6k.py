# Author: Hannah Lybbert
# Created: 2026-03-25
# Updated: 2026-03-25
# Purpose: Descriptive stats on the 6k author analysis-ready file (births_and_posts_22k.csv)

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[4]
INPUT_PATH = ROOT / "Reddit/data/final/births_and_posts_22k.csv"
OUTPUT_DIR = ROOT / "Reddit/output/descriptives"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df     = pd.read_csv(INPUT_PATH)
births = df[df["birth_post"] == 1].copy()
print(f"Loaded {len(df):,} total rows | {df['author'].nunique():,} unique authors | {len(births):,} birth posts")

# ----------------------------------------------------------------
# Birth post quality: days_from (days between actual birth and birth post)
# ----------------------------------------------------------------
n_999 = (births["days_from"] == -999).sum()
days  = births.loc[births["days_from"] != -999, "days_from"]
print(f"\n--- days_from (birth posts, excluding -999) ---")
print(f"  Count -999 (timing unknown): {n_999:,}")
print(f"  Mean:   {days.mean():.1f}")
print(f"  Median: {days.median():.1f}")
print(f"  Min:    {days.min():.1f}")
print(f"  Max:    {days.max():.1f}")
print(days.describe(percentiles=[.1, .25, .5, .75, .9]).round(1).to_string())

# ----------------------------------------------------------------
# Birth post quality: confidence
# ----------------------------------------------------------------
print(f"\n--- confidence (birth posts only) ---")
print(births["confidence"].describe(percentiles=[.1, .25, .5, .75, .9]).round(3).to_string())

# ----------------------------------------------------------------
# Gender breakdown
# ----------------------------------------------------------------
print(f"\n--- Gender breakdown (birth posts only) ---")
print(f"  Mean p_female: {births['p_female'].mean():.3f}")
print(f"  Mean p_male:   {births['p_male'].mean():.3f}")
print(f"  Likely female (p_female > 50): {(births['p_female'] > 50).sum():,} ({(births['p_female'] > 50).mean()*100:.1f}%)")
print(f"  Likely male   (p_male   > 50): {(births['p_male']   > 50).sum():,} ({(births['p_male']   > 50).mean()*100:.1f}%)")

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
# Sample restriction thresholds
# ----------------------------------------------------------------
print(f"\n--- Sample restriction flags ---")
one_year  = df.groupby("author")["one_year_pre"].first()
full_18 = df.groupby("author")["full_18_pre"].first()
print(f"  Authors with >= 12 months pre-birth (one_year_pre): {one_year.sum():,} ({one_year.mean()*100:.1f}%)")
print(f"  Authors with >= 18 months pre-birth (full_18_pre):  {full_18.sum():,} ({full_18.mean()*100:.1f}%)")

# ----------------------------------------------------------------
# Data completeness: birth posts matched vs appended
# ----------------------------------------------------------------
matched   = births["score"].notna().sum()
unmatched = births["score"].isna().sum()
print(f"\n--- Birth post data completeness ---")
print(f"  Birth posts matched in post history (have score/url): {matched:,} ({matched/len(births)*100:.1f}%)")
print(f"  Birth posts appended (no post history match):         {unmatched:,} ({unmatched/len(births)*100:.1f}%)")

# ----------------------------------------------------------------
# Top subreddits (all posts)
# ----------------------------------------------------------------
print(f"\n--- Top 10 subreddits (all posts) ---")
print(df["subreddit"].value_counts().head(10).to_string())

# ----------------------------------------------------------------
# Histograms
# ----------------------------------------------------------------
fig, axes = plt.subplots(3, 2, figsize=(14, 15))

# days_from (birth posts)
axes[0, 0].hist(days.dropna(), bins=40, edgecolor="white", color="steelblue")
axes[0, 0].axvline(0, color="black", linestyle="--", linewidth=1)
axes[0, 0].set_title("Days from Birth to Birth Post (birth posts only)")
axes[0, 0].set_xlabel("days_from")
axes[0, 0].set_ylabel("Number of Posts")

# confidence
axes[0, 1].hist(births["confidence"].dropna(), bins=30, edgecolor="white", color="steelblue")
axes[0, 1].set_title("Model Confidence (birth posts only)")
axes[0, 1].set_xlabel("Confidence")
axes[0, 1].set_ylabel("Number of Posts")

# p_female by gender assignment
pf_f = births.loc[births["female"] == 1,  "p_female"]
pf_m = births.loc[births["female"] == 0,  "p_female"]
pf_a = births.loc[births["female"] == -99, "p_female"]
bins_gender = range(0, 105, 5)
axes[1, 0].hist(pf_f.dropna(), bins=bins_gender, color="mediumpurple", edgecolor="white", alpha=0.85, label=f"Female (n={len(pf_f):,})")
axes[1, 0].hist(pf_m.dropna(), bins=bins_gender, color="steelblue",    edgecolor="white", alpha=0.85, label=f"Male (n={len(pf_m):,})")
axes[1, 0].hist(pf_a.dropna(), bins=bins_gender, color="lightgray",    edgecolor="white", alpha=0.85, label=f"Ambiguous (n={len(pf_a):,})")
axes[1, 0].axvline(50, color="black", linestyle="--", linewidth=1)
axes[1, 0].set_title("P(Female) by Gender Assignment (birth posts only)")
axes[1, 0].set_xlabel("p_female (0–100 scale)")
axes[1, 0].set_ylabel("Number of Authors")
axes[1, 0].legend(fontsize=8)

# weeks_from_birth distribution (all posts)
axes[1, 1].hist(df["weeks_from_birth"].dropna(), bins=60, edgecolor="white", color="steelblue")
axes[1, 1].axvline(0, color="black", linestyle="--", linewidth=1)
axes[1, 1].set_title("Weeks from Birth (all posts)")
axes[1, 1].set_xlabel("Weeks from Birth")
axes[1, 1].set_ylabel("Number of Posts")

# posts per author
axes[2, 0].hist(author_stats["total_posts"].clip(upper=author_stats["total_posts"].quantile(0.95)),
                bins=40, edgecolor="white", color="steelblue")
axes[2, 0].set_title("Posts per Author — clipped at 95th pct")
axes[2, 0].set_xlabel("Total Posts")
axes[2, 0].set_ylabel("Number of Authors")

# pre vs post posts per author
axes[2, 1].hist(author_stats["pre_birth_posts"].clip(upper=author_stats["pre_birth_posts"].quantile(0.95)),
                bins=40, edgecolor="white", color="steelblue", alpha=0.6, label="Pre-birth")
axes[2, 1].hist(author_stats["post_birth_posts"].clip(upper=author_stats["post_birth_posts"].quantile(0.95)),
                bins=40, edgecolor="white", color="coral", alpha=0.6, label="Post-birth")
axes[2, 1].set_title("Pre vs Post-birth Posts per Author — clipped at 95th pct")
axes[2, 1].set_xlabel("Number of Posts")
axes[2, 1].set_ylabel("Number of Authors")
axes[2, 1].legend()

plt.suptitle("6k Sample — Descriptives", fontsize=14, fontweight="bold")
plt.tight_layout()
out_path = OUTPUT_DIR / "descriptives_6k.jpg"
plt.savefig(out_path, dpi=150)
plt.close()
print(f"\nHistogram saved to {out_path}")

# ----------------------------------------------------------------
# Gender figure
# ----------------------------------------------------------------
author_gender = df.groupby("author").agg(
    female  = ("female", "first"),
    p_female = ("p_female", "first"),
).reset_index()

n_female = (author_gender["female"] == 1).sum()
n_male   = (author_gender["female"] == 0).sum()
n_ambig  = (author_gender["female"] == -99).sum()
n_total  = len(author_gender)

fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Left: gender breakdown bar chart
labels = ["Female\n(p_female > 50)", "Male\n(p_male > 50)", "Ambiguous\n(p_female = 50)"]
counts = [n_female, n_male, n_ambig]
colors = ["mediumpurple", "steelblue", "lightgray"]
bars = axes[0].bar(labels, counts, color=colors, edgecolor="white", width=0.5)
for bar, count in zip(bars, counts):
    axes[0].text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 20,
                 f"{count:,}\n({count/n_total*100:.1f}%)",
                 ha="center", va="bottom", fontsize=10)
axes[0].set_title("Gender Breakdown (author-level)")
axes[0].set_ylabel("Number of Authors")
axes[0].set_ylim(0, max(counts) * 1.2)

# Right: p_female histogram colored by assignment — shows share + confidence
pf_female = author_gender.loc[author_gender["female"] == 1,  "p_female"]
pf_male   = author_gender.loc[author_gender["female"] == 0,  "p_female"]
pf_ambig  = author_gender.loc[author_gender["female"] == -99, "p_female"]
axes[1].hist(pf_female.dropna(), bins=bins_gender, color="mediumpurple", edgecolor="white", alpha=0.85, label=f"Female (n={n_female:,})")
axes[1].hist(pf_male.dropna(),   bins=bins_gender, color="steelblue",    edgecolor="white", alpha=0.85, label=f"Male (n={n_male:,})")
axes[1].hist(pf_ambig.dropna(),  bins=bins_gender, color="lightgray",    edgecolor="white", alpha=0.85, label=f"Ambiguous (n={n_ambig:,})")
axes[1].axvline(50, color="black", linestyle="--", linewidth=1)
axes[1].set_title("Distribution of P(Female) by Gender Assignment")
axes[1].set_xlabel("p_female (0–100 scale)")
axes[1].set_ylabel("Number of Authors")
axes[1].legend()

plt.suptitle("6k Sample — Gender", fontsize=14, fontweight="bold")
plt.tight_layout()
out_path_gender = OUTPUT_DIR / "gender_6k.jpg"
plt.savefig(out_path_gender, dpi=150)
plt.close()
print(f"Gender figure saved to {out_path_gender}")

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
axes[0].set_xlabel("Months from Birth")
axes[0].set_ylabel("Number of Authors")

axes[1].hist(author_coverage["end_month"], bins=30, edgecolor="white", color="steelblue")
axes[1].axvline(0, color="black", linestyle="--", linewidth=1)
axes[1].set_title("Distribution of Author End Month\n(max months_from_birth per author)")
axes[1].set_xlabel("Months from Birth")
axes[1].set_ylabel("Number of Authors")

plt.tight_layout()
out_path_coverage = OUTPUT_DIR / "sample_coverage_6k.jpg"
plt.savefig(out_path_coverage, dpi=150)
plt.close()
print(f"Sample coverage figure saved to {out_path_coverage}")

# ----------------------------------------------------------------
# Distribution of date_birth
# ----------------------------------------------------------------
birth_dates = df[df["birth_post"] == 1]["date_birth"].dropna()
birth_dates = pd.to_datetime(birth_dates)

fig, ax = plt.subplots(figsize=(12, 5))
ax.hist(birth_dates, bins=60, edgecolor="white", color="steelblue")
ax.set_title("Distribution of Birth Dates")
ax.set_xlabel("Date of Birth")
ax.set_ylabel("Number of Authors")
fig.autofmt_xdate()

plt.tight_layout()
out_path_births = OUTPUT_DIR / "date_birth_dist_6k.jpg"
plt.savefig(out_path_births, dpi=150)
plt.close()
print(f"Birth date distribution saved to {out_path_births}")
