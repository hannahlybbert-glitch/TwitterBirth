### MFT LOGIC

import spacy
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
import warnings

warnings.filterwarnings("ignore", message=r".*The rule-based lemmatizer did not find POS annotation.*")


# 1. Load spaCy (only vectors)
nlp = spacy.load("en_core_web_md", disable=["parser", "tagger", "ner"])

# 2. Define Seed Words 
# BIG seed lists
family_seeds = [
    "baby", "newborn", "infant", "son", "daughter", "toddler", "kid", "children",
    "mom", "dad", "parent", "parenting", "family", "together",
    "brother", "sister", "sibling", "cousin",
    "grandparent", "grandma", "grandpa",
    "wife", "husband", 
    "pregnancy", "birth", "childcare", "diaper", "bedtime", "school", "teacher", "daycare",
    "hug", "cuddle", "nurture", "bond", "play",
    "home", "house", "kitchen", "backyard"
]
politics_seeds = [
    "gop", "dems", "progressive", "maga", "leftist", "socialist", "capitalist",
    "republican", "democrat", "conservative", "liberal",
    "government", "congress", "senate", "president", "campaign", "election", "policy", "administration", "vote",
    "bill", "amendment", "debate", "petition", "activism", "protest", "rally",
    "constitution", "flag", "liberty", "freedom", "patriot",
    "military", "troops", "security", "border", "immigration", "terrorism",
    "taxes", "economy", "healthcare", "climate", "guns", "abortion", "justice", "corruption",
    "trump", "biden", "clinton", "sanders"
]
religion_seeds = [
    "god", "jesus", "christ", "savior", "allah", "bible", "scripture", "church", "worship", "devotion",
    "faith", "prayer", "spiritual", "holy", "christian", "muslim", "jewish", "religion", "religious",
    "mosque", "temple", "synagogue", "monastery", "priest", "pastor", "imam", "rabbi",
    "sermon", "mass", "sacrifice", "ritual", "sacrament", "fasting", "meditation",
    "blessing", "sin", "forgiveness", "heaven", "hell", "afterlife", "miracle", "sacred",
    "hindu", "buddhist", "islamic", "catholic", "orthodox", "protestant", "sikh",
    "hinduism", "buddhism", "islam", "judaism"
]
sports_seeds = [
    "sports", "athlete", "player", "coach", "team", "fans", "score", "match", "game", "competition", 
     "training", "practice", "tournament", "league", "championship", "medal", "trophy", 
    "victory", "defeat", "win", "loss", "final", "playoffs", "stadium", "arena",
    "football", "soccer", "basketball", "baseball", "tennis", "golf", "hockey", "volleyball", 
    "rugby", "cricket", "swimming", "running", "track", "wrestling", "boxing", "mma", "esports",
    "quarterback", "touchdown", "superbowl", "nba", "nfl", "mlb", "nhl", "ncaa", "marchmadness",
    "worldcup", "olympics", "fifa", "uefa", "championsleague",
    "goalkeeper", "striker", "pitcher", "catcher", "referee", "umpire", 
    "offense", "defense", "penalty", "overtime",
]

# --- Helper functions ---

# 3. SEED words --> spaCy vectors to find Centroid point
def get_centroid(words, nlp):
    vectors = [nlp.vocab[w].vector for w in words if nlp.vocab[w].has_vector]
    return np.mean(vectors, axis=0) if vectors else np.zeros(nlp.vocab.vectors_length)
    ''' given a list of words, look up each word's vector in spaCy, 
    return the average (centroid) '''

# 4. Convert Tweet --> vector (doc=tweet, token=word in tweet)
def doc_vector(doc):
    vectors = [t.vector for t in doc if t.has_vector]
    return np.mean(vectors, axis=0).astype("float32") if vectors else np.zeros(nlp.vocab.vectors_length, dtype="float32")
    ''' Convert a tweet into a single vector
     extract vectors for each word, average them to get a tweet vector '''

