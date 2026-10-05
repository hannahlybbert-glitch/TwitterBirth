# Author: Hannah Lybbert
# Created: 2026-09-30
# Updated: 2026-10-05
# Purpose: Match each treatment author to a candidate control by weighted nearest neighbor, per spec in matching_specs.py (--spec NAME)
#
# Adapted from Karthik's create_matched_pipeline_expanded.py (example_code/):
#   1. log1p counts, standardize on the treatment median/IQR, multiply by sqrt(weight)
#   2. In random (seeded) order, each treatment author gets the nearest candidate under the reuse cap
# Outputs (4_matching/): <SPEC>_matched_pairs.parquet, <SPEC>_balance.csv (target |std_diff| < 0.1), <SPEC>_spec.json

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
# Configuration (everything else is per-spec)
# ----------------------------------------------------------------
TEST = False                # True -> run on the 4a test sample (same as --test)
NEIGHBOR_K = 200            # neighbors fetched per treatment author; doubles if all are used up

ALL_PRE_MONTHS = range(-18, 0)   # monthly columns available in 4a

# Monthly volume groups -> column prefix (always log1p)
VOLUME_GROUPS = {
    "submissions":            "sub_",
    "comments":               "com_",
    "designated_submissions": "sub_des_",
    "designated_comments":    "com_des_",
}
# Other groups -> (columns, log1p?); breadth always covers -18..-1
OTHER_GROUPS = {
    "subreddit_breadth": (["sub_n_subreddits_pre", "com_n_subreddits_pre", "n_subreddits_all_pre"], True),
    "account_age":       (["account_age_days"], False),
    "days_from":         (["days_from"], False),
}

# In the balance table but not matched on (unmatched monthly columns are added per spec)
BALANCE_ONLY = ["sub_n_subreddits_life", "com_n_subreddits_life", "n_subreddits_all_life", "birth_year"]


# ----------------------------------------------------------------
# 1. Paths and spec setup
# ----------------------------------------------------------------
# Test-mode files go in a test/ subfolder
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


# Spec -> matching columns and weights. Multi-month bins are returned in `derived` for load() to sum.
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


# Monthly columns not matched on directly (balance table only)
def unmatched_monthly(features):
    cols = [f"{prefix}{-m}pre" for prefix in VOLUME_GROUPS.values() for m in ALL_PRE_MONTHS]
    return [c for c in cols if c not in features]


# ----------------------------------------------------------------
# 2. Load data
# ----------------------------------------------------------------
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
# 3. Distance space
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
# 4. Matching
# ----------------------------------------------------------------
# Nearest candidate under the reuse cap (re-queries with double k if all fetched are used up)
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
# 5. Diagnostics
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


# ----------------------------------------------------------------
# 6. Main
# ----------------------------------------------------------------
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
