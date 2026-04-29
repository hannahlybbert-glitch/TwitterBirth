# Author: Hannah Lybbert
# Created: 2026-04-10
# Updated: 2026-04-10
# Purpose: Merge matched placebo birth dates onto full post history and compute time-relative variables

import pandas as pd
from pathlib import Path

ROOT         = Path(__file__).resolve().parents[5]
INPUT_BIRTHS = ROOT / "Reddit/data/intermediate/placebo_births/matched_placebo_births.csv"
INPUT_POSTS  = ROOT / "Reddit/data/intermediate/cleaned_raw/matched_placebo_post_history_clean.csv"
OUTPUT       = ROOT / "Reddit/data/intermediate/births_and_posts/matched_placebo_births_posts.csv"

OUTPUT_COLS = ["id", "author", "subreddit", "created_utc", "title", "selftext",
               "url", "score", "num_comments", "over_18", "stickied", "locked", "permalink",
               "days_from", "birth_post", "date_birth", "date_birth_post", "treatment_author",
               "days_from_birth", "weeks_from_birth", "months_from_birth",
               "post", "full_18_pre", "one_year_pre", "full_18_post",
               "treated"]

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
births = pd.read_csv(INPUT_BIRTHS, parse_dates=["created_utc", "date_birth", "date_birth_post"])
posts  = pd.read_csv(INPUT_POSTS)

print(f"Birth posts loaded:  {len(births):,} ({births['author'].nunique():,} unique authors)")
print(f"Post history loaded: {len(posts):,} ({posts['author'].nunique():,} unique authors)")

# ----------------------------------------------------------------
# Convert post history created_utc from Unix timestamp to datetime
# ----------------------------------------------------------------
posts["created_utc"] = pd.to_datetime(posts["created_utc"], unit="s")

# ----------------------------------------------------------------
# Merge author-level birth metadata onto full post history
# (date_birth, date_birth_post, days_from, treatment_author are the
# same for every post by the same placebo author)
# ----------------------------------------------------------------
birth_meta = births[["author", "id", "days_from", "date_birth",
                      "date_birth_post", "treatment_author"]].rename(columns={"id": "birth_post_id"})

posts = posts.merge(birth_meta, on="author", how="inner")
print(f"After merging birth metadata: {len(posts):,} rows ({posts['author'].nunique():,} authors)")

# ----------------------------------------------------------------
# Flag birth_post == 1 where post id matches the birth post id
# ----------------------------------------------------------------
posts["birth_post"] = (posts["id"] == posts["birth_post_id"]).astype(int)
posts = posts.drop(columns="birth_post_id")

n_flagged  = (posts["birth_post"] == 1).sum()
n_authors_flagged = posts[posts["birth_post"] == 1]["author"].nunique()
n_missing  = births["author"].nunique() - n_authors_flagged
print(f"  Birth posts found in post history: {n_flagged:,} ({n_authors_flagged:,} authors)")
if n_missing > 0:
    print(f"  WARNING: {n_missing:,} authors have no birth post in post history")

# ----------------------------------------------------------------
# Time-relative-to-birth variables
# ----------------------------------------------------------------
posts["days_from_birth"]   = (posts["created_utc"] - posts["date_birth"]).dt.days
posts["weeks_from_birth"]  = posts["days_from_birth"] // 7
posts["months_from_birth"] = posts["days_from_birth"] // 30

# ----------------------------------------------------------------
# Post indicator: 1 if post is on or after placebo birth, 0 if before
# ----------------------------------------------------------------
posts["post"] = (posts["days_from_birth"] >= 0).astype(int)

# ----------------------------------------------------------------
# Sample restriction flags
# ----------------------------------------------------------------
author_min = posts.groupby("author")["months_from_birth"].min()
author_max = posts.groupby("author")["months_from_birth"].max()
posts["full_18_pre"]  = posts["author"].map(author_min <= -18).astype(int)
posts["one_year_pre"] = posts["author"].map(author_min <= -12).astype(int)
posts["full_18_post"] = posts["author"].map(author_max >= 18).astype(int)

# ----------------------------------------------------------------
# Treated flag
# ----------------------------------------------------------------
posts["treated"] = 0

# ----------------------------------------------------------------
# Sort and save
# ----------------------------------------------------------------
posts = posts.sort_values(["author", "created_utc"]).reset_index(drop=True)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)
posts[OUTPUT_COLS].to_csv(OUTPUT, index=False)

af = posts.groupby("author")[["full_18_pre", "full_18_post", "one_year_pre"]].first()
print(f"\nDone. Saved {len(posts):,} rows to {OUTPUT}")
print(f"  Unique authors:                {posts['author'].nunique():,}")
print(f"  Post-birth posts  (post == 1): {(posts['post'] == 1).sum():,}")
print(f"  Pre-birth posts   (post == 0): {(posts['post'] == 0).sum():,}")
print(f"  Authors full_18_pre:           {af['full_18_pre'].sum():,}")
print(f"  Authors full_18_post:          {af['full_18_post'].sum():,}")
print(f"  Authors one_year_pre:          {af['one_year_pre'].sum():,}")
