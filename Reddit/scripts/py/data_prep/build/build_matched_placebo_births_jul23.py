# Author: Hannah Lybbert
# Created: 2026-04-13
# Updated: 2026-04-13
# Purpose: Compute date_birth for matched placebo authors by assigning days_from from their matched treatment author's birth post

import pandas as pd
from pathlib import Path

ROOT            = Path(__file__).resolve().parents[5]
INPUT_TREATMENT = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"
INPUT_MATCHED   = ROOT / "Reddit/data/intermediate/cleaned_raw/matched_authors_clean.csv"
INPUT_BIRTHS    = ROOT / "Reddit/data/intermediate/cleaned_raw/matched_placebo_birth_posts_clean.csv"
OUTPUT          = ROOT / "Reddit/data/intermediate/placebo_births/matched_placebo_births.csv"

# ----------------------------------------------------------------
# Load treatment birth posts — one row per treatment author
# Use this to get each treatment author's days_from
# ----------------------------------------------------------------
treat = pd.read_csv(INPUT_TREATMENT, usecols=["author", "days_from", "birth_post"])
treat = treat[treat["birth_post"] == 1][["author", "days_from"]].rename(columns={"author": "treatment_author"})
treat = treat.drop_duplicates(subset="treatment_author")
print(f"Treatment birth posts loaded: {len(treat):,} unique treatment authors")

# ----------------------------------------------------------------
# Load matched authors and merge in treatment author's days_from
# ----------------------------------------------------------------
matched = pd.read_csv(INPUT_MATCHED)
print(f"Matched authors loaded:       {len(matched):,}")

matched = matched.merge(treat, on="treatment_author", how="inner")
print(f"  After joining days_from:    {len(matched):,} pairs with days_from")

# ----------------------------------------------------------------
# Load placebo birth posts
# ----------------------------------------------------------------
births = pd.read_csv(INPUT_BIRTHS)
print(f"Placebo birth posts loaded:   {len(births):,} ({births['author'].nunique():,} unique authors)")

# ----------------------------------------------------------------
# Merge birth posts with matched_authors on placebo_author == author
# Brings in days_from (from treatment) and treatment_author for each placebo birth post
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
# Drop authors whose days_from is outside [-28, 28]
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
# Drop authors whose estimated date_birth is after June 30, 2023
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
