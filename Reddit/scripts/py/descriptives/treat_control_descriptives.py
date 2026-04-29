# Author: Hannah Lybbert
# Created: 2026-04-10
# Updated: 2026-04-10
# Purpose: Check for treatment/control author overlap and plot pre/post total post distributions

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[4]
INPUT      = ROOT / "Reddit/data/final/treatment_control_births_posts.csv"
OUTPUT_DIR = ROOT / "Reddit/output/descriptives"

# ----------------------------------------------------------------
# Load
# ----------------------------------------------------------------
df = pd.read_csv(INPUT, low_memory=False)
print(f"Loaded {len(df):,} rows | {df['author'].nunique():,} unique authors")
print(f"  Treatment (treated==1): {df[df['treated']==1]['author'].nunique():,} authors")
print(f"  Control   (treated==0): {df[df['treated']==0]['author'].nunique():,} authors")

# ----------------------------------------------------------------
# Check for authors appearing in both treated==1 and treated==0
# ----------------------------------------------------------------
treat_authors   = set(df.loc[df["treated"] == 1, "author"])
control_authors = set(df.loc[df["treated"] == 0, "author"])
overlap         = treat_authors & control_authors

print(f"\n--- Author overlap check ---")
print(f"  Authors in treatment only: {len(treat_authors - control_authors):,}")
print(f"  Authors in control only:   {len(control_authors - treat_authors):,}")
print(f"  Authors in BOTH:           {len(overlap):,}")
if overlap:
    print(f"  Overlapping authors (first 10): {sorted(overlap)[:10]}")

# ----------------------------------------------------------------
# Pre/post total post counts per author
# ----------------------------------------------------------------
pre_counts  = df[df["post"] == 0].groupby("author")["id"].count().rename("pre_posts")
post_counts = df[df["post"] == 1].groupby("author")["id"].count().rename("post_posts")
author_counts = pd.concat([pre_counts, post_counts], axis=1).fillna(0).astype(int)

print(f"\n--- Total posts per author ---")
for col, label in [("pre_posts", "Pre-birth"), ("post_posts", "Post-birth")]:
    s = author_counts[col]
    print(f"  {label}: mean={s.mean():.1f}  median={s.median():.0f}  "
          f"p95={s.quantile(0.95):.0f}  max={s.max():,}")

# ----------------------------------------------------------------
# Plot: distribution of total posts per author — pre vs post
# Cap x-axis at 95th percentile across both periods for readability
# ----------------------------------------------------------------
cap  = int(max(author_counts["pre_posts"].quantile(0.95),
               author_counts["post_posts"].quantile(0.95)))
bins = range(0, cap + 2)

fig, ax = plt.subplots(figsize=(10, 5))
ax.hist(author_counts["pre_posts"].clip(upper=cap),  bins=bins,
        alpha=0.6, color="steelblue", label=f"Pre-birth  (n={len(pre_counts):,})")
ax.hist(author_counts["post_posts"].clip(upper=cap), bins=bins,
        alpha=0.6, color="coral",     label=f"Post-birth (n={len(post_counts):,})")

ax.axvline(author_counts["pre_posts"].median(),  color="steelblue", linestyle="--",
           linewidth=1, label=f"Pre median ({author_counts['pre_posts'].median():.0f})")
ax.axvline(author_counts["post_posts"].median(), color="coral",     linestyle="--",
           linewidth=1, label=f"Post median ({author_counts['post_posts'].median():.0f})")

ax.set_xlabel("Total Posts per Author")
ax.set_ylabel("Number of Authors")
ax.set_title(f"Distribution of Total Posts per Author — Pre vs Post Birth\n(x-axis capped at 95th pct = {cap})")
ax.legend()

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "pre_post_posts_dist.jpg", dpi=150)
plt.close()
print(f"\nSaved to {OUTPUT_DIR / 'pre_post_posts_dist.jpg'}")
