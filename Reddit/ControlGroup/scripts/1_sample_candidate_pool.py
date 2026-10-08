# Author: Hannah Lybbert
# Created: 2026-09-02
# Updated: 2026-10-06
# Purpose: Pull 400,000 posts from unique authors not in our treatment author list Reddit/data/final/treatment_authors.csv
#          and save their author id, submission id, and data of submission into a 3X400,000 dataframe
# Input: Reddit/raw/submissions/ and Reddit/final/treatment_authors.csv
# Output: Reddit/ControlGroup/data/1_candidate_pool.parquet



'''
ORIGINAL DESIGN NOTES (kept for reference -- see the IMPLEMENTATION banner below for
what the code actually does):

Things to consider with sampling:
    - Do not pull seed posts form authors in treatment_authors.csv
    - Do not pull seed posts form authors with author == [deleted] or [removed]
    - Start pulling authors from 2007-07 to ensure 18 months of pre-seed-submission potential data
        - On second thought, start pulling from whatever the first YYYY_MM in the date_birth_dist_full.csv is.
            This will ensure that we are sampling from the same distribution of months as the treatment authors.
    - sampling must be random!

How many to sample per month? 100,000 authors from 222 months (18 full years + 6 months from 2007) = 4545 authors per month
    - problem.. are there 4,545 unique authors from the early months of Reddit?
        ex. we'd need over 27k unique authors from 2007 alone.
    - solution: I created date_birth_dist_full.csv where there is the share of posts that come from each of the YYYY-MM combinations
        from our treatment sample. So each "share_of_birth_posts" for each month needs to be multiplied by 100,000 to get
        the number of authors we need to sample from that month. Rules on rounding: if the # of authors needed is <10 for
        a given YYYY-MM then round up to 10. All other values should be rounded using the standard rounding rules
        (0.5 and above rounds up, below 0.5 rounds down).

All the things that will narrow the sample size:
    - If author's earliest post/comment was not at least 18 months before the seed tweet.

    - Not matching any treatment author

Final dataframe will be 3 columns: author, id, created_utc
                    and about 100,000 rows. Save to Reddit/ControlGroup/data/1_candidate_pool.parquet

'''

import argparse
import io
import json
import math
import os
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import zstandard as zstd

ROOT = Path(__file__).resolve().parents[3]

SUBMISSIONS_DIR = Path(os.environ.get("REDDIT_SUBMISSIONS_DIR", ROOT / "Reddit/raw/submissions"))
TREATMENT_CSV   = Path(os.environ.get("TREATMENT_AUTHORS_CSV", ROOT / "Reddit/data/final/treatment_authors.csv"))
BIRTH_DIST_CSV  = Path(os.environ.get("BIRTH_DATE_DIST_CSV", ROOT / "Reddit/data/descriptives/date_birth_dist_full.csv"))
DATA_DIR        = Path(os.environ.get("CONTROLGROUP_DATA_DIR", ROOT / "Reddit/ControlGroup/data"))
ALL_AUTHORS_DIR = Path(os.environ.get("ALL_AUTHORS_DIR", ROOT / "Reddit/data/all_authors"))

CHUNK_DIR     = DATA_DIR / "1_candidate_pool_chunks"
COMBINED_PATH = DATA_DIR / "1_candidate_pool.parquet"

DEFAULT_SEED = 20260902
TARGET_N     = 400_000     # updated to 400k candidate authors on 10/6/2026
MIN_QUOTA    = 10          # months whose scaled share rounds below this are bumped up to it

MAX_WINDOW = 2 ** 31       # some dumps use zstd windows > the library default (2**27)
FNAME_RE   = re.compile(r"RS_(\d{4})-(\d{2})\.zst$")
CHUNK_RE   = re.compile(r"chunk_RS_(\d{4}-\d{2})\.parquet$")

# Placeholder / bot authors
EXCLUDE_AUTHORS = {"[deleted]", "[removed]", "[unknown]", "AutoModerator"}

OUT_COLUMNS = ["author", "id", "created_utc", "seed_month", "subreddit"]
ALL_AUTHORS_COLUMNS = ["author", "is_treatment", "seed_month"]


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


# created_utc is a number in some dumps and a string in others
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
# 2. Monthly quotas and treatment exclusion list
# ----------------------------------------------------------------
# share * TARGET_N, floor of MIN_QUOTA, round half up (built-in round() is banker's rounding)
def month_quota(share):
    raw = share * TARGET_N
    if raw < MIN_QUOTA:
        return MIN_QUOTA
    return int(math.floor(raw + 0.5))


