# Author: Hannah Lybbert
# Created: 02/23/2026
# Updated: 02/25/2026
# Purpose: ROC AUC curve for LogReg L2 classifier — final figure

import os
import joblib
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc

# --- Paths ---
model_dir  = "D:/TwitterBirth/data/sentiment_analysis/output/logreg_l2/"
output_dir = "D:/TwitterBirth/output/final_figs/ML_final/"
fig_path   = output_dir + "roc_auc_logreg_l2.png"

# --- Figure style ---
title_size  = 18
label_size  = 16
xtick_size  = 14  # x-axis tick number size
ytick_size  = 14  # feature word label size
line_color  = "#34628D"

# --- Load model artifacts ---
clf        = joblib.load(model_dir + "clf.joblib")
X_test_sel = joblib.load(model_dir + "X_test_sel.joblib")
y_test     = joblib.load(model_dir + "y_test.joblib")

os.makedirs(output_dir, exist_ok=True)

# --- ROC curve ---
y_proba     = clf.predict_proba(X_test_sel)[:, 1]
fpr, tpr, _ = roc_curve(y_test, y_proba)
roc_auc     = auc(fpr, tpr)

plt.figure(figsize=(6, 6))
plt.plot(fpr, tpr, color=line_color, label=f"AUC = {roc_auc:.2f}")
plt.plot([0, 1], [0, 1], '--', color='gray')
plt.xlabel("False Positive Rate", fontsize=label_size)
plt.ylabel("True Positive Rate",  fontsize=label_size)
# TF-IDF, LogReg L2
plt.title("ROC Curve", fontsize=title_size)
plt.xticks(fontsize=xtick_size)
plt.yticks(fontsize=ytick_size)
plt.legend()
plt.savefig(fig_path, dpi=300, bbox_inches="tight")
plt.close()

print(f"ROC curve saved to {fig_path}")
