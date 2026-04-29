##### MFT analysis #####

import pandas as pd
import numpy as np
from MFT_logic import nlp, family_seeds, politics_seeds, sports_seeds, religion_seeds, get_centroid, classify_tweets

if __name__ == "__main__":
    # input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_FULL.csv"
    # output_path = "D:/TwitterBirth/data/sentiment_analysis/output/multi_dim_classified_FULL.csv"
    # input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_FULL_1mo_drop.csv"
    # output_path = "D:/TwitterBirth/data/sentiment_analysis/output/multi_dim_classified_FULL_1mo_drop.csv"

    # input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE.csv"
    # output_path = "D:/TwitterBirth/data/sentiment_analysis/output/multi_dim_classified_SAMPLE.csv"
    input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE_1mo_drop.csv"
    output_path = "D:/TwitterBirth/data/sentiment_analysis/output/multi_dim_classified_SAMPLE_1mo_drop.csv"

    # Precompute centroids (only do this once so it doesn't happen every chunk)
    centroids = {
        "family": get_centroid(family_seeds, nlp),
        "politics": get_centroid(politics_seeds, nlp),
        "sports": get_centroid(sports_seeds, nlp),
        "religion": get_centroid(religion_seeds, nlp),
    }

    chunksize = 40000  # adjust based on memory
    reader = pd.read_csv(input_path, chunksize=chunksize)

    open(output_path, "w").close()
    
    for i, chunk in enumerate(reader): # loop over chunks, classify, merge back to OG dataset
        print(f"Processing chunk {i+1} ({len(chunk)} rows)...")
        chunk["text"] = chunk["text"].fillna("").astype(str)
        result_df = classify_tweets(chunk, nlp, centroids)
        merged = chunk.merge(result_df, on="tweet_id", how="left")
        merged.to_csv(output_path, mode="a", index=False, header=(i == 0))

    print(f"\n✅ MFT analysis complete. Results saved to {output_path}")




# ------------------------- OLD ANALYSIS ------------------------------------------------- #


# import pandas as pd
# from MFT_logic import nlp, family_seeds, politics_seeds, sports_seeds, religion_seeds, get_centroid, classify_tweets

# if __name__ == "__main__":
#     df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_only_10kSAMPLE.csv")
#     # df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_only_FULL.csv") # tweet text, tweetID

#     # Average vector representation (centroid) for each category
#     family_centroid = get_centroid(family_seeds, nlp)
#     politics_centroid = get_centroid(politics_seeds, nlp)
#     religion_centroid = get_centroid(religion_seeds, nlp)
#     sports_centroid = get_centroid(sports_seeds, nlp)

#     # Classify tweets
#     results_df = classify_tweets(df, nlp, family_centroid, politics_centroid, religion_centroid, sports_centroid)

#     # Merge into original & save
#     df = df.merge(results_df, on="tweet_id")
#     df.to_csv("D:/TwitterBirth/data/sentiment_analysis/output/multi_dim_classified_SAMPLE.csv", index=False)
#     # df.to_csv("D:/TwitterBirth/data/sentiment_analysis/output/multi_dim_classified_FULL.csv", index=False)



# ## BEFORE SCALING
#     # change n_process = 4 (running across multiple cpu scores)

# # df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_ONLY.csv") # tweet text, tweetID
# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_ONLY_10kSAMPLE.csv") # Smaller sample to start

