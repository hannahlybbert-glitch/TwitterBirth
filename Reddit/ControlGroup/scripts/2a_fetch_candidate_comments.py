# Author: Hannah Lybbert
# Created: 2026-09-02
# Updated: 2026-10-05
# Purpose: Pull every comment by each candidate author into per-author files (per_author_candidates/bNNN/{author}_comments.parquet)
#
# Two stages so memory stays bounded:
#   fetch: one task per month -> rows split into N_BUCKETS chunk files by hash(author)
#   split: one task per bucket -> combine that bucket's chunks, write one file per author

import argparse
import io
import json
import os
import re
import time
import zlib
from pathlib import Path

import pandas as pd
import zstandard as zstd

ROOT = Path(__file__).resolve().parents[3]

COMMENTS_DIR = Path(os.environ.get("REDDIT_COMMENTS_DIR", ROOT / "Reddit/raw/comments"))
DATA_DIR     = Path(os.environ.get("CONTROLGROUP_DATA_DIR", ROOT / "Reddit/ControlGroup/data"))

CANDIDATE_POOL_PARQUET = DATA_DIR / "1_candidate_pool.parquet"
CHUNK_DIR              = DATA_DIR / "2a_candidate_comment_chunks"
PER_AUTHOR_DIR         = DATA_DIR / "per_author_candidates"

MAX_WINDOW = 2 ** 31          # some dumps use zstd windows > the library default (2**27)
FNAME_RE   = re.compile(r"RC_(\d{4}-\d{2})\.zst$")

N_BUCKETS = 64   # ~1,500 authors per bucket

# downs is ~0 after 2014 (Reddit stopped exposing downvotes); score is the popularity measure
OUT_COLUMNS    = ["author", "id", "created_utc", "months_from_birth", "subreddit", "score", "ups", "downs", "body"]
INT_COLUMNS    = ["created_utc", "months_from_birth", "score", "ups", "downs"]
STRING_COLUMNS = [c for c in OUT_COLUMNS if c not in INT_COLUMNS]


# ----------------------------------------------------------------
# 1. Helpers
# ----------------------------------------------------------------
# Stream a .zst NDJSON dump one record at a time
def iter_records(path):
    with open(path, "rb") as fh:
        dctx = zstd.ZstdDecompressor(max_window_size=MAX_WINDOW)
        with dctx.stream_reader(fh, read_across_frames=True) as reader:
            text = io.TextIOWrapper(reader, encoding="utf-8", errors="replace")
            for line in text:
                line = line.strip()
                if line:
                    yield line


# Numeric fields are numbers in some dumps and strings in others
def to_int(v):
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
    """Collapse newlines/tabs (same as the treatment side)."""
    if not isinstance(text, str):
        return None
    return text.replace("\r", " ").replace("\n", " ").replace("\t", " ")


def bucket_of(author):
    return zlib.crc32(author.encode("utf-8")) % N_BUCKETS


# ----------------------------------------------------------------
# 2. Stage 1: fetch one month
# ----------------------------------------------------------------
# author -> seed post epoch (months_from_birth here is relative to the seed post; step 3 recomputes it)
def load_candidates():
    if not CANDIDATE_POOL_PARQUET.exists():
        raise SystemExit(
            f"Candidate pool not found: {CANDIDATE_POOL_PARQUET}\n"
            f"Run 1_sample_candidate_pool.py first."
        )
    df = pd.read_parquet(CANDIDATE_POOL_PARQUET, columns=["author", "created_utc"])
    seed_epoch = dict(zip(df["author"], df["created_utc"].astype("int64")))
    print(f"Loaded {len(seed_epoch):,} candidate authors from {CANDIDATE_POOL_PARQUET}")
    return seed_epoch


# Every comment by a candidate author in one month
def process_file(path, seed_epoch):
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
        if n_seen % 5_000_000 == 0:
            print(f"[{path.stem}]   ... {n_seen:,} rows, {len(rows):,} kept", flush=True)

        author = rec.get("author")
        if author not in seed_epoch:
            continue

        created = to_int(rec.get("created_utc"))
        seed = seed_epoch[author]
        if created is not None:
            months_from_birth = ((created - seed) // 86_400) // 30
        else:
            months_from_birth = None

        rows.append({
            "author": author,
            "id": rec.get("id"),
            "created_utc": created,
            "months_from_birth": months_from_birth,
            "subreddit": rec.get("subreddit"),
            "score": to_int(rec.get("score")),
            "ups": to_int(rec.get("ups")),
            "downs": to_int(rec.get("downs")),
            "body": flatten(rec.get("body")),
        })

    elapsed = time.time() - start
    df = pd.DataFrame(rows, columns=OUT_COLUMNS)
    for c in INT_COLUMNS:
        df[c] = pd.array(df[c], dtype="Int64")
    for c in STRING_COLUMNS:
        df[c] = df[c].astype("string")
    print(
        f"[{path.stem}] {n_seen:,} comments scanned -> {len(df):,} kept "
        f"({df['author'].nunique():,} candidate authors) in {elapsed:.0f}s"
        + (f"  [{n_bad:,} bad lines]" if n_bad else "")
    )
    return df


# Retry the rename: OneDrive can briefly lock new files on Windows
def save_atomic(df, path, max_retries=5, retry_delay=1.0):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    df.to_parquet(tmp, index=False)
    for attempt in range(max_retries):
        try:
            tmp.replace(path)
            return
        except PermissionError:
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay * (attempt + 1))


