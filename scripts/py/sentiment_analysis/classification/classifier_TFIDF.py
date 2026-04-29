### Author: Hannah Lybbert
### Created: 11/19/2025
### Purpose: Running Full Dataset on classification model based on GridSearch optimal model

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
from matplotlib import cm as mpl_cm
import seaborn as sns
import numpy as np
from sklearn.metrics import confusion_matrix, roc_curve, auc



# Paths
output_path = "D:/TwitterBirth/output/sentiment_analysis/class_report/classif_report_L2.csv"
auc_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/classifier_ROCAUC_L2.png"
heatmap_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/classifier_conf_mtx_L2.png"
features_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/classifier_featwords_L2.png"
auc_title = "ROC Curve (TF-IDF, LogReg L2)"
heatmap_title = "Confusion Matrix (TF-IDF, LogReg L2)"
features_title = "Top 20 Most Important Features (TF-IDF, LogReg L2)"

output_path = "D:/TwitterBirth/output/sentiment_analysis/class_report/classif_report_L2_nofam.csv"
auc_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/classifier_ROCAUC_L2_nofam.png"
heatmap_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/classifier_conf_mtx_L2_nofam.png"
features_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/classifier_featwords_L2_nofam.png"
auc_title = "ROC Curve (TF-IDF, LogReg L2, No Family Tweets)"
heatmap_title = "Confusion Matrix (TF-IDF, LogReg L2, No Family Tweets)"
features_title = "Top 20 Most Important Features (TF-IDF, LogReg L2, No Family Tweets)"

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


# Feature Importance
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

# plt.barh(top_features, top_coef_values, color=colors)
# plt.xlabel("Coefficient Value")
# plt.title(features_title)
# plt.gca().invert_yaxis()  # most important at top
# plt.tight_layout()
# plt.savefig(features_fig, dpi=300)
# plt.show()

# plt.figure(figsize=(8,6))
# sns.barplot(x=importances[top_idx], y=selected_names[top_idx], palette="viridis")
# plt.title(features_title)
# plt.xlabel("Importance")
# plt.ylabel("Word")
# plt.savefig(features_fig, dpi=300, bbox_inches="tight")
# plt.close()





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


'''
no TF-IDF parameter change (my old ones) + Adaboost + K selection 5,000:
    Accuracy 80% test: 0.7486595174262735

TF-IDF parameter changes + Adaboost (learning rate=0.5) + k selection 5,000:
    Accuracy 80% test: 0.7761394101876675

*TF-IDF parameter changes + Adaboost (learning rate=0.5) + k selection 20,000:
    Accuracy 80% test: 0.7828418230563002
    sample --> 0.756

TF-IDF parameter changes + Adaboost (learning rate=0.25) + k selection 5,000:
    Accuracy 80% test: 0.7580428954423593

TF-IDF parameter changes + Adaboost (learning rate=0.25) + k selection 20,000:
    Accuracy 80% test: 0.7694369973190348


    
*TF-IDF parameter changes + LinearSVC + K selection 5,000
    Accuracy 80% test: 0.8016085790884718
    sample --> 0.7

TF-IDF parameter changes + LinearSVC + K selection 20,000
    Accuracy 80% test: 0.7935656836461126

    
clf = ('clf', LogisticRegression(random_state=42, max_iter=1000, solver='saga', C=10, penalty='l2'))
k_best = 5000
    Accuracy 80% test: 0.802949

clf = ('clf', LogisticRegression(random_state=42, max_iter=1000, solver='saga', C=10, penalty='l1'))
k_best = 5000
    Accuracy 80% test: 0.795576

clf = ('clf', LogisticRegression(random_state=42, max_iter=1000, solver='saga', C=10, penalty='elasticnet'))
k_best = 5000
    Accuracy 80% test: 0.8042895

clf = ('clf', RandomForestClassifier(random_state=42, max_depth=10, n_estimators=100))
k_best = 5000
    Accuracy 80% test: 0.76273458

clf = ('clf', AdaBoostClassifier(random_state=42, learning_rate=0.5, n_estimators=150))
k_best = 20000
    Accuracy 80% test: 0.7828418

clf = ('clf', LinearSVC(random_state=42, C=1.0, max_iter=5000, penalty='l2'))
k_best = 5000
    Accuracy 80% test: 0.801608579

'''


# ----------- PREVIOUS NOTES ---------------- #
# output_path = "D:/TwitterBirth/output/sentiment_analysis/class_report/classif_report_LSVC.csv"
# auc_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/one_doc/classifier_ROCAUC_LSVC.png"
# heatmap_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/one_doc/classifier_conf_mtx_LSVC.png"
# features_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/one_doc/classifier_featwords_LSVC.png"
# auc_title = "ROC Curve (TF-IDF, Linear SVC)"
# heatmap_title = "Confusion Matrix (TF-IDF, Linear SVC)"
# features_title = "Top 20 Most Important Features (TF-IDF, Linear SVC)"

