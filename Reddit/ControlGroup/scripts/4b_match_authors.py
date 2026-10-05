# Author: Hannah Lybbert
# Created: 2026-09-30
# Updated: 2026-10-02 (named matching specs)
# Purpose: Step 4b of the Reddit control-group pipeline. Match each treatment author
#          to a candidate control by weighted nearest neighbor on pre-birth features.
#
# Algorithm adapted from Karthik's create_matched_pipeline_expanded.py
# (example_code/; docs/REDDIT_MATCHING_PIPELINE.md section 4.4), fast stage only --
# 4a replaces his feature-building stage:
#   1. log1p the count columns (monthly volumes, subreddit counts).
#   2. Standardize every feature on the TREATMENT side's robust center/scale
#      (median, IQR / 1.349; falls back to SD, then 1).
#   3. Multiply each feature by sqrt(weight) -> Euclidean distance = weighted distance.
#   4. Shuffle treatment authors (seeded); for each, take the nearest candidate
#      (cKDTree) that hasn't hit max_control_reuse and is within max_match_distance.
#      No match -> left unmatched.
# Differences from Karthik's version: no blocking, no attachment score, no
# attachment/directional calipers; with replacement (reuse cap) is the only mode.
#
# Specs (2026-10-02): which months, how they're binned, the group weights, reuse cap,
# caliper and seed all come from a named spec in matching_specs.py (--spec NAME).
# Every output is named after the spec so past matching methods stay side by side.
#
# Weights: each feature group gets a share of the total weight (shares sum to 1),
# split evenly across the group's columns. Because the weights sum to 1,
# match_distance reads as a typical standardized gap per feature (e.g. 0.5 = about
# half a treatment-SD apart on average), whatever the number of features.
#
# Input:  Reddit/ControlGroup/data/4a_matching_dataset.parquet        (4a_build_matching_dataset.py)
#         Reddit/ControlGroup/data/test/4a_matching_dataset_test.parquet   (TEST mode)
# Output: Reddit/ControlGroup/data/4_matching/<SPEC>_matched_pairs.parquet
#           one row per matched treatment author: treatment_author, control_author,
#           match_distance, treatment_date_birth, control_date_birth. A control can
#           appear in up to max_control_reuse rows.
#         Reddit/ControlGroup/data/4_matching/<SPEC>_balance.csv
#           per feature, in raw units: treated vs control means before matching (all
#           candidates) and after (matched pairs), std_diff = (t_mean - c_mean) /
#           treatment SD. Target |std_diff| < 0.1. Rows with group "balance_only" are
#           reported but not matched on -- including every monthly volume column
#           (-18..-1) the spec doesn't match on, to show balance outside the matched window.
#         Reddit/ControlGroup/data/4_matching/<SPEC>_spec.json
#           the resolved spec and feature weights used for this run.
#         TEST mode writes the same files with a _test suffix, in 4_matching/test/.
#
# Usage (from this file's directory):
#   python 4b_match_authors.py --spec PRE10           # full data (or TEST = True below)
#   python 4b_match_authors.py --spec PRE10 --test    # 4a test sample (100 + 100)
#
# Paths can be overridden:
#   CONTROLGROUP_DATA_DIR  (default: repo Reddit/ControlGroup/data)

import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

from matching_specs import SPECS, bin_label, get_spec

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("CONTROLGROUP_DATA_DIR", ROOT / "Reddit/ControlGroup/data"))
MATCHING_DIR = DATA_DIR / "4_matching"

# ----------------------------------------------------------------
# Configuration (everything else is per-spec -- see matching_specs.py)
# ----------------------------------------------------------------
TEST = False                # True -> run on the 4a test sample (same as --test)
NEIGHBOR_K = 200            # neighbors fetched per treatment author up front; doubles if all are used up

ALL_PRE_MONTHS = range(-18, 0)   # monthly columns available in 4a

