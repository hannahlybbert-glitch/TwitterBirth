# Testing Sentiment Code -Hannah

# Load Packages 
import subprocess
import tweetnlp
import pandas as pd
from tqdm import tqdm
import numpy as np
import os
import warnings
import swifter
swifter.config.progress_bar = True 

# Preserve Documentation of Packages 
subprocess.run("pip freeze > requirements_nlp.txt", shell=True)
input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE.csv"
output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/sentiment_scores10k_mypipe.csv"


# Explicitly Load Model Version 
model = tweetnlp.load_model(
    "sentiment",
    model_name="cardiffnlp/twitter-roberta-base-2021-124m-sentiment"
)


# -------------------- SENTIMENT from my old code -------------------- # ~4mins for 10k
# --- Ignore Warnings --- #
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message=".*use_auth_token.*")

# ------ Function ------ # 
def get_sentiment_scores(tweet):

    if not isinstance(tweet, str):
        return pd.Series([np.nan, np.nan, np.nan, np.nan, np.nan], 
                         index=['label', 'neg', 'neu', 'pos', 'sentiment_score'])
    
    try:
        sentiment_dict = model.sentiment(tweet, return_probability=True)
        probs = sentiment_dict.get('probability', {})

        prob_neg = probs.get('negative', np.nan)
        prob_neu = probs.get('neutral', np.nan)
        prob_pos = probs.get('positive', np.nan)
        sentiment_score = prob_pos - prob_neg  

        return pd.Series([
            sentiment_dict.get('label', np.nan),
            prob_neg,
            prob_neu,
            prob_pos,
            sentiment_score
        ], index=['sentiment', 'neg', 'neu', 'pos', 'sentiment_score'])
    
    except Exception as e:
        print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
        return pd.Series([np.nan, np.nan, np.nan, np.nan], 
                         index=['label', 'neg', 'neu', 'pos'])
    

# ----- Analysis ----- #
df = pd.read_csv(input_path)

# --- Sentiment Analysis --- #
sentiment_results = df['text'].swifter.apply(get_sentiment_scores)
df = pd.concat([df, sentiment_results], axis=1)
df.to_csv(output_path, index=False)

print("✅ Sentiment Analysis complete.\n")
print(df.head())



# # ------------------------ KARTHIK CODE ---------------------------- #
# # ===== Batch inference function =====
# def batched_sentiment_scores(texts, model, batch_size=512):
#     """Compute P(pos)-P(neg) scores for a list of tweets."""
#     scores = []
#     for i in tqdm(range(0, len(texts), batch_size)):
#         batch = texts[i:i+batch_size]
#         results = model.sentiment(batch, return_probability=True)
#         for r in results:
#             p = r["probability"]
#             scores.append(p["positive"] - p["negative"])
#     return np.array(scores)


# # # Test the batched function
# # df = pd.DataFrame(tweets, columns=["text"])
# # df["sentiment_score"] = batched_sentiment_scores(df["text"].tolist(), model)


# df = pd.read_csv(input_path)
# texts = df['text'].astype(str).tolist()

# df["sentiment_score"] = batched_sentiment_scores(texts, model)

# df.to_csv(output_path, index=False, encoding="utf-8-sig")

# # Print results
# print(f"Sentiment Analysis complete. Results saved to: {output_path}")
# print(df.head())