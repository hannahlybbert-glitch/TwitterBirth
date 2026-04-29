## CLassifier Testing


### Classifier Full Sample

# 1. Import needed libraries
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support
import joblib



# 2. Load in dataset
# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_prepost_balanced_SAMPLE.csv")
df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_prepost_balanced_nolink_10k.csv")



# 3. Hold out 10%
X_temp, X_final, y_temp, y_final = train_test_split(
    df['text'], df['post'], test_size = 0.1, random_state = 42, stratify=df['post']
)

# 3A. Train/Test split on 90% from above
X_train, X_test, y_train, y_test = train_test_split(
    X_temp, y_temp, test_size = 0.2, random_state = 42, stratify=y_temp)


# 4. Define pipeline
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(
        lowercase=True, 
        stop_words='english', 
        max_features=30000,
        min_df = 5)),
    # ('clf', AdaBoostClassifier( #link
    #     random_state=42,
    #     learning_rate=1.0,
    #     n_estimators=100
    # ))
    ('clf', GradientBoostingClassifier( #nolink
        learning_rate=0.5,
        max_depth=5,
        n_estimators=100
    ))
    # ('clf', LogisticRegression( # link
    #     max_iter=1000,
    #     solver='saga',
    #     penalty= 'l1',
    #     C=0.1
    # ))
    # ('clf', XGBClassifier( # link
    #     learning_rate = 0.1,
    #     max_depth = 3,
    #     n_estimators = 100,
    #     subsample = 1.0)),
    # ('clf', XGBClassifier( # nolink
    #     learning_rate = 0.1,
    #     max_depth = 3,
    #     n_estimators = 100,
    #     subsample = 0.8))      
])


# 5. Fit and evaluate the model for 80% test
pipeline.fit(X_train, y_train)

# 5A. Evaluate the model
y_predict = pipeline.predict(X_test)

print("Accuracy 80% test:", accuracy_score(y_test, y_predict))
print(classification_report(y_test, y_predict))


# 6. Fit and evaluate the model for 10% holdout
pipeline.fit(X_temp, y_temp)

#6A. Evaluate the model
y_predict_final = pipeline.predict(X_final)

print("Accuracy 10% holdout:", accuracy_score(y_final, y_predict_final))
print(classification_report(y_final, y_predict_final))
metrics = classification_report(y_final, y_predict_final, output_dict=True)
pd.DataFrame(metrics).to_csv("D:/TwitterBirth/output/sentiment_analysis/classification_report_sample_nolink.csv")
# pd.DataFrame(metrics).to_csv("D:/TwitterBirth/output/sentiment_analysis/classification_report_sample.csv")


# 7. Save for future reference --> not sure how to open or reference a .pkl file
# joblib.dump(pipeline, "D:/TwitterBirth/output/sentiment_analysis/adaboost_tfidf_FULL.pkl")
# joblib.dump(pipeline, "D:/TwitterBirth/output/sentiment_analysis/adaboost_tfidf_nolink_FULL.pkl")


# ================================
# MODEL EVALUATION VISUALIZATIONS
# ================================

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, roc_curve, auc


# # --------------------------
# # 1. ROC Curve + AUC
# # --------------------------
# y_proba = pipeline.predict_proba(X_final)[:,1]  # predicted probabilities
# fpr, tpr, _ = roc_curve(y_final, y_proba)
# roc_auc = auc(fpr, tpr)

# plt.figure(figsize=(6,6))
# plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.2f}", color="blue")
# plt.plot([0,1],[0,1],'--',color='gray')
# plt.xlabel("False Positive Rate")
# plt.ylabel("True Positive Rate")
# plt.title("ROC Curve (Holdout Set, Link)")
# plt.legend()
# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/classifier_ROC_AUC10k_link.png", dpi=300, bbox_inches="tight")
# plt.close()

# # --------------------------
# # 2. Feature Importance (Top Words)
# # --------------------------
# feature_names = pipeline.named_steps['tfidf'].get_feature_names_out()
# importances = pipeline.named_steps['clf'].feature_importances_

# top_idx = importances.argsort()[::-1][:10]  # top 20 words
# plt.figure(figsize=(8,6))
# sns.barplot(x=importances[top_idx], y=feature_names[top_idx], palette="viridis")
# plt.title("Top 20 Most Important Features (Words), link")
# plt.xlabel("Importance")
# plt.ylabel("Word")
# plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/classifier_feature_words10k_link.png", dpi=300, bbox_inches="tight")
# plt.close()


## NO LINKS FIGURES
# 1. ROC Curve + AUC
y_proba = pipeline.predict_proba(X_final)[:,1]  # predicted probabilities
fpr, tpr, _ = roc_curve(y_final, y_proba)
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(6,6))
plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.2f}", color="blue")
plt.plot([0,1],[0,1],'--',color='gray')
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve (Holdout Set, NO links)")
plt.legend()
plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/classifier_ROC_AUC10k_nolink.png", dpi=300, bbox_inches="tight")
plt.close()

# 2. Feature Importance (Top Words)
feature_names = pipeline.named_steps['tfidf'].get_feature_names_out()
importances = pipeline.named_steps['clf'].feature_importances_

top_idx = importances.argsort()[::-1][:10]  # top 20 words
plt.figure(figsize=(8,6))
sns.barplot(x=importances[top_idx], y=feature_names[top_idx], palette="viridis")
plt.title("Top 20 Most Important Features (Words) NO links")
plt.xlabel("Importance")
plt.ylabel("Word")
plt.savefig("D:/TwitterBirth/output/sentiment_analysis/figures/10ksample/classifier_feature_words10k_nolink.png", dpi=300, bbox_inches="tight")
plt.close()





# # 4. Define pipeline
# pipeline = Pipeline([
#     ('tfidf', TfidfVectorizer(
#         lowercase=True, 
#         stop_words='english', 
#         max_features=5000)),
#     # ('clf', LogisticRegression(
#     #     max_iter=1000,
#     #     solver='saga',
#     #     penalty= 'l2',
#     #     C=1
#     # ))
#     # ('clf', RandomForestClassifier(
#     #     random_state=42,
#     #     max_depth=10,
#     #     n_estimators=200)),
#     ('clf', XGBClassifier(
#         learning_rate = 0.1,
#         max_depth = 3,
#         n_estimators = 100,
#         subsample = 1.0
#     ))
#     # ('clf', AdaBoostClassifier(
#     #     random_state=42,
#     #     n_estimators = 200,
#     #     learning_rate = 1.0)),
    
# ])