# Monthly volume groups: group -> column prefix in 4a. Always log1p.
VOLUME_GROUPS = {
    "submissions":            "sub_",
    "comments":               "com_",
    "designated_submissions": "sub_des_",
    "designated_comments":    "com_des_",
}
# Other groups: group -> (columns, log1p?). Breadth counts span -18..-1 in every spec.
OTHER_GROUPS = {
    "subreddit_breadth": (["sub_n_subreddits_pre", "com_n_subreddits_pre", "n_subreddits_all_pre"], True),
    "account_age":       (["account_age_days"], False),
    "days_from":         (["days_from"], False),
}

# Reported in the balance table but not matched on. The _life counts include
# post-birth activity (outcome-contaminated); birth_year checks calendar alignment
# since there's no time blocking. Unmatched monthly columns are added per spec.
BALANCE_ONLY = ["sub_n_subreddits_life", "com_n_subreddits_life", "n_subreddits_all_life", "birth_year"]


# Test-mode files live in a test/ subfolder of the usual folder (and keep the _test suffix).
def io_paths(test, spec_name):
    tag = "_test" if test else ""
    data_dir = DATA_DIR / "test" if test else DATA_DIR
    out_dir  = MATCHING_DIR / "test" if test else MATCHING_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    return (
        data_dir / f"4a_matching_dataset{tag}.parquet",
        out_dir / f"{spec_name}_matched_pairs{tag}.parquet",
        out_dir / f"{spec_name}_balance{tag}.csv",
        out_dir / f"{spec_name}_spec{tag}.json",
    )


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


# Resolve a spec into matching columns. Volume groups get one column per month bin;
# multi-month bins are new columns (sum of their months), returned in `derived`
# (column -> source columns) for load() to build.
def feature_config(spec):
    shares = spec["weights"]
    unknown = set(shares) - set(VOLUME_GROUPS) - set(OTHER_GROUPS)
    if unknown:
        raise SystemExit(f"Unknown feature groups in spec '{spec['name']}': {sorted(unknown)}")
    total = sum(shares.values())
    if not np.isclose(total, 1.0):
        raise SystemExit(f"Spec '{spec['name']}' weights must sum to 1; got {total:.4f}")

    weights, log_cols, group_of, derived = {}, [], {}, {}
    for group, share in shares.items():
        if group in VOLUME_GROUPS:
            prefix = VOLUME_GROUPS[group]
            cols = []
            for months in spec["month_bins"]:
                col = f"{prefix}{bin_label(months)}"
                if len(months) > 1:
                    derived[col] = [f"{prefix}{-m}pre" for m in months]
                cols.append(col)
            use_log = True
        else:
            cols, use_log = OTHER_GROUPS[group]
        for col in cols:
            weights[col] = share / len(cols)
            group_of[col] = group
        if use_log:
            log_cols.extend(cols)
    return list(weights), weights, log_cols, group_of, derived


# Every monthly volume column not matched on directly (months outside the spec's
# window, and single months inside a coarse bin) -- balance-table only.
def unmatched_monthly(features):
    cols = [f"{prefix}{-m}pre" for prefix in VOLUME_GROUPS.values() for m in ALL_PRE_MONTHS]
    return [c for c in cols if c not in features]


def load(path, features, derived, balance_only):
    if not path.exists():
        raise SystemExit(f"Input not found: {path}")
    df = pd.read_parquet(path)
    df["birth_year"] = pd.to_datetime(df["date_birth"]).dt.year
    for col, sources in derived.items():
        df[col] = df[sources].sum(axis=1)

    missing = [c for c in features + balance_only if c not in df.columns]
    if missing:
        raise SystemExit(f"Columns missing from {path.name}: {missing}")
    has_nan = [c for c in features if df[c].isna().any()]
    if has_nan:
        raise SystemExit(f"Matching features with missing values: {has_nan}")

    treatment  = df[df["treated"] == 1].reset_index(drop=True)
    candidates = df[df["treated"] == 0].reset_index(drop=True)
    if set(treatment["author"]) & set(candidates["author"]):
        raise SystemExit("Some authors are both treatment and candidate -- rebuild 4a.")
    return treatment, candidates


