# Author: Hannah Lybbert
# Created: 2026-09-22
# Updated: 2026-09-25
# Purpose: Build the treatment-side monthly volume matrix (18mo pre + 18mo post birth)
#          plus the author-level features used for matching, directly from
#          births_and_posts_FULL.csv and treatment_author_comments.parquet.
#          No per-author intermediate files -- treatment is small enough for a direct
#          groupby -> pivot.
#
# Eligibility: author needs (1) a cutoff-compliant date_birth (author universe is
#          anchored to the submissions file, not unioned with comments-only authors)
#          and (2) earliest activity across both sources <= -18 months from birth.
#
# The candidate side (ControlGroup/scripts/3_build_monthly_activity_matrix.py) builds
# the same columns with the same logic -- keep the two in sync.
#
# Input:
#   Reddit/data/final/births_and_posts_FULL.csv                          (submissions)
#   Reddit/data/intermediate/comments/treatment_author_comments.parquet  (comments)
# Output:
#   Reddit/data/volume/treatment_submission_volume.parquet
#   Reddit/data/volume/treatment_comment_volume.parquet
#   one row per eligible author. Author-level columns (identical in both files):
#     author, designated_subreddit (birth post's subreddit), date_birth_post, date_birth,
#     days_from, birth_after_cutoff, active_since (earliest observed submission or
#     comment -- NOT account creation), account_age_days (date_birth_post - active_since),
#     n_subreddits_all_life, n_subreddits_all_pre (distinct subreddits across
#     submissions+comments, whole history / months -18..-1)
#   Type-specific columns (submissions in one file, comments in the other):
#     n_subreddits_life, n_subreddits_pre,
#     18pre..1pre, 0post..17post           (all activity)
#     des_18pre..des_1pre, des_0post..des_17post   (designated subreddit only)
#
# Usage:
#   python build_treatment_volume_matrix.py
#
# Paths can be overridden:
#   BIRTHS_AND_POSTS_CSV, TREATMENT_COMMENTS_PARQUET, VOLUME_DATA_DIR

import os
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[4]

BIRTHS_AND_POSTS_CSV       = Path(os.environ.get("BIRTHS_AND_POSTS_CSV", ROOT / "Reddit/data/final/births_and_posts_FULL.csv"))
TREATMENT_COMMENTS_PARQUET = Path(os.environ.get("TREATMENT_COMMENTS_PARQUET", ROOT / "Reddit/data/intermediate/comments/treatment_author_comments.parquet"))
VOLUME_DATA_DIR             = Path(os.environ.get("VOLUME_DATA_DIR", ROOT / "Reddit/data/volume"))

SUBMISSION_VOLUME_PATH = VOLUME_DATA_DIR / "treatment_submission_volume.parquet"
COMMENT_VOLUME_PATH    = VOLUME_DATA_DIR / "treatment_comment_volume.parquet"

MONTH_RANGE = list(range(-18, 18))     # months_from_birth -18..17
PRE_RANGE   = list(range(-18, 0))      # months_from_birth -18..-1

# Same cutoff as build_analysis_ready_file.py. Flag only -- never dropped here.
BIRTH_CUTOFF = pd.Timestamp("2024-07-01")

AUTHOR_COLUMNS = [
    "author", "designated_subreddit", "date_birth_post", "date_birth", "days_from",
    "birth_after_cutoff", "active_since", "account_age_days",
    "n_subreddits_all_life", "n_subreddits_all_pre",
]


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


def to_epoch(ts):
    return (ts - pd.Timestamp("1970-01-01")) // pd.Timedelta(seconds=1)   # NaT -> NaN


def _clean_months(df):
    df = df.copy()
    df["months_from_birth"] = pd.to_numeric(df["months_from_birth"], errors="coerce")
    df = df.dropna(subset=["months_from_birth"])
    df["months_from_birth"] = df["months_from_birth"].astype(int)
    return df


