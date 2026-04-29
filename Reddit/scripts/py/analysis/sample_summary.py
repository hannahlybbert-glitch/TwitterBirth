# Author: Hannah Lybbert
# Created: 2026-03-26
# Updated: 2026-03-26
# Purpose: Show sample size breakdown for treatment group as filters are applied

import pandas as pd
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[4]
INPUT_PATH = ROOT / "Reddit/data/final/births_and_posts_22k.csv"
OUTPUT_DIR = ROOT / "Reddit/output/analysis"
OUTPUT     = OUTPUT_DIR / "sample_summary.csv"

# ----------------------------------------------------------------
# Load — one row per author for flag checks
# ----------------------------------------------------------------
df      = pd.read_csv(INPUT_PATH, low_memory=False)
authors = df.drop_duplicates("author").set_index("author")

n_total = len(authors)

def n(mask):
    return mask.sum()

def pct(mask):
    return 100 * mask.sum() / n_total

rows = []

def add_row(label, mask):
    count = n(mask)
    rows.append({"Sample restriction": label, "N authors": count, "% of total": round(pct(mask), 1)})

# ----------------------------------------------------------------
# Build masks
# ----------------------------------------------------------------
pre12  = authors["one_year_pre"] == 1
pre18  = authors["full_18_pre"]  == 1
female = authors["female"] == 1
male   = authors["female"] == 0
ambig  = authors["female"] == -99

add_row("All authors (births_and_posts_22k)",  pd.Series(True, index=authors.index))
add_row("≥12 months pre-birth (one_year_pre)", pre12)
add_row("≥18 months pre-birth (full_18_pre)",  pre18)
add_row("  └ female",                          pre18 & female)
add_row("  └ male",                            pre18 & male)
add_row("  └ gender ambiguous",                pre18 & ambig)

# ----------------------------------------------------------------
# Print
# ----------------------------------------------------------------
summary = pd.DataFrame(rows)
col_w   = max(len(s) for s in summary["Sample restriction"]) + 2

print(f"\n{'Sample restriction':<{col_w}} {'N authors':>10}  {'% of total':>10}")
print("-" * (col_w + 24))
for _, row in summary.iterrows():
    print(f"{row['Sample restriction']:<{col_w}} {row['N authors']:>10,}  {row['% of total']:>9.1f}%")

# ----------------------------------------------------------------
# Save
# ----------------------------------------------------------------
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
summary.to_csv(OUTPUT, index=False)
print(f"\nSaved to {OUTPUT}")