# ----------------------------------------------------------------
# Distance space (Karthik: fit_robust_standardizer / weighted_standardized_matrix)
# ----------------------------------------------------------------
def transform(df, features, log_cols):
    X = df[features].astype(float)
    if (X[log_cols] < 0).any().any():
        raise SystemExit("Negative values in log1p columns.")
    X[log_cols] = np.log1p(X[log_cols])
    return X


def fit_robust_standardizer(X):
    center = X.median()
    iqr_scale = (X.quantile(0.75) - X.quantile(0.25)) / 1.349
    scale = iqr_scale.where(iqr_scale > 0, X.std())
    scale = scale.replace(0, 1.0).fillna(1.0)
    return center, scale


def weighted_points(X, center, scale, weights):
    w = np.sqrt(np.array([weights[c] for c in X.columns]))
    return ((X - center) / scale).to_numpy(dtype=float) * w


# ----------------------------------------------------------------
# Matching (Karthik: match_authors / nearest_unused)
# ----------------------------------------------------------------
# Nearest candidate under the reuse cap, walking neighbors in distance order;
# re-queries with double k if every fetched neighbor is used up.
def nearest_available(tree, point, uses, k, first, max_reuse, max_distance):
    n = tree.n
    d_row, j_row = first
    while True:
        for d, j in zip(d_row, j_row):
            if max_distance is not None and d > max_distance:
                return None, None
            if uses[j] < max_reuse:
                return int(j), float(d)
        if k >= n:
            return None, None
        k = min(k * 2, n)
        d_row, j_row = tree.query(point, k=k)


def match(treatment, candidates, features, weights, log_cols, spec):
    t_X = transform(treatment, features, log_cols)
    c_X = transform(candidates, features, log_cols)
    center, scale = fit_robust_standardizer(t_X)
    t_points = weighted_points(t_X, center, scale, weights)
    c_points = weighted_points(c_X, center, scale, weights)

    print(f"Building tree: {len(c_points):,} candidates x {c_points.shape[1]} features")
    tree = cKDTree(c_points)
    k = min(NEIGHBOR_K, len(c_points))
    dists, idx = tree.query(t_points, k=k, workers=-1)
    dists, idx = dists.reshape(len(t_points), k), idx.reshape(len(t_points), k)

    uses = np.zeros(len(c_points), dtype=int)
    t_i, c_j, dist = [], [], []
    order = np.random.default_rng(spec["seed"]).permutation(len(t_points))
    for i in order:
        j, d = nearest_available(tree, t_points[i], uses, k, (dists[i], idx[i]),
                                 spec["max_control_reuse"], spec["max_match_distance"])
        if j is None:
            continue
        uses[j] += 1
        t_i.append(i)
        c_j.append(j)
        dist.append(d)

    t_i, c_j = np.array(t_i, dtype=int), np.array(c_j, dtype=int)
    return pd.DataFrame({
        "treatment_author":    treatment["author"].to_numpy()[t_i],
        "control_author":      candidates["author"].to_numpy()[c_j],
        "match_distance":      np.array(dist, dtype=float),
        "treatment_date_birth": treatment["date_birth"].to_numpy()[t_i],
        "control_date_birth":   candidates["date_birth"].to_numpy()[c_j],
    })


