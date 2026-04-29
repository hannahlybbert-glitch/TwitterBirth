# ---------- Classifier VIZ ----------- #

# ================================
# MODEL EVALUATION VISUALIZATIONS
# ================================
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.metrics import confusion_matrix, precision_recall_fscore_support, roc_curve, auc

# --------------------------
# 1. Confusion Matrix (Normalized %)
# --------------------------
cm = confusion_matrix(y_final, y_predict_final)
cm_norm = cm.astype("float") / cm.sum(axis=1)[:, np.newaxis]

plt.figure(figsize=(6,5))
sns.heatmap(cm_norm, annot=True, fmt=".2f", cmap="Blues",
            xticklabels=[0,1], yticklabels=[0,1])
plt.xlabel("Predicted")
plt.ylabel("Actual")
plt.title("Normalized Confusion Matrix (Holdout Set)")
plt.show()

# --------------------------
# 2. Precision / Recall / F1 per class
# --------------------------
precision, recall, f1, _ = precision_recall_fscore_support(
    y_final, y_predict_final, labels=[0,1]
)
metrics_df = pd.DataFrame({
    "Class": [0,1],
    "Precision": precision,
    "Recall": recall,
    "F1": f1
})

metrics_df.plot(x="Class", kind="bar", figsize=(8,6))
plt.title("Performance by Class (Holdout Set)")
plt.ylabel("Score")
plt.ylim(0,1)
plt.legend(loc="lower right")
plt.show()

# --------------------------
# 3. ROC Curve + AUC
# --------------------------
y_proba = pipeline.predict_proba(X_final)[:,1]  # predicted probabilities
fpr, tpr, _ = roc_curve(y_final, y_proba)
roc_auc = auc(fpr, tpr)

plt.figure(figsize=(6,6))
plt.plot(fpr, tpr, label=f"AUC = {roc_auc:.2f}", color="blue")
plt.plot([0,1],[0,1],'--',color='gray')
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.title("ROC Curve (Holdout Set)")
plt.legend()
plt.show()

# --------------------------
# 4. Feature Importance (Top Words)
# --------------------------
feature_names = pipeline.named_steps['tfidf'].get_feature_names_out()
importances = pipeline.named_steps['clf'].feature_importances_

top_idx = importances.argsort()[::-1][:20]  # top 20 words
plt.figure(figsize=(8,6))
sns.barplot(x=importances[top_idx], y=feature_names[top_idx], palette="viridis")
plt.title("Top 20 Most Important Features (Words)")
plt.xlabel("Importance")
plt.ylabel("Word")
plt.show()
