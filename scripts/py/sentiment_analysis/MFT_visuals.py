##### MFT VISUALIZATIONS ####

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
from sklearn.metrics.pairwise import cosine_similarity
import seaborn as sns
from MFT_analysis import nlp, family_seeds, politics_seeds, sports_seeds, religion_seeds, get_centroid

# FULL (no BA)
heatmap_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/MFT/multi_dim_heatmap_FULL.png"
heatmap_title = "Cosine Similarities between Centroids (full sample)"
network_title = "Centroid Similarity Network (full sample)"
network_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/MFT/network_graph_FULL.png"
df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/multi_dim_classified_FULL.csv")
histogram_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/MFT/fam_pol_hist.png"
hist_title = "Tweet distribution on Family-Politics axis (full sample)"
kernel_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/MFT/fam_pol_density.png"
kernel_title = "Density of Family ↔ Politics Scores (full sample)"
wordcloud_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/MFT/fam_pol_wordcloud.png"
fam_word_title = "Most Family-Oriented Tweets"
pol_word_title = "Most Politics-Oriented Tweets"

# ## No Birth Month
# heatmap_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/MFT/multi_dim_heatmap_FULL_1mo_drop.png"
# heatmap_title = "Cosine Similarities between Centroids (no birth month)"
# network_title = "Centroid Similarity Network (no birth month)"
# network_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/MFT/network_graph_FULL_1mo_drop.png"
# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/multi_dim_classified_FULL_1mo_drop.csv")
# histogram_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/MFT/fam_pol_hist_1mo_drop.png"
# hist_title = "Tweet distribution on Family-Politics axis (no birth month)"
# kernel_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/MFT/fam_pol_density_1mo_drop.png"
# kernel_title = "Density of Family ↔ Politics Scores (no birth month)"
# wordcloud_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/MFT/fam_pol_wordcloud_1mo_drop.png"
# fam_word_title = "Most Family-Oriented Tweets (no birth month)"
# pol_word_title = "Most Politics-Oriented Tweets (no birth month)"





## Sample
# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/multi_dim_classified_SAMPLE.csv")


if __name__ == "__main__":

    # Get centroids (avg word vector for each seed list)
    family_centroid = get_centroid(family_seeds, nlp)
    politics_centroid = get_centroid(politics_seeds, nlp)
    religion_centroid = get_centroid(religion_seeds, nlp)
    sports_centroid = get_centroid(sports_seeds, nlp)

    # 1. Similarity Matrix
    centroids = {"family": family_centroid, "politics": politics_centroid,
        "religion": religion_centroid, "sports": sports_centroid}
    names = list(centroids.keys()) # ['family', 'politics', 'religion', 'sports']
    vectors = np.stack(list(centroids.values())) #stack vectors in 2D numpy array (rows=centroids)
    sim_matrix = cosine_similarity(vectors) # [0,1] scores
    sim_df = pd.DataFrame(sim_matrix, index=names, columns=names)
    print(sim_df)

    # 2. HEAT MAP
    plt.figure(figsize=(6,5))
    sns.heatmap(sim_df, annot=True, cmap="Greens", vmin=0, vmax=1)
    plt.title(heatmap_title)
    plt.savefig(heatmap_fig, dpi=300, bbox_inches="tight")
    plt.close()
    # plt.show()

    # 3. NETWORK GRAPH
    G = nx.Graph() # Build graph
    for i, n1 in enumerate(names):
        for j, n2 in enumerate(names):
            if j > i:
                G.add_edge(n1, n2, weight=sim_df.loc[n1, n2]) # add edge with weight attribute (similarity value between two centroids)

    pos = nx.spring_layout(G, seed=42) # nodes with stronger connections are closer
    edges = G.edges(data=True) # extract edges and attributes
    weights = [d['weight']*5 for (_, _, d) in edges] # thicker lines for better visibility

    plt.figure(figsize=(6,6)) #6X6 inches
    nx.draw_networkx_nodes(G, pos, node_size=1000, node_color="lightblue") # large node size, light blue
    nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold")
    nx.draw_networkx_edges(G, pos, width=weights, edge_color="gray") # thicker lines for higher similarity

    edge_labels = {(u,v): f"{d['weight']:.2f}" for u,v,d in edges}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)

    plt.title(network_title)
    plt.axis("off") # hiding axes
    plt.savefig(network_fig, dpi=300, bbox_inches="tight")
    plt.close()