# ----------------------------------------------------------------
# Diagnostics (Karthik: print_match_diagnostics / print_balance_table)
# ----------------------------------------------------------------
def balance_table(treatment, candidates, pairs, features, group_of, balance_only):
    cols = features + balance_only
    sd = treatment[cols].std().replace(0, 1.0).fillna(1.0)
    t_all, c_all = treatment[cols].mean(), candidates[cols].mean()
    t_m = treatment.set_index("author").loc[pairs["treatment_author"], cols].mean()
    c_m = candidates.set_index("author").loc[pairs["control_author"], cols].mean()
    return pd.DataFrame({
        "feature":              cols,
        "group":                [group_of.get(c, "balance_only") for c in cols],
        "treated_mean_all":     t_all.to_numpy(),
        "control_mean_all":     c_all.to_numpy(),
        "std_diff_before":      ((t_all - c_all) / sd).to_numpy(),
        "treated_mean_matched": t_m.to_numpy(),
        "control_mean_matched": c_m.to_numpy(),
        "std_diff_matched":     ((t_m - c_m) / sd).to_numpy(),
    })


def print_diagnostics(pairs, treatment, balance):
    n_t = len(treatment)
    print(f"\nMatched: {len(pairs):,} / {n_t:,} treatment authors ({n_t - len(pairs):,} unmatched)")
    if pairs.empty:
        return
    reuse = pairs["control_author"].value_counts()
    print(f"Unique controls: {len(reuse):,}")
    print("Controls by number of treatment authors matched:")
    print(reuse.value_counts().sort_index().rename_axis("times_used").to_string())

    print("\nmatch_distance (weighted std units):")
    for p in [0, 50, 75, 90, 95, 99, 100]:
        print(f"  p{p}: {pairs['match_distance'].quantile(p / 100):.3f}")

    matched = balance[balance["group"] != "balance_only"]
    print(f"\nMatched features with |std_diff| > 0.1: before {(matched['std_diff_before'].abs() > 0.1).sum()} "
          f"-> after {(matched['std_diff_matched'].abs() > 0.1).sum()} (of {len(matched)})")
    worst = balance.reindex(balance["std_diff_matched"].abs().sort_values(ascending=False).index).head(15)
    print("Worst 15 by |std_diff_matched|:")
    print(worst[["feature", "group", "treated_mean_matched", "control_mean_matched",
                 "std_diff_before", "std_diff_matched"]].to_string(index=False, float_format="%.3f"))


def main():
    parser = argparse.ArgumentParser(description="Step 4b: match treatment authors to candidate controls.")
    parser.add_argument("--spec", required=True, choices=list(SPECS), help="Matching spec (matching_specs.py).")
    parser.add_argument("--test", action="store_true", help="Run on the 4a test sample.")
    args = parser.parse_args()
    test = TEST or args.test
    spec = get_spec(args.spec)

    input_path, pairs_path, balance_path, spec_path = io_paths(test, spec["name"])
    features, weights, log_cols, group_of, derived = feature_config(spec)
    balance_only = unmatched_monthly(features) + BALANCE_ONLY
    print(f"{'TEST MODE -- ' if test else ''}Spec: {spec['name']} | Input: {input_path}")
    print(f"{len(features)} matching features; max control reuse {spec['max_control_reuse']}; "
          f"max distance {spec['max_match_distance']}; seed {spec['seed']}")

    treatment, candidates = load(input_path, features, derived, balance_only)
    print(f"Treatment: {len(treatment):,} | Candidates: {len(candidates):,}")

    pairs = match(treatment, candidates, features, weights, log_cols, spec)
    assert pairs["treatment_author"].is_unique, "treatment author matched twice"
    assert pairs["control_author"].value_counts().max() <= spec["max_control_reuse"], "reuse cap violated"

    balance = balance_table(treatment, candidates, pairs, features, group_of, balance_only)
    print_diagnostics(pairs, treatment, balance)

    save_atomic(pairs, pairs_path)
    balance.to_csv(balance_path, index=False)
    spec_path.write_text(json.dumps({**spec, "feature_weights": weights, "binned_columns": derived}, indent=2))
    print(f"\nWrote {len(pairs):,} pairs -> {pairs_path}")
    print(f"Wrote balance table -> {balance_path}")
    print(f"Wrote spec record -> {spec_path}")


if __name__ == "__main__":
    main()
