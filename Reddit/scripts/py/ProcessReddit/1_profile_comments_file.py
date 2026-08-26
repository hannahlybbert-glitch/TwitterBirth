# Author: Hannah Lybbert
# Created: 2026-08-26
# Purpose: Profile a single Reddit comments .zst dump (rows, schema, subreddit/author
#          activity) — the per-file "map" step of a cluster-wide descriptives run.
#          Run with no arguments to loop over every RC_*.zst file in COMMENTS_DIR,
#          skipping files already profiled (resumable). Pass one file path to profile
#          just that file — the shape used by process_comments.sh's per-file loop.
#          Pair with 2_aggregate_comments_descriptives.py to combine results.
#          Sister script to 1_profile_submissions_file.py.
# Paths:   COMMENTS_DIR / OUTPUT_DIR default to the local repo layout, but can be
#          overridden with the REDDIT_COMMENTS_DIR / REDDIT_OUTPUT_DIR env vars —
#          set these in process_comments.sh, since the raw data lives at a different
#          path structure on the cluster (no nested "Reddit/" folder there).

import io
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import zstandard as zstd

ROOT         = Path(__file__).resolve().parents[4]
COMMENTS_DIR = Path(os.environ.get("REDDIT_COMMENTS_DIR", ROOT / "Reddit/raw/comments"))
OUTPUT_BASE  = Path(os.environ.get("REDDIT_OUTPUT_DIR", ROOT / "Reddit/data/ProcessReddit"))
OUTPUT_DIR   = OUTPUT_BASE / "comments_descriptives/per_file"

MAX_WINDOW = 2 ** 31  # some dumps use zstd windows larger than the library default (2**27)
FNAME_RE   = re.compile(r"RC_(\d{4})-(\d{2})\.zst$")


# ----------------------------------------------------------------
# Stream-decode a .zst NDJSON dump one record at a time.
# ----------------------------------------------------------------
def iter_records(path):
    with open(path, "rb") as fh:
        dctx = zstd.ZstdDecompressor(max_window_size=MAX_WINDOW)
        with dctx.stream_reader(fh, read_across_frames=True) as reader:
            text = io.TextIOWrapper(reader, encoding="utf-8", errors="replace")
            for line in text:
                line = line.strip()
                if line:
                    yield line


# ----------------------------------------------------------------
# created_utc comes through as int/float in some monthly dumps and as a
# string in others (confirmed on RC_2012-12) — coerce instead of relying
# on isinstance(created, (int, float)), which silently drops every row's
# timestamp on the string-typed months.
# ----------------------------------------------------------------
def to_epoch(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str):
        try:
            return int(v)
        except ValueError:
            return None
    return None


# ----------------------------------------------------------------
# Single pass over one file, accumulating everything the aggregator
# will need. Authors are tracked per-subreddit as sets so the
# aggregator can later union them exactly across files.
# ----------------------------------------------------------------
def profile_file(path):
    year = month = None
    m = FNAME_RE.search(path.name)
    if m:
        year, month = m.group(1), m.group(2)

    n_rows, n_bad_lines = 0, 0
    all_columns = set()
    null_counts = Counter()

    subreddit_comments = Counter()          # subreddit -> total comment count (incl. deleted/removed authors)
    subreddit_authors   = defaultdict(set)  # subreddit -> set of real authors (excl. deleted/removed)
    authors_total        = set()
    deleted_removed_rows = 0

    created_min = created_max = None
    score_n, score_sum, score_min, score_max = 0, 0, None, None
    body_n, body_len_sum, body_len_min, body_len_max = 0, 0, None, None
    controversial_n, controversial_true = 0, 0

    start = time.time()
    for line in iter_records(path):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            n_bad_lines += 1
            continue

        n_rows += 1
        all_columns.update(rec.keys())
        for k, v in rec.items():
            if v is None:
                null_counts[k] += 1

        sub = rec.get("subreddit")
        if sub:
            subreddit_comments[sub] += 1
            author = rec.get("author")
            if author in ("[deleted]", "[removed]"):
                deleted_removed_rows += 1
            elif author:
                subreddit_authors[sub].add(author)
                authors_total.add(author)

        created = to_epoch(rec.get("created_utc"))
        if created is not None:
            created_min = created if created_min is None else min(created_min, created)
            created_max = created if created_max is None else max(created_max, created)

        score = rec.get("score")
        if isinstance(score, (int, float)) and not isinstance(score, bool):
            score_n += 1
            score_sum += score
            score_min = score if score_min is None else min(score_min, score)
            score_max = score if score_max is None else max(score_max, score)

        body = rec.get("body")
        if isinstance(body, str):
            blen = len(body)
            body_n += 1
            body_len_sum += blen
            body_len_min = blen if body_len_min is None else min(body_len_min, blen)
            body_len_max = blen if body_len_max is None else max(body_len_max, blen)

        controversiality = rec.get("controversiality")
        if isinstance(controversiality, (int, bool)):
            controversial_n += 1
            controversial_true += bool(controversiality)

    elapsed = time.time() - start

    summary = {
        "file":                path.name,
        "year":                year,
        "month":               month,
        "file_size_bytes":     path.stat().st_size,
        "n_rows":              n_rows,
        "n_bad_lines":         n_bad_lines,
        "elapsed_sec":         round(elapsed, 1),
        "rows_per_sec":        round(n_rows / elapsed, 1) if elapsed else None,
        "n_columns":           len(all_columns),
        "columns":             sorted(all_columns),
        "pct_null_by_column":  {c: round(100 * null_counts[c] / n_rows, 2) for c in sorted(all_columns)} if n_rows else {},
        "date_min":            pd.to_datetime(created_min, unit="s").isoformat() if created_min is not None else None,
        "date_max":            pd.to_datetime(created_max, unit="s").isoformat() if created_max is not None else None,
        "n_unique_subreddits": len(subreddit_comments),
        "n_unique_authors":    len(authors_total),
        "deleted_removed_rows": deleted_removed_rows,
        "pct_deleted_removed": round(100 * deleted_removed_rows / n_rows, 2) if n_rows else None,
        "score_mean":          round(score_sum / score_n, 2) if score_n else None,
        "score_min":           score_min,
        "score_max":           score_max,
        "body_len_mean":       round(body_len_sum / body_n, 1) if body_n else None,
        "body_len_min":        body_len_min,
        "body_len_max":        body_len_max,
        "pct_controversial":   round(100 * controversial_true / controversial_n, 2) if controversial_n else None,
    }

    subreddit_stats = pd.DataFrame(
        [
            {
                "subreddit": sub,
                "n_comments": subreddit_comments[sub],
                "n_unique_authors": len(subreddit_authors.get(sub, ())),
            }
            for sub in subreddit_comments
        ]
    ).sort_values("n_comments", ascending=False).reset_index(drop=True)

    subreddit_author_pairs = pd.DataFrame(
        [(sub, author) for sub, authors in subreddit_authors.items() for author in authors],
        columns=["subreddit", "author"],
    )

    return summary, subreddit_stats, subreddit_author_pairs


