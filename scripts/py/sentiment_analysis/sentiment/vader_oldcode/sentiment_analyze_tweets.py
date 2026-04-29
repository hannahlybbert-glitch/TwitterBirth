## ANALYZE TWEET SENTIMENT

# import needed packages (will need to do on Git Bash first)
import pandas as pd
import swifter
swifter.config.progress_bar = True 
from sentiment_logic import get_sentiment_scores

# (1) Load dataset
# input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweet_sentiment_10kSAMPLE.csv"
input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_FULL.csv"
output_path = "D:/TwitterBirth/data/sentiment_analysis/output/sentimentVADER/tweet_sentiment_FULL.csv"
# input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_FULL_1mo_drop.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/sentimentVADER/tweet_sentiment_FULL_1mo_drop.csv"

df = pd.read_csv(input_path)


# (2) Apply sentiment scoring function to each tweet & (3) Store results in new columns / append scores

# # For test run:
# df[['neg', 'neu', 'pos', 'compound', 'overall']] = df['text'].apply(lambda x: pd.Series(get_sentiment_scores(x)))

# Multiprocessing (full sample):
df[['neg','neu','pos','compound','overall']] = df['text'].swifter.apply(lambda x: pd.Series(get_sentiment_scores(x)))


# (4) Save final output
df.to_csv(output_path, index=False)


print("\n ✅ Sentiment analysis complete. Output saved to:", output_path)







# ----------------------------------------------------------------------------------------#


# (4) Save final output
# CSV way (sample)
# input_path.to_csv(output_path, index=False)
# df.to_csv('D:/TwitterBirth/data/sentiment_analysis/output/tweet_sentiment_FULL.csv', index=False)


# # Parquet way (sample)
# df.to_parquet('D:/TwitterBirth/data/sentiment_analysis/output/tweets_sentiment_test.parquet', index = False)
# # to stata (sample)
# df.to_stata('D:/TwitterBirth/data/sentiment_analysis/output/tweets_sentiment_test.dta', index = False)

# # Parquet way (full)
# df.to_parquet('D:\TwitterBirth\data\sentiment_analysis\output\tweets_sentiment_full_sample.parquet', index = False)
# # to stata (full)
# df.to_stata('D:\TwitterBirth\data\sentiment_analysis\output\tweets_sentiment_full_sample.dta', index = False)


#----------------- Previous notes ------------------#

# # Parallelization
# df[['neg','neu','pos','compound','overall']] = df['text'].swifter.apply(get_sentiment_scores)
# # Normal way (for test run)
# df[['neg','neu','pos','compound','overall']] = df['text'].apply(get_sentiment_scores)



# df = pd.read_csv('D:/TwitterBirth/data/sentiment_analysis/tweet_text_only_10kSAMPLE.csv') 
# df = pd.read_csv('D:/TwitterBirth/data/sentiment_analysis/tweet_text_only_FULL.csv') # !! CHANGE PATH TO .CSV, this is the full sample .csv

# (2) Apply sentiment scoring function to each tweet (parallelized later, once 1.7M)
# (3) Store results in new columns / append scores

## Assign each element into separate columns in the DataFrame
# For test run:
# df[['neg', 'neu', 'pos', 'compound', 'overall']] = df['text'].apply(lambda x: pd.Series(get_sentiment_scores(x)))

# Multiprocessing (full sample):
# df[['neg','neu','pos','compound','overall']] = df['text'].swifter.apply(lambda x: pd.Series(get_sentiment_scores(x)))


## CHUNK analysis attempt (saved 9x the observations that went in initially)
# # (2) Chunk processing
# # Read in chunks
# chunksize = 1_000
# reader = pd.read_csv(input_path, chunksize=chunksize) # read in CSV

# for i, chunk in enumerate(reader):
#     print(f"Processing chunk {i+1}...")

#     # (3) Apply sentiment analysis
#     chunk[['neg','neu','pos','compound','overall']] = chunk['text'].swifter.apply(
#         lambda x: pd.Series(get_sentiment_scores(x))
#     )

#     # Optimize datatypes
#     chunk[['neg','neu','pos','compound']] = chunk[['neg','neu','pos','compound']].astype('float32')
#     chunk['overall'] = chunk['overall'].astype('category')

#     # (4) Save final output
#     chunk.to_csv(output_path, mode='a', index=False, header=(i == 0))