def chunk_path(month, b):
    return CHUNK_DIR / f"chunk_RC_{month}_b{b:03d}.parquet"


def month_marker(month):
    return CHUNK_DIR / f".done_{month}"


def bucket_marker(b):
    return CHUNK_DIR / f".split_done_b{b:03d}"


# Split a month's rows into chunk files by hash(author)
def write_month_buckets(df, month):
    df = df.copy()
    df["_bucket"] = df["author"].map(bucket_of)
    for b, part in df.groupby("_bucket"):
        save_atomic(part.drop(columns="_bucket"), chunk_path(month, b))
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    month_marker(month).touch()


def run_one(path, seed_epoch):
    m = FNAME_RE.search(path.name)
    if not m:
        raise SystemExit(f"Not an RC_YYYY-MM.zst file: {path.name}")
    month = m.group(1)
    df = process_file(path, seed_epoch)
    write_month_buckets(df, month)


# ----------------------------------------------------------------
# 3. Stage 2: split one bucket into per-author files
# ----------------------------------------------------------------
def split_bucket(b):
    chunks = sorted(CHUNK_DIR.glob(f"chunk_RC_*_b{b:03d}.parquet"))
    if not chunks:
        return 0
    combined = pd.concat([pd.read_parquet(c) for c in chunks], ignore_index=True)
    n_authors = 0
    # subfolder per bucket -- one flat ~200k-file folder times out the OnDemand file browser
    bucket_dir = PER_AUTHOR_DIR / f"b{b:03d}"
    bucket_dir.mkdir(parents=True, exist_ok=True)
    for author, part in combined.groupby("author"):
        part = part.sort_values("created_utc").reset_index(drop=True)
        save_atomic(part, bucket_dir / f"{author}_comments.parquet")
        n_authors += 1
    return n_authors


def split_all():
    total_authors = 0
    for b in range(N_BUCKETS):
        if bucket_marker(b).exists():
            print(f"[bucket {b:03d}] already split, skipping")
            continue
        n = split_bucket(b)
        bucket_marker(b).touch()
        total_authors += n
        print(f"[bucket {b:03d}] wrote {n:,} per-author comment files")
    print(f"\nSplit complete: {total_authors:,} candidate authors' comment files written to {PER_AUTHOR_DIR}")


# ----------------------------------------------------------------
# 4. Main
# ----------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="single RC_YYYY-MM.zst to process (name or path); omit to loop all")
    ap.add_argument("--split-only", action="store_true", help="skip fetching; (re)build per-author files from existing chunks")
    ap.add_argument("--bucket", type=int, default=None, help="with --split-only, process just this bucket (Slurm array shape)")
    ap.add_argument("--no-split", action="store_true", help="process all months but skip the split stage")
    args = ap.parse_args()

    if args.split_only:
        if args.bucket is not None:
            n = split_bucket(args.bucket)
            bucket_marker(args.bucket).touch()
            print(f"[bucket {args.bucket:03d}] wrote {n:,} per-author comment files")
        else:
            split_all()
        return

    seed_epoch = load_candidates()

    # single-file mode: Slurm array shape, one month, no split
    if args.file:
        p = Path(args.file)
        if not p.is_absolute() and not p.exists():
            p = COMMENTS_DIR / p.name
        if not p.exists():
            raise SystemExit(f"File not found: {p}")
        run_one(p, seed_epoch)
        return

    files = sorted(COMMENTS_DIR.glob("RC_*.zst"))
    if not files:
        raise SystemExit(
            f"No RC_*.zst files in {COMMENTS_DIR}\n"
            f"Set REDDIT_COMMENTS_DIR to the comments dir on this machine "
            f"(cluster: /nfs/turbo/si-ksrini/Reddit/raw/comments)."
        )
    print(f"Found {len(files)} comment files in {COMMENTS_DIR}")
    for p in files:
        m = FNAME_RE.search(p.name)
        if m and month_marker(m.group(1)).exists():
            print(f"[{m.group(1)}] already fetched, skipping")
            continue
        run_one(p, seed_epoch)

    if not args.no_split:
        split_all()


if __name__ == "__main__":
    main()
