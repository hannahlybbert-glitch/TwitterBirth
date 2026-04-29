### Author: Hannah Lybbert
### Created: 11/14/2025
### Purpose: testing TF-IDF vectorization for pre/post classification

## Build classification one doc file

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.svm import LinearSVC
import xgboost as xgb
from xgboost import XGBClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin

df_old = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/text_aid_prepost.csv")

df_old["text"] = df_old["text"].fillna("").astype(str)

df_full = (
    df_old
    .groupby(["author_id", "post"])["text"] # by aid and period
    .apply(lambda x: " ".join(x)) # join tweets with space
    .reset_index(name="text_concat"))

print(df_full.head())


# ------ 10k sample for GridSearch (5000 pre / 5000 post------ #
# authors = df_full["author_id"].unique()
valid_authors = (
    df_full.groupby("author_id")
    .filter(lambda x: len(x) == 2)["author_id"]
    .unique()
)
sampled_authors = pd.Series(valid_authors).sample(n=500, random_state=42).tolist()
df = df_full[df_full["author_id"].isin(sampled_authors)]
print(df["post"].value_counts())


# --- Define vars --- #
output_path = "D:/TwitterBirth/output/sentiment_analysis/class_report/classification_report_1doc_tfidf_T1.csv"
auc_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/one_doc/classifier_1doc_ROCAUC_tfidf_T1.png"
heatmap_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/one_doc/classifier_1doc_confusion_matrix_tfidf_T1.png"
features_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/one_doc/classifier_1doc_feature_words_tfidf_T1.png"
auc_title = "ROC Curve (TF-IDF)"
heatmap_title = "Confusion Matrix (TF-IDF)"
features_title = "Top 20 Most Important Features (TF-IDF)"



clf = ('clf', AdaBoostClassifier(random_state=42, learning_rate=0.5, n_estimators=150))


# ------ Classification best model ------ #

# 3. Hold out 10%
X_temp, X_final, y_temp, y_final = train_test_split(
    df['text_concat'], df['post'], test_size = 0.1, random_state = 42, stratify=df['post']
)

# 3A. Train/Test split on 90% from above
X_train, X_test, y_train, y_test = train_test_split(
    X_temp, y_temp, test_size = 0.2, random_state = 42, stratify=y_temp)




# 4. Define pipeline
# pipeline = Pipeline([
#     ('tfidf', TfidfVectorizer(
#         lowercase=True, 
#         stop_words='english', 
#         max_features=30000,
#         min_df = 5)),
#     ('clf', LogisticRegression())])
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(
        lowercase=True, 
        stop_words='english', 
        max_features=30000,
        min_df = 5)),
    clf
    ])


# 5. Fit and evaluate the model for 80% test
pipeline.fit(X_train, y_train)
y_predict = pipeline.predict(X_test)

print("Accuracy 80% test:", accuracy_score(y_test, y_predict))
print(classification_report(y_test, y_predict))



# ================================
# MODEL EVALUATION VISUALIZATIONS
# ================================

import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, roc_curve, auc, precision_recall_curve


# --------------------------
# 1. ROC Curve + AUC
# --------------------------
y_proba_test = pipeline.predict_proba(X_test)[:, 1]  # predicted probabilities
fpr, tpr, _ = roc_curve(y_test, y_proba_test)
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(6,6))
plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.2f}", color="blue")
plt.plot([0,1],[0,1],'--',color='gray')
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title(auc_title)
plt.legend()
plt.savefig(auc_fig, dpi=300, bbox_inches="tight")
plt.close()

# --------------------------
# 3. Confusion Matrix (heatmap)
# --------------------------
y_pred = pipeline.predict(X_test)

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

# --------------------------
# 2. Feature Importance (Top Words)
# --------------------------
feature_names = pipeline.named_steps['tfidf'].get_feature_names_out()
importances = pipeline.named_steps['clf'].feature_importances_

top_idx = importances.argsort()[::-1][:20]  # top 20 words
plt.figure(figsize=(8,6))
sns.barplot(x=importances[top_idx], y=feature_names[top_idx], palette="viridis")
plt.title(features_title)
plt.xlabel("Importance")
plt.ylabel("Word")
plt.savefig(features_fig, dpi=300, bbox_inches="tight")
plt.close()
# plt.show()






# ------ GRID SEARCH - best performing model ------ #

# # 5. Define parameter grid
# param_grid = [
#     # Logistic Regression L2 (ridge)
#     {
#         'clf': [LogisticRegression(max_iter=1000, solver='saga')],
#         'clf__penalty': ['l2'],
#         'clf__C': [0.01, 0.1, 1, 10]  # regularization strength
#     },
#     # Logistic Regression L1 (lasso)
#     {
#         'clf': [LogisticRegression(max_iter=1000, solver='saga')],
#         'clf__penalty': ['l1'],
#         'clf__C': [0.01, 0.1, 1, 10]
#     },
#     # Logistic Regression l1+l2 (elasticnet)
#     {
#         'clf': [LogisticRegression(max_iter=1000, solver='saga')],
#         'clf__penalty': ['elasticnet'],
#         'clf__C': [0.01, 0.1, 1, 10]
#     },
#     # Random Forest (bagging)
#     {
#         'clf': [RandomForestClassifier(random_state=42)],
#         'clf__n_estimators': [100, 200],
#         'clf__max_depth': [10, 20, None]
#     },
#     # Gradient Boosting
#     {
#         'clf': [GradientBoostingClassifier(random_state=42)],
#         'clf__n_estimators': [100, 200],
#         'clf__learning_rate': [0.5, 1.0], # sequential correction (each tree correcting previous tree errors)
#         'clf__max_depth': [3, 5, 7, 10] # tree depth
#     },
#     # AdaBoost 
#     {
#         'clf': [AdaBoostClassifier(random_state=42)],
#         'clf__n_estimators': [25, 50, 100, 150, 200],
#         'clf__learning_rate': [0.1, 0.25, 0.5, 1.0]
#     },
#     {
#         'clf': [LinearSVC(random_state=42)],
#         'clf__penalty': ['l2', 'l1'],
#         'clf__C': [0.01, 0.1, 1, 10],
#         'clf__max_iter': [2000, 5000, 10000]
#     }
# ]


# # 6. Run GridSearchCV
# grid = GridSearchCV(
#     pipeline,
#     param_grid,
#     cv=5,                # 5-fold cross validation
#     scoring='accuracy',  # could also use 'f1', 'roc_auc', etc.
#     n_jobs=-1,           # use all CPU cores
#     verbose=2
# )

# grid.fit(X_train, y_train)

# # 7. Evaluate on test set
# y_pred = grid.predict(X_test)
# print("\n Best Parameters:", grid.best_params_)
# print("Accuracy on Test:", accuracy_score(y_test, y_pred))
# print(classification_report(y_test, y_pred))


'''
my results:

 Best Parameters: {'clf': GradientBoostingClassifier(random_state=42), 'clf__learning_rate': 1.0, 'clf__max_depth': 7, 'clf__n_estimators': 100}
Accuracy on Test: 0.6944444444444444
'''