df["fam_pol_score"] = pd.to_numeric(df["fam_pol_score"], errors="coerce")

# --- Other Viz --- # 
# 4. Histogram
plt.hist(df["fam_pol_score"], bins=50)
plt.xlabel("Politics (-)   <----->   Family (+)")
plt.ylabel("Tweet count")
plt.title(hist_title)
plt.savefig(histogram_fig, dpi=300, bbox_inches="tight")
plt.close()

# 5. Kernel Density
sns.kdeplot(df["fam_pol_score"], fill=True)
plt.title(kernel_title)
plt.xlabel("Spectrum score (family - politics)")
plt.savefig(kernel_fig, dpi=300, bbox_inches="tight")
plt.close()


# 6. WORD CLOUD to view main predictors for family vs politics
from wordcloud import WordCloud
import matplotlib.pyplot as plt

# --- Parameters ---
top_pct = 0.05   # top 5% most extreme tweets on each side
text_column = "text"  # change this to your tweet text column name

# --- Split tweets into family-oriented and politics-oriented extremes ---
threshold_high = df["fam_pol_score"].quantile(1 - top_pct)
threshold_low = df["fam_pol_score"].quantile(top_pct)

family_tweets = df.loc[df["fam_pol_score"] >= threshold_high, text_column]
politics_tweets = df.loc[df["fam_pol_score"] <= threshold_low, text_column]

# --- Concatenate texts ---
family_text = " ".join(family_tweets.astype(str))
politics_text = " ".join(politics_tweets.astype(str))

# --- Generate Word Clouds ---
family_wc = WordCloud(width=800, height=400, background_color="white").generate(family_text)
politics_wc = WordCloud(width=800, height=400, background_color="white").generate(politics_text)

# --- Plot side by side ---
fig, axes = plt.subplots(1, 2, figsize=(16, 8))

axes[0].imshow(family_wc, interpolation="bilinear")
axes[0].set_title(fam_word_title, fontsize=16)
axes[0].axis("off")

axes[1].imshow(politics_wc, interpolation="bilinear")
axes[1].set_title(pol_word_title, fontsize=16)
axes[1].axis("off")

plt.savefig(wordcloud_fig, dpi=300, bbox_inches="tight")
plt.close()





# # ------------------------ 10K SAMPLE CODE -------------------------------- #
# if __name__ == "__main__":

#     # Get centroids (avg word vector for each seed list)
#     family_centroid = get_centroid(family_seeds, nlp)
#     politics_centroid = get_centroid(politics_seeds, nlp)
#     religion_centroid = get_centroid(religion_seeds, nlp)
#     sports_centroid = get_centroid(sports_seeds, nlp)

#     # Similarity Matrix
#     centroids = {"family": family_centroid, "politics": politics_centroid,
#         "religion": religion_centroid, "sports": sports_centroid}
#     names = list(centroids.keys()) # ['family', 'politics', 'religion', 'sports']
#     vectors = np.stack(list(centroids.values())) #stack vectors in 2D numpy array (rows=centroids)
#     sim_matrix = cosine_similarity(vectors) # [0,1] scores
#     sim_df = pd.DataFrame(sim_matrix, index=names, columns=names)
#     print(sim_df)

