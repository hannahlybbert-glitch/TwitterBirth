# Author: Hannah Lybbert
# Created: 2026-05-07
# Updated: 2026-05-07
# Purpose: Build week_list.csv with per-week target N for control group seed tweet pull

import os
import pandas as pd

os.chdir("D:/TwitterBirth")

# --- File paths ---
INPUT_DIR     = "data/ControlGroup/treatment_distributions"
YEAR_CSV      = f"{INPUT_DIR}/yearly_targets.csv"
WEEK_LIST_CSV = f"{INPUT_DIR}/week_list.csv"

WEEK_START   = "2013-01-07"
WEEK_END     = "2018-12-31"
TOTAL_TARGET = 40_000

# --- Load yearly targets ---
year_counts = pd.read_csv(YEAR_CSV)
yearly_share_lookup = year_counts.set_index("year")["share"].to_dict()

# --- Build week list ---
weeks = pd.date_range(start=WEEK_START, end=WEEK_END, freq="W-MON")
week_df = pd.DataFrame({"week_start": weeks.strftime("%Y-%m-%d")})
week_df["year"] = weeks.year
week_df["target_n"] = week_df["year"].map(
    lambda y: round(yearly_share_lookup.get(y, 0) * TOTAL_TARGET / 52)
)

week_df.to_csv(WEEK_LIST_CSV, index=False)
print(f"Week list saved to {WEEK_LIST_CSV}  ({len(week_df)} weeks)")
