### MFT test


# Import needed ibraries
import spacy
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity 
import seaborn as sns
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA


## BEFORE SCALING
    # change n_process = 4 (running across multiple cpu scores)

# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_ONLY.csv") # tweet text, tweetID
df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_ONLY_10kSAMPLE.csv") # Smaller sample to start


# 1. Load spaCy 
nlp = spacy.load("en_core_web_md")

# 2. Seed words
family_seeds = [
    "baby", "child", "mom", "dad", "parent", "family", "together", "brother", "sister", 
    "grandparent", "pregnancy", "birth", "home", "hug", "play"
]
politics_seeds = [
    "republican", "democrat", "conservative", "liberal", "election", "vote", "campaign", "government", "policy", 
    "congress", "president", "freedom", "justice", "taxes", "immigration", "trump", "biden", "clinton", "sanders"
]
sports_seeds = [
    "team", "game", "player", "coach", "score", "athlete", "ball", "sports",
    "basketball", "baseball", "football", "soccer", "tournament", "league", "championship"
]
religion_seeds = [
    "god", "jesus", "christ", "savior", "allah", "bible", "scripture", "church", "worship", "devotion", 
    "faith", "prayer", "spiritual", "holy", "christian", "muslim", "jewish", "religion", "religious"
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
def classify_tweets(df, nlp, family_centroid, politics_centroid, sports_centroid, religion_centroid, batch_size=1000):
    tweet_ids, family_sims, politics_sims, religion_sims, sports_sims, fam_pol_score = [], [], [], [], [], []

    for doc, tweet_id in zip(nlp.pipe(df["text"], batch_size=batch_size, n_process=1), df["tweet_id"]):
        vector = doc_vector(doc).reshape(1, -1) # takes tweet vector and reshapes
        family_sim = cosine_similarity(vector, family_centroid.reshape(1, -1))[0][0] # compare tweet vector to family centroid ([0][0] single numeric similarity score)
        politics_sim = cosine_similarity(vector, politics_centroid.reshape(1, -1))[0][0] # for politics centorid
        religion_sim = cosine_similarity(vector, religion_centroid.reshape(1, -1))[0][0] 
        sports_sim = cosine_similarity(vector, sports_centroid.reshape(1, -1))[0][0]         
        fam_pol = family_sim - politics_sim # positive = family, negative = politics, 0 = neutral

        tweet_ids.append(tweet_id)
        family_sims.append(family_sim)
        politics_sims.append(politics_sim)
        religion_sims.append(religion_sim)
        sports_sims.append(sports_sim)
        fam_pol_score.append(fam_pol)
    
    return pd.DataFrame({
        "tweet_id": tweet_ids,
        "family_sim": family_sims,
        "politics_sim": politics_sims,
        "religion_sim": religion_sim,
        "sports_sim": sports_sims,
        "spectrum_score": fam_pol_score
    })

# 6. Run functions
if __name__ == "__main__":
    # Average vector representation (centroid) for each category
    family_centroid = get_centroid(family_seeds, nlp)
    politics_centroid = get_centroid(politics_seeds, nlp)
    religion_centroid = get_centroid(religion_seeds, nlp)
    sports_centroid = get_centroid(sports_seeds, nlp)

    # Classify tweets
    results_df = classify_tweets(df, nlp, family_centroid, politics_centroid, religion_centroid, sports_centroid)

    # Merge into original & save
    df = df.merge(results_df, on="tweet_id")
    df.to_csv("D:/TwitterBirth/data/sentiment_analysis/output/multi_dimension_classified_SAMPLE.csv", index=False)

    # 7. Visualize reltionships:

    # Measure pairwise similarities
    centroids = {
        "family": family_centroid,
        "politics": politics_centroid,
        "religion": religion_centroid,
        "sports": sports_centroid
    }

    # Similarity matrix
    names = list(centroids.keys())
    vectors = np.stack(list(centroids.values()))
    sim_matrix = cosine_similarity(vectors)
    sim_df = pd.DataFrame(sim_matrix, index=names, columns=names)
    print(sim_df)

    # Visualize in HEATMAP
    plt.figure(figsize=(6,5))
    sns.heatmap(sim_df, annot=True, cmap="coolwarm", vmin=0, vmax=1)
    plt.title("Cosine Similarities between Centroids")
    plt.savefig("D:/TwitterBirth/data/sentiment_analysis/output/multi_dim_heatmap.png", dpi=300, bbox_inches="tight")
    plt.close()
    # plt.show()



###### OTHER NOTES ######

# # LARGE SEED WORD LISTS
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