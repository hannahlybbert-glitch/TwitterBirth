# Author: Hannah Lybbert
# Created: 2026-08-27
# Purpose: Pull the full Reddit *comment* history of every treatment author.
#          Reads treatment_authors.csv (author, date_birth), then streams the
#          monthly RC_*.zst comment dumps and keeps every comment whose author
#          is in the treatment set. One streaming pass over the whole archive
#          collects comments for ALL authors at once (see note below) — we never
#          re-scan the archive per author.
#
#          Output: per-month shards in
#            Reddit/data/intermediate/comments/treatment_author_comments/treatment_RC_YYYY-MM.parquet
#          concatenated at the end into
#            Reddit/data/intermediate/comments/treatment_author_comments.parquet
#          The shards make a multi-day cluster run resumable and crash-safe;
#          the single combined file is the deliverable. combine() also writes a
#          small per-author summary (date_birth, earliest_comment_date/epoch/id) to
#            Reddit/data/intermediate/comments/treatment_author_earliest_comment.csv
#
# Usage (run from this file's directory, data_prep/comments/):
#   python pair_authors_comments.py                # loop every RC_*.zst, then combine
#   python pair_authors_comments.py RC_2015-03.zst # one file only (Slurm array shape); no combine
#   python pair_authors_comments.py --combine-only  # just rebuild the combined parquet from shards
#   python pair_authors_comments.py --no-combine    # process all files, skip the combine step
#
# Paths: the raw comments live at a different layout on the cluster than in the
#        repo, so COMMENTS_DIR / the authors csv / the output dir can all be
#        overridden with env vars (same REDDIT_COMMENTS_DIR convention as
#        ProcessReddit/1_profile_comments_file.py):
#          REDDIT_COMMENTS_DIR      dir holding RC_YYYY-MM.zst   (default: repo Reddit/raw/comments)
#          TREATMENT_AUTHORS_CSV    path to treatment_authors.csv (default: repo Reddit/data/final/...)
#          REDDIT_INTERMEDIATE_DIR  dir for outputs               (default: repo Reddit/data/intermediate)

import argparse
import io
import json
import os
import re
import sys
import time
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq
import zstandard as zstd

ROOT = Path(__file__).resolve().parents[5]

COMMENTS_DIR     = Path(os.environ.get("REDDIT_COMMENTS_DIR", ROOT / "Reddit/raw/comments"))
AUTHORS_CSV      = Path(os.environ.get("TREATMENT_AUTHORS_CSV", ROOT / "Reddit/data/final/treatment_authors.csv"))
INTERMEDIATE_DIR = Path(os.environ.get("REDDIT_INTERMEDIATE_DIR", ROOT / "Reddit/data/intermediate"))

OUT_DIR             = INTERMEDIATE_DIR / "comments"
SHARD_DIR           = OUT_DIR / "treatment_author_comments"
COMBINED_PARQUET    = OUT_DIR / "treatment_author_comments.parquet"
EARLIEST_COMMENT_CSV = OUT_DIR / "treatment_author_earliest_comment.csv"

MAX_WINDOW = 2 ** 31          # some dumps use zstd windows > the library default (2**27)
FNAME_RE   = re.compile(r"RC_(\d{4})-(\d{2})\.zst$")

# Comment fields kept in the output. Pulled with rec.get(), so fields absent in
# a given schema year (Reddit's comment schema drifts over time) come through
# blank rather than raising. Rough parallel to (but not identical to — comments
# and submissions don't share a schema) the columns kept in
# clean_raw/clean_2_3M_post_history.py.
KEEP_FIELDS = [
    "id", "name", "subreddit", "subreddit_id", "created_utc", "body",
    "score", "ups", "downs", "controversiality",
    "parent_id", "link_id", "gilded", "edited", "distinguished",
    "stickied", "removal_reason",
]
OUT_COLUMNS = (
    ["author", "date_birth", "birth_epoch", "days_from_birth", "weeks_from_birth", "months_from_birth"]
    + KEEP_FIELDS
)

# Parquet needs one fixed dtype per column, shared across every shard, so that
# combine() can append them to a single file. The four birth-relative columns
# are always clean ints (or missing), so they get pandas' nullable "Int64".
# Everything else is cast to string: several raw fields are known to vary in
# type month-to-month (created_utc is int in some dumps, str in others — see
# to_epoch() — and Reddit's own "edited" field is `false` or a timestamp), so
# a shared numeric dtype for those would risk combine() failing on a schema
# mismatch between shards.
INT_COLUMNS    = ["birth_epoch", "days_from_birth", "weeks_from_birth", "months_from_birth"]
STRING_COLUMNS = [c for c in OUT_COLUMNS if c not in INT_COLUMNS]


