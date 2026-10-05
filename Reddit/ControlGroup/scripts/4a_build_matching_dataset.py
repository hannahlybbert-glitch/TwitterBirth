# Author: Hannah Lybbert
# Created: 2026-09-25
# Updated: 2026-09-30
# Purpose: Step 4a of the Reddit control-group pipeline. Stack treatment and candidate
#          authors into one author-level matching dataset.
#
# For each group, the submission and comment files are joined on author: the
# author-level columns (identical in both files) are kept once, and the
# type-specific columns get a sub_ / com_ prefix. Then the two groups are stacked
# with treated = 1 / 0. Drops (see main()):
#   - candidates who are also treatment authors
#   - anyone with birth_after_cutoff == 1 (steps 3 / treatment volume only flag it;
#     every author in the matching sample needs the full 18-month post-birth runway)
# This file is the sample definition only -- values stay raw. Transforms (log1p),
# standardization and weights live in 4b.
#
# Input:  Reddit/data/volume/treatment_submission_volume.parquet   (build_treatment_volume_matrix.py)
#         Reddit/data/volume/treatment_comment_volume.parquet
#         Reddit/ControlGroup/data/3b_candidate_submission_volume.parquet  (3_build_monthly_activity_matrix.py)
#         Reddit/ControlGroup/data/3a_candidate_comment_volume.parquet
# Output: Reddit/ControlGroup/data/4a_matching_dataset.parquet
#         Reddit/ControlGroup/data/test/4a_matching_dataset_test.parquet
#           random TEST_N treatment + TEST_N candidate rows of the above (seeded), for
#           testing 4b without the full data (4b_match_authors.py --test)
#   one row per author. Columns:
#     author, treated, designated_subreddit, date_birth_post, date_birth, days_from,
#     birth_after_cutoff, active_since, account_age_days,
#     n_subreddits_all_life, n_subreddits_all_pre,
#     sub_n_subreddits_life, sub_n_subreddits_pre, sub_18pre..sub_1pre, sub_des_18pre..sub_des_1pre,
#     com_n_subreddits_life, com_n_subreddits_pre, com_18pre..com_1pre, com_des_18pre..com_des_1pre,
#     then the treatment-only post-birth columns (sub_0post.., sub_des_0post.., com_0post..,
#     com_des_0post..), which are missing (NaN) for candidates.
#
# Usage (small -- fine on a login node), from this file's directory:
#   python 4a_build_matching_dataset.py
#
# Paths can be overridden:
#   CONTROLGROUP_DATA_DIR  (default: repo Reddit/ControlGroup/data)
#   VOLUME_DATA_DIR        (default: repo Reddit/data/volume)
#   TREATMENT_AUTHORS_CSV  (default: repo Reddit/data/final/treatment_authors.csv)

import os
import time
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR        = Path(os.environ.get("CONTROLGROUP_DATA_DIR", ROOT / "Reddit/ControlGroup/data"))
VOLUME_DATA_DIR = Path(os.environ.get("VOLUME_DATA_DIR", ROOT / "Reddit/data/volume"))
TREATMENT_AUTHORS_CSV = Path(os.environ.get("TREATMENT_AUTHORS_CSV", ROOT / "Reddit/data/final/treatment_authors.csv"))

TREATMENT_SUBMISSIONS = VOLUME_DATA_DIR / "treatment_submission_volume.parquet"
TREATMENT_COMMENTS    = VOLUME_DATA_DIR / "treatment_comment_volume.parquet"
CANDIDATE_SUBMISSIONS = DATA_DIR / "3b_candidate_submission_volume.parquet"
CANDIDATE_COMMENTS    = DATA_DIR / "3a_candidate_comment_volume.parquet"

OUTPUT_PATH = DATA_DIR / "4a_matching_dataset.parquet"
TEST_OUTPUT_PATH = DATA_DIR / "test" / "4a_matching_dataset_test.parquet"

