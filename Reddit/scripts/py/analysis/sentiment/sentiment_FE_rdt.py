# Author: Hannah Lybbert
# Created: 2026-04-09
# Updated: 2026-04-09
# Purpose: Author FE event-study plots for VADER sentiment around birth — Reddit
# Requires: linearmodels (pip install linearmodels)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from linearmodels.panel import PanelOLS

ROOT        = Path(__file__).resolve().parents[5]
INPUT_10K   = ROOT / "Reddit/data/NLP/sentiment/vader_sentiment_10k.csv"
INPUT_FULL  = ROOT / "Reddit/data/NLP/sentiment/vader_sentiment_FULL.csv"
OUTPUT_DIR  = ROOT / "Reddit/output/analysis/NLP/sentiment"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------
# Toggle: set TEST = True to run on 10k sample, False for full run
# ----------------------------------------------------------------
TEST = False

INPUT_PATH  = INPUT_10K if TEST else INPUT_FULL
LABEL       = "10k"    if TEST else "FULL"

WINDOW_MIN = -18
WINDOW_MAX =  18
BASE_MONTH = -1   # omitted category, same as Stata

# ----------------------------------------------------------------
# Load and restrict to window
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH)
print(f"Loaded {len(df):,} rows | {df['author'].nunique():,} unique authors")

df_win = df[
    (df["months_from_birth"] >= WINDOW_MIN) &
    (df["months_from_birth"] <= WINDOW_MAX)
].copy()

# ----------------------------------------------------------------
# Month dummies — all months except base (-1)
# ----------------------------------------------------------------
dummy_months = [m for m in range(WINDOW_MIN, WINDOW_MAX + 1) if m != BASE_MONTH]
for m in dummy_months:
    df_win[f"m_{m}"] = (df_win["months_from_birth"] == m).astype(float)

dummy_cols = [f"m_{m}" for m in dummy_months]

# Set panel index: (author, obs) — obs is a numeric integer unique per post
df_win["obs"] = range(len(df_win))
df_win = df_win.set_index(["author", "obs"])

n_authors = df_win.index.get_level_values("author").nunique()
print(f"Window sample: {len(df_win):,} posts | {n_authors:,} authors")
print(f"Base month: {BASE_MONTH}")

# ----------------------------------------------------------------
# Helper: run PanelOLS with entity FE, return betas + 95% CIs
# ----------------------------------------------------------------
def run_fe(df_panel, outcome):
    mask   = df_panel[outcome].notna()
    y      = df_panel.loc[mask, outcome]
    X      = df_panel.loc[mask, dummy_cols]
    model  = PanelOLS(y, X, entity_effects=True)
    result = model.fit(cov_type="clustered", cluster_entity=True)

    coefs = pd.DataFrame({
        "month":    dummy_months,
        "beta":     result.params.values,
        "ci_lower": result.conf_int()["lower"].values,
        "ci_upper": result.conf_int()["upper"].values,
    })
    # Insert base month at beta = 0
    base_row = pd.DataFrame({"month": [BASE_MONTH], "beta": [0.0],
                              "ci_lower": [0.0], "ci_upper": [0.0]})
    coefs = pd.concat([coefs, base_row], ignore_index=True).sort_values("month").reset_index(drop=True)
    return coefs

# ----------------------------------------------------------------
# Figure: FE event-study — pos, neg, neu, compound (2x2 panel)
# ----------------------------------------------------------------
plot_specs = [
    ("pos",      "Estimated Effect on Positivity",  "steelblue",    (0, 0)),
    ("neg",      "Estimated Effect on Negativity",  "firebrick",    (0, 1)),
    ("neu",      "Estimated Effect on Neutrality",  "gray",         (1, 0)),
    ("compound", "Estimated Effect on Compound",    "mediumpurple", (1, 1)),
]

fig, axes = plt.subplots(2, 2, figsize=(14, 9))

for outcome, ylabel, color, (r, c) in plot_specs:
    print(f"  Estimating FE model for: {outcome}")
    coefs = run_fe(df_win, outcome)
    ax    = axes[r, c]

    ax.errorbar(coefs["month"], coefs["beta"],
                yerr=[coefs["beta"] - coefs["ci_lower"], coefs["ci_upper"] - coefs["beta"]],
                color=color, linewidth=1.5, capsize=3, elinewidth=0.8, capthick=0.8)
    ax.axvline(0,          color="black", linestyle="--", linewidth=1)
    ax.axhline(0,          color="black", linestyle="--", linewidth=1)
    ax.scatter(BASE_MONTH, 0, color="black", marker="D", s=30, zorder=5, label=f"Base month ({BASE_MONTH})")
    ax.set_xlabel("Months from Birth")
    ax.set_ylabel(ylabel)
    ax.set_title(f"FE Estimates: {outcome.capitalize()} Around Birth")
    ax.set_xlim(WINDOW_MIN, WINDOW_MAX)
    ax.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 3))
    ax.annotate(f"N = {n_authors:,} authors",
                xy=(0.02, 0.97), xycoords="axes fraction", fontsize=8, color="gray", va="top")
    ax.legend(fontsize=7, loc="upper right")

plt.suptitle(f"Author FE Estimates of Reddit Sentiment Around Birth — {LABEL} Sample",
             fontsize=13, fontweight="bold")
plt.tight_layout()
out_fe = OUTPUT_DIR / f"fe_sentiment_month_{LABEL}.jpg"
plt.savefig(out_fe, dpi=150)
plt.close()
print(f"\nSaved: {out_fe}")
