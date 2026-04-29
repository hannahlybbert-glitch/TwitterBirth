# Author: Hannah Lybbert
# Created: 2026-04-09
# Updated: 2026-04-09
# Purpose: VADER sentiment scoring logic for Reddit posts

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import numpy as np

# Initialize analyzer once at import time (not per-call)
analyzer = SentimentIntensityAnalyzer()

def get_sentiment_scores(text):
    if not isinstance(text, str):
        return np.nan, np.nan, np.nan, np.nan, np.nan

    sentiment_dict = analyzer.polarity_scores(text)
    compound = sentiment_dict["compound"]

    if compound >= 0.05:
        overall = "Positive"
    elif compound <= -0.05:
        overall = "Negative"
    else:
        overall = "Neutral"

    return sentiment_dict["neg"], sentiment_dict["neu"], sentiment_dict["pos"], compound, overall