def load_quota_table():
    if not BIRTH_DIST_CSV.exists():
        raise SystemExit(f"Birth-date distribution not found: {BIRTH_DIST_CSV}")
    df = pd.read_csv(BIRTH_DIST_CSV, usecols=["year_month", "share_of_birth_posts"])
    quota = {str(ym): month_quota(s) for ym, s in zip(df["year_month"], df["share_of_birth_posts"])}
    print(
        f"Loaded quota table: {len(quota)} months "
        f"{df['year_month'].iloc[0]}..{df['year_month'].iloc[-1]}, "
        f"{sum(quota.values()):,} authors nominal"
    )
    return quota


def load_treatment_authors():
    if not TREATMENT_CSV.exists():
        raise SystemExit(f"Treatment authors file not found: {TREATMENT_CSV}")
    authors = set(pd.read_csv(TREATMENT_CSV, usecols=["author"])["author"].dropna().astype(str))
    print(f"Loaded {len(authors):,} treatment authors to exclude from {TREATMENT_CSV}")
    return authors


# ----------------------------------------------------------------
# 3. Sample one month
# ----------------------------------------------------------------
# One random submission per eligible author (reservoir sampling), then draw `quota` authors.
# Also records every author seen that month for the all_authors output.
def process_file(path, seed_month, quota, treatment, rng):
    reservoir  = {}   # author -> [id, created_utc_epoch, subreddit]  (non-treatment only)
    seen_count = {}   # author -> eligible rows seen so far this month (non-treatment only)
    all_authors_seen = set()   # every non-placeholder author this month (candidates + treatment)
    n_seen = n_bad = n_skip = 0
    start = time.time()

    for line in iter_records(path):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            n_bad += 1
            continue
        n_seen += 1
        if n_seen % 5_000_000 == 0:
            print(f"[{seed_month}]   ... {n_seen:,} rows, {len(reservoir):,} eligible authors", flush=True)

        author = rec.get("author")
        if not author or author in EXCLUDE_AUTHORS:
            n_skip += 1
            continue

        sid = rec.get("id")
        created = to_epoch(rec.get("created_utc"))
        if sid is None or created is None:
            n_skip += 1
            continue

        all_authors_seen.add(author)

        if author in treatment:
            n_skip += 1
            continue

        c = seen_count.get(author, 0) + 1
        seen_count[author] = c
        # replace with prob 1/c -> each of the author's posts equally likely to be the seed
        if c == 1 or rng.random() < 1.0 / c:
            reservoir[author] = [sid, created, rec.get("subreddit")]

    elapsed = time.time() - start

    save_all_authors(all_authors_seen, treatment, seed_month)

    n_eligible = len(reservoir)

    # Short month: take every eligible author and note the shortfall
    if n_eligible < quota:
        print(
            f"[{seed_month}] Note: cannot fill this stratum. {n_eligible:,} unique authors pulled "
            f"from this month, short by {quota - n_eligible:,} authors (quota {quota:,})",
            flush=True,
        )

    authors = np.array(list(reservoir.keys()), dtype=object)
    chosen = rng.choice(authors, size=min(quota, n_eligible), replace=False)

    df = pd.DataFrame(
        [(a, reservoir[a][0], reservoir[a][1], seed_month, reservoir[a][2]) for a in chosen],
        columns=OUT_COLUMNS,
    )
    df["created_utc"] = df["created_utc"].astype("Int64")

    print(
        f"[{seed_month}] {n_seen:,} rows -> {n_eligible:,} eligible authors -> {len(df):,} drawn "
        f"in {elapsed:.0f}s"
        + (f"  [{n_bad:,} bad lines]" if n_bad else "")
    )
    return df


# ----------------------------------------------------------------
# 4. Save outputs
# ----------------------------------------------------------------
def all_authors_path(seed_month):
    return ALL_AUTHORS_DIR / f"{seed_month}_RS_authors.parquet"


def save_all_authors(all_authors_seen, treatment, seed_month):
    rows = [(author, author in treatment, seed_month) for author in all_authors_seen]
    df = pd.DataFrame(rows, columns=ALL_AUTHORS_COLUMNS)
    df["is_treatment"] = df["is_treatment"].astype(bool)
    save_atomic(df, all_authors_path(seed_month))