# ----------------------------------------------------------------
# Stream-decode a .zst NDJSON dump one record at a time (never hold the
# whole ~2 GB-compressed month in memory). Same shape as the ProcessReddit
# profilers.
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
# created_utc is int/float in some monthly dumps and a string in others
# (confirmed on RC_2012-12). Coerce instead of isinstance-checking.
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


def flatten(text):
    """Collapse newlines/tabs in a comment body so each comment stays one row."""
    return text.replace("\r", " ").replace("\n", " ").replace("\t", " ")


# ----------------------------------------------------------------
# Load treatment authors -> {author: birth_epoch|None} and {author: date_birth_str}.
# birth_epoch lets us stamp each comment with days/weeks/months relative to birth
# in the same pass, matching build_analysis_ready_file.py's floor-division convention.
# ----------------------------------------------------------------
def load_targets():
    if not AUTHORS_CSV.exists():
        raise SystemExit(
            f"Treatment authors file not found: {AUTHORS_CSV}\n"
            f"Run Reddit/scripts/py/data_prep/build/authors.py first, or set "
            f"TREATMENT_AUTHORS_CSV to its path on this machine."
        )
    df = pd.read_csv(AUTHORS_CSV, usecols=["author", "date_birth"])
    df = df.dropna(subset=["author"]).drop_duplicates(subset="author")

    births = pd.to_datetime(df["date_birth"], format="mixed", errors="coerce")
    epochs = (births - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)  # NaT -> NaN

    birth_epoch = {}
    birth_str   = {}
    for author, raw, ep in zip(df["author"], df["date_birth"].astype(str), epochs):
        birth_str[author]   = raw
        birth_epoch[author] = int(ep) if pd.notna(ep) else None

    print(f"Loaded {len(birth_epoch):,} treatment authors from {AUTHORS_CSV}")
    return birth_epoch, birth_str


# ----------------------------------------------------------------
# One streaming pass over a single month's file. Returns a DataFrame of every
# comment written by a treatment author that month.
# ----------------------------------------------------------------
def process_file(path, birth_epoch, birth_str):
    rows = []
    n_seen = n_bad = 0
    start = time.time()

    for line in iter_records(path):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            n_bad += 1
            continue
        n_seen += 1

        author = rec.get("author")
        if author not in birth_epoch:          # O(1) set-style membership; also skips [deleted]/[removed]
            continue

        created = to_epoch(rec.get("created_utc"))
        b = birth_epoch[author]
        if created is not None and b is not None:
            days = (created - b) // 86_400     # floor div, matches build_analysis_ready_file.py
            weeks = days // 7
            months = days // 30
        else:
            days = weeks = months = None

        row = {
            "author": author,
            "date_birth": birth_str.get(author, ""),
            "birth_epoch": b,
            "days_from_birth": days,
            "weeks_from_birth": weeks,
            "months_from_birth": months,
        }
        for f in KEEP_FIELDS:
            v = rec.get(f)
            if f == "body" and isinstance(v, str):
                v = flatten(v)
            row[f] = v
        rows.append(row)

    elapsed = time.time() - start
    df = pd.DataFrame(rows, columns=OUT_COLUMNS)
    for c in INT_COLUMNS:
        df[c] = df[c].astype("Int64")
    for c in STRING_COLUMNS:
        df[c] = df[c].astype("string")
    print(
        f"[{path.stem}] {n_seen:,} comments scanned -> {len(df):,} kept "
        f"({df['author'].nunique():,} authors) in {elapsed:.0f}s"
        + (f"  [{n_bad:,} bad lines]" if n_bad else "")
    )
    return df