#     # HEAT MAP
#     plt.figure(figsize=(6,5))
#     sns.heatmap(sim_df, annot=True, cmap="Greens", vmin=0, vmax=1)
#     plt.title("Cosine Similarities between Centroids (10k), no birth month")
#     # plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/multi_dim_heatmap_10k.png", dpi=300, bbox_inches="tight")
#     plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/multi_dim_heatmap_10k_1mo_drop.png", dpi=300, bbox_inches="tight")
#     # plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/MFT/multi_dim_heatmap_FULL.png", dpi=300, bbox_inches="tight")
#     plt.close()
#     # plt.show()

#     # NETWORK GRAPH
#     G = nx.Graph() # Build graph
#     for i, n1 in enumerate(names):
#         for j, n2 in enumerate(names):
#             if j > i:
#                 G.add_edge(n1, n2, weight=sim_df.loc[n1, n2]) # add edge with weight attribute (similarity value between two centroids)

#     pos = nx.spring_layout(G, seed=42) # nodes with stronger connections are closer
#     edges = G.edges(data=True) # extract edges and attributes
#     weights = [d['weight']*5 for (_, _, d) in edges] # thicker lines for better visibility

#     plt.figure(figsize=(6,6)) #6X6 inches
#     nx.draw_networkx_nodes(G, pos, node_size=1000, node_color="lightblue") # large node size, light blue
#     nx.draw_networkx_labels(G, pos, font_size=12, font_weight="bold")
#     nx.draw_networkx_edges(G, pos, width=weights, edge_color="gray") # thicker lines for higher similarity

#     edge_labels = {(u,v): f"{d['weight']:.2f}" for u,v,d in edges}
#     nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_size=10)

#     plt.title("Centroid Similarity Network (10k), no birth month")
#     plt.axis("off") # hiding axes
#     # plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/network_graph_10k.png", dpi=300, bbox_inches="tight")
#     plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/network_graph_10k_1mo_drop.png", dpi=300, bbox_inches="tight")
#     # plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/MFT/network_graph_FULL.png", dpi=300, bbox_inches="tight")
#     plt.close()


# # df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/multi_dim_classified_SAMPLE.csv")
# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/multi_dim_classified_SAMPLE_1mo_drop.csv")
# df["fam_pol_score"] = pd.to_numeric(df["fam_pol_score"], errors="coerce")

# # 7. VISUALIZE
# # Histogram
# plt.hist(df["fam_pol_score"], bins=50)
# plt.xlabel("Politics (-)   <----->   Family (+)")
# plt.ylabel("Tweet count")
# plt.title("Tweet distribution on Family-Politics axis (10k), no birth month")
# # Set x-axis range and tick spacing
# plt.xlim(-0.3, 0.5)
# plt.xticks(np.arange(-0.3, 0.51, 0.1))
# # plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_hist_10k.png", dpi=300, bbox_inches="tight")
# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_hist_10k_1mo_drop.png", dpi=300, bbox_inches="tight")
# # plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_hist_big_seed_list10k.png", dpi=300, bbox_inches="tight")
# plt.close()

# # Kernel Density
# sns.kdeplot(df["fam_pol_score"], fill=True)
# plt.title("Density of Family ↔ Politics Scores (10k), no birth month")
# plt.xlabel("Spectrum score (family - politics)")
# # Set x-axis range and tick spacing
# plt.xlim(-0.3, 0.5)
# plt.xticks(np.arange(-0.3, 0.51, 0.1))
# # plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_density_10k.png", dpi=300, bbox_inches="tight")
# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_density_10k_1mo_drop.png", dpi=300, bbox_inches="tight")
# # plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_density_big_seed_list10k.png", dpi=300, bbox_inches="tight")
# plt.close()
# # plt.show()


# ## WORD CLOUD option?
# from wordcloud import WordCloud
# import matplotlib.pyplot as plt

# # --- Parameters ---
# top_pct = 0.05   # top 5% most extreme tweets on each side
# text_column = "text"  # change this to your tweet text column name