# 5. Batch Process Tweets (optimization)
def classify_tweets(df, nlp, centroids, batch_size=7000, n_process=4):
    tweet_ids, vectors = [], []

    # Extract vectors
    for doc, tweet_id in zip(nlp.pipe(df["text"], batch_size=batch_size, n_process=n_process), df["tweet_id"]):
        tweet_ids.append(tweet_id)
        vectors.append(doc_vector(doc))

    vectors = np.vstack(vectors)
    ''' for each tweet in a batch, convert into a vector '''

    # Compute similarities in bulk
    sims = {name: cosine_similarity(vectors, centroid.reshape(1, -1)).ravel()
            for name, centroid in centroids.items()}
    ''' compute cosine similarity for each tweet to each centroid '''

    # Family – politics axis
    fam_pol = sims["family"] - sims["politics"]

    return pd.DataFrame({
        "tweet_id": tweet_ids,
        "family_sim": sims["family"],
        "politics_sim": sims["politics"],
        "religion_sim": sims["religion"],
        "sports_sim": sims["sports"],
        "fam_pol_score": fam_pol
    })






# ------------------------- OLD LOGIC ------------------------------------------------- #

# # Import needed ibraries
# import spacy
# import numpy as np
# import pandas as pd
# from sklearn.metrics.pairwise import cosine_similarity 
# import seaborn as sns
# import matplotlib.pyplot as plt
# from sklearn.decomposition import PCA


# # 1. Load spaCy 
# nlp = spacy.load("en_core_web_md", disable=["parser", "tagger", "ner"])

# # 2. Seed words
# family_seeds = [
#     "baby", "child", "mom", "dad", "parent", "family", "together", "brother", "sister", 
#     "grandparent", "pregnancy", "birth", "home", "hug", "play", "wife", "husband"
# ]
# politics_seeds = [
#     "republican", "democrat", "conservative", "liberal", "election", "vote", "campaign", "government", "policy", 
#     "congress", "president", "freedom", "justice", "taxes", "immigration", "trump", "biden", "clinton", "sanders"
# ]
# sports_seeds = [
#     "team", "game", "player", "coach", "score", "athlete", "ball", "sports", "defense", "offense",
#     "basketball", "baseball", "football", "soccer", "tournament", "league", "championship",
#     "quarterback", "touchdown", "superbowl", "nba", "nfl", "mlb", "nhl", "ncaa", "marchmadness"
# ]
# religion_seeds = [
#     "god", "jesus", "christ", "savior", "allah", "bible", "scripture", "church", "worship", "devotion", 
#     "faith", "prayer", "spiritual", "holy", "christian", "muslim", "jewish", "religion", "religious",
#     "mosque", "temple", "synagogue", "monastery", "priest", "pastor", "imam", "rabbi"
# ]


# # 3. SEED words --> spaCy vectors to find Centroid point
# def get_centroid(words, nlp):
#     vectors = []
#     for w in words:
#         lex = nlp.vocab[w] # direct vocab look up from spaCy
#         if lex.has_vector:
#             vectors.append(lex.vector)
#     if len(vectors) == 0:
#         return np.zeros(nlp.vocab.vectors_length) 

#     centroid = np.mean(vectors, axis=0)
#     return centroid

# # 4. Convert Tweet --> vector (doc=tweet, token=word in tweet)
# def doc_vector(doc):
#     vectors = [token.vector for token in doc if token.has_vector]

#     if len(vectors) > 0: # if list isn't empty
#         return np.mean(vectors, axis=0).astype("float32") # average all the vectors in tweet --> final tweet vector
#     else:
#         return np.zeros(nlp.vocab.vectors_length).astype("float32") # return 0 vector if empty list
    
# # 5. Batch Process Tweets (optimization)
# def classify_tweets(df, nlp, family_centroid, politics_centroid, sports_centroid, religion_centroid, batch_size=5000):
#     tweet_ids, family_sims, politics_sims, religion_sims, sports_sims, fam_pol_score = [], [], [], [], [], []

