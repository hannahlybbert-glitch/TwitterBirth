## SENTIMENT LOGIC

# Install needed packages
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import numpy as np

# Initialize analyzer
analyzer = SentimentIntensityAnalyzer()

# SENTIMENT FUNCTION --> no printing in this function! (make changes as necessary)
def get_sentiment_scores(tweet):

    # Check if tweet is a string
    if not isinstance(tweet, str):
        return np.nan, np.nan, np.nan, np.nan, np.nan # return "." in stata
    
    sentiment_dict = analyzer.polarity_scores(tweet)
    compound = sentiment_dict['compound']

    # test print statement (when I swap to adding all the output to a .csv make sure to change to JUST the output (not the tweet and all the additional characters))
    # print("{:-<65} {}".format(tweet, str(sentiment_dict)))

    # overall sentiment (one word)
    if compound >= 0.05:
        overall = "Positive"
    elif compound <= -0.05:
        overall = "Negative"
    else:
        overall = "Neutral"  

    return sentiment_dict['neg'], sentiment_dict['neu'], sentiment_dict['pos'], sentiment_dict['compound'], overall






# ## TESTING FOR PRINTING (delete later)
# def get_sentiment_score(tweet):
#     analyzer = SentimentIntensityAnalyzer()
#     sentiment_dict = analyzer.polarity_scores(tweet)

#     # test print statement 
#     print("{:-<65} {}".format(tweet, str(sentiment_dict)))