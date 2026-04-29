# Author: Hannah Lybbert
# Created: 02/23/2026
# Purpose: Concatenate tweets by author_id & post_birth into one-doc format for classification

import pandas as pd

# --- Paths ---
input_path = "D:/TwitterBirth/data/sentiment_analysis/text_aid_prepost.csv"
out_full   = "D:/TwitterBirth/data/sentiment_analysis/output/text_onedoc.csv"

# --- Load ---
df = pd.read_csv(input_path)
df["text"] = df["text"].fillna("").astype(str)

# --- Strip years from text ---
df["text"] = df["text"].str.replace(r"(18|19|20)\d{2}", " ", regex=True)
df["text"] = df["text"].str.replace(r"\s+", " ", regex=True).str.strip()

# --- Filter to authors who have BOTH pre (0) and post (1) ---
author_has_both = df.groupby("author_id")["post_birth"].nunique().eq(2)
valid_authors   = author_has_both[author_has_both].index
df = df[df["author_id"].isin(valid_authors)].reset_index(drop=True)

print("Remaining tweets: ", len(df))
print("Remaining authors:", df["author_id"].nunique())

# --- Concatenate tweets by author_id & post_birth ---
df_full = (
    df
    .groupby(["author_id", "post_birth"])["text"]
    .apply(lambda x: " ".join(x))
    .reset_index(name="text_concat")
)

print(df_full.head())

# --- Save ---
df_full.to_csv(out_full, index=False)
print(f"Saved full dataset: {len(df_full)} obs  →  {out_full}")
