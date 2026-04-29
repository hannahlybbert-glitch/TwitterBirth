# Author: Hannah Lybbert
# Created: 2026-04-09
# Updated: 2026-04-09
# Purpose: Descriptive figures for the full sample births_and_posts_FULL.csv (birth posts only)

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[4]
INPUT_PATH = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"
OUTPUT_DIR = ROOT / "Reddit/output/descriptives"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------
# Load and filter to birth posts
# ----------------------------------------------------------------
df     = pd.read_csv(INPUT_PATH)
births = df[df["birth_post"] == 1].copy()
print(f"Loaded {len(df):,} total rows | {df['author'].nunique():,} unique authors | {len(births):,} birth posts")

# ----------------------------------------------------------------
# Pre-compute data shared across individual figures and panel
# ----------------------------------------------------------------
n_female  = (births["female"] == 1).sum()
n_male    = (births["female"] == 0).sum()
n_unknown = (births["female"] == -99).sum()
n_total   = len(births)

birth_dates = pd.to_datetime(births["date_birth"].dropna())

days_raw = births["days_from"].dropna()
n_999    = (days_raw == -999).sum()
days     = days_raw[days_raw != -999]

posts_per_author = df.groupby("author").size()
cap_95           = posts_per_author.quantile(0.95)
posts_clipped    = posts_per_author[posts_per_author <= cap_95]

# ----------------------------------------------------------------
# Figure 1: Gender shares bar chart
# ----------------------------------------------------------------
labels = ["Female\n(p_female > 50)", "Male\n(p_male > 50)", "Unknown\n(p_female = 50)"]
counts = [n_female, n_male, n_unknown]
colors = ["mediumpurple", "steelblue", "lightgray"]

fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(labels, counts, color=colors, edgecolor="white", width=0.5)
for bar, count in zip(bars, counts):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + n_total * 0.005,
            f"{count:,}\n({count / n_total * 100:.1f}%)",
            ha="center", va="bottom", fontsize=10)
ax.set_title("Gender Shares — Full Sample (Birth Posts)")
ax.set_ylabel("Number of Authors")
ax.set_ylim(0, max(counts) * 1.2)
plt.tight_layout()
out_gender = OUTPUT_DIR / "gender_shares_full.jpg"
plt.savefig(out_gender, dpi=150)
plt.close()
print(f"Saved: {out_gender}")

# ----------------------------------------------------------------
# Figure 2: date_birth distribution
# ----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 5))
ax.hist(birth_dates, bins=48, edgecolor="white", color="steelblue")
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_title("Distribution of Birth Dates — Full Sample")
ax.set_xlabel("Year of Birth")
ax.set_ylabel("Number of Authors")
fig.autofmt_xdate()
plt.tight_layout()
out_date = OUTPUT_DIR / "date_birth_dist_full.jpg"
plt.savefig(out_date, dpi=150)
plt.close()
print(f"Saved: {out_date}")

# ----------------------------------------------------------------
# Figure 3: days_from distribution
# (days between birth post and actual birth date)
# ----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(days, bins=57, edgecolor="white", color="steelblue")
ax.axvline(0, color="black", linestyle="--", linewidth=1, label="Birth date (day 0)")
ax.set_title("Days from Birth to Birth Post — Full Sample")
ax.set_xlabel("Days (negative = post before birth, positive = post after birth)")
ax.set_ylabel("Number of Authors")
ax.legend(fontsize=9)
if n_999 > 0:
    ax.text(0.98, 0.95, f"Excluded {n_999:,} with days_from = -999",
            transform=ax.transAxes, ha="right", va="top", fontsize=8, color="gray")
plt.tight_layout()
out_days = OUTPUT_DIR / "days_from_dist_full.jpg"
plt.savefig(out_days, dpi=150)
plt.close()
print(f"Saved: {out_days}")

# ----------------------------------------------------------------
# Figure 4: Subreddit breakdown (horizontal bar chart, top 8)
# ----------------------------------------------------------------
TOP_N      = 8
sub_counts = births["subreddit"].value_counts().head(TOP_N).sort_values()

fig, ax = plt.subplots(figsize=(8, 10))
ax.barh(sub_counts.index, sub_counts.values, color="steelblue", edgecolor="white")
for i, (val, name) in enumerate(zip(sub_counts.values, sub_counts.index)):
    ax.text(val + sub_counts.values.max() * 0.005, i,
            f"{val:,}", va="center", fontsize=8)
