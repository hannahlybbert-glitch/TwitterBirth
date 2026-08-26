# Author: Hannah Lybbert
# Created: 2026-08-26
# Purpose: Aggregate per-file outputs from 1_profile_comments_file.py into a
#          macro-level view of the full comments archive — yearly trends, schema
#          evolution across files, and true cross-file top-subreddit rankings.
#          Sister script to 2_aggregate_submissions_descriptives.py.
# Paths:   OUTPUT_DIR defaults to the local repo layout, but can be overridden with
#          the REDDIT_OUTPUT_DIR env var — set in process_comments.sh to match 1_'s
#          output location on the cluster.

import json
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

ROOT          = Path(__file__).resolve().parents[4]
OUTPUT_BASE   = Path(os.environ.get("REDDIT_OUTPUT_DIR", ROOT / "Reddit/data/ProcessReddit"))
PER_FILE_DIR  = OUTPUT_BASE / "comments_descriptives/per_file"
OUTPUT_DIR    = OUTPUT_BASE / "comments_descriptives"

TOP_N = 25
FNAME_RE = re.compile(r"RC_(\d{4})-(\d{2})")


# ----------------------------------------------------------------
# One row for a single month; columns rank_01..rank_n hold that month's
# top-n subreddit names ranked by `metric` (n_comments or n_unique_authors).
# Months with fewer than n subreddits get blank trailing columns.
# Takes one file's subreddit_stats at a time — callers append rows in
# chronological filename order as they stream through files, instead of
# holding every month's rows in one DataFrame before ranking (see the
# stats loop below for why that matters at this data's scale).
# ----------------------------------------------------------------
def monthly_top_row(df, metric, month_id, n=TOP_N):
    top = df.sort_values(metric, ascending=False).head(n)["subreddit"].tolist()
    row = {"month_id": month_id}
    for i in range(n):
        row[f"rank_{i + 1:02d}"] = top[i] if i < len(top) else None
    return row

# ----------------------------------------------------------------
# Load every per-file summary.json
# ----------------------------------------------------------------
summary_paths = sorted(PER_FILE_DIR.glob("*__summary.json"))
failed_paths  = sorted(PER_FILE_DIR.glob("*__FAILED.txt"))

print(f"Found {len(summary_paths):,} completed file summaries, {len(failed_paths):,} failed files")
if failed_paths:
    print("  Failed files:")
    for p in failed_paths:
        print(f"    {p.name}: {p.read_text().strip()}")

summaries = [json.loads(p.read_text()) for p in summary_paths]
if not summaries:
    raise SystemExit(f"No completed summaries found in {PER_FILE_DIR} — run 1_profile_comments_file.py first")

file_level = pd.DataFrame(summaries)

# ----------------------------------------------------------------
# File-level manifest (one row per RC_*.zst file processed)
# ----------------------------------------------------------------
manifest_cols = [
    "file", "year", "month", "file_size_bytes", "n_rows", "n_bad_lines",
    "elapsed_sec", "rows_per_sec", "n_columns", "date_min", "date_max",
    "n_unique_subreddits", "n_unique_authors", "deleted_removed_rows",
    "pct_deleted_removed", "score_mean", "body_len_mean", "pct_controversial",
]
file_level_out = file_level[manifest_cols].sort_values(["year", "month"])
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
file_level_out.to_csv(OUTPUT_DIR / "file_level_summary.csv", index=False)
print(f"\nSaved file-level manifest ({len(file_level_out)} files) to file_level_summary.csv")

# ----------------------------------------------------------------
# Yearly trends — growth curve of the platform in this data
# ----------------------------------------------------------------
yearly = (
    file_level.groupby("year")
    .agg(
        n_files=("file", "count"),
        n_rows=("n_rows", "sum"),
        n_bad_lines=("n_bad_lines", "sum"),
        deleted_removed_rows=("deleted_removed_rows", "sum"),
        avg_pct_deleted_removed=("pct_deleted_removed", "mean"),
        avg_n_columns=("n_columns", "mean"),
        avg_body_len=("body_len_mean", "mean"),
        avg_pct_controversial=("pct_controversial", "mean"),
        total_file_size_mb=("file_size_bytes", lambda s: s.sum() / 1_048_576),
    )
    .round(2)
    .sort_index()
)
yearly.to_csv(OUTPUT_DIR / "yearly_files_summary.csv")
print("Saved yearly trends to yearly_files_summary.csv")

