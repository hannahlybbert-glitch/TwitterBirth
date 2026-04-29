# Author: Hannah Lybbert
# Created: 02/23/2026
# Purpose: Train Logistic Regression L2 classifier on one-doc TF-IDF features and save model artifacts

import os
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, accuracy_score

# --- Paths ---
input_path   = "D:/TwitterBirth/data/sentiment_analysis/output/text_onedoc.csv"
model_dir    = "D:/TwitterBirth/data/sentiment_analysis/output/logreg_l2/"
report_path  = "D:/TwitterBirth/output/sentiment_analysis/class_report/classif_report_L2.csv"

# --- Hyperparameters ---
n_features   = 5000
random_seed  = 42
C            = 10
max_iter     = 1000
lockbox_size = 0.10
test_size    = 0.20

# --- Load ---
df    = pd.read_csv(input_path)
texts = df["text_concat"].astype(str)
y     = df["post_birth"]

# --- TF-IDF ---
tfidf = TfidfVectorizer(
    ngram_range=(1, 2),
    min_df=3,
    max_df=0.7,
    max_features=200_000,
    sublinear_tf=True
)
X_tfidf = tfidf.fit_transform(texts)
print("TF-IDF shape:", X_tfidf.shape)

# --- Split: 10% lockbox holdout, then 80/20 train/test on remainder ---
X_temp, X_lock, y_temp, y_lock = train_test_split(
    X_tfidf, y, test_size=lockbox_size, random_state=random_seed, stratify=y
)
X_train, X_test, y_train, y_test = train_test_split(
    X_temp, y_temp, test_size=test_size, random_state=random_seed, stratify=y_temp
)

# --- Feature selection ---
selector    = SelectKBest(score_func=f_classif, k=n_features)
selector.fit(X_train, y_train)
X_train_sel = selector.transform(X_train)
X_test_sel  = selector.transform(X_test)
print("Selected features:", X_train_sel.shape[1])

# --- Train ---
clf = LogisticRegression(
    random_state=random_seed, max_iter=max_iter, solver='saga', C=C, penalty='l2'
)
clf.fit(X_train_sel, y_train)

# --- Evaluate ---
y_pred = clf.predict(X_test_sel)
print("\n### LogReg L2 Performance ###")
print("Accuracy:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))

report_df = pd.DataFrame(
    classification_report(y_test, y_pred, output_dict=True)
).transpose()
report_df.to_csv(report_path)
print(f"Classification report saved to {report_path}")

# --- Save model artifacts for figure scripts ---
os.makedirs(model_dir, exist_ok=True)
joblib.dump(clf,        model_dir + "clf.joblib")
joblib.dump(selector,   model_dir + "selector.joblib")
joblib.dump(tfidf,      model_dir + "tfidf.joblib")
joblib.dump(X_test_sel, model_dir + "X_test_sel.joblib")
joblib.dump(y_test,     model_dir + "y_test.joblib")
print(f"Model artifacts saved to {model_dir}")
