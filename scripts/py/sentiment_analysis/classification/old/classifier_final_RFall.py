### Classifier Full Sample

# 1. Import needed libraries
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.model_selection import cross_val_score
from statsmodels.stats.proportion import proportion_confint
import scipy.stats as st
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier, GradientBoostingClassifier
from xgboost import XGBClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support
import joblib


# 2. Load in variables (datasets, titles, links...)
clf = ('clf', RandomForestClassifier(random_state=42, max_depth=20, n_estimators=200))

# ## Full dataset (link included, no BA)
# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_prepost_balanced_FULL.csv")
# output_path = "D:/TwitterBirth/output/sentiment_analysis/class_report/classification_report_RF.csv"
# auc_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/RF/classifier_ROC_AUC.png"
# heatmap_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/RF/classifier_confusion_matrix.png"
# features_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/RF/feature_words_link.png"
# auc_title = "ROC Curve (Holdout Set) RF"
# heatmap_title = "Confusion Matrix (Row-normalized, Holdout Set) RF"
# features_title = "Top 20 Most Important Features (Words) RF"

# ## No Link, no BA
# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_prepost_balanced_nolink_FULL.csv")
# output_path = "D:/TwitterBirth/output/sentiment_analysis/class_report/classification_report_nolink_RF.csv"
# auc_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/RF/classifier_ROC_AUC_nolink.png"
# heatmap_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/RF/classifier_confusion_matrix_nolink.png"
# features_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/RF/feature_words_nolink.png"
# auc_title = "ROC Curve (Holdout Set) No Link RF"
# heatmap_title = "Confusion Matrix (Row-normalized, Holdout Set) No Link RF"
# features_title = "Top 20 Most Important Features (Words) No Link RF"

## Link included, no Birth Month
df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_prepost_balanced_1mo_drop.csv")
output_path = "D:/TwitterBirth/output/sentiment_analysis/class_report/classification_report_1mo_drop_RF.csv"
auc_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/RF/classifier_ROC_AUC_1mo_drop.png"
heatmap_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/RF/classifier_confusion_matrix_1mo_drop.png"
features_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/RF/feature_words_link_1mo_drop.png"
auc_title = "ROC Curve (Holdout Set) No Birth Month RF"
heatmap_title = "Confusion Matrix (Row-normalized, Holdout Set) No Birth Month RF"
features_title = "Top 20 Most Important Features (Words) No Birth Month RF"

# ## No Link, No Birth Month
# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_prepost_balanced_1mo_drop_nolink.csv")
# output_path = "D:/TwitterBirth/output/sentiment_analysis/class_report/classification_report_nolink_1mo_drop_RF.csv"
# auc_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/RF/classifier_ROC_AUC_nolink_1mo_drop.png"
# heatmap_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/RF/classifier_confusion_matrix_nolink_1mo_drop.png"
# features_fig = "D:/TwitterBirth/output/sentiment_analysis/figures/classification/RF/feature_words_nolink_1mo_drop.png"
# auc_title = "ROC Curve (Holdout Set) No Link & No Birth Month RF"
# heatmap_title = "Confusion Matrix (Row-normalized, Holdout Set) No Link & No Birth Month RF"
# features_title = "Top 20 Most Important Features (Words) No Link & No Birth Month RF"



# 3. Hold out 10%
X_temp, X_final, y_temp, y_final = train_test_split(
    df['text'], df['post_birth'], test_size = 0.1, random_state = 42, stratify=df['post_birth']
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
    clf
])


#---------- 80% test ----------#

# 5. Fit and evaluate the model for 80% test
pipeline.fit(X_train, y_train)
y_predict = pipeline.predict(X_test)

print("Accuracy 80% test:", accuracy_score(y_test, y_predict))
print(classification_report(y_test, y_predict))

# 5B. ConfIntervals for 80%
# scores_cv = cross_val_score(pipeline, X_temp, y_temp, cv=5, scoring='accuracy')
# print(f"Mean CV accuracy (80% train): {scores_cv.mean():.3f} (+/- {scores_cv.std():.3f})")
# ci_low, ci_high = st.t.interval(
#     0.95, len(scores_cv)-1, loc=np.mean(scores_cv), scale=st.sem(scores_cv)
# )
# print(f"95% CI for 80% train: ({ci_low:.3f}, {ci_high:.3f})")


#---------- 10% holdout ----------#

# 6. Fit and evaluate the model for 10% holdout
pipeline.fit(X_temp, y_temp)
y_predict_final = pipeline.predict(X_final)

print("\n Accuracy 10% holdout:", accuracy_score(y_final, y_predict_final))
print(classification_report(y_final, y_predict_final))
metrics = classification_report(y_final, y_predict_final, output_dict=True)
pd.DataFrame(metrics).to_csv(output_path)


# 6B. CI for 10% (Wilson CI for holdout accuracy)
holdout_acc = accuracy_score(y_final, y_predict_final)
ci_low_h, ci_high_h = proportion_confint(
    holdout_acc * len(y_final), len(y_final), alpha=0.05, method='wilson'
)
print(f"95% CI for 10% holdout (analytical): ({ci_low_h:.3f}, {ci_high_h:.3f})\n")



# # 7. Save for future reference --> not sure how to open or reference a .pkl file
# joblib.dump(pipeline, pkl_output)





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
y_proba = pipeline.predict_proba(X_final)[:,1]  # predicted probabilities
fpr, tpr, _ = roc_curve(y_final, y_proba)
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
# plt.show()

# --------------------------
# 3. Confusion Matrix (heatmap)
# --------------------------
cm = confusion_matrix(y_final, y_predict_final)
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
# plt.show()

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