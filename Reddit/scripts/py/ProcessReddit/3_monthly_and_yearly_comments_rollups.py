# Author: Hannah Lybbert
# Created: 2026-08-26
# Purpose: Three condensed views built mostly from 2_aggregate_comments_descriptives.py's
#          outputs, answering the three questions this pipeline exists for:
#            1. monthly_avg_comments_per_author.csv — Q1/Q2 (unique commenters per month,
#               avg comments per commenter per month). Per file, n_rows/deleted_removed_rows/
#               n_unique_authors are each already exact for that single month, so
#               (n_rows - deleted_removed_rows) / n_unique_authors is an exact monthly
#               average with no cross-file dedup required — unlike a global or yearly
#               average, a month-scoped author count needs no unioning across files.
#               Re-reads only file_level_summary.csv (no raw .zst or parquet).
#            2. yearly_top5_subreddits_by_comments.csv — Q3 (total-comments half). Reads
#               each file's *_subreddit_stats.csv (already exact per-file comment counts),
#               sums by (year, subreddit), and takes the top 5 per year.
#            3. yearly_top5_subreddits_by_authors.csv — Q3 (unique-authors half). Unlike
#               comment totals, author counts don't sum cleanly across a year's 12 files
#               (the same author commenting in a subreddit across several months of the
#               same year must count once) — this needs real cross-file dedup. Re-runs the
#               candidate-shortlist trick from 2_ (see its comments for why an exact
#               all-subreddit union isn't memory-safe), scoped to one year's ~12 files at a
#               time instead of the full ~18-year history, using each year's own per-file
#               *_subreddit_authors.parquet pairs.
# Paths:   Same REDDIT_OUTPUT_DIR convention as 1_/2_.

import os
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT         = Path(__file__).resolve().parents[4]
OUTPUT_BASE  = Path(os.environ.get("REDDIT_OUTPUT_DIR", ROOT / "Reddit/data/ProcessReddit"))
PER_FILE_DIR = OUTPUT_BASE / "comments_descriptives/per_file"
OUTPUT_DIR   = OUTPUT_BASE / "comments_descriptives"

FNAME_RE = re.compile(r"RC_(\d{4})-(\d{2})")
TOP_N = 5
CANDIDATE_POOL_SIZE = max(TOP_N * 20, 500)  # same generous heuristic as 2_'s all-time version, scoped per year here

# ----------------------------------------------------------------
# 1. Monthly average comments per author (Q1 / Q2)
# ----------------------------------------------------------------
file_level = pd.read_csv(OUTPUT_DIR / "file_level_summary.csv")

file_level["month_id"] = file_level["year"].astype(str) + "-" + file_level["month"].astype(str).str.zfill(2)
file_level["n_active_comments"] = file_level["n_rows"] - file_level["deleted_removed_rows"]
file_level["avg_comments_per_author"] = (
    file_level["n_active_comments"] / file_level["n_unique_authors"]
).round(3)

monthly_avg = file_level[
    ["month_id", "year", "month", "n_active_comments", "n_unique_authors", "avg_comments_per_author"]
].sort_values(["year", "month"])

monthly_avg.to_csv(OUTPUT_DIR / "monthly_avg_comments_per_author.csv", index=False)
print(f"Saved monthly avg comments/author ({len(monthly_avg)} months) to monthly_avg_comments_per_author.csv")
print(
    f"  overall range: {monthly_avg['avg_comments_per_author'].min()} - "
    f"{monthly_avg['avg_comments_per_author'].max()}, "
    f"median {monthly_avg['avg_comments_per_author'].median()}"
)
print(
    f"  unique commenters per month — mean {monthly_avg['n_unique_authors'].mean():,.0f}, "
    f"median {monthly_avg['n_unique_authors'].median():,.0f}"
)

# ----------------------------------------------------------------
# 2. Yearly top-5 subreddits by total comments (Q3, comment-volume half)
# ----------------------------------------------------------------
stats_paths = sorted(PER_FILE_DIR.glob("*__subreddit_stats.csv"))

# Group each month's file path by year up front — reused below for the
# unique-authors pass too, so the filename regex only runs once per file.
paths_by_year = defaultdict(list)
for p in stats_paths:
    m = FNAME_RE.search(p.name)
    if m:
        paths_by_year[m.group(1)].append(p)

