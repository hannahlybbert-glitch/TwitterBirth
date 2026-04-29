# Author:  Hannah Lybbert
# Created: 2026-04-14
# Updated: 2026-04-14
# Purpose: Print unique author counts overall, for full_18_pre==1, and after p99 post trim

import pandas as pd
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[4]
INPUT_PATH = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH, low_memory=False)

authors_all      = df["author"].nunique()
authors_full_18  = df.loc[df["full_18_pre"] == 1, "author"].nunique()

# ----------------------------------------------------------------
# p99 trim: drop authors who exceed the 99th percentile of
# posts per author-month in any month
# ----------------------------------------------------------------
posts_per_am = df.groupby(["author", "months_from_birth"]).size().rename("n_posts")
p99          = posts_per_am.quantile(0.99)
flagged      = posts_per_am[posts_per_am > p99].index.get_level_values("author").unique()
df_trimmed   = df.loc[~df["author"].isin(flagged)]

authors_trimmed     = df_trimmed["author"].nunique()
authors_trim_full18 = df_trimmed.loc[df_trimmed["full_18_pre"] == 1, "author"].nunique()

print(f"Unique authors (all):                        {authors_all:,}")
print(f"Unique authors (full_18_pre==1):             {authors_full_18:,}")
print(f"")
print(f"p99 posts/author-month threshold:            {p99:.0f}")
print(f"Authors dropped (exceed p99 in any month):  {len(flagged):,}")
print(f"")
print(f"Unique authors after p99 trim (all):         {authors_trimmed:,}")
print(f"Unique authors after p99 trim (full_18_pre): {authors_trim_full18:,}")
