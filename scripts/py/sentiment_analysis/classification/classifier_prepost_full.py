### Author: Hannah Lybbert
### Created: 11/14/2025
### Purpose: Full Script for pre/post prediction


import pandas as pd

df_old = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/text_aid_prepost.csv") # built in stata from "tweets_by_user_full_sample_CLEAN.dta." but just kept author_id, text, and post_birth

df_old["text"] = df_old["text"].fillna("").astype(str)

# -----------------------------------------
# STRIP YEARS from the text column
# -----------------------------------------
df_old["text"] = df_old["text"].str.replace(r"(18|19|20)\d{2}", " ", regex=True)
df_old["text"] = df_old["text"].str.replace(r"\s+", " ", regex=True).str.strip()


# Filter to authors who have BOTH pre (0) and post (1)
author_has_both = (
    df_old.groupby("author_id")["post_birth"]
             .nunique()
             .eq(2)
)

valid_authors = author_has_both[author_has_both].index

df_old = df_old[df_old["author_id"].isin(valid_authors)].reset_index(drop=True)

print("Remaining tweets:", len(df_old))
print("Remaining authors:", df_old["author_id"].nunique())

# -----------------------------------
# CONCATENATE TWEETS BY author_id & post
# -----------------------------------
df_full = (
    df_old
    .groupby(["author_id", "post_birth"])["text"]   # by aid and period
    .apply(lambda x: " ".join(x))             # join tweets with space
    .reset_index(name="text_concat")
)

print(df_full.head())

# --- Sample down to 10k entries for GridSearch (5000 pre / 5000 post) --- #
sampled_authors = (
    pd.Series(df_full["author_id"].unique())
      .sample(n=500, random_state=42)
      .tolist()
)

df = df_full[df_full["author_id"].isin(sampled_authors)]

print(df["post"].value_counts())

# Save for later 
df_full.to_csv("D:/TwitterBirth/data/sentiment_analysis/output/text_onedoc.csv", index=False) #8,280 observations, 4,140 accounts
df.to_csv("D:/TwitterBirth/data/sentiment_analysis/output/text_onedoc_sample.csv", index=False) # 1,000 obs, 500 accounts



# ---------------------------- ANALYSIS ---------------------------------------- #
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.svm import LinearSVC
from sklearn.metrics import classification_report, accuracy_score
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

# ---- figures
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from sklearn.metrics import confusion_matrix, roc_curve, auc

# Paths
# output_path = "D:/TwitterBirth/output/sentiment_analysis/class_report/classif_report_LSVC.csv"
# auc_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/one_doc/classifier_ROCAUC_LSVC.png"
# heatmap_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/one_doc/classifier_conf_mtx_LSVC.png"
# features_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/one_doc/classifier_featwords_LSVC.png"
# auc_title = "ROC Curve (TF-IDF, Linear SVC)"
# heatmap_title = "Confusion Matrix (TF-IDF, Linear SVC)"
# features_title = "Top 20 Most Important Features (TF-IDF, Linear SVC)"

output_path = "D:/TwitterBirth/output/sentiment_analysis/class_report/classif_report_L2.csv"
auc_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/classifier_ROCAUC_L2.png"
heatmap_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/classifier_conf_mtx_L2.png"
features_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/classifier_featwords_L2.png"
auc_title = "ROC Curve (TF-IDF, LogReg L2)"
heatmap_title = "Confusion Matrix (TF-IDF, LogReg L2)"
features_title = "Top 20 Most Important Features (TF-IDF, LogReg L2)"

# 1. Load dataset 
df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/text_onedoc.csv")
# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/text_onedoc_sample.csv")

texts = df["text_concat"].astype(str)
y = df["post_birth"]

# 2. TF-IDF
tfidf =  TfidfVectorizer(
        ngram_range=(1,2),
        min_df=3,
        max_df=0.7,
        # lowercase=True,
        # stop_words='english',
        max_features=200_000,
        sublinear_tf=True
)

X_tfidf = tfidf.fit_transform(texts)
print("TF-IDF shape:", X_tfidf.shape)

print("Checking TF-IDF vocabulary for 2019:")
print([w for w in tfidf.get_feature_names_out() if "2019" in w])

# ------- SPLIT DATA ------ #
# 3. 10% lockbox holdout
X_temp, X_lock, y_temp, y_lock = train_test_split(
    X_tfidf, y, test_size=0.10, random_state=42, stratify=y
)

# 4. Train/test on remaining 90% (from above)
X_train_tfidf, X_test_tfidf, y_train, y_test = train_test_split(
    X_temp, y_temp, test_size=0.20, random_state=42, stratify=y_temp
)