# ----------------------------------------------------------------
# Schema evolution — which columns exist in which files, over time.
# ----------------------------------------------------------------
schema_rows = []
presence = {}
for s in summaries:
    schema_rows.append({
        "file": s["file"], "year": s["year"], "month": s["month"],
        "n_columns": s["n_columns"], "columns": ";".join(s["columns"]),
    })
    presence[s["file"]] = set(s["columns"])

schema_evolution = pd.DataFrame(schema_rows).sort_values(["year", "month"])
schema_evolution.to_csv(OUTPUT_DIR / "schema_evolution.csv", index=False)

all_cols_ever = sorted(set().union(*presence.values())) if presence else []
presence_matrix = pd.DataFrame(
    {col: [1 if col in presence[f] else 0 for f in presence] for col in all_cols_ever},
    index=list(presence.keys()),
).sort_index()
presence_matrix.to_csv(OUTPUT_DIR / "schema_presence_matrix.csv")
print(f"Saved schema evolution ({len(all_cols_ever)} distinct columns ever seen) to schema_evolution.csv / schema_presence_matrix.csv")

# ----------------------------------------------------------------
# Top N subreddits by TOTAL COMMENTS, and top-N-per-month tables — computed by
# streaming one file's subreddit_stats.csv at a time and folding into
# running totals / per-month rows, instead of concatenating every month
# into one DataFrame first. A concatenated frame would hold one row per
# (subreddit, month) for the *entire* history at once — none of these
# metrics need more than one file's data in memory at a time.
# ----------------------------------------------------------------
stats_paths = sorted(PER_FILE_DIR.glob("*__subreddit_stats.csv"))

comments_totals = Counter()       # subreddit -> total comments, exact (comments are disjoint across files)
authors_upper_bound = Counter()   # subreddit -> sum of per-file unique-author counts — an upper bound
                                   # on the true cross-file dedup count (see candidate shortlist below),
                                   # not itself an exact answer since the same author can appear in a
                                   # subreddit across many months.
monthly_top_by_comments_rows = []
monthly_top_by_authors_rows = []

for p in stats_paths:
    m = FNAME_RE.search(p.name)
    if not m:
        continue
    month_id = f"{m.group(2)}{m.group(1)}"  # MMYYYY, e.g. "122012" for Dec 2012
    df = pd.read_csv(p)
    for sub, n in zip(df["subreddit"], df["n_comments"]):
        comments_totals[sub] += n
    for sub, n in zip(df["subreddit"], df["n_unique_authors"]):
        authors_upper_bound[sub] += n
    monthly_top_by_comments_rows.append(monthly_top_row(df, "n_comments", month_id))
    monthly_top_by_authors_rows.append(monthly_top_row(df, "n_unique_authors", month_id))

top_by_comments = (
    pd.Series(comments_totals, name="n_comments")
    .rename_axis("subreddit")
    .sort_values(ascending=False)
    .head(TOP_N)
    .reset_index()
)
top_by_comments.to_csv(OUTPUT_DIR / f"top_{TOP_N}_subreddits_by_comments.csv", index=False)
print(f"Saved top {TOP_N} subreddits by total comments")

# ----------------------------------------------------------------
# Top N subreddits PER MONTH, wide format — one row per month (MMYYYY id),
# one column per rank, so you can see how the top-{TOP_N} composition shifts
# over time. Two separate files: ranked by that month's comment volume
# (activity) and by that month's unique-author count (author diversity —
# per-file, not cross-file deduped, since each row is scoped to one month).
# Rows come out in chronological order because stats_paths sorts that way
# already: "RC_YYYY-MM" filenames are zero-padded, so lexical sort ==
# chronological sort — no separate (year, month) re-sort needed.
# ----------------------------------------------------------------
monthly_top_by_comments = pd.DataFrame(monthly_top_by_comments_rows)
monthly_top_by_comments.to_csv(OUTPUT_DIR / f"top_{TOP_N}_subreddits_by_comments_monthly.csv", index=False)

monthly_top_by_authors = pd.DataFrame(monthly_top_by_authors_rows)
monthly_top_by_authors.to_csv(OUTPUT_DIR / f"top_{TOP_N}_subreddits_by_authors_monthly.csv", index=False)

