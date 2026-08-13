# Author: Hannah Lybbert
# Created: 2026-08-13
# Updated: 2026-08-13
# Purpose: Profile the structure of a raw Reddit comments .zst dump (columns,
#          types, row counts, subreddit/author activity) to scope out cluster-scale
#          processing of the full comments archive. Sister script to
#          understanding_submissions.py.

import io
import json
import time
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd
import zstandard as zstd

ROOT       = Path(__file__).resolve().parents[4]
INPUT      = ROOT / "Reddit/raw/comments/RC_2012-12.zst"   # change to point at other RC_*.zst files on the cluster
OUTPUT_DIR = ROOT / "Reddit/output/ProcessReddit/comments"

TOP_N        = 50
HEAD_N       = 5        # rows to preview raw
MAX_WINDOW   = 2 ** 31  # some dumps use zstd windows larger than the library default (2**27)
SAMPLE_TYPES = 5_000    # rows used to infer per-column python types; schema is stable within a month, so a sample is enough


# ----------------------------------------------------------------
# Stream-decode a .zst NDJSON dump one record at a time.
# Avoids loading the whole (potentially huge) file into memory,
# which matters once this is pointed at years of cluster data.
# ----------------------------------------------------------------
def iter_records(path):
    with open(path, "rb") as fh:
        dctx = zstd.ZstdDecompressor(max_window_size=MAX_WINDOW)
        with dctx.stream_reader(fh, read_across_frames=True) as reader:
            text = io.TextIOWrapper(reader, encoding="utf-8", errors="replace")
            for line in text:
                line = line.strip()
                if not line:
                    continue
                yield line


# ----------------------------------------------------------------
# Grab just the first n raw records, for a quick eyeball of the data.
# Stops reading as soon as n lines are seen, so this is fast even
# against a huge file — it never decompresses the rest of it.
# ----------------------------------------------------------------
def get_head(path, n=HEAD_N):
    records = []
    for i, line in enumerate(iter_records(path)):
        if i >= n:
            break
        records.append(json.loads(line))
    return records


# ----------------------------------------------------------------
# Pass over the file, accumulating summary stats without holding
# individual records or raw values in memory.
# ----------------------------------------------------------------
def profile(path):
    n_rows      = 0
    n_bad_lines = 0

    all_columns = set()
    type_counts = defaultdict(Counter)   # column -> {python type: count}, from first SAMPLE_TYPES rows
    null_counts = Counter()              # column -> count of None values, over all rows

    subreddits         = set()
    subreddit_authors   = defaultdict(set)  # subreddit -> set of authors (drives the top-50 ranking)
    authors_total       = set()
    deleted_author_rows = 0

    created_min = None
    created_max = None

    score_n, score_sum, score_min, score_max = 0, 0, None, None
    body_n, body_len_sum, body_len_min, body_len_max = 0, 0, None, None
    controversial_n, controversial_true = 0, 0

    start = time.time()
    for i, line in enumerate(iter_records(path)):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            n_bad_lines += 1
            continue

        n_rows += 1
        all_columns.update(rec.keys())

        if i < SAMPLE_TYPES:
            for k, v in rec.items():
                type_counts[k][type(v).__name__] += 1

        for k, v in rec.items():
            if v is None:
                null_counts[k] += 1

        sub = rec.get("subreddit")
        if sub:
            subreddits.add(sub)
            author = rec.get("author")
            if author:
                subreddit_authors[sub].add(author)
                authors_total.add(author)
                if author in ("[deleted]", "[removed]"):
                    deleted_author_rows += 1

        created = rec.get("created_utc")
        if isinstance(created, (int, float)):
            created_min = created if created_min is None else min(created_min, created)
            created_max = created if created_max is None else max(created_max, created)

        score = rec.get("score")
        if isinstance(score, (int, float)):
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

    return {
        "n_rows": n_rows,
        "n_bad_lines": n_bad_lines,
        "all_columns": all_columns,
        "type_counts": type_counts,
        "null_counts": null_counts,
        "subreddits": subreddits,
        "subreddit_authors": subreddit_authors,
        "authors_total": authors_total,
        "deleted_author_rows": deleted_author_rows,
        "created_min": created_min,
        "created_max": created_max,
        "score_stats": (score_n, score_sum, score_min, score_max),
        "body_len_stats": (body_n, body_len_sum, body_len_min, body_len_max),
        "controversial_stats": (controversial_n, controversial_true),
        "elapsed": elapsed,
    }


