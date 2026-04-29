## Tweet Topic Classifier (using TweetNLP package)

import tweetnlp
import numpy as np
import os
import warnings
import pandas as pd

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message=".*use_auth_token.*")


# -- Initialize Models -- #
# model_topic = tweetnlp.load_model('topic_classification', multi_label=False)
model_sentiment = tweetnlp.load_model('sentiment')
batch_size = 64



# ------------------- PREVIOUS FUNCTIONS ----------------------- #

# Function for Sentiment Analysis
def get_sentiment_scores(tweet):

    if not isinstance(tweet, str):
        return pd.Series([np.nan, np.nan, np.nan, np.nan, np.nan], 
                         index=['label', 'neg', 'neu', 'pos', 'sentiment_score'])
    
    try:
        sentiment_dict = model_sentiment.sentiment(tweet, return_probability=True)
        probs = sentiment_dict.get('probability', {})

        prob_neg = probs.get('negative', np.nan)
        prob_neu = probs.get('neutral', np.nan)
        prob_pos = probs.get('positive', np.nan)
        sentiment_score = prob_pos - prob_neg  

        return pd.Series([
            sentiment_dict.get('label', np.nan),
            prob_neg, prob_neu, prob_pos, sentiment_score
        ], index=['sentiment', 'neg', 'neu', 'pos', 'sentiment_score'])
    
    except Exception as e:
        print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
        return pd.Series([np.nan, np.nan, np.nan, np.nan], 
                         index=['label', 'neg', 'neu', 'pos'])
    

# # Function for Tweet Topic Classification
# def get_topic_classification(tweet):
    
#     # Check if tweet is a string
#     if not isinstance(tweet, str):
#         return np.nan # return "." in stata
#     try:
#         topic_dict = model_topic.topic(tweet)
#         # print tests
#         # print(topic_dict)
        
#         return topic_dict['label']

#     except Exception as e:
#         print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
#         return np.nan
    







# # ----- Topic Classification ----- #
# def batch_topic_classification(tweets, batch_size):

#     topic_labels = []

#     # Check if tweet is a string
#     if not isinstance(tweets, list) or len(tweets) == 0:
#         return [np.nan] # return "." in stata
    
#     for i in range(0, len(tweets), batch_size):
#         batch = tweets[i:i + batch_size] # slice a batch of tweets
#         try:
#             output = model_topic.topic(batch)
#             labels = [t.get('label', np.nan) for t in output]
#             topic_labels.extend(labels) # each output element is a dict: {'label': '...', 'probability': {...}}

#         except Exception as e:
#             print(f"⚠️ Error in topic batch {i//batch_size + 1}: {e}")
#             topic_labels.extend([np.nan] * len(batch))
#     return topic_labels
    

# # ----- Sentiment Analysis ----- #
# def batch_sentiment_scores(tweets, batch_size):

#     if not isinstance(tweets, list) or len(tweets) == 0:
#         return pd.DataFrame({'sentiment': [], 'prob_neg': [], 'prob_neu': [], 'prob_pos': []})
    
#     labels, negs, neus, poss = [], [], [], []

#     for i in range(0, len(tweets), batch_size):
#         batch = tweets[i:i + batch_size]
#         try:
#             output = model_sentiment.sentiment(batch, return_probability=True)
#             for s in output:
#                 probs = s.get('probability', {})
#                 labels.append(s.get('label', np.nan))
#                 negs.append(probs.get('negative', np.nan))
#                 neus.append(probs.get('neutral', np.nan))
#                 poss.append(probs.get('positive', np.nan))
#         except Exception as e:
#             print(f"⚠️ Error in sentiment batch {i//batch_size + 1}: {e}")
#             # On error, fill missing rows
#             labels += [np.nan]*len(batch)
#             negs += [np.nan]*len(batch)
#             neus += [np.nan]*len(batch)
#             poss += [np.nan]*len(batch)

#     return pd.DataFrame({'sentiment': labels, 'prob_neg': negs, 'prob_neu': neus, 'prob_pos': poss})



