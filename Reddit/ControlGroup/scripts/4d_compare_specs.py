# Author: Hannah Lybbert
# Created: 2026-10-07
# Updated: 2026-10-07
# Purpose: Rank matching specs by balance on a common set of columns and list each spec's best and worst matched columns
#
# Score = mean |std_diff| after matching over EVAL_COLUMNS (same columns for every spec, matched on or not).

import argparse
import os
from pathlib import Path

import pandas as pd

from matching_specs import SPECS

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR   = Path(os.environ.get("CONTROLGROUP_DATA_DIR", ROOT / "Reddit/ControlGroup/data"))
OUTPUT_DIR = Path(os.environ.get("CONTROLGROUP_OUTPUT_DIR", ROOT / "Reddit/ControlGroup/output")) / "matching"

TEST = False    # True -> compare the test-mode files (same as --test)
TARGET = 0.1    # |std_diff| above this counts as unbalanced
N_SHOW = 5      # best / worst columns listed per spec

# Columns every spec is scored on: all pre-birth monthly volumes, full-window text length, account age, breadth
EVAL_COLUMNS = (
    [f"{p}{m}pre" for p in ["sub_", "com_", "sub_des_", "com_des_"] for m in range(18, 0, -1)]
    + ["com_median_body_chars", "sub_median_title_chars", "sub_median_selftext_chars"]
    + ["account_age_days", "sub_n_subreddits_pre", "com_n_subreddits_pre", "n_subreddits_all_pre"]
)


# ----------------------------------------------------------------
# 1. Load balance tables
# ----------------------------------------------------------------
def load_balance(test):
    folder = DATA_DIR / "4_matching" / ("test" if test else "")
    tag = "_test" if test else ""
    balance, pairs = {}, {}
    for spec in SPECS:
        bal_path = folder / f"{spec}_balance{tag}.csv"
        pairs_path = folder / f"{spec}_matched_pairs{tag}.parquet"
        if not bal_path.exists():
            continue
        bal = pd.read_csv(bal_path).drop_duplicates("feature")   # older 4b runs listed some text columns twice
        balance[spec] = bal.set_index("feature")["std_diff_matched"]
        if pairs_path.exists():
            pairs[spec] = pd.read_parquet(pairs_path)
    if not balance:
        raise SystemExit(f"No balance tables found in {folder}")
    return pd.DataFrame(balance), pairs


# ----------------------------------------------------------------
# 2. Score and rank specs
# ----------------------------------------------------------------
def summarize(std_diff, pairs):
    evals = std_diff.reindex(EVAL_COLUMNS).abs()
    rows = []
    for spec in std_diff.columns:
        col = evals[spec]
        row = {
            "spec": spec,
            "mean_abs_std_diff": col.mean(),
            "n_over_target": int((col > TARGET).sum()),
            "max_abs_std_diff": col.max(),
            "worst_column": col.idxmax(),
            "n_eval_missing": int(col.isna().sum()),
        }
        if spec in pairs:
            reuse = pairs[spec]["control_author"].value_counts()
            row.update(unique_controls=len(reuse), controls_at_cap=int((reuse >= SPECS[spec].get("max_control_reuse", 5)).sum()),
                       median_distance=pairs[spec]["match_distance"].median())
        rows.append(row)
    return pd.DataFrame(rows).sort_values(["mean_abs_std_diff", "n_over_target"]).reset_index(drop=True)


# ----------------------------------------------------------------
# 3. Main
# ----------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="Step 4d: compare matching specs.")
    parser.add_argument("--test", action="store_true", help="Compare the test-mode files.")
    test = TEST or parser.parse_args().test
    tag = "_test" if test else ""

    std_diff, pairs = load_balance(test)
    summary = summarize(std_diff, pairs)

    pd.set_option("display.width", 200, "display.max_columns", 20)
    print(f"Specs compared: {len(summary)} | scored on {len(EVAL_COLUMNS)} columns | target |std_diff| < {TARGET}\n")
    print(summary.round(3).to_string(index=False))
    best = summary.iloc[0]
    print(f"\nBest spec: {best['spec']} (mean |std_diff| {best['mean_abs_std_diff']:.3f}, "
          f"{best['n_over_target']} columns over {TARGET})")

    # Best and worst matched columns per spec
    abs_diff = std_diff.reindex(EVAL_COLUMNS).abs()
    for spec in summary["spec"]:
        col = abs_diff[spec].dropna().sort_values()
        print(f"\n{spec}")
        print("  strongest: " + ", ".join(f"{c} ({v:.3f})" for c, v in col.head(N_SHOW).items()))
        print("  weakest:   " + ", ".join(f"{c} ({v:.3f})" for c, v in col.tail(N_SHOW)[::-1].items()))

    out_dir = OUTPUT_DIR / ("test" if test else "")
    out_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out_dir / f"4d_spec_ranking{tag}.csv", index=False)
    std_diff.reindex(EVAL_COLUMNS)[summary["spec"]].to_csv(out_dir / f"4d_column_balance{tag}.csv")
    print(f"\nWrote {out_dir / f'4d_spec_ranking{tag}.csv'} and {out_dir / f'4d_column_balance{tag}.csv'}")


if __name__ == "__main__":
    main()