ax.set_title(f"Top {TOP_N} Subreddits — Full Sample (Birth Posts)")
ax.set_xlabel("Number of Birth Posts")
ax.set_xlim(0, sub_counts.values.max() * 1.15)
plt.tight_layout()
out_sub = OUTPUT_DIR / "subreddits_birth_full.jpg"
plt.savefig(out_sub, dpi=150)
plt.close()
print(f"Saved: {out_sub}")

# ----------------------------------------------------------------
# Figure 5: Post date distribution (all posts)
# ----------------------------------------------------------------
post_dates = pd.to_datetime(df["created_utc"])

fig, ax = plt.subplots(figsize=(12, 5))
ax.hist(post_dates, bins=72, edgecolor="white", color="steelblue")
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_title("Distribution of Post Dates — Full Sample (All Posts)")
ax.set_xlabel("Year")
ax.set_ylabel("Number of Posts")
fig.autofmt_xdate()
plt.tight_layout()
out_posts = OUTPUT_DIR / "post_date_dist_full.jpg"
plt.savefig(out_posts, dpi=150)
plt.close()
print(f"Saved: {out_posts}")

# ----------------------------------------------------------------
# Figure 6: Posts per author (clipped at 95th percentile)
# ----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5))
ax.hist(posts_clipped, bins=50, edgecolor="white", color="steelblue")
ax.set_title("Posts per Author — Full Sample (Clipped at 95th Percentile)")
ax.set_xlabel("Number of Posts")
ax.set_ylabel("Number of Authors")
ax.text(0.98, 0.95,
        f"95th pct cap: {cap_95:.0f} posts\n({(posts_per_author > cap_95).sum():,} authors excluded)",
        transform=ax.transAxes, ha="right", va="top", fontsize=8, color="gray")
plt.tight_layout()
out_ppa = OUTPUT_DIR / "posts_per_author_full.jpg"
plt.savefig(out_ppa, dpi=150)
plt.close()
print(f"Saved: {out_ppa}")

# ----------------------------------------------------------------
# Panel: date_birth_dist | days_from_dist | gender_shares | posts_per_author
# ----------------------------------------------------------------
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# [0, 0] Birth date distribution
ax = axes[0, 0]
ax.hist(birth_dates, bins=48, edgecolor="white", color="steelblue")
ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
ax.set_title("Distribution of Birth Dates")
ax.set_xlabel("Year of Birth")
ax.set_ylabel("Number of Authors")
fig.autofmt_xdate()

# [0, 1] Days from birth to birth post
ax = axes[0, 1]
ax.hist(days, bins=57, edgecolor="white", color="steelblue")
ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_title("Days from Birth to Birth Post")
ax.set_xlabel("Days")
ax.set_ylabel("Number of Authors")
if n_999 > 0:
    ax.text(0.98, 0.95, f"Excluded {n_999:,} with days_from = -999",
            transform=ax.transAxes, ha="right", va="top", fontsize=7, color="gray")

# [1, 0] Gender shares
ax = axes[1, 0]
bars = ax.bar(labels, counts, color=colors, edgecolor="white", width=0.5)
for bar, count in zip(bars, counts):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + n_total * 0.005,
            f"{count:,}\n({count / n_total * 100:.1f}%)",
            ha="center", va="bottom", fontsize=9)
ax.set_title("Gender Shares (Birth Posts)")
ax.set_ylabel("Number of Authors")
ax.set_ylim(0, max(counts) * 1.25)

# [1, 1] Posts per author
ax = axes[1, 1]
ax.hist(posts_clipped, bins=50, edgecolor="white", color="steelblue")
ax.set_title("Posts per Author (Clipped at 95th Percentile)")
ax.set_xlabel("Number of Posts")
ax.set_ylabel("Number of Authors")
ax.text(0.98, 0.95,
        f"95th pct cap: {cap_95:.0f} posts\n({(posts_per_author > cap_95).sum():,} authors excluded)",
        transform=ax.transAxes, ha="right", va="top", fontsize=7, color="gray")

plt.suptitle("Full Sample Descriptives", fontsize=14, fontweight="bold")
plt.tight_layout()
out_panel = OUTPUT_DIR / "sample_panel_full.jpg"
plt.savefig(out_panel, dpi=150)
plt.close()
print(f"Saved: {out_panel}")
