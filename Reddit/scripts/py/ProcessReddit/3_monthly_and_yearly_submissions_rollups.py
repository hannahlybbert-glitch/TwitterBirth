# Author: Hannah Lybbert
# Created: 2026-08-25
# Purpose: Two condensed views built from 2_aggregate_submissions_descriptives.py's
#          outputs (no re-reading of raw .zst or author-pair parquet needed):
#            1. monthly_avg_posts_per_author.csv — north-star metric. Per file,
#               n_rows/deleted_removed_rows/n_unique_authors are each already exact
#               for that single month, so (n_rows - deleted_removed_rows) /
#               n_unique_authors is an exact monthly average with no cross-file
#               dedup required — unlike a global or yearly average, a month-scoped
#               author count needs no unioning across files.
#            2. yearly_top5_subreddits_by_posts.csv — condensed alternative to
#               scanning top_25_subreddits_by_posts_monthly.csv's 247 rows. Reads
#               each file's *_subreddit_stats.csv (already exact per-file post
#               counts), sums by (year, subreddit), and takes the top 5 per year.
#               Monthly top-25 name lists can't be re-aggregated to yearly totals
#               because they carry no counts and drop everything past rank 25;
#               this recomputes from the exact per-file counts instead.
# Paths:   Same REDDIT_OUTPUT_DIR convention as 1_/2_.

import os
import re
from pathlib import Path

import pandas as pd

ROOT         = Path(__file__).resolve().parents[4]
OUTPUT_BASE  = Path(os.environ.get("REDDIT_OUTPUT_DIR", ROOT / "Reddit/data/ProcessReddit"))
PER_FILE_DIR = OUTPUT_BASE / "submissions_descriptives/per_file"
OUTPUT_DIR   = OUTPUT_BASE / "submissions_descriptives"

FNAME_RE = re.compile(r"RS_(\d{4})-(\d{2})")
TOP_N = 5

# ----------------------------------------------------------------
# 1. Monthly average posts per author
# ----------------------------------------------------------------
file_level = pd.read_csv(OUTPUT_DIR / "file_level_summary.csv")

file_level["month_id"] = file_level["year"].astype(str) + "-" + file_level["month"].astype(str).str.zfill(2)
file_level["n_active_posts"] = file_level["n_rows"] - file_level["deleted_removed_rows"]
file_level["avg_posts_per_author"] = (
    file_level["n_active_posts"] / file_level["n_unique_authors"]
).round(3)

monthly_avg = file_level[
    ["month_id", "year", "month", "n_active_posts", "n_unique_authors", "avg_posts_per_author"]
].sort_values(["year", "month"])

monthly_avg.to_csv(OUTPUT_DIR / "monthly_avg_posts_per_author.csv", index=False)
print(f"Saved monthly avg posts/author ({len(monthly_avg)} months) to monthly_avg_posts_per_author.csv")
print(
    f"  overall range: {monthly_avg['avg_posts_per_author'].min()} - "
    f"{monthly_avg['avg_posts_per_author'].max()}, "
    f"median {monthly_avg['avg_posts_per_author'].median()}"
)

# ----------------------------------------------------------------
# 2. Yearly top-5 subreddits by posts
# ----------------------------------------------------------------
stats_paths = sorted(PER_FILE_DIR.glob("*__subreddit_stats.csv"))

yearly_posts = {}  # year -> Counter-like dict[subreddit] -> n_posts
for p in stats_paths:
    m = FNAME_RE.search(p.name)
    if not m:
        continue
    year = m.group(1)
    df = pd.read_csv(p)
    bucket = yearly_posts.setdefault(year, {})
    for sub, n in zip(df["subreddit"], df["n_posts"]):
        bucket[sub] = bucket.get(sub, 0) + int(n)

rows = []
for year in sorted(yearly_posts):
    totals = yearly_posts[year]
    year_total_posts = sum(totals.values())
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:TOP_N]
    row = {"year": year, "year_total_posts": year_total_posts}
    for i in range(TOP_N):
        if i < len(top):
            sub, n = top[i]
            row[f"rank_{i + 1:02d}_subreddit"] = sub
            row[f"rank_{i + 1:02d}_posts"] = n
            row[f"rank_{i + 1:02d}_share_pct"] = round(100 * n / year_total_posts, 2) if year_total_posts else None
        else:
            row[f"rank_{i + 1:02d}_subreddit"] = None
            row[f"rank_{i + 1:02d}_posts"] = None
            row[f"rank_{i + 1:02d}_share_pct"] = None
    rows.append(row)

yearly_top5 = pd.DataFrame(rows).sort_values("year")
yearly_top5.to_csv(OUTPUT_DIR / "yearly_top5_subreddits_by_posts.csv", index=False)
print(f"Saved yearly top-{TOP_N} subreddits by posts ({len(yearly_top5)} years) to yearly_top5_subreddits_by_posts.csv")
