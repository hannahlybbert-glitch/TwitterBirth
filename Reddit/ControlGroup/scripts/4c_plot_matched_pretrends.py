# Author: Hannah Lybbert
# Created: 2026-09-30
# Updated: 2026-10-05
# Purpose: Plot mean monthly pre-birth volume (-18..-1) for treatment vs matched controls vs all candidates -> output/matching/<SPEC>_pretrends.png
# Controls are averaged over pairs (a control used 3 times counts 3 times); matched months are shaded.

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

    # Test-mode files go in a test/ subfolder
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
