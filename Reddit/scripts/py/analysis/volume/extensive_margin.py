# Author: Hannah Lybbert
# Created: 2026-03-20
# Updated: 2026-03-20
# Purpose: Extensive margin figure — share of authors active each month relative to birth

import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT       = Path(__file__).resolve().parents[5]
INPUT_PATH = ROOT / "Reddit/data/final/births_and_posts_FULL.csv"
OUTPUT_DIR = ROOT / "Reddit/output/analysis/volume"

WINDOW_MIN = -18
WINDOW_MAX =  18

# ----------------------------------------------------------------
# Load and filter to full_18_pre sample and window
# ----------------------------------------------------------------
df = pd.read_csv(INPUT_PATH)
df = df[df["full_18_pre"] == 1].copy()
df = df[(df["months_from_birth"] >= WINDOW_MIN) & (df["months_from_birth"] <= WINDOW_MAX)]

n_authors = df["author"].nunique()
print(f"Authors in sample (full_18_pre == 1): {n_authors:,}")

# ----------------------------------------------------------------
# Gender already assigned in build_analysis_ready_file.py
# ----------------------------------------------------------------
author_gender = df[["author", "female"]].drop_duplicates("author")

n_female = (author_gender["female"] == 1).sum()
n_male   = (author_gender["female"] == 0).sum()
print(f"  Female: {n_female:,} ({100*n_female/n_authors:.0f}%)  |  Male: {n_male:,} ({100*n_male/n_authors:.0f}%)")

# ----------------------------------------------------------------
# Build complete panel: all authors x all months in window
# ----------------------------------------------------------------
all_months  = pd.DataFrame({"months_from_birth": range(WINDOW_MIN, WINDOW_MAX + 1)})
all_authors = df[["author"]].drop_duplicates()
panel = all_authors.merge(all_months, how="cross")

# Count actual posts per author per month, then merge onto full panel
post_counts = (
    df.groupby(["author", "months_from_birth"])["id"]
    .count()
    .reset_index()
    .rename(columns={"id": "post_count"})
)
panel = panel.merge(post_counts, on=["author", "months_from_birth"], how="left")
panel["post_count"] = panel["post_count"].fillna(0)
panel["active"]     = (panel["post_count"] > 0).astype(int)

# Merge gender onto panel
monthly = panel.merge(author_gender[["author", "female"]], on="author", how="left")

# ----------------------------------------------------------------
# Figure 1: Overall extensive margin
# ----------------------------------------------------------------
extensive = monthly.groupby("months_from_birth")["active"].mean().reset_index()

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(extensive["months_from_birth"], extensive["active"],
        color="steelblue", linewidth=1.5)
ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Months from Birth")
ax.set_ylabel("Share Active This Month")
ax.set_title("Extensive Margin — Monthly Active Users")
ax.set_xlim(WINDOW_MIN, WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 2))
ax.annotate(f"N = {n_authors:,} authors", xy=(0.02, 0.02),
            xycoords="axes fraction", fontsize=9, color="gray")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "extensive_margin.jpg", dpi=150)
plt.close()
print(f"Saved to {OUTPUT_DIR / 'extensive_margin.jpg'}")

# ----------------------------------------------------------------
# Figure 2: Extensive margin by gender
# ----------------------------------------------------------------
extensive_gender = (
    monthly.groupby(["months_from_birth", "female"])["active"]
    .mean()
    .reset_index()
)

fig, ax = plt.subplots(figsize=(10, 5))
for gender, color, label in [(1, "red", "Female"), (0, "blue", "Male")]:
    sub = extensive_gender[extensive_gender["female"] == gender]
    ax.plot(sub["months_from_birth"], sub["active"],
            color=color, linewidth=1.5, label=label)

ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Months from Birth")
ax.set_ylabel("Share Active This Month")
ax.set_title("Extensive Margin — Monthly Active Users by Gender")
ax.set_xlim(WINDOW_MIN, WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 2))
ax.legend(loc="upper right")
ax.annotate(f"N = {n_authors:,} authors ({n_female:,} female, {n_male:,} male)",
            xy=(0.02, 0.02), xycoords="axes fraction", fontsize=9, color="gray")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "extensive_margin_gender.jpg", dpi=150)