# ----------------------------------------------------------------
# Atomic write: temp file + rename, so a job killed mid-write never leaves a
# partial shard that already_done() would later treat as complete.
# ----------------------------------------------------------------
def save_atomic(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    df.to_parquet(tmp, index=False)
    tmp.replace(path)


def already_done(stem):
    return (SHARD_DIR / f"treatment_{stem}.parquet").exists()


def run_one(path, birth_epoch, birth_str):
    df = process_file(path, birth_epoch, birth_str)
    save_atomic(df, SHARD_DIR / f"treatment_{path.stem}.parquet")


# ----------------------------------------------------------------
# Concatenate shards -> single deliverable, writing one shard's table at a time
# (as a Parquet row group) so the full (potentially many-GB) table is never
# held in memory at once. Every shard shares the same fixed schema (see
# INT_COLUMNS / STRING_COLUMNS above), so appending row groups is safe.
#
# While we're already streaming every row once for the combine, also track
# each author's earliest comment (epoch + id) in a small in-memory dict —
# one entry per treatment author (~45k), negligible next to the row stream —
# and write it out as a separate per-author summary at the end.
# ----------------------------------------------------------------
def combine():
    shards = sorted(SHARD_DIR.glob("treatment_RC_*.parquet"))
    if not shards:
        print(f"No shards in {SHARD_DIR}; nothing to combine.")
        return
    COMBINED_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    tmp = COMBINED_PARQUET.with_name(COMBINED_PARQUET.name + ".tmp")
    writer = None
    total = 0
    earliest = {}  # author -> (epoch, comment_id)
    try:
        for shard in shards:
            table = pq.read_table(shard)
            if writer is None:
                writer = pq.ParquetWriter(tmp, table.schema)
            writer.write_table(table)
            total += table.num_rows

            for author, created_utc, cid in zip(
                table.column("author").to_pylist(),
                table.column("created_utc").to_pylist(),
                table.column("id").to_pylist(),
            ):
                epoch = to_epoch(created_utc)
                if epoch is None:
                    continue
                if author not in earliest or epoch < earliest[author][0]:
                    earliest[author] = (epoch, cid)
    finally:
        if writer is not None:
            writer.close()
    tmp.replace(COMBINED_PARQUET)
    print(f"Combined {len(shards)} shards -> {COMBINED_PARQUET}  ({total:,} rows)")

    _, birth_str = load_targets()
    save_earliest_comments(earliest, birth_str)


def save_earliest_comments(earliest, birth_str):
    if not earliest:
        print("No comments found; skipping earliest-comment summary.")
        return
    df = pd.DataFrame(
        [(author, epoch, cid) for author, (epoch, cid) in earliest.items()],
        columns=["author", "earliest_comment_epoch", "earliest_comment_id"],
    )
    df["earliest_comment_date"] = pd.to_datetime(df["earliest_comment_epoch"], unit="s").dt.strftime("%Y-%m-%d")
    df["date_birth"] = df["author"].map(birth_str)
    df = df[["author", "date_birth", "earliest_comment_date", "earliest_comment_epoch", "earliest_comment_id"]]
    df = df.sort_values("author").reset_index(drop=True)
    EARLIEST_COMMENT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(EARLIEST_COMMENT_CSV, index=False)
    print(f"Saved earliest-comment summary for {len(df):,} authors -> {EARLIEST_COMMENT_CSV}")


# ----------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="single RC_YYYY-MM.zst to process (name or path); omit to loop all")
    ap.add_argument("--combine-only", action="store_true", help="rebuild the combined parquet from existing shards and exit")
    ap.add_argument("--no-combine", action="store_true", help="process files but skip the final combine step")
    args = ap.parse_args()

    if args.combine_only:
        combine()
        return

    birth_epoch, birth_str = load_targets()

    if args.file:
        p = Path(args.file)
        if not p.is_absolute() and not p.exists():
            p = COMMENTS_DIR / p.name
        if not p.exists():
            raise SystemExit(f"File not found: {p}")
        run_one(p, birth_epoch, birth_str)
        return  # single-file mode is for parallel array jobs; combine separately with --combine-only

    files = sorted(COMMENTS_DIR.glob("RC_*.zst"))
    if not files:
        raise SystemExit(
            f"No RC_*.zst files in {COMMENTS_DIR}\n"
            f"Set REDDIT_COMMENTS_DIR to the comments dir on this machine "
            f"(cluster: /nfs/turbo/si-ksrini/reddit/raw/comments)."
        )
    print(f"Found {len(files)} comment files in {COMMENTS_DIR}")
    for p in files:
        if already_done(p.stem):
            print(f"[{p.stem}] shard exists, skipping")
            continue
        run_one(p, birth_epoch, birth_str)

    if not args.no_combine:
        combine()


if __name__ == "__main__":
    main()
