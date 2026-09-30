# Author: Hannah Lybbert
# Created: 2026-09-18
# Updated: 2026-09-25
# Purpose: For each candidate author with a comments and/or submissions file from
#          step 2, assign a placebo birth date, then build the 18-month pre-birth
#          volume vectors (comment and submission counts per month,
#          months_from_birth -18..-1) plus the author-level features used for matching.
#
# Placebo birth (2026-09-25): each candidate draws a days_from value from the
# treatment distribution (days_from_dist_full.csv, written by
# scripts/py/descriptives/full_sample_descriptives.py), weighted by share. Same
# convention as the treatment side (build_analysis_ready_file.py):
#     date_birth_post = the step-1 seed post
#     date_birth      = date_birth_post - days_from
# The draw is seeded by (DRAW_SEED, crc32(author)), so each author's value is the
# same across array tasks and reruns. months_from_birth is RECOMPUTED here from
# created_utc relative to the placebo date_birth -- the months_from_birth stored in
# the step-2 per-author files is relative to the seed post and is ignored. Step 2
# pulled full lifetime history, so the shifted window is always covered.
#
# Author set: union of every author with a comments file OR a submissions file
# under per_author_candidates/*/*.parquet. Missing one type -> zero-fill that
# type's columns (not dropped -- e.g. an author who only ever posted, never
# commented, still needs to be in both outputs for matching against treated
# authors with the same pattern).
#
# Eligibility: earliest months_from_birth across BOTH types (whichever exist)
# must be <= -18. Authors who don't clear that are dropped entirely, from both
# outputs -- the 18-month pre-trend is non-negotiable, not something to flag and
# defer. No other drops: birth_after_cutoff is a flag only (these are candidates;
# restrictions wait until matching).
#
# The treatment side (scripts/py/volume/build_treatment_volume_matrix.py) builds the
# same columns with the same logic -- keep the two in sync.
#
# Parallelization: reuses the per_author_candidates/bNNN/ bucket folders from
# step 2. One task per bucket (64 total), same fetch/split/combine shape as
# steps 1 and 2.
#
# Input:  Reddit/ControlGroup/data/1_candidate_pool.parquet   (seed post: created_utc, subreddit)
#         Reddit/ControlGroup/data/per_author_candidates/bNNN/{author}_comments.parquet
#         Reddit/ControlGroup/data/per_author_candidates/bNNN/{author}_submissions.parquet
#         Reddit/data/descriptives/days_from_dist_full.csv  (days_from, n_birth_posts, share)
# Output: Reddit/ControlGroup/data/3_candidate_volume_chunks/{comments,submissions}_bNNN.parquet
#           per-bucket, resumable
#         Reddit/ControlGroup/data/3a_candidate_comment_volume.parquet
#         Reddit/ControlGroup/data/3b_candidate_submission_volume.parquet
#           the deliverables: one row per eligible author. Author-level columns
#           (identical in both files):
#             author, designated_subreddit (seed post's subreddit), date_birth_post,
#             date_birth, days_from, birth_after_cutoff, active_since (earliest observed
#             submission or comment -- NOT account creation), account_age_days
#             (date_birth_post - active_since), n_subreddits_all_life,
#             n_subreddits_all_pre (distinct subreddits across submissions+comments,
#             whole history / months -18..-1)
#           Type-specific columns (comments in 3a, submissions in 3b):
#             n_subreddits_life, n_subreddits_pre,
#             18pre..1pre (all activity), des_18pre..des_1pre (designated subreddit only)
#
# Usage (from this file's directory, Reddit/ControlGroup/scripts/):
#   python 3_build_monthly_activity_matrix.py            # loop every bucket, then combine
#   python 3_build_monthly_activity_matrix.py 5          # one bucket only (Slurm array shape); no combine
#   python 3_build_monthly_activity_matrix.py --combine-only   # rebuild 3a/3b from chunks
#   python 3_build_monthly_activity_matrix.py --no-combine     # process all buckets, skip combine
#
# Paths can be overridden:
#   CONTROLGROUP_DATA_DIR  (default: repo Reddit/ControlGroup/data)
#   DAYS_FROM_DIST_CSV     (default: repo Reddit/data/descriptives/days_from_dist_full.csv)

import argparse
import json
import os
import re
import time
import zlib
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("CONTROLGROUP_DATA_DIR", ROOT / "Reddit/ControlGroup/data"))
DAYS_FROM_DIST_CSV = Path(os.environ.get("DAYS_FROM_DIST_CSV", ROOT / "Reddit/data/descriptives/days_from_dist_full.csv"))

