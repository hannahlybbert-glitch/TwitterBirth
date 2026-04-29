## Vader Sentiment analysis first pass


# BIG PICTURE WORK FLOW

# (1) Load csv of tweets

# (2) Run VADER sentiment analysis on the "text" column for each tweet

# (3) Extract sentiment scores (neg, neu, pos, compound)

# (4) Classify each tweet's sentiment (positive/negative/neutral)

# (5) Append these scores to original dataset (now 18 columns)

# (6) Save the output (.csv)


''' exmaple output:

unique_id,author_id,tweet_id,created_at,text,like_count,retweet_count,...,neg,neu,pos,compound,overall
123,98765,67890,2016-06-12,"I'm so excited for the big day!",10,5,...,0.0,0.33,0.67,0.8,"positive"

'''



# -------------------------------------------------------------------------------------------- #

# Install needed packages
# pip install vaderSentiment # already installed via Git Bash
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

# SENTIMENT FUNCTION
def sentiment_score(tweet):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_dict = analyzer.polarity_scores(tweet)

    # test print statement (when I swap to adding all the output to a .csv make sure to change to JUST the output (not the tweet and all the additional characters))
    print("{:-<65} {}".format(tweet, str(sentiment_dict)))

    # overall sentiment (one word)
    overall_sentiment = ""
    if sentiment_dict['compound'] >= 0.05:
        print("Overall Sentiment: Positive")
        overall_sentiment = "Positive"
    elif sentiment_dict['compound'] <= -0.05:
        print("Overall Sentiment: Negative")
        overall_sentiment = "Negative"
    else:
        print("Overall Sentiment: Netural")
        overall_sentiment = "Neutral"    

    # # What it might look like in the future...
    # tweet_text.append(sentiment_dict['neg'])
    # tweet_text.append(sentiment_dict['neu'])
    # tweet_text.append(sentiment_dict['pos'])
    # tweet_text.append(overall_sentiment)



analyzer = SentimentIntensityAnalyzer()
for sentence in sentences:
    vs = analyzer.polarity_scores(sentence)
    print("{:-<65} {}".format(sentence, str(vs)))


# Funciton to calculate sentiment scores
def sentiment_score(sentence):
    sid_obj = SentimentIntensityAnalyzer()
    sentiment_dict = sid_obj.polarity_scores(sentence)

    print(f"Sentiment Scores: {sentiment_dict}")
    print(f"Negative Sentiment: {sentiment_dict['neg']*100}%")
    print(f"Neutral Sentiment: {sentiment_dict['neu']*100}%")
    print(f"Positive Sentiment: {sentiment_dict['pos']*100}%")

    if sentiment_dict['compound'] >= 0.05:
        print("Overall Sentiment: Positive")
    elif sentiment_dict['compound'] <= -0.05:
        print("Overall Sentiment: Negative")
    else:
        print("Overall Sentiment: Netural")
    

'''
    - want to loop through each tweet in the datafile (will need to convert back to a csv to be able to do this)
    - loop through each tweet text (text = sentence) and plug it into the sentiment_score function
        for tweet in data:
            tweet = text variable
            sentiment_score(tweet)

            # save/add to a json maybe? Some bigger datafile 
            # store the sentiment scores along with the unique_id author_id tweet_id created_at text sentiment_score
                # one variable for each neg, neutral, positive, and overall sentiment (polarity scores not percentages)
    - DONT want to output the sentiment score function output for each tweet, only want to save into a datafile

'''

# # Test to see if function works
# if __name__ == "__main__":
#     print("\n1st Statement:")
#     sentence = "Geeks for Geeks is an excellent platform for CSE studnets."
#     print(f"Statement: {sentence}")
#     sentiment_score(sentence)

#     print("\n2nd Statement:")
#     sentence = "Shewta played well in the match as usual."
#     print(f"Statement: {sentence}")
#     sentiment_score(sentence)

#     print("\3rd Statement")
#     sentence = "I am feeling sad today"
#     print(f"Statement: {sentence}")
#     sentiment_score(sentence)
