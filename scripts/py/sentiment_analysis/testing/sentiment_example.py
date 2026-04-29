## Vader Sentiment analysis example code (to be built upon for actual analysis)

# Install needed packages --> make sure to install via Git Bash first
# pip install vaderSentiment
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# Create funciton to calculate sentiment scores
def sentiment_score(sentence):
    analyzer = SentimentIntensityAnalyzer()
    sentiment_dict = analyzer.polarity_scores(sentence)

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
    
# Test to see if function works
if __name__ == "__main__":
    print("\n1st Statement:")
    sentence = "Geeks for Geeks is an excellent platform for CSE studnets."
    print(f"Statement: {sentence}")
    sentiment_score(sentence)

    print("\n2nd Statement:")
    sentence = "Shewta played well in the match as usual."
    print(f"Statement: {sentence}")
    sentiment_score(sentence)

    print("\3rd Statement")
    sentence = "I am feeling sad today"
    print(f"Statement: {sentence}")
    sentiment_score(sentence)


# --------------------------------------------------------------------------------------------------#
# EXAMPLE 2

# from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
# #note: depending on how you installed (e.g., using source code download versus pip install), you may need to import like this:
# #from vaderSentiment import SentimentIntensityAnalyzer

# # --- examples -------
# sentences = ["VADER is smart, handsome, and funny.",      # positive sentence example
#             "VADER is smart, handsome, and funny!",       # punctuation emphasis handled correctly (sentiment intensity adjusted)
#             "VADER is very smart, handsome, and funny.",  # booster words handled correctly (sentiment intensity adjusted)
#             "VADER is VERY SMART, handsome, and FUNNY.",  # emphasis for ALLCAPS handled
#             "VADER is VERY SMART, handsome, and FUNNY!!!",# combination of signals - VADER appropriately adjusts intensity
#             "VADER is VERY SMART, uber handsome, and FRIGGIN FUNNY!!!",# booster words & punctuation make this close to ceiling for score
            
#             "VADER is not smart, handsome, nor funny.",   # negation sentence example
#             "VADER is definitely not smart, handsome, or funny.",   # booster word negative sentence example --> but it doesn't actually handle this very well 
#             "VADER is NOT smart, handsome, nor funny.",   # ALLCAPS negative sentence example
#             "VADER is not smart, handsome, nor funny!",   # punctuation negative sentence example
#             "VADER is NOT smart, handsome, nor funny!",   # punctuation and ALL CAPS negative sentence example
#             "VADER is NOT SMART, handsome, nor funny!!!",   # punctuation and ALL CAPS intensified negative sentence example
            
#             "The book was good.",                         # positive sentence
#             "The book was kind of good.",                 # qualified positive sentence is handled correctly (intensity adjusted)
#             "The plot was good, but the characters are uncompelling and the dialog is not great.", # mixed negation sentence
#             "At least it isn't a horrible book.",         # negated negative sentence with contraction
#             "Make sure you :) or :D today!",              # emoticons handled
#             "Make sure you 😊 or 😄 today!",              # image emoticons handled (image emojis receive a higher score than text emojis)
#             ":)",
#             "🙂",                                        # this one gets a worse score than just ":)" maybe because its creepy

#             "Today SUX!",                                 # negative slang with capitalization emphasis
#             "Today SUX! But I'll get by lol",
#             "Today SUX! But I'll get by",
#             "Today only kinda sux! But I'll get by, lol"  # mixed sentiment example with slang and constrastive conjunction "but"
#              ]

# analyzer = SentimentIntensityAnalyzer()
# for sentence in sentences:
#     vs = analyzer.polarity_scores(sentence)
#     print("{:-<65} {}".format(sentence, str(vs))) # {:-<65} is just for pretty printing (- fills empty spaces, < left aligns the text inside the field, 65 total characters is the width of the field)


# def sentiment_score(sentence):
#     analyzer = SentimentIntensityAnalyzer()
#     sentiment_dict = analyzer.polarity_scores(sentence)