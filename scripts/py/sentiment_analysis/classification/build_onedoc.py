### Author: Hannah Lybbert
### Created: 11/14/2025
### Purpose: Build dataset with one doc per author and period


import pandas as pd
import numpy as np

# df_old = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/text_aid_prepost.csv") # built in stata from "tweets_by_user_full_sample_CLEAN.dta." (acct active for 3 years and >=1 tweet post birth announcement)
df_old = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/topic_sentiment_FULL.csv") 


df_old["text"] = df_old["text"].fillna("").astype(str)

# -----------------------------------
# REMOVE FAMILY RELATED TWEETS 
# -----------------------------------
df_old = df_old[df_old["family"] < 0.2]

df_old.to_csv("D:/TwitterBirth/data/sentiment_analysis/output/text_onedoc_test.csv", index=False)

# -----------------------------------------
# STRIP YEARS from the text column
# -----------------------------------------
df_old["text"] = df_old["text"].str.replace(r"(18|19|20)\d{2}", " ", regex=True)
df_old["text"] = df_old["text"].str.replace(r"\s+", " ", regex=True).str.strip()


# Filter to authors who have BOTH pre (0) and post (1)
author_has_both = (
    df_old.groupby("author_id")["post_birth"]
             .nunique()
             .eq(2)
)

valid_authors = author_has_both[author_has_both].index

df_old = df_old[df_old["author_id"].isin(valid_authors)].reset_index(drop=True)

print("Remaining tweets:", len(df_old))
print("Remaining authors:", df_old["author_id"].nunique())


# GROUP TWEETS
groups = dict(
    sorted(
        df_old.groupby(["author_id", "post_birth"]).indices.items()
    )
)

# CREATE LABEL VECTOR (y)
doc_labels = [post for (auth, post) in groups.keys()]
y = np.array(doc_labels).astype(int)

# ------------------------------------
# CONCATENATE TWEETS into ONE DOC
# ------------------------------------
doc_texts = []
for (auth, post), idxs in groups.items():
    # Join tweets in the *original row order* using idxs
    doc_texts.append(" ".join(df_old.loc[idxs, "text"].astype(str)))


# Build final dataframe 
df_full = pd.DataFrame({
    "author_id": [auth for (auth, post) in groups.keys()],
    "post_birth":      [post for (auth, post) in groups.keys()],
    "text_concat": doc_texts
})



# Save for later 
df_full.to_csv("D:/TwitterBirth/data/sentiment_analysis/output/text_onedoc.csv", index=False) #8,280 observations, 4,140 accounts
# df.to_csv("D:/TwitterBirth/data/sentiment_analysis/output/text_onedoc_sample.csv", index=False) # 1,000 obs, 500 accounts

# when I remove all family related tweets we're down to 4,126 authors 


# ---------------------  OLD CODE  ---------------------

# -----------------------------------
# CONCATENATE TWEETS BY author_id & post
# -----------------------------------
# df_full = (
#     df_old
#     .groupby(["author_id", "post"])["text"]   # by aid and period
#     .apply(lambda x: " ".join(x))             # join tweets with space
#     .reset_index(name="text_concat")
# )

# print(df_full.head())

# # --- Sample down to 10k entries for GridSearch (5000 pre / 5000 post) --- #
# sampled_authors = (
#     pd.Series(df_full["author_id"].unique())
#       .sample(n=500, random_state=42)
#       .tolist()
# )

# df = df_full[df_full["author_id"].isin(sampled_authors)]

# print(df["post"].value_counts())



# import pandas as pd

# test = [
#     "I was born in 2019",
#     "covid2019 hit hard",
#     "year2020report",
#     "this is from1999test"
# ]

# cleaned = (
#     pd.Series(test)
#       .str.replace(r"(18|19|20)\d{2}", " ", regex=True)
#       .str.replace(r"\s+", " ", regex=True)
#       .str.strip()
# )

# print(cleaned.tolist())


# valid_authors = (
#     df_full.groupby("author_id")
#     .filter(lambda x: len(x) == 2)["author_id"]
#     .unique()
# )

# sampled_authors = pd.Series(valid_authors).sample(n=500, random_state=42).tolist()