print(f"Saved monthly top-{TOP_N} subreddit rankings (by comments, by authors) — {len(monthly_top_by_comments)} months")

# ----------------------------------------------------------------
# Top N subreddits by UNIQUE AUTHORS — true cross-file dedup. Building an
# exact author set for every subreddit that ever existed would mean holding
# every unique (subreddit, author) pair ever seen in memory at once — that's
# what OOM'd on the submissions pipeline, not the file read order, since
# each parquet was already read one at a time.
#
# Instead: authors_upper_bound (summed above, per-file exact counts) is a
# safe upper bound on each subreddit's true dedup count — a union can only
# be <= the sum of its parts. Only build exact sets for a generous
# shortlist of top candidates by that bound; any subreddit outside the
# shortlist has an upper bound below the shortlist cutoff, so its true
# count can't clear that cutoff either, and it can't be a real top-TOP_N
# entry. This bounds peak memory to ~CANDIDATE_POOL_SIZE subreddits' worth
# of author sets instead of all of them.
#
# This is a generous heuristic, not a mathematical guarantee (a subreddit
# with very few but highly repeat-commenting authors could in principle be
# undercounted relative to its upper bound rank) — acceptable here since
# these are exploratory descriptives, not published figures.
# ----------------------------------------------------------------
CANDIDATE_POOL_SIZE = max(TOP_N * 20, 500)
candidates = {sub for sub, _ in authors_upper_bound.most_common(CANDIDATE_POOL_SIZE)}
print(f"Shortlisted {len(candidates):,} candidate subreddits for exact author dedup "
      f"(out of {len(authors_upper_bound):,} subreddits seen)")

pairs_paths = sorted(PER_FILE_DIR.glob("*__subreddit_authors.parquet"))

subreddit_authors = defaultdict(set)   # only candidates get populated
global_authors = set()                 # every author seen anywhere — for the true global count below
subreddits_with_authors = set()        # every subreddit with >=1 non-deleted author — for the count below

for p in pairs_paths:
    df = pd.read_parquet(p)
    subreddits_with_authors.update(df["subreddit"].unique())
    global_authors.update(df["author"].unique())
    candidate_rows = df[df["subreddit"].isin(candidates)]
    for sub, authors in candidate_rows.groupby("subreddit")["author"].apply(set).items():
        subreddit_authors[sub] |= authors

top_by_authors = (
    pd.DataFrame(
        [(sub, len(authors)) for sub, authors in subreddit_authors.items()],
        columns=["subreddit", "n_unique_authors"],
    )
    .sort_values("n_unique_authors", ascending=False)
    .head(TOP_N)
    .reset_index(drop=True)
)
top_by_authors.to_csv(OUTPUT_DIR / f"top_{TOP_N}_subreddits_by_authors.csv", index=False)
print(f"Saved top {TOP_N} subreddits by unique authors")

global_unique_authors = len(global_authors)
global_unique_subreddits = len(subreddits_with_authors)

# ----------------------------------------------------------------
# Console summary
# ----------------------------------------------------------------
print(f"\n{'=' * 60}")
print("MACRO SUMMARY")
print(f"{'=' * 60}")
print(f"Files processed:              {len(summaries):,}")
print(f"Date range covered:           {file_level['date_min'].min()}  to  {file_level['date_max'].max()}")
print(f"Total rows (all files):       {file_level['n_rows'].sum():,}")
print(f"Total deleted/removed rows:   {file_level['deleted_removed_rows'].sum():,} "
      f"({100 * file_level['deleted_removed_rows'].sum() / file_level['n_rows'].sum():.2f}%)")
print(f"Global unique authors:        {global_unique_authors:,}  (excl. [deleted]/[removed])")
print(f"Global unique subreddits:     {global_unique_subreddits:,}")
print(f"Distinct columns ever seen:   {len(all_cols_ever)}")
print(f"Column count range by file:   {file_level['n_columns'].min()}–{file_level['n_columns'].max()}")

print(f"\n--- Top {TOP_N} subreddits by total comments ---")
print(top_by_comments.to_string(index=False))

print(f"\n--- Top {TOP_N} subreddits by unique authors ---")
print(top_by_authors.to_string(index=False))

print(f"\nAll outputs saved to {OUTPUT_DIR}")