# # Hate Speech Detection
# def batch_hate_detection(tweets, batch_size):

#     if not isinstance(tweets, str):
#         return pd.Series([np.nan, np.nan, np.nan, np.nan], 
#                          index=['label', 'prob_non_hate', 'prob_hate', 'prob_dict'])

#     labels, non_hate, hate = [], [], []

#     for i in range(0, len(tweets), batch_size):
#         batch = tweets[i:i + batch_size]
#         try:
#             output = model_hate.hate(batch, return_probability=True)
#             for s in output:
#                 probs = s.get('probability', {})
#                 labels.append(s.get('label', np.nan))
#                 non_hate.append(probs.get('non-hate', np.nan))
#                 hate.append(probs.get('hate', np.nan))
#         except Exception as e:
#             print(f"⚠️ Error in sentiment batch: {e}")
#             # On error, fill missing rows
#             labels += [np.nan]*len(batch)
#             non_hate += [np.nan]*len(batch)
#             hate += [np.nan]*len(batch)

#     return pd.DataFrame({'hate_speech': labels, 'prob_non_hate': non_hate, 'prob_hate': hate})



# # Offensive Language Detection
# def batch_offensive_lang(tweets, batch_size):

#     if not isinstance(tweets, str):
#         return pd.Series([np.nan, np.nan, np.nan, np.nan], 
#                          index=['label', 'prob_non_offesnive', 'prob_offensive', 'prob_dict'])

#     labels, non_offensive, offensive = [], [], []

#     for i in range(0, len(tweets), batch_size):
#         batch = tweets[i:i + batch_size]
#         try:
#             output = model_offensive.offensive(batch, return_probability=True)
#             for s in output:
#                 probs = s.get('probability', {})
#                 labels.append(s.get('label', np.nan))
#                 non_offensive.append(probs.get('non-offensive', np.nan))
#                 offensive.append(probs.get('offensive', np.nan))
#         except Exception as e:
#             print(f"⚠️ Error in sentiment batch: {e}")
#             # On error, fill missing rows
#             labels += [np.nan]*len(batch)
#             non_offensive += [np.nan]*len(batch)
#             offensive += [np.nan]*len(batch)

#     return pd.DataFrame({'offensive_lang': labels, 'prob_non_offensive': non_offensive, 'prob_offensive': offensive})









# # ------------------- PREVIOUS FUNCTIONS ----------------------- #

# # Function for Tweet Topic Classification
# def get_topic_classification(tweet):
    
#     # Check if tweet is a string
#     if not isinstance(tweet, str):
#         return np.nan # return "." in stata
#     try:
#         topic_dict = model_topic.topic(tweet)
#         # print tests
#         # print(topic_dict)
        
#         return topic_dict['label']

#     except Exception as e:
#         print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
#         return np.nan
    

# # Function for Sentiment Analysis
# def get_sentiment_scores(tweet):

#     if not isinstance(tweet, str):
#         return pd.Series([np.nan, np.nan, np.nan, np.nan, np.nan], 
#                          index=['label', 'neg', 'neu', 'pos', 'sentiment_score'])
    
#     try:
#         sentiment_dict = model_sentiment.sentiment(tweet, return_probability=True)
#         probs = sentiment_dict.get('probability', {})

#         prob_neg = probs.get('negative', np.nan)
#         prob_neu = probs.get('neutral', np.nan)
#         prob_pos = probs.get('positive', np.nan)
#         sentiment_score = prob_pos - prob_neg  

#         return pd.Series([
#             sentiment_dict.get('label', np.nan),
#             prob_neg, prob_neu, prob_pos, sentiment_score
#         ], index=['sentiment', 'neg', 'neu', 'pos', 'sentiment_score'])
    
#     except Exception as e:
#         print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
#         return pd.Series([np.nan, np.nan, np.nan, np.nan], 
#                          index=['label', 'neg', 'neu', 'pos'])


# # Previous Sentiment Function
# def get_sentiment_scores(tweet):

