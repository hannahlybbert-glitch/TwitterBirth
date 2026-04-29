## Build classification one doc file with spaCy embeddings

import pandas as pd
import numpy as np
import spacy
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.metrics import classification_report, accuracy_score


# 1. Take each document and convert every word in the doc to 300-length spaCy vectors

# 2. Average these vectors creating 300 variables per document

# 3. With these variables as the X and pre/post birth as the y, use scikit-learn GridSearch pipeline


# -------------------------------------
# ----- LOAD & PREPROCESS DATA ----- #

df_old = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/text_aid_prepost.csv")
df_old["text"] = df_old["text"].fillna("").astype(str)

# concatenate all tweets per author per period
df_full = (
    df_old.groupby(["author_id", "post"])["text"]
    .apply(lambda x: " ".join(x))
    .reset_index(name="text_concat")
)

# Sample authors (for GridSearch)
valid_authors = (
    df_full.groupby("author_id")
    .filter(lambda x: len(x) == 2)["author_id"]
    .unique()
)
# 100 author sample = 200 documents (100 pre, 100 post per author)
sampled_authors = pd.Series(valid_authors).sample(n=100, random_state=42).tolist()
df = df_full[df_full["author_id"].isin(sampled_authors)]
print(df["post"].value_counts()) # confirm its a balanced panel pre/post


# --------------------------------
# ---- CREATE spaCy VECTOR ---- #

# Load model with word vectors only
nlp = spacy.load("en_core_web_md", disable=[
    "ner", "parser", "tagger", "senter", "attribute_ruler", "lemmatizer"
        ])

nlp.max_length = 2_000_000

# average vectors & create 300 variables per doc
class SpacyAveragedEmbeddings(BaseEstimator, TransformerMixin):
    def __init__(self, nlp):
        self.nlp = nlp

    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        vectors = []
        for doc in self.nlp.pipe(X, batch_size=32):
            vectors.append(doc.vector) # 300-dimension average embedding
        return np.vstack(vectors)


# -------------------------
# ----- SPLIT DATA ----- #

# Train/Test split (don't worry about 10% hold out right now during testing)
X_train, X_test, y_train, y_test = train_test_split(
    df['text_concat'], 
    df['post'], 
    test_size = 0.2, 
    random_state = 42, 
    stratify=df['post'],
)


# --------------------------------
# ----- DEFINE PIPELINE ----- #

pipeline = Pipeline([
    ('embed', SpacyAveragedEmbeddings(nlp)),
    ('clf', LogisticRegression())
])


# -----------------------------------------------------
# ------ GRID SEARCH - best performing model ------ #

# 1. Define parameter grid
param_grid = [
    # Logistic Regression L2 (ridge)
    {
        'clf': [LogisticRegression(max_iter=1000, solver='saga')],
        'clf__penalty': ['l2'],
        'clf__C': [0.01, 0.1, 1, 10]  # regularization strength
    },
    # Logistic Regression L1 (lasso)
    {
        'clf': [LogisticRegression(max_iter=1000, solver='saga')],
        'clf__penalty': ['l1'],
        'clf__C': [0.01, 0.1, 1, 10]
    },
    # Logistic Regression l1+l2 (elasticnet)
    {
        'clf': [LogisticRegression(max_iter=1000, solver='saga')],
        'clf__penalty': ['elasticnet'],
        'clf__C': [0.01, 0.1, 1, 10]
    },
    # Random Forest (bagging)
    {
        'clf': [RandomForestClassifier(random_state=42)],
        'clf__n_estimators': [100, 200],
        'clf__max_depth': [10, 20, None]
    },
    # Gradient Boosting
    {
        'clf': [GradientBoostingClassifier(random_state=42)],
        'clf__n_estimators': [100, 200],
        'clf__learning_rate': [0.5, 1.0], # sequential correction (each tree correcting previous tree errors)
        'clf__max_depth': [3, 5, 7, 10] # tree depth
    },
    # AdaBoost 
    {
        'clf': [AdaBoostClassifier(random_state=42)],
        'clf__n_estimators': [25, 50, 100, 150, 200],
        'clf__learning_rate': [0.1, 0.25, 0.5, 1.0]
    }
]

# 2. Run GridSearchCV
grid = GridSearchCV(
    pipeline,
    param_grid,
    cv=5,                # 5-fold cross validation
    scoring='accuracy',
    n_jobs=1,          # originally was "-1" but code editor recommmended I change to "1" 
    verbose=2
)

grid.fit(X_train, y_train)

# 3. Evaluate on test set
y_pred = grid.predict(X_test)
print("\n Best Parameters:", grid.best_params_)
print("Accuracy on Test:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))





# ----- OLD NOTES ----- #

# # Hold out 10%
# X_temp, X_final, y_temp, y_final = train_test_split(
#     df['text'], 
#     df['post_birth'], 
#     test_size = 0.1, 
#     random_state = 42, 
#     stratify=df['post_birth']
# )

# # Train/Test split on 90% from above
# X_train, X_test, y_train, y_test = train_test_split(
#     X_temp, 
#     y_temp, 
#     test_size = 0.2, 
#     random_state = 42, 
#     stratify=y_temp)

# # -----------------------------
# # spaCy word-vector embedding
# # -----------------------------
# nlp = spacy.load("en_core_web_md", disable=[
#     "ner", "parser", "tagger", "senter", "attribute_ruler", "lemmatizer"
# ])
# nlp.max_length = 2_000_000  # Allow very long concatenated docs

# class SpacyTransformerEmbedding(BaseEstimator, TransformerMixin):
#     def __init__(self, nlp):
#         self.nlp = nlp

#     def fit(self, X, y=None):
#         return self

#     def transform(self, X):
#         vecs = []
#         for doc in self.nlp.pipe(X, batch_size=16, disable=["ner"]):
#             vecs.append(doc.vector)
#         return np.array(vecs)

# # -----------------------------
# # Pipeline
# # -----------------------------
# spacy_embedder = SpacyTransformerEmbedding(nlp)

# pipeline = Pipeline([
#     ('embed', spacy_embedder),
#     ('clf', LogisticRegression())  # placeholder for GridSearch
# ])

# # -----------------------------
# # GridSearch parameters
# # -----------------------------
# param_grid = [
#     # Logistic Regression L2
#     {
#         'clf': [LogisticRegression(max_iter=1000, solver='saga')],
#         'clf__penalty': ['l2'],
#         'clf__C': [0.01, 0.1, 1, 10]
#     },
#     # Random Forest
#     {
#         'clf': [RandomForestClassifier(random_state=42)],
#         'clf__n_estimators': [100, 200],
#         'clf__max_depth': [10, 20, None]
#     },
#     # AdaBoost
#     {
#         'clf': [AdaBoostClassifier(random_state=42)],
#         'clf__n_estimators': [50, 100, 150],
#         'clf__learning_rate': [0.1, 0.5, 1.0]
#     }
# ]

# # -----------------------------
# # Run GridSearch
# # -----------------------------
# grid = GridSearchCV(
#     pipeline,
#     param_grid,
#     cv=5,
#     scoring='accuracy',
#     n_jobs=-1,
#     verbose=2,
#     error_score='raise'
# )

# grid.fit(X_train, y_train)

# # -----------------------------
# # Evaluate on test set
# # -----------------------------
# y_pred = grid.predict(X_test)
# print("\nBest Parameters:", grid.best_params_)
# print("Accuracy on Test:", accuracy_score(y_test, y_pred))
# print(classification_report(y_test, y_pred))