# ----------------------------------------------------------------
# Write outputs atomically (temp file + rename) so a job that dies
# mid-write never leaves a partial file that looks "done" later.
# ----------------------------------------------------------------
def save_outputs(stem, summary, subreddit_stats, subreddit_author_pairs, output_dir):
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / f"{stem}__summary.json"
    stats_path   = output_dir / f"{stem}__subreddit_stats.csv"
    pairs_path   = output_dir / f"{stem}__subreddit_authors.parquet"

    tmp_summary = summary_path.with_suffix(".json.tmp")
    tmp_stats   = stats_path.with_suffix(".csv.tmp")
    tmp_pairs   = pairs_path.with_suffix(".parquet.tmp")

    # Write all three temp files first, then rename all three only if every
    # write succeeds — a failure partway through (e.g. a missing parquet
    # engine) must never leave a partial set of "final" files behind, since
    # already_done() would then wrongly treat this file as complete forever.
    tmp_summary.write_text(json.dumps(summary, indent=2))
    subreddit_stats.to_csv(tmp_stats, index=False)
    subreddit_author_pairs.to_parquet(tmp_pairs, index=False)

    tmp_summary.replace(summary_path)
    tmp_stats.replace(stats_path)
    tmp_pairs.replace(pairs_path)


def already_done(stem, output_dir):
    return (
        (output_dir / f"{stem}__summary.json").exists()
        and (output_dir / f"{stem}__subreddit_stats.csv").exists()
        and (output_dir / f"{stem}__subreddit_authors.parquet").exists()
    )


def run_one(path, output_dir=OUTPUT_DIR):
    stem = path.stem
    print(f"[{stem}] profiling {path.name} ({path.stat().st_size / 1_048_576:,.1f} MB)...")
    try:
        summary, subreddit_stats, subreddit_author_pairs = profile_file(path)
        save_outputs(stem, summary, subreddit_stats, subreddit_author_pairs, output_dir)
    except Exception as e:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / f"{stem}__FAILED.txt").write_text(f"{type(e).__name__}: {e}")
        print(f"[{stem}] FAILED: {e}")
        return
    print(
        f"[{stem}] done — {summary['n_rows']:,} rows, {summary['n_unique_authors']:,} authors, "
        f"{summary['n_unique_subreddits']:,} subreddits, {summary['n_columns']} columns "
        f"in {summary['elapsed_sec']}s"
    )


if __name__ == "__main__":
    if len(sys.argv) > 1:
        run_one(Path(sys.argv[1]))
    else:
        files = sorted(COMMENTS_DIR.glob("RC_*.zst"))
        print(f"Found {len(files)} comments files in {COMMENTS_DIR}")
        for path in files:
            if already_done(path.stem, OUTPUT_DIR):
                print(f"[{path.stem}] already profiled, skipping")
                continue
            run_one(path)
