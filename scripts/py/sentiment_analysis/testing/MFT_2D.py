### MFT test


# Import needed ibraries
import spacy
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity 
import matplotlib.pyplot as plt
import seaborn as sns


## BEFORE SCALING
    # change n_process = 4 (running across multiple cpu scores)

# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_FULL.csv") # tweet text, tweetID
df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE.csv") # Smaller sample to start


# 1. Load spaCy 
nlp = spacy.load("en_core_web_md")

# 2. Seed words
# family_seeds = [
#     "baby", "newborn", "infant", "son", "daughter", "toddler", "kid", "children",
#     "mom", "dad", "parent", "parenting", "family", "together",
#     "brother", "sister", "sibling", "cousin",
#     "grandparent", "grandma", "grandpa",
#     "wife", "husband", 
#     "pregnancy", "birth", "childcare", "diaper", "bedtime", "school", "teacher", "daycare",
#     "hug", "cuddle", "nurture", "bond", "play",
#     "home", "house", "kitchen", "backyard"
# ]
# politics_seeds = [
#     "gop", "dems", "progressive", "maga", "leftist", "socialist", "capitalist",
#     "republican", "democrat", "conservative", "liberal",
#     "government", "congress", "senate", "president", "campaign", "election", "policy", "administration", "vote",
#     "bill", "amendment", "debate", "petition", "activism", "protest", "rally",
#     "constitution", "flag", "liberty", "freedom", "patriot",
#     "military", "troops", "security", "border", "immigration", "terrorism",
#     "taxes", "economy", "healthcare", "climate", "guns", "abortion", "justice", "corruption",
#     "trump", "biden", "clinton", "sanders"
# ]

# concise seed word lists:
family_seeds = [
    "baby", "child", "mom", "dad", "parent", "family", "together", "brother", "sister", 
    "grandparent", "pregnancy", "birth", "home", "hug", "play","wife","husband"
]
politics_seeds = [
    "republican","democrat","conservative","liberal","election","vote","campaign",
    "government","policy","congress","president","freedom","justice","taxes",
    "immigration","trump","biden","clinton","sanders"
    ]

# 3. SEED words --> spaCy vectors to find Centroid point
def get_centroid(words, nlp):
    vectors = []
    for w in words:
        lex = nlp.vocab[w] # direct vocab look up from spaCy
        if lex.has_vector:
            vectors.append(lex.vector)
    if len(vectors) == 0:
        return np.zeros(nlp.vocab.vectors_length) 

    centroid = np.mean(vectors, axis=0)
    return centroid

# 4. Convert Tweet --> vector (doc=tweet, token=word in tweet)
def doc_vector(doc):
    vectors = [token.vector for token in doc if token.has_vector]

    if len(vectors) > 0: # if list isn't empty
        return np.mean(vectors, axis=0) # average all the vectors in tweet --> final tweet vector
    else:
        return np.zeros(nlp.vocab.vectors_length) # return 0 vector if empty list
    
# 5. Batch Process Tweets (optimization)
def classify_tweets(df, nlp, family_centroid, politics_centroid, batch_size=1000):
    tweet_ids, family_sims, politics_sims, scores = [], [], [], []

    for doc, tweet_id in zip(nlp.pipe(df["text"], batch_size=batch_size, n_process=1), df["tweet_id"]):
        vector = doc_vector(doc).reshape(1, -1) # takes tweet vector and reshapes
        family_sim = cosine_similarity(vector, family_centroid.reshape(1, -1))[0][0] # compare tweet vector to family centroid ([0][0] single numeric similarity score)
        politics_sim = cosine_similarity(vector, politics_centroid.reshape(1, -1))[0][0] # for politics centorid
        score = family_sim - politics_sim # positive = family, negative = politics, 0 = neutral

        tweet_ids.append(tweet_id)
        family_sims.append(family_sim)
        politics_sims.append(politics_sim)
        scores.append(score)
    
    return pd.DataFrame({
        "tweet_id": tweet_ids,
        "family_sim": family_sims,
        "politics_sim": politics_sims,
        "spectrum_score": scores
    })