#     for doc, tweet_id in zip(nlp.pipe(df["text"], batch_size=batch_size, n_process=4), df["tweet_id"]):
#         vector = doc_vector(doc).reshape(1, -1) # takes tweet vector and reshapes
#         family_sim = cosine_similarity(vector, family_centroid.reshape(1, -1))[0][0] # compare tweet vector to family centroid ([0][0] single numeric similarity score)
#         politics_sim = cosine_similarity(vector, politics_centroid.reshape(1, -1))[0][0] # for politics centorid
#         religion_sim = cosine_similarity(vector, religion_centroid.reshape(1, -1))[0][0] 
#         sports_sim = cosine_similarity(vector, sports_centroid.reshape(1, -1))[0][0]         
#         fam_pol = family_sim - politics_sim # positive = family, negative = politics, 0 = neutral

#         tweet_ids.append(tweet_id)
#         family_sims.append(family_sim)
#         politics_sims.append(politics_sim)
#         religion_sims.append(religion_sim)
#         sports_sims.append(sports_sim)
#         fam_pol_score.append(fam_pol)
    
#     return pd.DataFrame({
#         "tweet_id": tweet_ids,
#         "family_sim": family_sims,
#         "politics_sim": politics_sims,
#         "religion_sim": religion_sim,
#         "sports_sim": sports_sims,
#         "fam_pol_score": fam_pol_score
#     })





###### OTHER NOTES ######
# # SMALL seed list
# family_seeds = ["baby","child","mom","dad","parent","family","together","brother","sister",
#                 "grandparent","pregnancy","birth","home","hug","play","wife","husband"]
# politics_seeds = ["republican","democrat","conservative","liberal","election","vote","campaign",
#                   "government","policy","congress","president","freedom","justice","taxes",
#                   "immigration","trump","biden","clinton","sanders"]
# sports_seeds = ["team","game","player","coach","score","athlete","ball","sports","defense","offense",
#                 "basketball","baseball","football","soccer","tournament","league","championship",
#                 "quarterback","touchdown","superbowl","nba","nfl","mlb","nhl","ncaa","marchmadness"]
# religion_seeds = ["god","jesus","christ","savior","allah","bible","scripture","church","worship",
#                   "devotion","faith","prayer","spiritual","holy","christian","muslim","jewish",
#                   "religion","religious","mosque","temple","synagogue","monastery","priest","pastor",
#                   "imam","rabbi"]


# # LARGE SEED WORD LISTS
# BIG seed lists
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
# religion_seeds = [
#     "god", "jesus", "christ", "savior", "allah", "bible", "scripture", "church", "worship", "devotion",
#     "faith", "prayer", "spiritual", "holy", "christian", "muslim", "jewish", "religion", "religious",
#     "mosque", "temple", "synagogue", "monastery", "priest", "pastor", "imam", "rabbi",
#     "sermon", "mass", "sacrifice", "ritual", "sacrament", "fasting", "meditation",
#     "blessing", "sin", "forgiveness", "heaven", "hell", "afterlife", "miracle", "sacred",
#     "hindu", "buddhist", "islamic", "catholic", "orthodox", "protestant", "sikh",
#     "hinduism", "buddhism", "islam", "judaism"
# ]
# sports_seeds = [
#     "sports", "athlete", "player", "coach", "team", "fans", "score", "match", "game", "competition", 
#      "training", "practice", "tournament", "league", "championship", "medal", "trophy", 
#     "victory", "defeat", "win", "loss", "final", "playoffs", "stadium", "arena",
#     "football", "soccer", "basketball", "baseball", "tennis", "golf", "hockey", "volleyball", 
#     "rugby", "cricket", "swimming", "running", "track", "wrestling", "boxing", "mma", "esports",
#     "quarterback", "touchdown", "superbowl", "nba", "nfl", "mlb", "nhl", "ncaa", "marchmadness",
#     "worldcup", "olympics", "fifa", "uefa", "championsleague",
#     "goalkeeper", "striker", "pitcher", "catcher", "referee", "umpire", 
#     "offense", "defense", "penalty", "overtime",
# ]