def save_atomic(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    df.to_parquet(tmp, index=False)
    tmp.replace(path)


def chunk_path(seed_month):
    return CHUNK_DIR / f"chunk_RS_{seed_month}.parquet"


def month_rng(seed, seed_month):
    year, month = seed_month.split("-")
    return np.random.default_rng([seed, int(year), int(month)])


def run_one(path, quota_table, treatment, seed):
    m = FNAME_RE.search(path.name)
    if not m:
        raise SystemExit(f"Not an RS_YYYY-MM.zst file: {path.name}")
    seed_month = f"{m.group(1)}-{m.group(2)}"
    if seed_month not in quota_table:
        print(f"[{seed_month}] not in the quota table ({BIRTH_DIST_CSV.name}); skipping")
        return
    df = process_file(path, seed_month, quota_table[seed_month], treatment, month_rng(seed, seed_month))
    save_atomic(df, chunk_path(seed_month))


# ----------------------------------------------------------------
# 5. Combine monthly chunks (drop cross-month duplicates and current treatment authors)
# ----------------------------------------------------------------
def combine(quota_table, seed):
    chunks = sorted(CHUNK_DIR.glob("chunk_RS_*.parquet"))
    if not chunks:
        print(f"No chunks in {CHUNK_DIR}; nothing to combine.")
        return

    have = {CHUNK_RE.search(s.name).group(1) for s in chunks}
    missing = [ym for ym in quota_table if ym not in have]
    if missing:
        print(
            f"WARNING: {len(missing)} required month(s) have no chunk yet; the pool will be "
            f"short by their quotas. e.g. {missing[:8]}{'...' if len(missing) > 8 else ''}"
        )

    combined = pd.concat([pd.read_parquet(s) for s in chunks], ignore_index=True)
    n_before = len(combined)
    combined = (
        combined.sample(frac=1, random_state=seed)          # shuffle so the kept dupe is random
        .drop_duplicates("author", keep="first")
        .sort_values(["seed_month", "author"])
        .reset_index(drop=True)
    )
    n_after_dedup = len(combined)

    # re-check against the current treatment list (it can grow after months were drawn)
    treatment = load_treatment_authors()
    combined = combined[~combined["author"].isin(treatment)].reset_index(drop=True)
    n_final = len(combined)
    save_atomic(combined, COMBINED_PATH)

    print(f"\nCombined {len(chunks)} chunk(s) -> {COMBINED_PATH}")
    print(
        f"  {n_before:,} rows -> {n_after_dedup:,} unique candidate authors "
        f"({n_before - n_after_dedup:,} cross-month duplicates dropped)"
    )
    if n_final != n_after_dedup:
        print(f"  Dropped {n_after_dedup - n_final:,} now-treatment author(s) -> {n_final:,} final")

    realized = combined["seed_month"].value_counts().to_dict()
    off = [
        (ym, quota_table[ym], realized.get(ym, 0))
        for ym in sorted(quota_table)
        if realized.get(ym, 0) != quota_table[ym]
    ]
    if off:
        total_short = sum(t - r for _, t, r in off)
        print(f"  {len(off)} month(s) off target ({total_short:,} authors short overall):")
        for ym, t, r in off[:8]:
            print(f"    {ym}: target {t}, got {r}")
        if len(off) > 8:
            print(f"    ... and {len(off) - 8} more")


# ----------------------------------------------------------------
# 6. Main
# ----------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="single RS_YYYY-MM.zst to process (name or path); omit to loop all")
    ap.add_argument("--combine-only", action="store_true", help="rebuild 1_candidate_pool.parquet from existing chunks and exit")
    ap.add_argument("--no-combine", action="store_true", help="process all months but skip the final combine")
    ap.add_argument("--seed", type=int, default=DEFAULT_SEED, help=f"RNG seed (default {DEFAULT_SEED})")
    ap.add_argument("--allow-missing-months", action="store_true", help="don't error when a required month's .zst is absent (local testing)")
    args = ap.parse_args()

    quota_table = load_quota_table()

    if args.combine_only:
        combine(quota_table, args.seed)
        return

    treatment = load_treatment_authors()

    # single-file mode: Slurm array shape, one month, no combine
    if args.file:
        p = Path(args.file)
        if not p.is_absolute() and not p.exists():
            p = SUBMISSIONS_DIR / p.name
        if not p.exists():
            raise SystemExit(f"File not found: {p}")
        run_one(p, quota_table, treatment, args.seed)
        return

    # loop mode: every month in the quota table
    required = sorted(quota_table)
    present = [ym for ym in required if (SUBMISSIONS_DIR / f"RS_{ym}.zst").exists()]
    absent  = [ym for ym in required if ym not in present]

    if absent and not args.allow_missing_months:
        raise SystemExit(
            f"{len(absent)} required month(s) missing from {SUBMISSIONS_DIR}:\n  "
            + ", ".join(absent[:12]) + ("..." if len(absent) > 12 else "")
            + "\nRe-run with --allow-missing-months to sample only the months present."
        )
    if absent:
        print(f"WARNING: skipping {len(absent)} missing month(s) (--allow-missing-months)")

    print(f"Processing {len(present)} month(s) from {SUBMISSIONS_DIR}")
    for ym in present:
        if chunk_path(ym).exists() and all_authors_path(ym).exists():
            print(f"[{ym}] chunk + all_authors exist, skipping")
            continue
        run_one(SUBMISSIONS_DIR / f"RS_{ym}.zst", quota_table, treatment, args.seed)

    if not args.no_combine:
        combine(quota_table, args.seed)


if __name__ == "__main__":
    main()