yearly_comments = {}  # year -> dict[subreddit] -> n_comments
for year, paths in paths_by_year.items():
    bucket = yearly_comments.setdefault(year, {})
    for p in paths:
        df = pd.read_csv(p)
        for sub, n in zip(df["subreddit"], df["n_comments"]):
            bucket[sub] = bucket.get(sub, 0) + int(n)

rows = []
for year in sorted(yearly_comments):
    totals = yearly_comments[year]
    year_total_comments = sum(totals.values())
    top = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:TOP_N]
    row = {"year": year, "year_total_comments": year_total_comments}
    for i in range(TOP_N):
        if i < len(top):
            sub, n = top[i]
            row[f"rank_{i + 1:02d}_subreddit"] = sub
            row[f"rank_{i + 1:02d}_comments"] = n
            row[f"rank_{i + 1:02d}_share_pct"] = round(100 * n / year_total_comments, 2) if year_total_comments else None
        else:
            row[f"rank_{i + 1:02d}_subreddit"] = None
            row[f"rank_{i + 1:02d}_comments"] = None
            row[f"rank_{i + 1:02d}_share_pct"] = None
    rows.append(row)

yearly_top5_comments = pd.DataFrame(rows).sort_values("year")
yearly_top5_comments.to_csv(OUTPUT_DIR / "yearly_top5_subreddits_by_comments.csv", index=False)
print(f"\nSaved yearly top-{TOP_N} subreddits by comments ({len(yearly_top5_comments)} years) to yearly_top5_subreddits_by_comments.csv")

# ----------------------------------------------------------------
# 3. Yearly top-5 subreddits by unique authors (Q3, author-diversity half)
# ----------------------------------------------------------------
pairs_paths = sorted(PER_FILE_DIR.glob("*__subreddit_authors.parquet"))
pairs_by_year = defaultdict(list)
for p in pairs_paths:
    m = FNAME_RE.search(p.name)
    if m:
        pairs_by_year[m.group(1)].append(p)

author_rows = []
for year in sorted(yearly_comments):
    # Upper bound per subreddit for this year only (sum of that year's per-file
    # exact unique-author counts) — see 2_'s comments for why this bounds the
    # candidate shortlist safely without needing exact sets for every subreddit.
    upper_bound = Counter()
    for p in paths_by_year.get(year, []):
        df = pd.read_csv(p)
        for sub, n in zip(df["subreddit"], df["n_unique_authors"]):
            upper_bound[sub] += n

    candidates = {sub for sub, _ in upper_bound.most_common(CANDIDATE_POOL_SIZE)}

    subreddit_authors = defaultdict(set)
    year_authors = set()  # every author active this year, for the share_pct denominator
    for p in pairs_by_year.get(year, []):
        df = pd.read_parquet(p)
        year_authors.update(df["author"].unique())
        candidate_rows = df[df["subreddit"].isin(candidates)]
        for sub, authors in candidate_rows.groupby("subreddit")["author"].apply(set).items():
            subreddit_authors[sub] |= authors

    year_total_authors = len(year_authors)
    top = sorted(
        ((sub, len(authors)) for sub, authors in subreddit_authors.items()),
        key=lambda kv: kv[1], reverse=True,
    )[:TOP_N]

    row = {"year": year, "year_total_unique_authors": year_total_authors}
    for i in range(TOP_N):
        if i < len(top):
            sub, n = top[i]
            row[f"rank_{i + 1:02d}_subreddit"] = sub
            row[f"rank_{i + 1:02d}_unique_authors"] = n
            row[f"rank_{i + 1:02d}_share_pct"] = round(100 * n / year_total_authors, 2) if year_total_authors else None
        else:
            row[f"rank_{i + 1:02d}_subreddit"] = None
            row[f"rank_{i + 1:02d}_unique_authors"] = None
            row[f"rank_{i + 1:02d}_share_pct"] = None
    author_rows.append(row)
    print(f"  [{year}] shortlisted {len(candidates):,}/{len(upper_bound):,} subreddits for exact author dedup")

yearly_top5_authors = pd.DataFrame(author_rows).sort_values("year")
yearly_top5_authors.to_csv(OUTPUT_DIR / "yearly_top5_subreddits_by_authors.csv", index=False)
print(f"\nSaved yearly top-{TOP_N} subreddits by unique authors ({len(yearly_top5_authors)} years) to yearly_top5_subreddits_by_authors.csv")
