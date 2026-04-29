# Author: Hannah Lybbert
# Created: 02/23/2026
# Updated: 02/25/2026
# Purpose: Feature importance plot for LogReg L2 classifier — final figure

import os
import joblib
import numpy as np
import matplotlib.pyplot as plt

# --- Paths ---
model_dir  = "D:/TwitterBirth/data/sentiment_analysis/output/logreg_l2/"
output_dir = "D:/TwitterBirth/output/final_figs/ML_final/"
fig_path   = output_dir + "feature_importance_logreg_l2.png"

# --- Settings ---
top_n       = 20
title_size  = 25
label_size  = 22
xtick_size  = 20  # x-axis tick number size
ytick_size  = 20  # feature word label size
bar_color   = "#34628D"

# --- Load model artifacts ---
clf      = joblib.load(model_dir + "clf.joblib")
selector = joblib.load(model_dir + "selector.joblib")
tfidf    = joblib.load(model_dir + "tfidf.joblib")

os.makedirs(output_dir, exist_ok=True)

# --- Feature importance ---
selected_idx  = selector.get_support(indices=True)
feature_names = tfidf.get_feature_names_out()[selected_idx]
coefs         = clf.coef_[0]
abs_coefs     = np.abs(coefs)

top_idx       = np.argsort(abs_coefs)[-top_n:][::-1]
top_features  = feature_names[top_idx]
top_abs_coefs = abs_coefs[top_idx]

plt.figure(figsize=(10, 8))
plt.barh(top_features, top_abs_coefs, color=bar_color)
plt.xlabel("Absolute Coefficient Value", fontsize=label_size)
# TF-IDF, LogReg L2
plt.title(f"Most Important Features", fontsize=title_size)
plt.gca().invert_yaxis()
plt.xticks(fontsize=xtick_size)
plt.yticks(fontsize=ytick_size)
plt.tight_layout()
plt.savefig(fig_path, dpi=300)
plt.close()

print(f"Feature importance plot saved to {fig_path}")
