## TweetNLP analyze
import os
import warnings
import tweetnlp
import pandas as pd
import numpy as np
import swifter
swifter.config.progress_bar = True 
from tweetNLP_logic import get_sentiment_scores
# from tweetNLP_logic import get_sentiment_scores, get_topic_classification
# from tweetNLP_logic import batch_topic_classification, batch_sentiment_scores, batch_hate_detection, batch_offensive_lang


# --- Ignore Warnings --- #
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message=".*use_auth_token.*")


# --- Set Up --- # 
# input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/topic_classifier_10k.csv"
input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_FULL.csv"
output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/sentiment_FULL.csv"


# --------------------- OLD CODE --------------------- #
df = pd.read_csv(input_path)


# --- Sentiment Analysis --- #
sentiment_results = df['text'].swifter.apply(get_sentiment_scores)
df = pd.concat([df, sentiment_results], axis=1)
df.to_csv(output_path, index=False)

print("\n ✅ Sentiment Analysis complete.")


# # --- Topic Classification --- #
# df['label'] = df['text'].swifter.apply(get_topic_classification)
# # df[['label']] = df['text'].swifter.apply(lambda x: pd.Series(get_topic_classification(x)))

# print("\n ✅ Topic classification complete.")


# --- All Analyses Complete --- #
print("\n ✅ Tweet NLP complete. Output saved to:", output_path)

# # --- Hate Speech  --- #
# hate_results = df['text'].swifter.apply(get_hate_speech_scores)
# df = pd.concat([df, hate_results], axis=1)
# df.to_csv(output_path, index=False)

# print("\n ✅ Hate Speech Analysis complete.")


# # --- Offensive Language  --- #
# offensive_results = df['text'].swifter.apply(get_offensive_lang_scores)
# df = pd.concat([df, offensive_results], axis=1)
# df.to_csv(output_path, index=False)

# print("\n ✅ Offensive Language Analysis complete.")








# # ------------------ CHUNK PROCESSING ATTEMPTS ------------------ #

# input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE.csv"
# output_dir = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/tweetNLP_chunks10k"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/topic_classifier_10k_t2.csv"
# input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_mini_testing.csv"
# output_dir = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP_chunks_mini"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/tweetnlp_MINItest.csv"

# CHUNK_SIZE = 1000 # how many tweets load at once
# BATCH_SIZE = 64 # how many tweets are sent to the model per call

# # Create the output directory if it doesn't exist
# os.makedirs(output_dir, exist_ok=True)


# for i, chunk in enumerate(pd.read_csv(input_path, chunksize=CHUNK_SIZE)):
#     print(f"\n Processing chunk {i+1} ({len(chunk)} tweets)")

#     # Make sure text column is clear
#     tweets = chunk['text'].astype(str).tolist()

#     # --- 1. Topic Classification --- #
#     chunk['topic_label'] = batch_topic_classification(tweets, BATCH_SIZE)
#     print(f"\n ✅ Topic classification complete, chunk {i+1}")

#     # --- 2. Sentiment Analysis --- #
#     sentiment_df = batch_sentiment_scores(tweets, BATCH_SIZE)
#     chunk = pd.concat([chunk, sentiment_df], axis=1)
#     print(f"\n ✅ Sentiment Analysis complete, chunk {i+1}")

#     # # --- 3. Hate Speech Detection --- #
#     # hate_df = batch_hate_detection(tweets, BATCH_SIZE)
#     # chunk = pd.concat([chunk, hate_df], axis=1)
#     # print(f"\n ✅ Hate Speech Detection complete, chunk {i+1}")

#     # # --- 4. Offensive Language Detection --- #
#     # offensive_df = batch_offensive_lang(tweets, BATCH_SIZE)
#     # chunk = pd.concat([chunk, offensive_df], axis=1)
#     # print(f"\n ✅ Offensive Language Detection complete, chunk {i+1}")


#     # --- Save Processed Chunk --- #
#     chunk_path = os.path.join(output_dir, f"chunk_{i+1:03}.csv")
#     chunk.to_csv(chunk_path, index=False)
#     print(f"Saved: {chunk_path}")


# # ----- MERGE ALL CHUNKS INTO 1 CSV ----- #
# print("\n All chunks processed. Now merging...")

# # Load all chunk files
# all_chunks = [
#     pd.read_csv(os.path.join(output_dir, f))
#     for f in sorted(os.listdir(output_dir))
#     if f.endswith(".csv")
# ]

# # Concatenate all chunks into one datset
# merged = pd.concat(all_chunks, ignore_index=True)

# # Save final output
# merged.to_csv(output_path, index=False)
# print(f"\n Merging complete. Output saved to: {output_path}")


# df = pd.read_csv(input_path)

# # --- Topic Classification --- #
# df['label'] = df['text'].swifter.apply(get_topic_classification)
# # df[['label']] = df['text'].swifter.apply(lambda x: pd.Series(get_topic_classification(x)))

# print("\n ✅ Topic classification complete.")


# # --- Sentiment Analysis --- #
# sentiment_results = df['text'].swifter.apply(get_sentiment_scores)
# df = pd.concat([df, sentiment_results], axis=1)
# df.to_csv(output_path, index=False)

# print("\n ✅ Sentiment Analysis complete.")


# # --- Hate Speech  --- #
# hate_results = df['text'].swifter.apply(get_hate_speech_scores)
# df = pd.concat([df, hate_results], axis=1)
# df.to_csv(output_path, index=False)

# print("\n ✅ Hate Speech Analysis complete.")


# # --- Offensive Language  --- #
# offensive_results = df['text'].swifter.apply(get_offensive_lang_scores)
# df = pd.concat([df, offensive_results], axis=1)
# df.to_csv(output_path, index=False)

# print("\n ✅ Offensive Language Analysis complete.")


# # --- All Analyses Complete --- #
# print("\n ✅ Tweet NLP complete. Output saved to:", output_path)



# # ------------------------- CHUNKING ATTEMPT ------------------------------ #
# if __name__ == "__main__":
#     input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE.csv"
#     output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/topic_classifier_10k.csv"

#     # # Precompute centroids (only do this once so it doesn't happen every chunk)
#     # centroids = {
#     #     "family": get_centroid(family_seeds, nlp),
#     #     "politics": get_centroid(politics_seeds, nlp),
#     #     "sports": get_centroid(sports_seeds, nlp),
#     #     "religion": get_centroid(religion_seeds, nlp),
#     # }

#     chunksize = 2000  # adjust based on memory
#     df = pd.read_csv(input_path, chunksize=chunksize)

#     open(output_path, "w").close()
    
#     for i, chunk in enumerate(df): # loop over chunks, run sentiment, merge back to OG dataset
#         print(f"Processing chunk {i+1} ({len(chunk)} rows)...")
#         df['label'] = df['text'].swifter.apply(get_topic_classification)
        
#         chunk["text"] = chunk["text"].fillna("").astype(str)
#         result_df = classify_tweets(chunk, nlp, centroids)
#         merged = chunk.merge(result_df, on="tweet_id", how="left")
#         merged.to_csv(output_path, mode="a", index=False, header=(i == 0))

#     print(f"\n✅ TweetNLP analysis complete. Results saved to {output_path}")
# ------------------------- CHUNKING ATTEMPT ------------------------------ #