# 5. Feature selection
k = 5000 # change to 5000 if better performance that way

selector = SelectKBest(score_func=f_classif, k=k)
selector.fit(X_train_tfidf, y_train)

X_train_sel = selector.transform(X_train_tfidf)
X_test_sel  = selector.transform(X_test_tfidf)
X_lock_sel  = selector.transform(X_lock)


print("Original dimensionality:", X_train_tfidf.shape[1])
print("Selected dimensionality:", X_train_sel.shape[1])


# 6. Final Classifier (models to run)
# clf = LinearSVC(random_state=42, C=1.0, max_iter=5000, penalty='l2') # use k=5k
clf = LogisticRegression(random_state=42, max_iter=1000, solver='saga', C=10, penalty='l2') # 5k

clf.fit(X_train_sel, y_train)

# 7. Evaluate Test Set
y_pred = clf.predict(X_test_sel)
print("\n### TF-IDF Performance ###")
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))




# =========================
# MODEL EVALUATION FIGURES
# =========================

# --- ROC Curve ---
# Get predicted probabilities from your fitted classifier
y_proba_test = clf.predict_proba(X_test_sel)[:, 1]

fpr, tpr, _ = roc_curve(y_test, y_proba_test)
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(6,6))
plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.2f}")
plt.plot([0,1],[0,1],'--',color='gray')
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title(auc_title)
plt.legend()
plt.savefig(auc_fig, dpi=300, bbox_inches="tight")
plt.close()


# --- Confusion Matrix ---
y_pred = clf.predict(X_test_sel)

cm = confusion_matrix(y_test, y_pred)
cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

plt.figure(figsize=(6,4))
sns.heatmap(cm_normalized, annot=True, fmt=".2f", cmap="Blues",
            xticklabels=["Pre","Post"],
            yticklabels=["Pre","Post"])
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title(heatmap_title)
plt.savefig(heatmap_fig, dpi=300, bbox_inches="tight")
plt.close()


# --- Feature Importance ---
selected_indx = selector.get_support(indices=True) # get indices of selected features
selected_feature_names = tfidf.get_feature_names_out()[selected_indx] # index into the tf-idf vocab
coefs = clf.coef_[0] # pair with coefs from log reg
abs_coefs = np.abs(coefs) # compute abs values of coefficients 

# Get top 20 indices:
topN = 20
top_idx = np.argsort(abs_coefs)[-topN:][::-1]
top_features = selected_feature_names[top_idx]
top_coef_values = coefs[top_idx]

cmap = mpl_cm.get_cmap("viridis")
colors = cmap(np.linspace(0, 1, len(top_features)))

plt.figure(figsize=(10, 8))

plt.barh(top_features, abs_coefs[top_idx], color=colors)
plt.xlabel("Absolute Coefficient Value")
plt.title(features_title)
plt.gca().invert_yaxis()
plt.tight_layout()
plt.savefig(features_fig, dpi=300)
plt.close()





# # ---- ROC for LSVC ---- #
# # SVM scores (distance from hyperplane)
# scores_test = clf.decision_function(X_test_sel)

# # Compute ROC
# fpr, tpr, _ = roc_curve(y_test, scores_test)
# roc_auc = auc(fpr, tpr)

# # Plot ROC curve
# plt.figure(figsize=(6,6))
# plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.2f}")
# plt.plot([0,1], [0,1], '--', color='gray')
# plt.xlabel("False Positive Rate")
# plt.ylabel("True Positive Rate")
# plt.title(auc_title)
# plt.legend()
# plt.savefig(auc_fig, dpi=300, bbox_inches="tight")
# plt.close()

# # ----- FEATURE IMPORTANCE LSVC ---- #
# tfidf_names = tfidf.get_feature_names_out()
# mask = selector.get_support()
# selected_names = tfidf_names[mask]

# # Coefficients (weights)
# coefs = clf.coef_[0]                # shape (k,)

# # Absolute magnitude → importance
# abs_coefs = np.abs(coefs)

# # Top 20 strongest features
# top_idx = abs_coefs.argsort()[::-1][:20]

# plt.figure(figsize=(8,6))
# sns.barplot(
#     x=abs_coefs[top_idx],
#     y=[selected_names[i] for i in top_idx],
#     palette="viridis"
# )
# plt.title(features_title)
# plt.xlabel("Importance (|weight|)")
# plt.ylabel("Feature (word/phrase)")
# plt.tight_layout()
# plt.savefig(features_fig, dpi=300, bbox_inches="tight")
# plt.close()