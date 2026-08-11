# Author: Hannah Lybbert
# Created: 2026-05-07
# Updated: 2026-05-07
# Purpose: Compute year-share and day-of-week x hour-of-day distributions from treatment sample for control group matching

import os
import pandas as pd

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

# --- File paths ---
INPUT_DTA    = "data/final/user_analysis_sample.dta"
OUTPUT_DIR   = "ControlGroup/data/treatment_distributions"
YEAR_CSV      = f"{OUTPUT_DIR}/yearly_targets.csv"
DOW_HOD_CSV   = f"{OUTPUT_DIR}/hour_weights.csv"

# Day and hour label helpers
DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

def hour_label(h):
    if h == 0:
        return "12am"
    elif h < 12:
        return f"{h}am"
    elif h == 12:
        return "12pm"
    else:
        return f"{h - 12}pm"

# --- Load data ---
print("Loading data...")
df = pd.read_stata(INPUT_DTA, columns=["unique_id"])
print(f"  {len(df):,} observations loaded")

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Parse datetime from unique_id format: {user_id}_{YYYY-MM-DD}T{HH:MM:SS.mmmZ}
df["dt"] = pd.to_datetime(
    df["unique_id"].str.split("_", n=1).str[1],
    format="%Y-%m-%dT%H:%M:%S.%fZ",
    utc=True
)

# --- 1. Yearly share of observations ---
df["year"] = df["dt"].dt.year

year_counts = (
    df.groupby("year", sort=True)
    .size()
    .reset_index(name="count")
)
year_counts = year_counts[year_counts["year"].between(2012, 2018)].copy()
year_counts["share"] = year_counts["count"] / year_counts["count"].sum()

year_counts.to_csv(YEAR_CSV, index=False)
print(f"Year shares saved to {YEAR_CSV}  ({len(year_counts)} years)")

# --- 2. Day-of-week x hour-of-day distribution (168 bins) ---
df["dow"] = df["dt"].dt.dayofweek   # 0=Monday, 6=Sunday
df["hod"] = df["dt"].dt.hour        # 0–23

dow_hod_counts = (
    df.groupby(["dow", "hod"], sort=True)
    .size()
    .reset_index(name="count")
)
dow_hod_counts["dow_hod_label"] = dow_hod_counts.apply(
    lambda r: f"{DAY_NAMES[int(r['dow'])]}_{hour_label(int(r['hod']))}", axis=1
)
dow_hod_counts["share"] = dow_hod_counts["count"] / dow_hod_counts["count"].sum()

dow_hod_counts = dow_hod_counts[["dow", "hod", "dow_hod_label", "count", "share"]]

dow_hod_counts.to_csv(DOW_HOD_CSV, index=False)
print(f"DoW x HoD shares saved to {DOW_HOD_CSV}  ({len(dow_hod_counts)} bins)")