# # --- Split tweets into family-oriented and politics-oriented extremes ---
# threshold_high = df["fam_pol_score"].quantile(1 - top_pct)
# threshold_low = df["fam_pol_score"].quantile(top_pct)

# family_tweets = df.loc[df["fam_pol_score"] >= threshold_high, text_column]
# politics_tweets = df.loc[df["fam_pol_score"] <= threshold_low, text_column]

# # --- Concatenate texts ---
# family_text = " ".join(family_tweets.astype(str))
# politics_text = " ".join(politics_tweets.astype(str))

# # --- Generate Word Clouds ---
# family_wc = WordCloud(width=800, height=400, background_color="white").generate(family_text)
# politics_wc = WordCloud(width=800, height=400, background_color="white").generate(politics_text)

# # --- Plot side by side ---
# fig, axes = plt.subplots(1, 2, figsize=(16, 8))

# axes[0].imshow(family_wc, interpolation="bilinear")
# axes[0].set_title("Most Family-Oriented Tweets (10k), no birth month", fontsize=16)
# axes[0].axis("off")

# axes[1].imshow(politics_wc, interpolation="bilinear")
# axes[1].set_title("Most Politics-Oriented Tweets (10k), no birth month", fontsize=16)
# axes[1].axis("off")

# # plt.show()
# # plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_wordcloud_10k.png", dpi=300, bbox_inches="tight")
# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_wordcloud_10k_1mo_drop.png", dpi=300, bbox_inches="tight")
# # plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/fam_pol_wordcloud_big_seed_list10k.png", dpi=300, bbox_inches="tight")
# plt.close()















# ## FOUR DIMENSIONAL WORD CLOUD
# top_pct = 0.05
# text_column = "text"

# threshold_high = df["fam_pol_score"].quantile(1 - top_pct)
# threshold_low = df["fam_pol_score"].quantile(top_pct)
# family_tweets = df.loc[df["fam_pol_score"] >= threshold_high, text_column]
# politics_tweets = df.loc[df["fam_pol_score"] <= threshold_low, text_column]

# threshold_high = df["rel_sports_score"].quantile(1 - top_pct)
# threshold_low = df["rel_sports_score"].quantile(top_pct)
# religion_tweets = df.loc[df["rel_sports_score"] >= threshold_high, text_column]
# sports_tweets = df.loc[df["rel_sports_score"] <= threshold_low, text_column]

# family_text = " ".join(family_tweets.astype(str))
# politics_text = " ".join(politics_tweets.astype(str))
# religion_text = " ".join(religion_tweets.astype(str))
# sports_text = " ".join(sports_tweets.astype(str))

# family_wc = WordCloud(width=800, height=400, background_color="white").generate(family_text)
# politics_wc = WordCloud(width=800, height=400, background_color="white").generate(politics_text)
# religion_wc = WordCloud(width=800, height=400, background_color="white").generate(religion_text)
# sports_wc = WordCloud(width=800, height=400, background_color="white").generate(sports_text)

# fig, axes = plt.subplots(2, 2, figsize=(20, 16))

# axes[0, 0].imshow(family_wc, interpolation="bilinear")
# axes[0, 0].set_title("Most Family-Oriented Tweets", fontsize=16)
# axes[0, 0].axis("off")

# axes[0, 1].imshow(politics_wc, interpolation="bilinear")
# axes[0, 1].set_title("Most Politics-Oriented Tweets", fontsize=16)
# axes[0, 1].axis("off")

# axes[1, 0].imshow(religion_wc, interpolation="bilinear")
# axes[1, 0].set_title("Most Religion-Oriented Tweets", fontsize=16)
# axes[1, 0].axis("off")

# axes[1, 1].imshow(sports_wc, interpolation="bilinear")
# axes[1, 1].set_title("Most Sports-Oriented Tweets", fontsize=16)
# axes[1, 1].axis("off")

# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/four_way_wordcloud_10k.png", dpi=300, bbox_inches="tight")
# plt.close()
