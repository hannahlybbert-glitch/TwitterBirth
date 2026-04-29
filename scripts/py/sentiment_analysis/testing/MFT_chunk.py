## MFT_chunking

# ================================
# MFT LOGIC with Chunk Processing
# ================================
import spacy
import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

# 1. Load spaCy model (embeddings only for speed)
nlp = spacy.load("en_core_web_md", disable=["parser", "tagger", "ner"])

# 2. Seed words
family_seeds = [
    "baby", "child", "mom", "dad", "parent", "family", "together", "brother", "sister", 
    "grandparent", "pregnancy", "birth", "home", "hug", "play"
]
politics_seeds = [
    "republican", "democrat", "conservative", "liberal", "election", "vote", "campaign", 
    "government", "policy", "congress", "president", "freedom", "justice", "taxes", 
    "immigration", "trump", "biden", "clinton", "sanders"
]
sports_seeds = [
    "team", "game", "player", "coach", "score", "athlete", "ball", "sports", "#superbowl",
    "basketball", "baseball", "football", "soccer", "tournament", "league", 
    "championship", "defense", "offense", "MLB", "NBA", "NFL", "dodgers", "yankees"
]
religion_seeds = [
    "god", "jesus", "christ", "savior", "allah", "bible", "scripture", "church", "worship", 
    "devotion", "faith", "prayer", "spiritual", "holy", "christian", "muslim", 
    "jewish", "religion", "religious"
]

# 3. Centroid function
def get_centroid(words, nlp):
    vectors = []
    for w in words:
        lex = nlp.vocab[w]
        if lex.has_vector:
            vectors.append(lex.vector.astype("float32"))
    if len(vectors) == 0:
        return np.zeros(nlp.vocab.vectors_length, dtype="float32")
    return np.mean(vectors, axis=0).astype("float32")

# 4. Tweet vector
def doc_vector(doc):
    vectors = [token.vector for token in doc if token.has_vector]
    if len(vectors) > 0:
        return np.mean(vectors, axis=0).astype("float32")
    else:
        return np.zeros(nlp.vocab.vectors_length, dtype="float32")

# 5. Classify one chunk
def classify_tweets(df, nlp, centroids, batch_size=5000, n_process=4):
    results = []
    for doc, tweet_id in zip(
        nlp.pipe(df["text"], batch_size=batch_size, n_process=n_process),
        df["tweet_id"]
    ):
        vector = doc_vector(doc).reshape(1, -1)

        sims = {name: cosine_similarity(vector, c.reshape(1, -1))[0][0] 
                for name, c in centroids.items()}
        fam_pol = sims["family"] - sims["politics"]

        results.append({
            "tweet_id": tweet_id,
            **sims,
            "fam_pol_score": fam_pol
        })
    return pd.DataFrame(results)

# ================================
# MAIN SCRIPT
# ================================
if __name__ == "__main__":
    input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_only_10kSAMPLE.csv"
    output_path = "D:/TwitterBirth/data/sentiment_analysis/output/multi_dim_classified_SAMPLE_test.csv"

    # Precompute centroids ONCE
    centroids = {
        "family": get_centroid(family_seeds, nlp),
        "politics": get_centroid(politics_seeds, nlp),
        "sports": get_centroid(sports_seeds, nlp),
        "religion": get_centroid(religion_seeds, nlp)
    }

    # Process in chunks
    chunksize = 20000   # adjust up/down depending on RAM
    reader = pd.read_csv(input_path, chunksize=chunksize)

    for i, chunk in enumerate(reader):
        print(f"Processing chunk {i+1} ({len(chunk)} rows)...")

        result_df = classify_tweets(chunk, nlp, centroids)

        # Save incrementally (append mode)
        result_df.to_csv(output_path, mode="a", index=False, header=(i == 0))

    print(f"\n✅ MFT analysis complete. Output saved to: {output_path}")