# output_path = "D:/TwitterBirth/output/sentiment_analysis/class_report/classif_report_AdaB.csv"
# auc_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/one_doc/classifier_ROCAUC_AdaB.png"
# heatmap_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/one_doc/classifier_conf_mtx_AdaB.png"
# features_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/one_doc/classifier_featwords_AdaB.png"
# auc_title = "ROC Curve (TF-IDF, AdaBoost)"
# heatmap_title = "Confusion Matrix (TF-IDF, AdaBoost)"
# features_title = "Top 20 Most Important Features (TF-IDF, AdaBoost)"

# output_path = "D:/TwitterBirth/output/sentiment_analysis/class_report/classif_report_LogReg.csv"
# auc_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/one_doc/classifier_ROCAUC_LogReg.png"
# heatmap_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/one_doc/classifier_conf_mtx_LogReg.png"
# auc_title = "ROC Curve (TF-IDF, ElasticNet)"
# heatmap_title = "Confusion Matrix (TF-IDF, ElasticNet)"
# features_title = "Top 20 Most Important Features (TF-IDF, ElasticNet)"


# clf = AdaBoostClassifier(random_state=42, learning_rate=0.5, n_estimators=150) # use k=10k
# clf = RandomForestClassifier(random_state=42, max_depth=10, n_estimators=100) # use k=5k
# clf = LogisticRegression(random_state=42, max_iter=1000, solver='saga', C=10, l1_ratio=0.75, penalty='elasticnet') # use k=5k
# clf = LogisticRegression(random_state=42, max_iter=1000, solver='saga', C=10, penalty='l1') # use k=20k


# # 1. Load dataset 
# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/text_onedoc.csv")
# # df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/text_onedoc_sample.csv")

# # ------- SPLIT DATA ------ #
# # Hold out 10%
# X_temp, X_final, y_temp, y_final = train_test_split(
#     df['text_concat'], df['post'], test_size = 0.1, random_state = 42, stratify=df['post']
# )

# # Train/Test split on 90% from above
# X_train, X_test, y_train, y_test = train_test_split(
#     X_temp, y_temp, test_size = 0.2, random_state = 42, stratify=y_temp)


# -------- MODELS ----------- #
# clf = ('clf', AdaBoostClassifier(random_state=42, learning_rate=0.5, n_estimators=150))
# # clf = ('clf', AdaBoostClassifier(random_state=42, learning_rate=0.25, n_estimators=200))
# clf = ('clf', LinearSVC(random_state=42, C=1.0, max_iter=5000, penalty='l2'))

# clf = ('clf', LogisticRegression(random_state=42, max_iter=1000, solver='saga', C=10, penalty='l2'))
# k_best = 5000

# clf = ('clf', LogisticRegression(random_state=42, max_iter=1000, solver='saga', C=10, penalty='l1'))
# k_best = 5000

# clf = ('clf', LogisticRegression(random_state=42, max_iter=1000, solver='saga', C=10, l1_ratio=0.75, penalty='elasticnet'))
# k_best = 5000

# clf = ('clf', RandomForestClassifier(random_state=42, max_depth=10, n_estimators=100))
# k_best = 5000

# clf = ('clf', AdaBoostClassifier(random_state=42, learning_rate=0.5, n_estimators=150))
# k_best = 20000

# clf = ('clf', LinearSVC(random_state=42, C=1.0, max_iter=5000, penalty='l2'))
# k_best = 5000


# # 4. Define pipeline
# pipeline = Pipeline([
#     ('tfidf', TfidfVectorizer(
#         ngram_range=(1,2),
#         min_df=3,
#         max_df=0.7,
#         # lowercase=True,
#         # stop_words='english',
#         max_features=200_000,
#         sublinear_tf=True)),
#     ('select', SelectKBest(score_func=f_classif, k=k_best)),
#     clf
# ])


# # 5. Fit and evaluate the model for 80% test
# pipeline.fit(X_train, y_train)
# y_predict = pipeline.predict(X_test)

# print("Accuracy 80% test:", accuracy_score(y_test, y_predict))
# print(classification_report(y_test, y_predict))


# # Feature Importance
# tfidf_names = tfidf.get_feature_names_out()

# mask = selector.get_support()
# selected_names = tfidf_names[mask]

# importances = clf.feature_importances_

# top_idx = importances.argsort()[::-1][:20]

# plt.figure(figsize=(8,6))
# sns.barplot(x=importances[top_idx], y=selected_names[top_idx], palette="viridis")
# plt.title(features_title)
# plt.xlabel("Importance")
# plt.ylabel("Word")
# plt.savefig(features_fig, dpi=300, bbox_inches="tight")
# plt.close()