CANDIDATE_POOL_PARQUET = DATA_DIR / "1_candidate_pool.parquet"
PER_AUTHOR_DIR         = DATA_DIR / "per_author_candidates"
CHUNK_DIR              = DATA_DIR / "3_candidate_volume_chunks"

COMMENT_VOLUME_PATH    = DATA_DIR / "3a_candidate_comment_volume.parquet"
SUBMISSION_VOLUME_PATH = DATA_DIR / "3b_candidate_submission_volume.parquet"

N_BUCKETS = 64   # must match N_BUCKETS in 2a_fetch_candidate_comments.py / 2b_...
DRAW_SEED = 20260925

COMMENT_SUFFIX_RE    = re.compile(r"_comments\.parquet$")
SUBMISSION_SUFFIX_RE = re.compile(r"_submissions\.parquet$")

PRE_RANGE = list(range(-18, 0))        # months_from_birth -18..-1

# Same cutoff as build_analysis_ready_file.py. Flag only -- never dropped here.
BIRTH_CUTOFF = pd.Timestamp("2024-07-01")

AUTHOR_COLUMNS = [
    "author", "designated_subreddit", "date_birth_post", "date_birth", "days_from",
    "birth_after_cutoff", "active_since", "account_age_days",
    "n_subreddits_all_life", "n_subreddits_all_pre",
]
OUT_COLUMNS = (
    AUTHOR_COLUMNS + ["n_subreddits_life", "n_subreddits_pre"]
    + [f"{-m}pre" for m in PRE_RANGE] + [f"des_{-m}pre" for m in PRE_RANGE]
)


def month_label(m):
    return f"{-m}pre" if m < 0 else f"{m}post"


# Windows note: see 2a_fetch_candidate_comments.py -- same transient-lock retry.
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


def comment_chunk_path(b):
    return CHUNK_DIR / f"comments_b{b:03d}.parquet"


def submission_chunk_path(b):
    return CHUNK_DIR / f"submissions_b{b:03d}.parquet"


def bucket_marker(b):
    return CHUNK_DIR / f".done_b{b:03d}"


def stats_path(b):
    return CHUNK_DIR / f"stats_b{b:03d}.json"


# ----------------------------------------------------------------
# Placebo births. days_from is drawn per author from a generator seeded by the
# author's name, so the draw doesn't depend on which bucket/task/order ran it.
# ----------------------------------------------------------------
def load_days_from_dist():
    if not DAYS_FROM_DIST_CSV.exists():
        raise SystemExit(
            f"days_from distribution not found: {DAYS_FROM_DIST_CSV}\n"
            f"Run scripts/py/descriptives/full_sample_descriptives.py first, or set DAYS_FROM_DIST_CSV."
        )
    dist = pd.read_csv(DAYS_FROM_DIST_CSV)
    values = dist["days_from"].to_numpy(dtype=float)
    probs  = dist["share"].to_numpy(dtype=float)
    return values, probs / probs.sum()


def draw_days_from(author, values, probs):
    rng = np.random.default_rng([DRAW_SEED, zlib.crc32(author.encode("utf-8"))])
    return float(rng.choice(values, p=probs))


def placebo_births(authors):
    pool = pd.read_parquet(CANDIDATE_POOL_PARQUET, columns=["author", "created_utc", "subreddit"])
    pool = pool[pool["author"].isin(authors)].drop_duplicates(subset="author").set_index("author")
    values, probs = load_days_from_dist()

    seed_epoch = pool["created_utc"].astype("int64")
    days_from  = pd.Series([draw_days_from(a, values, probs) for a in pool.index], index=pool.index)
    birth_epoch = seed_epoch - (days_from * 86_400).round().astype("int64")

    return pd.DataFrame({
        "designated_subreddit": pool["subreddit"],
        "date_birth_post": pd.to_datetime(seed_epoch, unit="s"),
        "date_birth": pd.to_datetime(birth_epoch, unit="s"),
        "days_from": days_from,
        "birth_epoch": birth_epoch,
    })


# ----------------------------------------------------------------
# Feature helpers -- mirrored in scripts/py/volume/build_treatment_volume_matrix.py.
# Subreddit comparisons are case-insensitive.
# ----------------------------------------------------------------
def add_subreddit_flags(df, designated):
    df = df.copy()
    df["sub_lc"] = df["subreddit"].str.lower()
    df["is_des"] = (df["sub_lc"] == df["author"].map(designated.str.lower())).fillna(False).astype(bool)
    return df