# 6. Run functions
if __name__ == "__main__":
    # Average vector representation (centroid) for each category
    family_centroid = get_centroid(family_seeds, nlp)
    politics_centroid = get_centroid(politics_seeds, nlp)

    # classify tweets
    results_df = classify_tweets(df, nlp, family_centroid, politics_centroid)

    # # Merge back into original dataset
    # df = df.merge(results_df, on="tweet_id")

    # saftey check:
    print("Original df columns:", df.columns.tolist())
    print("Results df columns:", results_df.columns.tolist())
    print("Rows before merge:", len(df))
    print("Rows in results_df:", len(results_df))
    
    # Merge back into original dataset
    df = df.merge(results_df, on="tweet_id")
    print("Merged df columns:", df.columns.tolist())
    print(df.head(5))
    print("Rows after merge:", len(df))

    # save results to .csv file
    df.to_csv("D:/TwitterBirth/data/sentiment_analysis/output/fam_politics_classified_SAMPLE.csv", index=False)
    # df.to_csv("D:/TwitterBirth/data/sentiment_analysis/output/fam_politics_classified_bigseed_SAMPLE.csv", index=False)
    # df.to_csv("D:/TwitterBirth/data/sentiment_analysis/output/fam_politics_classified_FULL.csv", index=False)



# 7. VISUALIZE
# Histogram
plt.hist(df["spectrum_score"], bins=50)
plt.xlabel("Politics (-)   <----->   Family (+)")
plt.ylabel("Tweet count")
plt.title("Tweet distribution on Family-Politics axis")
plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_hist_10k.png", dpi=300, bbox_inches="tight")
# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_hist_big_seed_list10k.png", dpi=300, bbox_inches="tight")
plt.close()

# Kernel Density
sns.kdeplot(df["spectrum_score"], fill=True)
plt.title("Density of Family ↔ Politics Scores")
plt.xlabel("Spectrum score (family - politics)")
plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_density_10k.png", dpi=300, bbox_inches="tight")
# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_density_big_seed_list10k.png", dpi=300, bbox_inches="tight")
plt.close()
# plt.show()


## WORD CLOUD option?
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# --- Parameters ---
top_pct = 0.05   # top 5% most extreme tweets on each side
text_column = "text"  # change this to your tweet text column name

# --- Split tweets into family-oriented and politics-oriented extremes ---
threshold_high = df["spectrum_score"].quantile(1 - top_pct)
threshold_low = df["spectrum_score"].quantile(top_pct)

family_tweets = df.loc[df["spectrum_score"] >= threshold_high, text_column]
politics_tweets = df.loc[df["spectrum_score"] <= threshold_low, text_column]

# --- Concatenate texts ---
family_text = " ".join(family_tweets.astype(str))
politics_text = " ".join(politics_tweets.astype(str))

# --- Generate Word Clouds ---
family_wc = WordCloud(width=800, height=400, background_color="white").generate(family_text)
politics_wc = WordCloud(width=800, height=400, background_color="white").generate(politics_text)

# --- Plot side by side ---
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

axes[0].imshow(family_wc, interpolation="bilinear")
axes[0].set_title("Most Family-Oriented Tweets", fontsize=16)
axes[0].axis("off")

axes[1].imshow(politics_wc, interpolation="bilinear")
axes[1].set_title("Most Politics-Oriented Tweets", fontsize=16)
axes[1].axis("off")

# plt.show()
plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_wordcloud_10k.png", dpi=300, bbox_inches="tight")
# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_wordcloud_big_seed_list10k.png", dpi=300, bbox_inches="tight")
plt.close()






# ######### OTHER NOTES ##########

# # 4. TWEETS --> vectors
# def tweet_vector(text, nlp):
#     doc = nlp(text) # creating a doc object running the tweet through the spaCy npl

#     vectors = [token.vector for token in doc if token.has_vector]

#     vectors = []
#     for token in doc: # for each word vector
#         if token.has_vector:
#             vectors.append(token.vector) # append its vector to the list

#     if len(vectors) > 0: # if list isn't empty
#         return np.mean(vectors, axis=0) # average all the vectors --> final tweet vector
#     else:
#         return np.zeros(nlp.vocab.vectors_length) # return 0 vector if empty list
    
# # 5. Take cosine similarity between vectors
# def classify_tweet(text, nlp, family_centroid, politics_centroid):
#     vector = tweet_vector(text, nlp).reshape(1, -1) # convert tweet into a vector, average all word embeddings in tweet, return 1D numpy array, conver to 2D array for cosine_similarity compatibility
#     family_sim = cosine_similarity(vector, family_centroid.reshape(1, -1))[0][0] # compare tweet vector to family centroid ([0][0] single numeric similarity score)
#     politics_sim = cosine_similarity(vector, politics_centroid.reshape(1, -1)[0][0]) # for politics centorid
    
#     score = family_sim - politics_sim # positive = family, negative = politics, 0 = neutral
#     return family_sim, politics_sim, score




