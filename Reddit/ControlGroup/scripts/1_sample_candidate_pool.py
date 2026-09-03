# Author: Hannah Lybbert
# Created: 2026-09-02
# Purpose: Pull 100,000 posts from unique authors not in our treatment author list Reddit/data/final/treatment_authors.csv
#          and save their author id, submission id, and data of submission into a 3X100,000 dataframe
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

# ======================================================================================
# IMPLEMENTATION
# ======================================================================================
# Step 1 of the Reddit control-group matching pipeline. Draw a calendar-month stratified
# random pool of ~100k candidate control authors from the monthly Reddit *submissions*
# dumps, with one "seed" submission recorded per author. Each month's quota is that
# month's share of treatment birth posts (date_birth_dist_full.csv, scaled to 100,000,
# floor of 10, round-half-up), so the pool's seed-date distribution matches the
# treatment sample's birth-date distribution. Nominal total = 100,019.
#
# Sampling is per-AUTHOR uniform, not per-post: within a month we collapse to distinct
# eligible authors, keep one uniformly-random submission each (reservoir sampling, k=1),
# then draw that month's quota of authors without replacement. Months are processed
# independently (embarrassingly parallel). The combine step concatenates the per-month
# shards and drops the handful of authors drawn in more than one month, so the final
# pool lands slightly under 100,019 -- expected: this is a deliberately large starting
# pool that later steps (18-month pre-history, matching) whittle down.
#
# Excluded from the pool: rows with no author / no id / no parseable created_utc, author
# in {[deleted], [removed], [unknown], AutoModerator}, and any author in
# treatment_authors.csv.
#
# Input:   Reddit/raw/submissions/RS_YYYY-MM.zst              (monthly NDJSON dumps)
#          Reddit/data/final/treatment_authors.csv            (author column -> exclude)
#          Reddit/data/descriptives/date_birth_dist_full.csv  (year_month, share_of_birth_posts)
#
# Output:  Reddit/ControlGroup/data/1_candidate_pool_shards/shard_RS_YYYY-MM.parquet
#            per-month, resumable; columns: author, id, created_utc, seed_month, subreddit
#          Reddit/ControlGroup/data/1_candidate_pool.parquet
#            the deliverable: one row per candidate author, same columns
#
# Usage (from this file's directory, Reddit/ControlGroup/scripts/):
#   python 1_sample_candidate_pool.py                 # loop every required month, then combine
#   python 1_sample_candidate_pool.py RS_2015-03.zst  # one month only (Slurm array shape); no combine
#   python 1_sample_candidate_pool.py --combine-only  # rebuild 1_candidate_pool.parquet from shards
#   python 1_sample_candidate_pool.py --allow-missing-months   # local testing with a partial archive
#
# Paths: the raw dumps sit at a different layout on the cluster, so the submissions dir /
#        treatment csv / birth-dist csv / output dir can each be overridden:
#          REDDIT_SUBMISSIONS_DIR   dir holding RS_YYYY-MM.zst   (default: repo Reddit/raw/submissions)
#          TREATMENT_AUTHORS_CSV    treatment_authors.csv        (default: repo Reddit/data/final/...)
#          BIRTH_DATE_DIST_CSV      date_birth_dist_full.csv      (default: repo Reddit/data/descriptives/...)
#          CONTROLGROUP_DATA_DIR    output dir                    (default: repo Reddit/ControlGroup/data)

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

SHARD_DIR     = DATA_DIR / "1_candidate_pool_shards"
COMBINED_PATH = DATA_DIR / "1_candidate_pool.parquet"

DEFAULT_SEED = 20260902
TARGET_N     = 100_000     # nominal pool size the monthly shares are scaled to
MIN_QUOTA    = 10          # months whose scaled share rounds below this are bumped up to it

MAX_WINDOW = 2 ** 31       # some dumps use zstd windows > the library default (2**27)
FNAME_RE   = re.compile(r"RS_(\d{4})-(\d{2})\.zst$")
SHARD_RE   = re.compile(r"shard_RS_(\d{4}-\d{2})\.parquet$")

# Authors that are never real people. [deleted]/[removed]/[unknown] are Reddit's
# own placeholders; AutoModerator is the site-wide bot. Kept deliberately small.
EXCLUDE_AUTHORS = {"[deleted]", "[removed]", "[unknown]", "AutoModerator"}

OUT_COLUMNS = ["author", "id", "created_utc", "seed_month", "subreddit"]


