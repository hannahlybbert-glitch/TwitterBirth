
import pandas as pd
import matplotlib.pyplot as plt

# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/vader_tweetNLP_comp_10k.csv")
df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/vader_sentiment_Kcode_10k.csv")

plt.scatter(df["vader_score"], df["tweetNLP_score"], alpha=0.3)
plt.xlabel("VADER Sentiment")
plt.ylabel("TweetNLP Sentiment")
plt.title("VADER vs TweetNLP Sentiment Comparison")
plt.show()

print("Correlation:", df["vader_score"].corr(df["tweetNLP_score"]))