def volume(df, authors, months, prefix=""):
    counts = (
        df[df["months_from_birth"].isin(months)]
        .groupby(["author", "months_from_birth"]).size().unstack(fill_value=0)
        .reindex(index=authors, columns=months, fill_value=0)
    )
    return pd.DataFrame({f"{prefix}{month_label(m)}": counts[m].to_numpy() for m in months}, index=authors)


def subreddit_pairs(df, pre_only=False):
    if pre_only:
        df = df[df["months_from_birth"].isin(PRE_RANGE)]
    return df[["author", "sub_lc"]].drop_duplicates()


def n_distinct(pairs, authors):
    return pairs.groupby("author")["sub_lc"].nunique().reindex(authors, fill_value=0).to_numpy()


def author_features(births, sub_df, com_df, authors):
    b = births.loc[authors]
    out = pd.DataFrame({"author": authors}, index=authors)
    out["designated_subreddit"] = b["designated_subreddit"]
    out["date_birth_post"]      = b["date_birth_post"]
    out["date_birth"]           = b["date_birth"]
    out["days_from"]            = b["days_from"]
    out["birth_after_cutoff"]   = (out["date_birth"] >= BIRTH_CUTOFF).astype(int)

    first = pd.concat(
        [sub_df.groupby("author")["created_utc"].min(), com_df.groupby("author")["created_utc"].min()], axis=1
    ).min(axis=1).reindex(authors)
    out["active_since"]     = pd.to_datetime(first, unit="s")
    out["account_age_days"] = (out["date_birth_post"] - out["active_since"]).dt.days

    out["n_subreddits_all_life"] = n_distinct(pd.concat([subreddit_pairs(sub_df), subreddit_pairs(com_df)]), authors)
    out["n_subreddits_all_pre"]  = n_distinct(
        pd.concat([subreddit_pairs(sub_df, pre_only=True), subreddit_pairs(com_df, pre_only=True)]), authors
    )
    return out[AUTHOR_COLUMNS]


def type_matrix(base, df, authors, months):
    out = base.copy()
    out["n_subreddits_life"] = n_distinct(subreddit_pairs(df), authors)
    out["n_subreddits_pre"]  = n_distinct(subreddit_pairs(df, pre_only=True), authors)
    out = pd.concat([out, volume(df, authors, months), volume(df[df["is_des"]], authors, months, "des_")], axis=1)
    return out.reset_index(drop=True)


# ----------------------------------------------------------------
# Read every per-author file of one type in a bucket into one long frame, with
# months_from_birth recomputed relative to the placebo birth.
# ----------------------------------------------------------------
def load_activity(files, birth_epoch):
    frames = []
    for author, path in files.items():
        df = pd.read_parquet(path, columns=["created_utc", "subreddit"])
        df["author"] = author
        frames.append(df)
    if not frames:
        return pd.DataFrame({"author": pd.Series(dtype="string"), "created_utc": pd.Series(dtype="int64"),
                             "subreddit": pd.Series(dtype="string"), "months_from_birth": pd.Series(dtype="int64")})
    df = pd.concat(frames, ignore_index=True)
    df = df[df["author"].isin(birth_epoch.index)].dropna(subset=["created_utc"])
    df["created_utc"] = df["created_utc"].astype("int64")
    df["months_from_birth"] = ((df["created_utc"] - df["author"].map(birth_epoch)) // 86_400) // 30
    return df


# ----------------------------------------------------------------
# One bucket folder: union of authors with a comments and/or submissions file,
# assign placebo births, drop anyone whose earliest activity (either type) is less
# than 18 months before their placebo birth, write the two per-bucket chunk files.
# ----------------------------------------------------------------
def write_bucket(b, comments_df, submissions_df, n_considered):
    save_atomic(comments_df, comment_chunk_path(b))
    save_atomic(submissions_df, submission_chunk_path(b))
    stats_path(b).write_text(json.dumps({"n_considered": n_considered, "n_eligible": len(comments_df)}))
    bucket_marker(b).touch()


def process_bucket(b):
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)
    bucket_dir = PER_AUTHOR_DIR / f"b{b:03d}"
    empty = pd.DataFrame(columns=OUT_COLUMNS)
    if not bucket_dir.exists():
        write_bucket(b, empty, empty, 0)
        return 0, 0

    comment_files    = {COMMENT_SUFFIX_RE.sub("", p.name): p for p in bucket_dir.glob("*_comments.parquet")}
    submission_files = {SUBMISSION_SUFFIX_RE.sub("", p.name): p for p in bucket_dir.glob("*_submissions.parquet")}
    considered = set(comment_files) | set(submission_files)

    births = placebo_births(considered)
    com_df = load_activity(comment_files, births["birth_epoch"])
    sub_df = load_activity(submission_files, births["birth_epoch"])

    earliest = pd.concat(
        [com_df.groupby("author")["months_from_birth"].min(), sub_df.groupby("author")["months_from_birth"].min()],
        axis=1,
    ).min(axis=1)
    authors = sorted(earliest[earliest <= -18].index)   # < 18 months of pre-birth history -> drop from both
    if not authors:
        write_bucket(b, empty, empty, len(considered))
        return 0, 0

    com_df = add_subreddit_flags(com_df[com_df["author"].isin(authors)], births["designated_subreddit"])
    sub_df = add_subreddit_flags(sub_df[sub_df["author"].isin(authors)], births["designated_subreddit"])

    base = author_features(births, sub_df, com_df, authors)
    comments_df    = type_matrix(base, com_df, authors, PRE_RANGE)[OUT_COLUMNS]
    submissions_df = type_matrix(base, sub_df, authors, PRE_RANGE)[OUT_COLUMNS]
    write_bucket(b, comments_df, submissions_df, len(considered))
    return len(comments_df), len(submissions_df)


