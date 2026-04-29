# Author: Hannah Lybbert
# Created: 2026-03-25
# Updated: 2026-03-25
# Purpose: Plot event study coefficients (beta_k + 95% CI) from TWFE regression

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[5]
INPUT_PATH = ROOT / "Reddit/data/intermediate/diff_n_diff/event_study_results.csv"
OUTPUT_DIR = ROOT / "Reddit/output/analysis/diff_n_diff"

WINDOW_MIN = -18
WINDOW_MAX =  18

# ----------------------------------------------------------------
# Load results
# ----------------------------------------------------------------
results = pd.read_csv(INPUT_PATH)
print(f"Loaded {len(results)} monthly coefficients")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------------------------------------------
# Plot: coefficients + 95% CI
# ----------------------------------------------------------------
fig, ax = plt.subplots(figsize=(12, 5))

ax.fill_between(results["month"], results["ci_low"], results["ci_hi"],
                alpha=0.2, color="steelblue", label="95% CI")
ax.plot(results["month"], results["beta"],
        color="steelblue", linewidth=1.5, label="β_k")
ax.scatter(results["month"], results["beta"],
           color="steelblue", s=20, zorder=3)

ax.axvline(0,   color="black", linestyle="--", linewidth=1, label="Birth")
ax.axhline(0.0, color="gray",  linestyle="-",  linewidth=0.8)

ax.set_xlabel("Months from Birth")
ax.set_ylabel("Effect on Post Count (vs. control, ref = month −1)")
ax.set_title("Event Study: Effect of Birth on Reddit Posting Volume")
ax.set_xlim(WINDOW_MIN, WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 2))
ax.legend(loc="lower left")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "event_study_volume.jpg", dpi=150)
plt.close()
print(f"Saved to {OUTPUT_DIR / 'event_study_volume.jpg'}")
