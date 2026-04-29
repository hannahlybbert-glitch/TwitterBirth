# Author: Hannah Lybbert
# Created: 02/23/2026
# Updated: 02/25/2026
# Purpose: Confusion matrix for LogReg L2 classifier — final figure

import os
import joblib
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
from sklearn.metrics import confusion_matrix

# --- Paths ---
model_dir  = "D:/TwitterBirth/data/sentiment_analysis/output/logreg_l2/"
output_dir = "D:/TwitterBirth/output/final_figs/ML_final/"
fig_path   = output_dir + "conf_matrix_logreg_l2.png"

# --- Figure style ---
title_size   = 18
label_size   = 16
xtick_size   = 14  # x-axis tick label size (Pre-birth/Post-birth)
ytick_size   = 14  # y-axis tick label size (Pre-birth/Post-birth)
annot_size   = 16  # numbers inside the matrix cells
plot_color   = "#34628D"

# --- Load model artifacts ---
clf        = joblib.load(model_dir + "clf.joblib")
X_test_sel = joblib.load(model_dir + "X_test_sel.joblib")
y_test     = joblib.load(model_dir + "y_test.joblib")

os.makedirs(output_dir, exist_ok=True)

# --- Confusion matrix ---
y_pred        = clf.predict(X_test_sel)
cm            = confusion_matrix(y_test, y_pred)
cm_normalized = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

blue_cmap = mcolors.LinearSegmentedColormap.from_list("blue_cmap", ["white", plot_color])

plt.figure(figsize=(6, 4))
ax = sns.heatmap(cm_normalized, annot=True, fmt=".2f", cmap=blue_cmap,
                 annot_kws={"size": annot_size},
                 xticklabels=["Pre-birth", "Post-birth"],
                 yticklabels=["Pre-birth", "Post-birth"],
                 cbar=False)
plt.xlabel("Predicted", fontsize=label_size)
plt.ylabel("Actual",    fontsize=label_size)
plt.xticks(fontsize=xtick_size)
plt.yticks(fontsize=ytick_size)
# TF-IDF, LogReg L2
plt.title("Confusion Matrix", fontsize=title_size)
plt.savefig(fig_path, dpi=300, bbox_inches="tight")
plt.close()

print(f"Confusion matrix saved to {fig_path}")
