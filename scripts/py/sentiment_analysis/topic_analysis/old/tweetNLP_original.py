## Clean old code

## TweetNLP analyze
import os
import warnings
import tweetnlp
import pandas as pd
import numpy as np
import swifter
swifter.config.progress_bar = True 



# --- Ignore Warnings --- #
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message=".*use_auth_token.*")


# --- Data --- # 
input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE.csv"
output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/topic_classifier_10k.csv"
# input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_mini_testing.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/tweetnlp_MINItest.csv"


# -- Initialize Models -- #
model_topic = tweetnlp.load_model('topic_classification', multi_label=False)
model_sentiment = tweetnlp.load_model('sentiment')
model_hate = tweetnlp.load_model('hate')
model_offensive = tweetnlp.load_model('offensive')


# --- BUILD FUNCTIONS --- #

# Function for Tweet Topic Classification
def get_topic_classification(tweet):
    
    # Check if tweet is a string
    if not isinstance(tweet, str):
        return np.nan # return "." in stata
    try:
        topic_dict = model_topic.topic(tweet)
        # return topic_dict['label']
        if topic_dict is None:
            return np.nan
        if isinstance(topic_dict, dict):
            return topic_dict.get('label', np.nan)
        return topic_dict

    except Exception as e:
        print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
        return np.nan
    

# Function for Sentiment Analysis
def get_sentiment_scores(tweet):

    if not isinstance(tweet, str):
        return pd.Series([np.nan, np.nan, np.nan, np.nan], 
                         index=['label', 'prob_neg', 'prob_neu', 'prob_pos'])
    
    try:
        sentiment_dict = model_sentiment.sentiment(tweet, return_probability=True)
        # print(sentiment_dict)

        probs = sentiment_dict.get('probability', {})
        return pd.Series([
            sentiment_dict.get('label', np.nan),
            probs.get('negative', np.nan),
            probs.get('neutral', np.nan),
            probs.get('positive', np.nan),
        ], index=['sentiment', 'prob_neg', 'prob_neu', 'prob_pos'])
    
    except Exception as e:
        print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
        return pd.Series([np.nan, np.nan, np.nan, np.nan], 
                         index=['label', 'prob_neg', 'prob_neu', 'prob_pos'])


# Hate Speech Detection
def get_hate_speech_scores(tweet):

    if not isinstance(tweet, str):
        return pd.Series([np.nan, np.nan, np.nan], 
                         index=['label', 'prob_non_hate', 'prob_hate'])
    
    try:
        hate_dict = model_hate.hate(tweet, return_probability=True)
        # print(hate_dict)

        probs = hate_dict.get('probability', {})
        return pd.Series([
            hate_dict.get('label', np.nan),
            probs.get('non-hate', np.nan),
            probs.get('hate', np.nan),
        ], index=['hate_speech', 'prob_non_hate', 'prob_hate'])
    
    except Exception as e:
        print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
        return pd.Series([np.nan, np.nan, np.nan], 
                         index=['label', 'prob_non_hate', 'prob_hate'])


# Offensive Language Detection
def get_offensive_lang_scores(tweet):

    if not isinstance(tweet, str):
        return pd.Series([np.nan, np.nan, np.nan], 
                         index=['label', 'prob_non_offensive', 'prob_offensive'])
    
    try:
        offensive_dict = model_offensive.offensive(tweet, return_probability=True)
        # print(offensive_dict)

        probs = offensive_dict.get('probability', {})
        return pd.Series([
            offensive_dict.get('label', np.nan),
            probs.get('non-offensive', np.nan),
            probs.get('offensive', np.nan),
        ], index=['offensive_lang', 'prob_non_offensive', 'prob_offensive'])
    
    except Exception as e:
        print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
        return pd.Series([np.nan, np.nan, np.nan], 
                         index=['label', 'prob_non_offensive', 'prob_offensive'])




# ------------------------ RUN ANALYSES ------------------------ #

df = pd.read_csv(input_path)

# --- Topic Classification --- #
df['label'] = df['text'].swifter.apply(get_topic_classification)
# df[['label']] = df['text'].swifter.apply(lambda x: pd.Series(get_topic_classification(x)))

print("✅ Topic classification complete.\n")


# --- Sentiment Analysis --- #
sentiment_results = df['text'].swifter.apply(get_sentiment_scores)
df = pd.concat([df, sentiment_results], axis=1)
df.to_csv(output_path, index=False)

print("✅ Sentiment Analysis complete.\n")


# --- Hate Speech  --- #
hate_results = df['text'].swifter.apply(get_hate_speech_scores)
df = pd.concat([df, hate_results], axis=1)
df.to_csv(output_path, index=False)

print("✅ Hate Speech Analysis complete.\n")


# --- Offensive Language  --- #
offensive_results = df['text'].swifter.apply(get_offensive_lang_scores)
df = pd.concat([df, offensive_results], axis=1)
df.to_csv(output_path, index=False)

print("✅ Offensive Language Analysis complete.\n")


# --- All Analyses Complete --- #
print("✅ Tweet NLP complete. Output saved to:", output_path)