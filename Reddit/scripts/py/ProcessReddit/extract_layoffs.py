# Author: Hannah Lybbert
# Created: 2026-10-16
# Updated: 2026-10-16
# Purpose: Pull every comment/submission (all columns) from one subreddit into monthly, then yearly, parquet files

import argparse
import io
import json
import os
import re
import time
from pathlib import Path

import pandas as pd
import zstandard as zstd

ROOT            = Path(__file__).resolve().parents[4]
COMMENTS_DIR    = Path(os.environ.get("REDDIT_COMMENTS_DIR", ROOT / "Reddit/raw/comments"))
SUBMISSIONS_DIR = Path(os.environ.get("REDDIT_SUBMISSIONS_DIR", ROOT / "Reddit/raw/submissions"))
OUTPUT_BASE     = Path(os.environ.get("REDDIT_OUTPUT_DIR", ROOT / "Reddit/data/ProcessReddit"))

SUBREDDIT  = "layoffs"
MAX_WINDOW = 2 ** 31  # some dumps use zstd windows > the library default (2**27)

KINDS = {
    "comments":    {"dir": COMMENTS_DIR,    "prefix": "RC"},
    "submissions": {"dir": SUBMISSIONS_DIR, "prefix": "RS"},
}


# ----------------------------------------------------------------
# 1. Helpers
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


def to_int(v):
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(v)
    if isinstance(v, str):
        try:
            return int(float(v))
        except ValueError:
            return None
    return None


def output_name(period, subreddit, kind):
    return f"{period}_{subreddit.upper()}_{kind}.parquet"


# Columns with mixed types (e.g. edited = False / epoch) -> strings
def fix_mixed_types(df):
    for c in df.columns:
        if df[c].dtype == object:
            types = {type(v) for v in df[c].dropna()}
            if len(types) > 1:
                df[c] = df[c].map(lambda v: None if v is None else str(v)).astype("string")
    return df


# Nested fields -> JSON strings
def to_frame(rows):
    rows = [{k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
             for k, v in r.items()} for r in rows]
    df = fix_mixed_types(pd.DataFrame(rows))
    if "created_utc" in df.columns:
        df["created_utc"] = pd.array(df["created_utc"].map(to_int), dtype="Int64")
    return df.sort_values("created_utc").reset_index(drop=True)


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


# ----------------------------------------------------------------
# 2. Extract one monthly dump
# ----------------------------------------------------------------
def process_file(path, kind, subreddit, out_dir):
    month = re.search(r"_(\d{4}-\d{2})\.zst$", path.name).group(1)
    marker = out_dir / f".done_{month}"
    if marker.exists():
        print(f"[{path.stem}] already done, skipping")
        return

    # cheap regex prefilter on the raw line before json parsing
    pre = re.compile(r'"subreddit"\s*:\s*"' + re.escape(subreddit) + '"', re.IGNORECASE)
    rows = []
    n_seen = n_bad = 0
    start = time.time()
    for line in iter_records(path):
        n_seen += 1
        if not pre.search(line):
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            n_bad += 1
            continue
        if str(rec.get("subreddit", "")).lower() == subreddit.lower():
            rows.append(rec)

    if rows:
        save_atomic(to_frame(rows), out_dir / output_name(month, subreddit, kind))
    out_dir.mkdir(parents=True, exist_ok=True)
    marker.touch()
    print(f"[{path.stem}] {n_seen:,} {kind} scanned -> {len(rows):,} kept in {time.time() - start:.0f}s"
          + (f"  [{n_bad:,} bad lines]" if n_bad else ""))


# ----------------------------------------------------------------
# 3. Combine monthly files into YYYY_<SUBREDDIT>_<kind>.parquet
# ----------------------------------------------------------------
def combine_years(subreddit, kind, out_dir, monthly_dir):
    files = sorted(monthly_dir.glob(output_name("*", subreddit, kind)))
    years = sorted({f.name[:4] for f in files})
    for year in years:
        parts = [pd.read_parquet(f) for f in files if f.name.startswith(year)]
        n_done = len(list(monthly_dir.glob(f".done_{year}-*")))
        df = fix_mixed_types(pd.concat(parts, ignore_index=True))
        df = df.sort_values("created_utc").reset_index(drop=True)
        save_atomic(df, out_dir / output_name(year, subreddit, kind))
        print(f"[{year}] {len(parts)} monthly files ({n_done}/12 months scanned) -> {len(df):,} rows")


# ----------------------------------------------------------------
# 4. Main
# ----------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=KINDS)
    ap.add_argument("file", nargs="?", help="single RC_/RS_YYYY-MM.zst (name or path); omit to loop all")
    ap.add_argument("--subreddit", default=SUBREDDIT)
    ap.add_argument("--combine", action="store_true", help="only combine existing monthly files into yearly files")
    args = ap.parse_args()

    cfg = KINDS[args.kind]
    out_dir = OUTPUT_BASE / args.subreddit / args.kind
    monthly_dir = out_dir / "monthly"

    if args.combine:
        combine_years(args.subreddit, args.kind, out_dir, monthly_dir)
        return

    if args.file:
        p = Path(args.file)
        if not p.exists():
            p = cfg["dir"] / p.name
        files = [p]
    else:
        files = sorted(cfg["dir"].glob(f"{cfg['prefix']}_*.zst"))
        print(f"Found {len(files)} {args.kind} files in {cfg['dir']}")

    for p in files:
        process_file(p, args.kind, args.subreddit, monthly_dir)

    # loop-all mode combines at the end; single-file (array) mode leaves it to --combine
    if not args.file:
        combine_years(args.subreddit, args.kind, out_dir, monthly_dir)


if __name__ == "__main__":
    main()
