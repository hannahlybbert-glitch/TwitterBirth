# ------ SENTIMENT VIZ ------ #

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

# df = pd.read_csv('D:/TwitterBirth/data/sentiment_analysis/output/tweet_sentiment_10kSAMPLE.csv')
# df = pd.read_csv('D:/TwitterBirth/data/sentiment_analysis/output/sentimentVADER/tweet_sentiment_FULL.csv')
df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/sentimentVADER/tweet_sentiment_FULL_1mo_drop.csv")


# Make sure 'post' is categorical for nice labeling
df['post'] = df['post'].map({0: 'Pre', 1: 'Post'})
df['post'] = pd.Categorical(df['post'], categories=["Pre", "Post"], ordered=True)

# ------------------------
# 1. Side-by-side Boxplot
# ------------------------
plt.figure(figsize=(8,6))
sns.boxplot(x='post', y='compound', data=df, palette="Set2", order=["Pre", "Post"])
plt.title("Compound Sentiment Score: Pre vs Post (1 month drop)")
plt.xlabel("Tweet Timing")
plt.ylabel("Compound Sentiment Score [(-) Negative | (+) Positive]")
# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/sentiment_boxplot10k.png", dpi=300, bbox_inches="tight")
# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/sentiment/boxplotFULL.png", dpi=300, bbox_inches="tight")
plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/sentiment/boxplotFULL_1mo_drop.png", dpi=300, bbox_inches="tight")
plt.close()

# ------------------------
# 2. Heatmap of Sentiment Counts
# ------------------------
heatmap_data = pd.crosstab(df['overall'], df['post'], normalize='columns') * 100
plt.figure(figsize=(6,4))
sns.heatmap(heatmap_data, annot=True, fmt=".1f", cmap="Blues")
plt.title("Distribution of Sentiment Categories (%) (1 month drop)")
plt.ylabel("Sentiment Category")
plt.xlabel("Tweet Timing")
# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/sentiment_heat_map10k.png", dpi=300, bbox_inches="tight")
# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/sentiment/heat_mapFULL.png", dpi=300, bbox_inches="tight")
plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/sentiment/heat_mapFULL_1mo_drop.png", dpi=300, bbox_inches="tight")
plt.close()

# ------------------------
# 3. Side-by-side Bar Chart
# ------------------------
bar_data = df.groupby(['post', 'overall']).size().reset_index(name='count')
bar_data['percent'] = bar_data.groupby('post')['count'].transform(lambda x: 100 * x / x.sum())
plt.figure(figsize=(8,6))
ax = sns.barplot(
    x='overall', 
    y='percent', 
    hue='post', 
    data=bar_data, 
    hue_order=["Pre","Post"], 
    palette="Set2"
)
# Add percentage labels on top of each bar
for container in ax.containers:
    ax.bar_label(container, fmt="%.1f%%", label_type="edge", fontsize=10, padding=2)
plt.title("Sentiment Category Counts Pre vs Post (1 month drop)")
plt.xlabel("Sentiment Category")
plt.ylabel("Percentage of Tweets (%)")
plt.legend(title="Tweet Timing")
# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/sentiment_barchart10k.png", dpi=300, bbox_inches="tight")
# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/sentiment/barchartFULL.png", dpi=300, bbox_inches="tight")
plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/sentiment/barchartFULL_1mo_drop.png", dpi=300, bbox_inches="tight")
plt.close()