plt.close()
print(f"Saved to {OUTPUT_DIR / 'extensive_margin_gender.jpg'}")

# ----------------------------------------------------------------
# Figures 3 & 4: one_year_pre == 1 sample
# ----------------------------------------------------------------
df_1yr = pd.read_csv(INPUT_PATH)
df_1yr = df_1yr[df_1yr["one_year_pre"] == 1].copy()
df_1yr = df_1yr[(df_1yr["months_from_birth"] >= WINDOW_MIN) & (df_1yr["months_from_birth"] <= WINDOW_MAX)]

n_authors_1yr = df_1yr["author"].nunique()
print(f"\nAuthors in sample (one_year_pre == 1): {n_authors_1yr:,}")

author_gender_1yr = df_1yr[["author", "female"]].drop_duplicates("author")

n_female_1yr = (author_gender_1yr["female"] == 1).sum()
n_male_1yr   = (author_gender_1yr["female"] == 0).sum()

all_months_1yr  = pd.DataFrame({"months_from_birth": range(WINDOW_MIN, WINDOW_MAX + 1)})
all_authors_1yr = df_1yr[["author"]].drop_duplicates()
panel_1yr = all_authors_1yr.merge(all_months_1yr, how="cross")

post_counts_1yr = (
    df_1yr.groupby(["author", "months_from_birth"])["id"]
    .count()
    .reset_index()
    .rename(columns={"id": "post_count"})
)
panel_1yr = panel_1yr.merge(post_counts_1yr, on=["author", "months_from_birth"], how="left")
panel_1yr["post_count"] = panel_1yr["post_count"].fillna(0)
panel_1yr["active"]     = (panel_1yr["post_count"] > 0).astype(int)
monthly_1yr = panel_1yr.merge(author_gender_1yr[["author", "female"]], on="author", how="left")

# Figure 3: Overall — one_year_pre
extensive_1yr = monthly_1yr.groupby("months_from_birth")["active"].mean().reset_index()

fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(extensive_1yr["months_from_birth"], extensive_1yr["active"],
        color="steelblue", linewidth=1.5)
ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Months from Birth")
ax.set_ylabel("Share Active This Month")
ax.set_title("Extensive Margin — Monthly Active Users (1-Year Pre Sample)")
ax.set_xlim(WINDOW_MIN, WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 2))
ax.annotate(f"N = {n_authors_1yr:,} authors", xy=(0.02, 0.02),
            xycoords="axes fraction", fontsize=9, color="gray")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "extensive_margin_1yr_pre.jpg", dpi=150)
plt.close()
print(f"Saved to {OUTPUT_DIR / 'extensive_margin_1yr_pre.jpg'}")

# Figure 4: By gender — one_year_pre
extensive_gender_1yr = (
    monthly_1yr.groupby(["months_from_birth", "female"])["active"]
    .mean()
    .reset_index()
)

fig, ax = plt.subplots(figsize=(10, 5))
for gender, color, label in [(1, "red", "Female"), (0, "blue", "Male")]:
    sub = extensive_gender_1yr[extensive_gender_1yr["female"] == gender]
    ax.plot(sub["months_from_birth"], sub["active"],
            color=color, linewidth=1.5, label=label)

ax.axvline(0, color="black", linestyle="--", linewidth=1)
ax.set_xlabel("Months from Birth")
ax.set_ylabel("Share Active This Month")
ax.set_title("Extensive Margin — Monthly Active Users by Gender (1-Year Pre Sample)")
ax.set_xlim(WINDOW_MIN, WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN, WINDOW_MAX + 1, 2))
ax.legend(loc="upper right")
ax.annotate(f"N = {n_authors_1yr:,} authors ({n_female_1yr:,} female, {n_male_1yr:,} male)",
            xy=(0.02, 0.02), xycoords="axes fraction", fontsize=9, color="gray")

plt.tight_layout()
plt.savefig(OUTPUT_DIR / "extensive_margin_gender_1yr_pre.jpg", dpi=150)
plt.close()
print(f"Saved to {OUTPUT_DIR / 'extensive_margin_gender_1yr_pre.jpg'}")
