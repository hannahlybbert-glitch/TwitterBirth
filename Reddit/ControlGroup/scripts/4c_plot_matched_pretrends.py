# Author: Hannah Lybbert
# Created: 2026-09-30
# Updated: 2026-10-02 (named matching specs)
# Purpose: Step 4c of the Reddit control-group pipeline. Visual check of 4b's match:
#          average monthly volume, months -18..-1 before (placebo) birth, for
#          treatment authors vs their matched controls, with the full candidate pool
#          for reference. Good matching = the treatment and matched-control lines
#          overlap; the all-candidates line shows where controls started. The months
#          the spec matched on are shaded; all 18 are always plotted.
#
# Matched controls are averaged over pairs, so a control used 3 times counts 3
# times -- the same weighting the balance table in 4b uses. Treatment = matched
# treatment authors only. No zero-activity exclusion (unlike
# plot_candidate_volume_trends.py): the lines must cover the same authors 4b matched.
#
# Input:  Reddit/ControlGroup/data/4a_matching_dataset.parquet
#         Reddit/ControlGroup/data/4_matching/<SPEC>_matched_pairs.parquet
# Output: Reddit/ControlGroup/output/matching/<SPEC>_pretrends.png
#         (test mode: same files with a _test suffix, each in a test/ subfolder)
#           2x2 panels: submissions, comments, designated-subreddit submissions,
#           designated-subreddit comments. Mean +/- 95% CI.
#
# Usage (from this file's directory):
#   python 4c_plot_matched_pretrends.py --spec PRE10           # full data (or TEST = True below)
#   python 4c_plot_matched_pretrends.py --spec PRE10 --test    # test sample
#
# Paths can be overridden:
#   CONTROLGROUP_DATA_DIR    (default: repo Reddit/ControlGroup/data)
#   CONTROLGROUP_OUTPUT_DIR  (default: repo Reddit/ControlGroup/output)

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")   # no display on the cluster
import matplotlib.pyplot as plt

from matching_specs import SPECS, get_spec

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR   = Path(os.environ.get("CONTROLGROUP_DATA_DIR", ROOT / "Reddit/ControlGroup/data"))
OUTPUT_DIR = Path(os.environ.get("CONTROLGROUP_OUTPUT_DIR", ROOT / "Reddit/ControlGroup/output")) / "matching"

TEST = False   # True -> plot the test-mode files (same as --test)

MONTHS = list(range(-18, 0))

PANELS = [
    ("sub_",     "Submissions"),
    ("com_",     "Comments"),
    ("sub_des_", "Designated-Subreddit Submissions"),
    ("com_des_", "Designated-Subreddit Comments"),
]

LINES = [
    ("Treatment",        "darkorange", "-"),
    ("Matched controls", "steelblue",  "-"),
    ("All candidates",   "gray",       "--"),
]


def month_stats(df, prefix):
    cols = [f"{prefix}{-m}pre" for m in MONTHS]
    values = df[cols].to_numpy(dtype=float)
    mean = values.mean(axis=0)
    se = values.std(axis=0, ddof=1) / np.sqrt(len(values)) if len(values) > 1 else np.zeros(len(cols))
    return mean, 1.96 * se


def main():
    parser = argparse.ArgumentParser(description="Step 4c: plot matched pre-birth trends.")
    parser.add_argument("--spec", required=True, choices=list(SPECS), help="Matching spec (matching_specs.py).")
    parser.add_argument("--test", action="store_true", help="Plot the test-mode files.")
    args = parser.parse_args()
    test = TEST or args.test
    tag = "_test" if test else ""
    spec = get_spec(args.spec)
    matched_months = [m for months in spec["month_bins"] for m in months]

    # Test-mode files live in a test/ subfolder of the usual folder (and keep the _test suffix).
    sub = "test" if test else ""
    dataset_path = DATA_DIR / sub / f"4a_matching_dataset{tag}.parquet"
    pairs_path   = DATA_DIR / "4_matching" / sub / f"{spec['name']}_matched_pairs{tag}.parquet"
    out_dir      = OUTPUT_DIR / sub
    for path in (dataset_path, pairs_path):
        if not path.exists():
            raise SystemExit(f"Input not found: {path}")

    df = pd.read_parquet(dataset_path).set_index("author")
    pairs = pd.read_parquet(pairs_path)

    groups = {
        "Treatment":        df.loc[pairs["treatment_author"]],
        "Matched controls": df.loc[pairs["control_author"]],
        "All candidates":   df[df["treated"] == 0],
    }
    n_label = (f"N: {len(pairs):,} matched pairs ({pairs['control_author'].nunique():,} unique controls); "
               f"{len(groups['All candidates']):,} candidates")
    print(n_label)

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    for ax, (prefix, title) in zip(axes.flat, PANELS):
        ax.axvspan(min(matched_months) - 0.5, max(matched_months) + 0.5, color="gray", alpha=0.12,
                   label="Matched window")
        for label, color, style in LINES:
            mean, ci = month_stats(groups[label], prefix)
            ax.errorbar(MONTHS, mean, yerr=ci, label=label, color=color, linestyle=style,
                        linewidth=1.5, capsize=3, elinewidth=0.8, capthick=0.8)
        ax.set_title(title)
        ax.set_xlabel("Months Before Birth")
        ax.set_ylabel("Avg per Month")
        ax.set_xlim(-18.5, -0.5)
        ax.set_xticks(MONTHS)
        ax.tick_params(axis="x", labelsize=8)
    axes.flat[0].legend(fontsize=9)
    fig.suptitle(f"Pre-Birth Volume: Treatment vs Matched Controls -- spec: {spec['name']}"
                 f"{' (TEST)' if test else ''}\n{n_label}", fontsize=12)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{spec['name']}_pretrends{tag}.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
