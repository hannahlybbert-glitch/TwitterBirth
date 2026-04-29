# VADER sentiment with Karthik's code

# %%time 

# Load Packages 
import subprocess
import tweetnlp
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
# from nltk.sentiment.vader import SentimentIntensityAnalyzer
from tqdm import tqdm
import numpy as np
import pandas as pd

# Preserve Documentation of Packages 
subprocess.run("pip freeze > requirements_vader.txt", shell=True)
# subprocess.run("pip freeze > requirements_nlp.txt", shell=True)

# Explicitly Load Model Version 
analyzer = SentimentIntensityAnalyzer()
# model = tweetnlp.load_model(
#     "sentiment",
#     model_name="cardiffnlp/twitter-roberta-base-2021-124m-sentiment")

# ===== Batch inference function =====
def batched_vader_scores(texts, analyzer, batch_size=512, use_compound=False):
    """Compute compound sentiment scores for tweets"""
    scores = []
    for i in tqdm(range(0, len(texts), batch_size)):
        batch = texts[i:i+batch_size]
        for text in batch:
            if not isinstance(text, str):
                scores.append(np.nan)
                continue
            result = analyzer.polarity_scores(text)
            score = result["compound"] if use_compound else(result["pos"] - result["neg"])
            scores.append(score)
    return np.array(scores)

# def batched_tweetNLP_scores(texts, model, batch_size=512):
#     """Compute P(pos)-P(neg) scores for a list of tweets."""
#     scores = []
#     for i in tqdm(range(0, len(texts), batch_size)):
#         batch = texts[i:i+batch_size]
#         results = model.sentiment(batch, return_probability=True)
#         for r in results:
#             p = r["probability"]
#             scores.append(p["positive"] - p["negative"])
#     return np.array(scores)


# Load datasets
# input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/vader_sentiment_Kcode_10k.csv"
input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_FULL.csv"
output_path = "D:/TwitterBirth/data/sentiment_analysis/output/vader_posneg_Kcode_FULL.csv"


df = pd.read_csv(input_path)
texts = df['text'].astype(str).tolist()

df["vader_score"] = batched_vader_scores(texts, analyzer)
# df["tweetNLP_score"] = batched_tweetNLP_scores(texts, model)


df.to_csv(output_path, index=False, encoding="utf-8-sig")

# Print results
print(f"Sentiment Analysis complete. Results saved to: {output_path}")
print(df.head())