#     if not isinstance(tweet, str):
#         return pd.Series([np.nan, np.nan, np.nan, np.nan, np.nan], 
#                          index=['label', 'prob_neg', 'prob_neu', 'prob_pos', 'prob_dict'])
    
#     try:
#         sentiment_dict = model_sentiment.sentiment(tweet, return_probability=True)
#         # print(sentiment_dict)

#         probs = sentiment_dict.get('probability', {})
#         return pd.Series([
#             sentiment_dict.get('label', np.nan),
#             probs.get('negative', np.nan),
#             probs.get('neutral', np.nan),
#             probs.get('positive', np.nan),
#             probs # storing full dictionary if needed later
#         ], index=['sentiment', 'prob_neg', 'prob_neu', 'prob_pos', 'prob_sentiment_dict'])
    
#     except Exception as e:
#         print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
#         return pd.Series([np.nan, np.nan, np.nan, np.nan, np.nan], 
#                          index=['label', 'prob_neg', 'prob_neu', 'prob_pos', 'prob_sentiment_dict'])


# # Hate Speech Detection
# def get_hate_speech_scores(tweet):

#     if not isinstance(tweet, str):
#         return pd.Series([np.nan, np.nan, np.nan, np.nan], 
#                          index=['label', 'prob_non_hate', 'prob_hate', 'prob_hate_dict'])
    
#     try:
#         hate_dict = model_hate.hate(tweet, return_probability=True)
#         # print(hate_dict)

#         probs = hate_dict.get('probability', {})
#         return pd.Series([
#             hate_dict.get('label', np.nan),
#             probs.get('non-hate', np.nan),
#             probs.get('hate', np.nan),
#             probs # storing full dictionary if needed later
#         ], index=['hate_speech', 'prob_non_hate', 'prob_hate', 'prob_hate_dict'])
    
#     except Exception as e:
#         print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
#         return pd.Series([np.nan, np.nan, np.nan, np.nan], 
#                          index=['label', 'prob_non_hate', 'prob_hate', 'prob_hate_dict'])


# # Offensive Language Detection
# def get_offensive_lang_scores(tweet):

#     if not isinstance(tweet, str):
#         return pd.Series([np.nan, np.nan, np.nan, np.nan], 
#                          index=['label', 'prob_non_offensive', 'prob_offensive', 'prob_offensive_dict'])
    
#     try:
#         offensive_dict = model_offensive.offensive(tweet, return_probability=True)
#         # print(offensive_dict)

#         probs = offensive_dict.get('probability', {})
#         return pd.Series([
#             offensive_dict.get('label', np.nan),
#             probs.get('non-offensive', np.nan),
#             probs.get('offensive', np.nan),
#             probs # storing full dictionary if needed later
#         ], index=['offensive_lang', 'prob_non_offensive', 'prob_offensive', 'prob_offensive_dict'])
    
#     except Exception as e:
#         print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
#         return pd.Series([np.nan, np.nan, np.nan, np.nan], 
#                          index=['label', 'prob_non_offensive', 'prob_offensive', 'prob_offensive_dict'])





# -------------- OLD CODE ----------------------- #

# import pandas as pd
# import numpy as np

# family_keywords = ["baby", "child", "daughter", "son", "pregnant", "born", "family", "parent"]
# politics_keywords = ["election", "vote", "biden", "trump", "policy", "senate"]
# sports_keywords = ["game", "team", "score", "nba", "soccer", "football", "baseball"]
# religion_keywords = ["god", "church", "pray", "blessed", "faith", "bible"]

# def label_tweet(text):
#     text = text.lower()
#     if any(word in text for word in family_keywords):
#         return "family"
#     elif any(word in text for word in politics_keywords):
#         return "politics"
#     elif any(word in text for word in sports_keywords):
#         return "sports"
#     elif any(word in text for word in religion_keywords):
#         return "religion"
#     else:
#         return "other"

# df["label"] = df["text"].apply(label_tweet)