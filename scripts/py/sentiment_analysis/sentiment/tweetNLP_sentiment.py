# Author: Hannah Lybbert
# Created: 10/29/2025
# Purpose: Compare Karthik's sentiment pipeline to mine, determine final & efficient pipeline for sentiment analysis

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

# Load datasets
# input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/sentiment_scores10k_mypipe.csv"
input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_FULL.csv"
output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/sentiment_scoresFULL.csv"

# Explicitly Load Model Version 
model = tweetnlp.load_model(
    "sentiment",
    model_name="cardiffnlp/twitter-roberta-base-2021-124m-sentiment"
)


# -------------------- JUST SENTIMENT from my old code -------------------- # ~4mins for 10k

# --- Ignore Warnings --- #
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message=".*use_auth_token.*")

# model_sentiment = tweetnlp.load_model('sentiment')


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






# ---------- a few notes from old iterations ---------- #
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/sentiment_scores10k_chat.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/sentiment_scores10k_kpipe.csv"


# -------NONE OF THIS ACTUALLY RUNS ---------- #
# # ------------------------ CHUNK & MULTIPROCESSING ------------------------ #
# import pandas as pd
# import tweetnlp
# import multiprocessing as mp

# # -------- Worker (each process loads its own model) ----------
# model = None
# def init_worker():
#     global model
#     model = tweetnlp.load_model("sentiment",
#                                 model_name="cardiffnlp/twitter-roberta-base-2021-124m-sentiment")
    

# # -------- Analyze a single tweet -------- #
# def analyze(text):
#     global model
#     out = model.predict(text)

#     p_pos = out["prob"].get("positive", 0)
#     p_neg = out["prob"].get("negative", 0)
#     sentiment_score = p_pos - p_neg

#     return {
#         "sentiment": out["label"],
#         # "p_pos": p_pos,
#         # "p_neg": p_neg,
#         "sentiment_score": sentiment_score
#     }

# # -------- Process a chunk (worker) -------- #
# def process_chunk(df_chunk):
#     results = df_chunk["text"].apply(analyze).tolist()
#     out_df = pd.DataFrame(results)
#     out_df["tweet_id"] = df_chunk["tweet_id"].values
#     return out_df


# # -------- Main parallel runner -------- #
# def run_parallel_sentiment(input_path, output_path, chunksize=25000, n_workers=4):

#     pool = mp.Pool(processes=n_workers, initializer=init_worker)

#     writer = None  # we'll create this after first chunk

#     for idx, df_chunk in enumerate(pd.read_csv(input_path, chunksize=chunksize)):

#         print(f"Submitting chunk {idx}")
#         result = pool.apply_async(process_chunk, (df_chunk,))

#         processed = result.get()

#         # write output in main process only
#         if writer is None:
#             processed.to_csv(output_path, index=False, mode="w")
#         else:
#             processed.to_csv(output_path, index=False, header=False, mode="a")

#     pool.close()
#     pool.join()


# # -------- Run -------- #
# if __name__ == "__main__":
#     run_parallel_sentiment(
#         input_path,
#         output_path,
#         chunksize=25000,
#         n_workers=4
#     )





# def process_chunk(df_chunk):
#     model = tweetnlp.load_model(
#         "sentiment",
#         model_name="cardiffnlp/twitter-roberta-base-2021-124m-sentiment"
#     )

#     def analyze(text):
#         out = model.predict(text)
#         probs = out.get("prob", {})   # sometimes missing
#         pos = probs.get("positive", 0.0)
#         neg = probs.get("negative", 0.0)
#         return pd.Series({
#             "sentiment": out.get("label", "neutral"),
#             # "positive_prob": pos,
#             # "negative_prob": neg,
#             "sentiment_score": pos - neg
#         })

#     df_chunk[["sentiment", "sentiment_score"]] = (
#         df_chunk["text"].apply(analyze)
#     )

#     return df_chunk



# def run_parallel_sentiment(input_csv, output_csv,
#                            chunksize=50000,  # controls RAM + speed tradeoff
#                            n_workers=4):     # match your CPU cores
#     # Prepare output file
#     open(output_csv, "w").close()

#     # Start pool
#     with Pool(processes=n_workers) as pool:
#         # Stream the CSV in chunks so RAM never explodes
#         for i, chunk in enumerate(pd.read_csv(input_csv, chunksize=chunksize)):
#             print(f"Submitting chunk {i}")

#             # Submit each chunk to the worker
#             result = pool.apply_async(process_chunk, (chunk,))

#             # When ready, append to disk
#             processed_chunk = result.get()
#             processed_chunk.to_csv(
#                 output_csv,
#                 mode="a",
#                 header=(i == 0),  # write header only on first chunk
#                 index=False
#             )

#     print("✅ All chunks processed & written to:", output_csv)


# if __name__ == "__main__":

#     print("Preloading model cache...")
#     tweetnlp.load_model("sentiment",
#     model_name="cardiffnlp/twitter-roberta-base-2021-124m-sentiment")

#     run_parallel_sentiment(
#         input_path, 
#         output_path,
#         chunksize=50000,
#         n_workers=4     # adjust based on CPU
#     )

# input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/sentiment_scores10k_chat.csv"