# Submissions + the per-author birth info (designated subreddit = birth post's subreddit).
def load_submissions():
    if not BIRTHS_AND_POSTS_CSV.exists():
        raise SystemExit(f"Treatment submissions file not found: {BIRTHS_AND_POSTS_CSV}")
    df = pd.read_csv(
        BIRTHS_AND_POSTS_CSV,
        usecols=["author", "subreddit", "created_utc", "months_from_birth",
                 "birth_post", "days_from", "date_birth", "date_birth_post"],
    )
    df["created_utc"] = to_epoch(pd.to_datetime(df["created_utc"], format="mixed", errors="coerce"))

    births = df[df["birth_post"] == 1].drop_duplicates(subset="author").set_index("author")
    births = pd.DataFrame({
        "designated_subreddit": births["subreddit"],
        "date_birth_post": pd.to_datetime(births["date_birth_post"], format="mixed", errors="coerce"),
        "date_birth": pd.to_datetime(births["date_birth"], format="mixed", errors="coerce"),
        "days_from": births["days_from"].astype(float),
    })

    df = _clean_months(df[["author", "subreddit", "created_utc", "months_from_birth"]])
    print(f"Loaded {len(df):,} submissions ({df['author'].nunique():,} authors, "
          f"{len(births):,} birth posts) from {BIRTHS_AND_POSTS_CSV}")
    return df, births


def load_comments():
    if not TREATMENT_COMMENTS_PARQUET.exists():
        raise SystemExit(f"Treatment comments file not found: {TREATMENT_COMMENTS_PARQUET}")
    df = pd.read_parquet(TREATMENT_COMMENTS_PARQUET, columns=["author", "subreddit", "created_utc", "months_from_birth"])
    df["created_utc"] = pd.to_numeric(df["created_utc"], errors="coerce")
    df = _clean_months(df)
    print(f"Loaded {len(df):,} comments ({df['author'].nunique():,} authors) from {TREATMENT_COMMENTS_PARQUET}")
    return df


# Earliest activity per author across BOTH sources, restricted to the submissions
# author universe (see module docstring) so a comments-only author with no
# cutoff-compliant birth date can't sneak in.
def eligible_authors(sub_df, com_df, births):
    sub_min = sub_df.groupby("author")["months_from_birth"].min()
    com_min = com_df.groupby("author")["months_from_birth"].min()
    universe = sub_min.index.intersection(births.index)
    earliest = pd.concat([sub_min, com_min], axis=1).loc[universe].min(axis=1)  # skipna by default
    eligible = earliest[earliest <= -18]
    print(f"Eligible authors (earliest activity <= -18mo, of {len(universe):,} authors with a "
          f"cutoff-compliant birth date): {len(eligible):,}")
    return sorted(eligible.index)


# ----------------------------------------------------------------
# Feature helpers -- mirrored in ControlGroup/scripts/3_build_monthly_activity_matrix.py.
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


def main():
    sub_df, births = load_submissions()
    com_df = load_comments()

    authors = eligible_authors(sub_df, com_df, births)
    sub_df = add_subreddit_flags(sub_df[sub_df["author"].isin(authors)], births["designated_subreddit"])
    com_df = add_subreddit_flags(com_df[com_df["author"].isin(authors)], births["designated_subreddit"])

    base = author_features(births, sub_df, com_df, authors)
    print(f"  birth_after_cutoff == 1: {int(base['birth_after_cutoff'].sum()):,}")

    submissions_out = type_matrix(base, sub_df, authors, MONTH_RANGE)
    save_atomic(submissions_out, SUBMISSION_VOLUME_PATH)
    print(f"Wrote {len(submissions_out):,} authors -> {SUBMISSION_VOLUME_PATH}")

    comments_out = type_matrix(base, com_df, authors, MONTH_RANGE)
    save_atomic(comments_out, COMMENT_VOLUME_PATH)
    print(f"Wrote {len(comments_out):,} authors -> {COMMENT_VOLUME_PATH}")


if __name__ == "__main__":
    main()