TEST_N = 100              # authors per group in the test file
TEST_SEED = 20260930

AUTHOR_COLUMNS = [
    "author", "designated_subreddit", "date_birth_post", "date_birth", "days_from",
    "birth_after_cutoff", "active_since", "account_age_days",
    "n_subreddits_all_life", "n_subreddits_all_pre",
]


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


def read(path):
    if not path.exists():
        raise SystemExit(f"Input not found: {path}")
    return pd.read_parquet(path)


def read_treatment_authors():
    if not TREATMENT_AUTHORS_CSV.exists():
        raise SystemExit(f"Treatment authors file not found: {TREATMENT_AUTHORS_CSV}")
    return pd.read_csv(TREATMENT_AUTHORS_CSV, usecols=["author"])["author"].dropna()


# Author-level columns from the submission file, then the type-specific columns
# of each file with their sub_ / com_ prefix.
def join_types(sub, com, treated):
    if set(sub["author"]) != set(com["author"]):
        raise SystemExit("Submission and comment files have different author sets -- rebuild them together.")
    sub_specific = sub.drop(columns=AUTHOR_COLUMNS[1:]).set_index("author").add_prefix("sub_")
    com_specific = com.drop(columns=AUTHOR_COLUMNS[1:]).set_index("author").add_prefix("com_")
    out = sub[AUTHOR_COLUMNS].set_index("author").join(sub_specific).join(com_specific).reset_index()
    out.insert(1, "treated", treated)
    return out


def main():
    treatment = join_types(read(TREATMENT_SUBMISSIONS), read(TREATMENT_COMMENTS), treated=1)
    candidates = join_types(read(CANDIDATE_SUBMISSIONS), read(CANDIDATE_COMMENTS), treated=0)

    # Step 1 excluded treatment authors as of its draw; treatment_authors.csv was later
    # rebuilt with the June 2024 cutoff, so a few candidates are now treatment authors.
    # They're real birth-post authors -- keep them as treated only.
    # Check against the full treatment list too, not just the eligible treatment
    # authors above -- a new parent who failed the treatment-side 18mo check still
    # can't be a control.
    treatment_list = set(read_treatment_authors()) | set(treatment["author"])
    overlap = treatment_list & set(candidates["author"])
    if overlap:
        candidates = candidates[~candidates["author"].isin(overlap)]
        print(f"Dropped {len(overlap):,} candidate(s) who are also treatment authors, e.g. {sorted(overlap)[:5]}")

    # Treatment should already be all 0 here (build_analysis_ready_file.py applies the
    # same cutoff) -- a nonzero treatment count means the two cutoffs disagree.
    for label, group in [("treatment", treatment), ("candidate", candidates)]:
        print(f"Dropping {int(group['birth_after_cutoff'].sum()):,} {label} author(s) with birth_after_cutoff == 1")
    treatment  = treatment[treatment["birth_after_cutoff"] == 0]
    candidates = candidates[candidates["birth_after_cutoff"] == 0]

    # Candidate columns first so the pre-birth block leads; treatment-only post
    # columns land at the end (NaN for candidates).
    columns = list(candidates.columns) + [c for c in treatment.columns if c not in candidates.columns]
    df = pd.concat([treatment, candidates], ignore_index=True)[columns]
    save_atomic(df, OUTPUT_PATH)

    print(f"Treatment authors: {len(treatment):,}")
    print(f"Candidate authors: {len(candidates):,}")
    print(f"Wrote {len(df):,} rows x {df.shape[1]} columns -> {OUTPUT_PATH}")

    test = pd.concat(
        [g.sample(n=min(TEST_N, len(g)), random_state=TEST_SEED) for g in (df[df["treated"] == 1], df[df["treated"] == 0])],
        ignore_index=True,
    )
    save_atomic(test, TEST_OUTPUT_PATH)
    print(f"Wrote test sample ({(test['treated'] == 1).sum()} treatment + {(test['treated'] == 0).sum()} candidate) -> {TEST_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