# ----------------------------------------------------------------
# Run + report
# ----------------------------------------------------------------
file_size_mb = INPUT.stat().st_size / 1_048_576
print(f"Input:      {INPUT}")
print(f"File size:  {file_size_mb:,.2f} MB (compressed, .zst)")

head_records = get_head(INPUT, HEAD_N)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
head_path = OUTPUT_DIR / "comment_head.csv"
pd.DataFrame(head_records).to_csv(head_path, index=False)
print(f"Saved first {HEAD_N} rows to {head_path}")

print("\nReading full file...\n")
stats = profile(INPUT)

print(f"--- Row count ---")
print(f"  Rows (comments): {stats['n_rows']:,}")
if stats["n_bad_lines"]:
    print(f"  Skipped malformed JSON lines: {stats['n_bad_lines']:,}")
print(f"  Read in {stats['elapsed']:.1f}s  ({stats['n_rows'] / max(stats['elapsed'], 1e-9):,.0f} rows/sec)")
print(f"  Avg compressed bytes/row: {INPUT.stat().st_size / max(stats['n_rows'], 1):,.1f}")

print(f"\n--- Columns ({len(stats['all_columns'])} total) ---")
type_rows = []
for col in sorted(stats["all_columns"]):
    types  = stats["type_counts"].get(col, Counter())
    dtype  = ", ".join(f"{t} ({n})" for t, n in types.most_common())
    n_null = stats["null_counts"].get(col, 0)
    pct_null = 100 * n_null / stats["n_rows"] if stats["n_rows"] else 0
    type_rows.append({"column": col, "observed_types_in_sample": dtype, "pct_null": round(pct_null, 2)})
print(pd.DataFrame(type_rows).to_string(index=False))

if stats["created_min"] is not None:
    print(f"\n--- Date range ---")
    print(f"  {pd.to_datetime(stats['created_min'], unit='s')}  to  {pd.to_datetime(stats['created_max'], unit='s')}")

print(f"\n--- Subreddits & authors ---")
print(f"  Unique subreddits: {len(stats['subreddits']):,}")
print(f"  Unique authors:    {len(stats['authors_total']):,}")
if stats["n_rows"]:
    pct_deleted = 100 * stats["deleted_author_rows"] / stats["n_rows"]
    print(f"  Rows with [deleted]/[removed] author: {stats['deleted_author_rows']:,} ({pct_deleted:.2f}%)")

score_n, score_sum, score_min, score_max = stats["score_stats"]
if score_n:
    print(f"\n--- Score ---")
    print(f"  mean={score_sum / score_n:.2f}  min={score_min}  max={score_max}  (n={score_n:,})")

body_n, body_len_sum, body_len_min, body_len_max = stats["body_len_stats"]
if body_n:
    print(f"\n--- Comment body length (characters) ---")
    print(f"  mean={body_len_sum / body_n:.1f}  min={body_len_min}  max={body_len_max}  (n={body_n:,})")

controversial_n, controversial_true = stats["controversial_stats"]
if controversial_n:
    pct_controversial = 100 * controversial_true / controversial_n
    print(f"\n--- Controversiality ---")
    print(f"  Controversial comments: {controversial_true:,} ({pct_controversial:.2f}%)  (n={controversial_n:,})")

# ----------------------------------------------------------------
# Top N subreddits by unique author count
# ----------------------------------------------------------------
top_subs = (
    pd.DataFrame(
        [(sub, len(authors)) for sub, authors in stats["subreddit_authors"].items()],
        columns=["subreddit", "unique_authors"],
    )
    .sort_values("unique_authors", ascending=False)
    .head(TOP_N)
    .reset_index(drop=True)
)
print(f"\n--- Top {TOP_N} subreddits by unique authors ---")
print(top_subs.to_string(index=False))

# ----------------------------------------------------------------
# Save
# ----------------------------------------------------------------
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
top_subs.to_csv(OUTPUT_DIR / f"{INPUT.stem}_top_subreddits_by_authors.csv", index=False)
pd.DataFrame(type_rows).to_csv(OUTPUT_DIR / f"{INPUT.stem}_column_summary.csv", index=False)
print(f"\nSaved top subreddits + column summary to {OUTPUT_DIR}")