def process_all():
    for b in range(N_BUCKETS):
        if bucket_marker(b).exists():
            print(f"[bucket {b:03d}] already built, skipping")
            continue
        n_c, n_s = process_bucket(b)
        print(f"[bucket {b:03d}] {n_c:,} eligible authors (comments), {n_s:,} (submissions)")


def combine():
    comment_chunks    = sorted(CHUNK_DIR.glob("comments_b*.parquet"))
    submission_chunks = sorted(CHUNK_DIR.glob("submissions_b*.parquet"))
    if not comment_chunks or not submission_chunks:
        print(f"No chunks in {CHUNK_DIR}; nothing to combine.")
        return

    comments = pd.concat([pd.read_parquet(c) for c in comment_chunks], ignore_index=True)
    comments = comments.sort_values("author").reset_index(drop=True)
    save_atomic(comments, COMMENT_VOLUME_PATH)

    submissions = pd.concat([pd.read_parquet(c) for c in submission_chunks], ignore_index=True)
    submissions = submissions.sort_values("author").reset_index(drop=True)
    save_atomic(submissions, SUBMISSION_VOLUME_PATH)

    print(f"Combined {len(comment_chunks)} bucket(s) -> {COMMENT_VOLUME_PATH} ({len(comments):,} authors)")
    print(f"Combined {len(submission_chunks)} bucket(s) -> {SUBMISSION_VOLUME_PATH} ({len(submissions):,} authors)")

    # Funnel: candidate pool (step 1) -> had step 2 data -> cleared 18mo pre-birth -> final
    n_considered = n_eligible = 0
    for sp in sorted(CHUNK_DIR.glob("stats_b*.json")):
        s = json.loads(sp.read_text())
        n_considered += s["n_considered"]
        n_eligible   += s["n_eligible"]

    n_pool = None
    if CANDIDATE_POOL_PARQUET.exists():
        n_pool = pd.read_parquet(CANDIDATE_POOL_PARQUET, columns=["author"])["author"].nunique()

    print("\n--- Funnel ---")
    if n_pool is not None:
        print(f"Candidate pool (step 1):                 {n_pool:,}")
        print(f"No step 2 data (never posted/commented): {n_pool - n_considered:,}")
    else:
        print(f"Candidate pool (step 1): not found at {CANDIDATE_POOL_PARQUET}, skipping that count")
    print(f"Dropped (< 18mo pre-birth history):      {n_considered - n_eligible:,}")
    print(f"Final eligible authors:                  {n_eligible:,}")
    print(f"  of which birth_after_cutoff == 1 (flag only, kept): {int(comments['birth_after_cutoff'].sum()):,}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("bucket", nargs="?", type=int, help="single bucket (0-63) to process (Slurm array shape); omit to loop all")
    ap.add_argument("--combine-only", action="store_true", help="rebuild 3a/3b from existing chunks and exit")
    ap.add_argument("--no-combine", action="store_true", help="process all buckets but skip the final combine")
    args = ap.parse_args()

    if args.combine_only:
        combine()
        return

    if args.bucket is not None:
        n_c, n_s = process_bucket(args.bucket)
        print(f"[bucket {args.bucket:03d}] {n_c:,} eligible authors (comments), {n_s:,} (submissions)")
        return

    process_all()
    if not args.no_combine:
        combine()


if __name__ == "__main__":
    main()
