# Author: Hannah Lybbert
# Created: 2026-09-18
# Purpose: Plot average pre-seed monthly volume (comments, submissions) for
#          eligible candidate authors from 3_build_monthly_activity_matrix.py.
#          Mirrors the style of scripts/py/analysis/volume/volume_analysis.py
#          (the main treatment-group volume plot).
#
# "No comments/submissions ever" = zero across all 18 pre-seed columns in that
# author's row (3a/3b already zero-fill missing months, so this reads directly
# off the volume matrix -- it does not check for activity outside the pre-seed
# window). Such authors are excluded from that type's average per Hannah,
# 2026-09-18, so a large block of structural non-users doesn't drag the mean down.
#
# Input:  Reddit/ControlGroup/data/3a_candidate_comment_volume.parquet
#         Reddit/ControlGroup/data/3b_candidate_submission_volume.parquet
# Output: Reddit/ControlGroup/output/3_volume_candidate_authors/candidate_comments.png
#         Reddit/ControlGroup/output/3_volume_candidate_authors/candidate_submissions.png
#
# Paths can be overridden:
#   CONTROLGROUP_DATA_DIR  (default: repo Reddit/ControlGroup/data)

import os
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT     = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("CONTROLGROUP_DATA_DIR", ROOT / "Reddit/ControlGroup/data"))
OUTPUT_DIR = ROOT / "Reddit/ControlGroup/output/3_volume_candidate_authors"

COMMENT_VOLUME_PATH    = DATA_DIR / "3a_candidate_comment_volume.parquet"
SUBMISSION_VOLUME_PATH = DATA_DIR / "3b_candidate_submission_volume.parquet"

MONTH_COLS = [f"{m}pre" for m in range(18, 0, -1)]   # "18pre", ..., "1pre"


def compute_stats(df):
    long = df.melt(id_vars="author", value_vars=MONTH_COLS, var_name="month_label", value_name="count")
    long["months_from_birth"] = -long["month_label"].str.replace("pre", "", regex=False).astype(int)
    stats = long.groupby("months_from_birth")["count"].agg(["mean", "std", "count"]).reset_index()
    stats["se"]       = stats["std"] / np.sqrt(stats["count"])
    stats["ci_lower"] = stats["mean"] - 1.96 * stats["se"]
    stats["ci_upper"] = stats["mean"] + 1.96 * stats["se"]
    return stats.sort_values("months_from_birth")


def plot_volume(path, label, color, out_name):
    df = pd.read_parquet(path)
    n_total = len(df)

    active = df[df[MONTH_COLS].sum(axis=1) > 0].copy()
    n_active = len(active)
    print(f"{label}: {n_active:,} of {n_total:,} eligible authors had any pre-seed {label.lower()}")

    stats = compute_stats(active)

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.errorbar(stats["months_from_birth"], stats["mean"],
                yerr=[stats["mean"] - stats["ci_lower"], stats["ci_upper"] - stats["mean"]],
                color=color, linewidth=1.5, capsize=3, elinewidth=0.8, capthick=0.8)
    ax.set_xlabel("Months Before Seed Post")
    ax.set_ylabel(f"Avg {label} per Month")
    ax.set_title(f"Average Candidate {label} Volume Pre-Seed Post")
    ax.set_xlim(-18, -1)
    ax.set_xticks(range(-18, 0, 1))
    ax.annotate(f"N = {n_active:,} authors", xy=(0.02, 0.97), xycoords="axes fraction",
                fontsize=9, color="gray", va="top")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / out_name, dpi=150)
    plt.close()
    print(f"Saved to {OUTPUT_DIR / out_name}")


plot_volume(COMMENT_VOLUME_PATH, "Comments", "steelblue", "candidate_comments.png")
plot_volume(SUBMISSION_VOLUME_PATH, "Submissions", "darkorange", "candidate_submissions.png")
