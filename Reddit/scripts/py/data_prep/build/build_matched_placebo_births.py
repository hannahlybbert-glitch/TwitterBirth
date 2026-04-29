# Author: Hannah Lybbert
# Created: 2026-04-10
# Updated: 2026-04-10
# Purpose: Compute date_birth for matched placebo authors from their birth post and days_from

import pandas as pd
from pathlib import Path

ROOT          = Path(__file__).resolve().parents[5]
INPUT_MATCHED = ROOT / "Reddit/data/intermediate/cleaned_raw/matched_authors_clean.csv"
INPUT_BIRTHS  = ROOT / "Reddit/data/intermediate/cleaned_raw/matched_placebo_birth_posts_clean.csv"
OUTPUT        = ROOT / "Reddit/data/intermediate/placebo_births/matched_placebo_births.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
matched = pd.read_csv(INPUT_MATCHED)
births  = pd.read_csv(INPUT_BIRTHS)

print(f"Matched authors loaded:  {len(matched):,}")
print(f"Birth posts loaded:      {len(births):,} ({births['author'].nunique():,} unique authors)")

# ----------------------------------------------------------------
# Rename days_from_birth → days_from (consistent with treatment pipeline)
# ----------------------------------------------------------------
matched = matched.rename(columns={"days_from_birth": "days_from"})

# ----------------------------------------------------------------
# Merge birth posts with matched_authors on placebo_author == author
# Brings in days_from and treatment_author for each placebo birth post
# ----------------------------------------------------------------
births = births.merge(
    matched[["placebo_author", "treatment_author", "days_from"]],
    left_on="author", right_on="placebo_author", how="inner"
).drop(columns="placebo_author")

print(f"After merging with matched_authors: {len(births):,} rows ({births['author'].nunique():,} unique placebo authors)")

# ----------------------------------------------------------------
# Check for duplicate placebo authors — each should have exactly one birth post
# ----------------------------------------------------------------
dup_authors = births[births.duplicated(subset="author", keep=False)]
if not dup_authors.empty:
    print(f"  WARNING: {dup_authors['author'].nunique():,} placebo authors have >1 birth post — keeping row with lowest abs(days_from)")
    births["_abs_days"] = births["days_from"].abs()
    births = (births.sort_values("_abs_days")
                    .drop_duplicates(subset="author", keep="first")
                    .drop(columns="_abs_days"))
else:
    print(f"  No duplicate placebo authors — all good")

# ----------------------------------------------------------------
# Drop authors whose days_from is outside [-28, 28] (mirrors treatment filter in extract_2_3M_births.py)
# ----------------------------------------------------------------
before = len(births)
births = births[births["days_from"].between(-28, 28)]
print(f"  Dropped {before - len(births):,} authors with days_from outside [-28, 28] ({len(births):,} remain)")

# ----------------------------------------------------------------
# Convert created_utc to datetime
# ----------------------------------------------------------------
births["created_utc"] = pd.to_datetime(births["created_utc"], unit="s")

# ----------------------------------------------------------------
# Compute date_birth and date_birth_post
# date_birth = created_utc of birth post - timedelta(days_from)
# (days_from > 0: post written after birth; < 0: before birth)
# ----------------------------------------------------------------
births["date_birth_post"] = births["created_utc"]
births["date_birth"]      = births["created_utc"] - pd.to_timedelta(births["days_from"], unit="D")

# ----------------------------------------------------------------
# Drop authors whose estimated date_birth is after June 30, 2024
# (post-cutoff births have incomplete post-birth histories)
# ----------------------------------------------------------------
before = len(births)
births = births[births["date_birth"] <= "2023-06-30"]
print(f"  Dropped {before - len(births):,} authors with date_birth after 2023-06-30 ({len(births):,} remain)")

# ----------------------------------------------------------------
# Flag all rows as birth_post == 1 (one birth post per author)
# ----------------------------------------------------------------
births["birth_post"] = 1

# ----------------------------------------------------------------
# Sort and save
# ----------------------------------------------------------------
births = births.sort_values("author").reset_index(drop=True)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
births.to_csv(OUTPUT, index=False)

print(f"\nDone. Saved {len(births):,} rows to {OUTPUT}")
print(f"  Unique placebo authors: {births['author'].nunique():,}")
print(f"  date_birth range:       {births['date_birth'].min()} — {births['date_birth'].max()}")
print(f"  days_from range:        {births['days_from'].min()} — {births['days_from'].max()}")