# ----------------------------------------------------------------
# Stream-decode a .zst NDJSON dump one record at a time (never hold a whole
# multi-GB month in memory). Same shape as the ProcessReddit profilers and
# data_prep/comments/pair_authors_comments.py.
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
# (confirmed on the 2012-12 dumps). Coerce instead of isinstance-checking.
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
# Per-month author quota: that month's share of treatment birth posts, scaled
# to TARGET_N, with a floor of MIN_QUOTA. Explicit round-half-up (Python's
# built-in round() is banker's rounding).
# ----------------------------------------------------------------
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
# One streaming pass over a month: collapse to distinct eligible authors,
# keeping one uniformly-random submission per author via reservoir sampling
# (Algorithm R, k=1), then draw `quota` authors without replacement. Returns a
# DataFrame of the drawn authors' seed submissions.
# ----------------------------------------------------------------
def process_file(path, seed_month, quota, treatment, rng):
    reservoir  = {}   # author -> [id, created_utc_epoch, subreddit]
    seen_count = {}   # author -> eligible rows seen so far this month
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
        if not author or author in EXCLUDE_AUTHORS or author in treatment:
            n_skip += 1
            continue

        sid = rec.get("id")
        created = to_epoch(rec.get("created_utc"))
        if sid is None or created is None:
            n_skip += 1
            continue

        c = seen_count.get(author, 0) + 1
        seen_count[author] = c
        # the c-th eligible row for this author replaces the stored one with
        # probability 1/c, so every one of the author's rows is equally likely
        # to end up as their seed submission.
        if c == 1 or rng.random() < 1.0 / c:
            reservoir[author] = [sid, created, rec.get("subreddit")]

    elapsed = time.time() - start
    n_eligible = len(reservoir)

    if n_eligible < quota:
        raise SystemExit(
            f"[{seed_month}] only {n_eligible:,} eligible authors but quota is {quota:,}; "
            f"cannot fill this stratum."
        )

    authors = np.array(list(reservoir.keys()), dtype=object)
    chosen = rng.choice(authors, size=quota, replace=False)

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
def save_atomic(df, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    df.to_parquet(tmp, index=False)
    tmp.replace(path)


def shard_path(seed_month):
    return SHARD_DIR / f"shard_RS_{seed_month}.parquet"


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
    save_atomic(df, shard_path(seed_month))


# ----------------------------------------------------------------
# Concatenate the per-month shards, drop authors drawn in more than one month
# (keep a random one, reproducibly via a seeded shuffle), and write the
# deliverable. Reports realized vs. target counts per month.
# ----------------------------------------------------------------
def combine(quota_table, seed):
    shards = sorted(SHARD_DIR.glob("shard_RS_*.parquet"))
    if not shards:
        print(f"No shards in {SHARD_DIR}; nothing to combine.")
        return

    have = {SHARD_RE.search(s.name).group(1) for s in shards}
    missing = [ym for ym in quota_table if ym not in have]
    if missing:
        print(
            f"WARNING: {len(missing)} required month(s) have no shard yet; the pool will be "
            f"short by their quotas. e.g. {missing[:8]}{'...' if len(missing) > 8 else ''}"
        )

    combined = pd.concat([pd.read_parquet(s) for s in shards], ignore_index=True)
    n_before = len(combined)
    combined = (
        combined.sample(frac=1, random_state=seed)          # shuffle so the kept dupe is random
        .drop_duplicates("author", keep="first")
        .sort_values(["seed_month", "author"])
        .reset_index(drop=True)
    )
    n_after = len(combined)
    save_atomic(combined, COMBINED_PATH)

    print(f"\nCombined {len(shards)} shard(s) -> {COMBINED_PATH}")
    print(
        f"  {n_before:,} rows -> {n_after:,} unique candidate authors "
        f"({n_before - n_after:,} cross-month duplicates dropped)"
    )

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
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", nargs="?", help="single RS_YYYY-MM.zst to process (name or path); omit to loop all")
    ap.add_argument("--combine-only", action="store_true", help="rebuild 1_candidate_pool.parquet from existing shards and exit")
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
        if shard_path(ym).exists():
            print(f"[{ym}] shard exists, skipping")
            continue
        run_one(SUBMISSIONS_DIR / f"RS_{ym}.zst", quota_table, treatment, args.seed)

    if not args.no_combine:
        combine(quota_table, args.seed)


if __name__ == "__main__":
    main()
