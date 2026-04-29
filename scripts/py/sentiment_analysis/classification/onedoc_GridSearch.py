### Author: Hannah Lybbert
### Created: 11/14/2025
### Purpose: GridSearch for best classification model 

import pandas as pd
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.metrics import classification_report


# Load prepared author-period dataset
df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/text_onedoc_sample.csv")

# Train-test split
X_temp, X_final, y_temp, y_final = train_test_split(
    df['text_concat'], df['post'], test_size=0.1,
    random_state=42, stratify=df['post']
)

X_train, X_test, y_train, y_test = train_test_split(
    X_temp, y_temp, test_size=0.2,
    random_state=42, stratify=y_temp
)

ngr = (1,2)
# ngr = (1,3)
# ngr = (1,1)

# TF-IDF 
tfidf = TfidfVectorizer(
    ngram_range=ngr,
    min_df=3,
    max_df=0.7,
    # lowercase=True,
    # stop_words='english',
    max_features=200_000,
    sublinear_tf=True)

X_train_tfidf = tfidf.fit_transform(X_train)
X_test_tfidf  = tfidf.transform(X_test)

# Pipeline
pipeline = Pipeline([
    # ('select', SelectKBest(f_classif, k=20000)),
    ('select', SelectKBest(score_func=f_classif)),
    ('clf', LogisticRegression())  # placeholder, will be replaced in GridSearch
])

# Parameter grid
param_grid = [
    {
        'select__k': [5000],
        'clf': [LogisticRegression(max_iter=1000, solver='saga')],
        'clf__penalty': ['l2'],
        'clf__C': [0.01, 0.1, 1, 10]
    },
    {
        'select__k': [20000], #20k = best performer by .006 points accuracy
        'clf': [LogisticRegression(max_iter=1000, solver='saga')],
        'clf__penalty': ['l1'],
        'clf__C': [0.01, 0.1, 1, 10]
    },
    {
        'select__k': [5000], # said it was 20k but I don't believe it
        'clf': [LogisticRegression(max_iter=1000, solver='saga')],
        'clf__penalty': ['elasticnet'],
        'clf__l1_ratio': [0.75],
        'clf__C': [0.01, 0.1, 1, 10]
    },
    {
        'select__k': [5000], # 5k best
        'clf': [RandomForestClassifier(random_state=42)],
        'clf__n_estimators': [100, 200],
        'clf__max_depth': [10, 20, None]
    },
    {
        'select__k': [5000],
        'clf': [GradientBoostingClassifier(random_state=42)],
        'clf__n_estimators': [100, 200],
        'clf__learning_rate': [0.5, 1.0],
        'clf__max_depth': [3, 5, 7, 10]
    },
    {
        'select__k': [10000], # either 5k, 10k, 20k (confirming right now with full run)
        'clf': [AdaBoostClassifier(random_state=42)],
        'clf__n_estimators': [100, 150, 200],
        'clf__learning_rate': [0.25, 0.5, 1.0]
    },
    {
        'select__k': [5000], # grid search had said the best was 10000 but it was not
        'clf': [LinearSVC(random_state=42)],
        'clf__penalty': ['l2'],
        'clf__C': [0.1, 1, 10],
        'clf__max_iter': [2000, 5000]
    }
]

# GridSearchCV
grid = GridSearchCV(
    pipeline,
    param_grid,
    cv=5,
    scoring='accuracy',
    n_jobs=-1,
    verbose=2
)

grid.fit(X_train_tfidf, y_train)

print("\nBest Parameters:", grid.best_params_)
print("Test Accuracy:", grid.score(X_test_tfidf, y_test))

y_pred = grid.predict(X_test_tfidf)
print(classification_report(y_test, y_pred))

# # Save best model and results
# import joblib
# joblib.dump(grid.best_estimator_, "D:/TwitterBirth/output/sentiment_analysis/best_one_doc_model.pkl")


''' Best parameters from my original run (no feature selection)
    Best Parameters: {'clf': AdaBoostClassifier(random_state=42), 'clf__learning_rate': 0.5, 'clf__n_estimators': 150}
    Test Accuracy: 0.7111111111111111

with feature selection... why is it worse?
    Best Parameters: {'clf': AdaBoostClassifier(random_state=42), 'clf__learning_rate': 0.5, 'clf__n_estimators': 100, 'select__k': 5000}
    Test Accuracy: 0.7055555555555556

Best Parameters: {'clf': AdaBoostClassifier(random_state=42), 'clf__learning_rate': 0.25, 'clf__n_estimators': 200, 'select__k': 5000}
Test Accuracy: 0.7277777777777777

Removed 'l1' from LinearSVC
    Best Parameters: {'clf': AdaBoostClassifier(random_state=42), 'clf__learning_rate': 0.25, 'clf__n_estimators': 200, 'select__k': 5000}
    Test Accuracy: 0.7277777777777777

Took feature selection out of gridsearch (allow all possible features)
    Best Parameters: {'clf': AdaBoostClassifier(random_state=42), 'clf__learning_rate': 0.25, 'clf__n_estimators': 200}
    Test Accuracy: 0.7277777777777777

Grid Search just a model at a time:
    LinearSVC sample no k selection:
        Best Parameters: {'clf': LinearSVC(random_state=42), 'clf__C': 10, 'clf__max_iter': 2000, 'clf__penalty': 'l2'}
        Test Accuracy: 0.6555555555555556
    LinearSVC sample k selection:
        Best Parameters: {'clf': LinearSVC(random_state=42), 'clf__C': 1, 'clf__max_iter': 2000, 'clf__penalty': 'l2', 'select__k': 5000}
        Test Accuracy: 0.7

    Adaboost sample no k selection
        Best Parameters: {'clf': AdaBoostClassifier(random_state=42), 'clf__learning_rate': 0.25, 'clf__n_estimators': 200}
        Test Accuracy: 0.7277777777777777
    Adaboost sample k selection
        Best Parameters: {'clf': AdaBoostClassifier(random_state=42), 'clf__learning_rate': 0.25, 'clf__n_estimators': 200, 'select__k': 5000}
        Test Accuracy: 0.7277777777777777

'''


# import pandas as pd
# import numpy as np
# from sklearn.model_selection import train_test_split, GridSearchCV
# from sklearn.pipeline import Pipeline
# from sklearn.feature_extraction.text import TfidfVectorizer
# from sklearn.feature_selection import SelectKBest, f_classif
# from sklearn.metrics import (
#     accuracy_score, precision_recall_fscore_support, classification_report
# )

# # MODELS
# from sklearn.linear_model import LogisticRegression
# from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
# from sklearn.svm import LinearSVC

# # ================================
# # 1. Load data
# # ================================
# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/output/text_onedoc_sample.csv")

# # ---------------- Split ---------------- #
# X_temp, X_final, y_temp, y_final = train_test_split(
#     df['text_concat'], df['post'],
#     test_size=0.1, random_state=42, stratify=df['post']
# )

# X_train, X_test, y_train, y_test = train_test_split(
#     X_temp, y_temp,
#     test_size=0.2, random_state=42, stratify=y_temp
# )

# # ================================
# # 2. Base Pipeline (clf replaced later)
# # ================================
# pipeline = Pipeline([
#     ('tfidf', TfidfVectorizer(
#         ngram_range=(1,2),
#         min_df=3,
#         max_df=0.7,
#         max_features=200_000,
#         sublinear_tf=True
#     )),
#     ('select', SelectKBest(score_func=f_classif)),
#     ('clf', LogisticRegression())   # placeholder
# ])

# # ================================
# # 3. Define MODEL BLOCKS (like old pipeline)
# # ================================
# param_grids = {
#     "Logistic L2": {
#         'select__k': [5000, 20000],
#         'clf': [LogisticRegression(max_iter=1000, solver='saga')],
#         'clf__penalty': ['l2'],
#         'clf__C': [0.01, 0.1, 1, 10]
#     },

#     "Logistic L1": {
#         'select__k': [5000, 20000],
#         'clf': [LogisticRegression(max_iter=1000, solver='saga')],
#         'clf__penalty': ['l1'],
#         'clf__C': [0.01, 0.1, 1, 10]
#     },

#     "Logistic ElasticNet": {
#         'select__k': [5000, 20000],
#         'clf': [LogisticRegression(max_iter=1000, solver='saga')],
#         'clf__penalty': ['elasticnet'],
#         'clf__l1_ratio': [0.25, 0.5, 0.75],
#         'clf__C': [0.01, 0.1, 1, 10]
#     },

#     "Random Forest": {
#         'select__k': [5000, 20000],
#         'clf': [RandomForestClassifier(random_state=42)],
#         'clf__n_estimators': [100, 200],
#         'clf__max_depth': [10, 20, None]
#     },

#     "AdaBoost": {
#         'select__k': [5000, 20000],
#         'clf': [AdaBoostClassifier(random_state=42)],
#         'clf__n_estimators': [100, 150, 200],
#         'clf__learning_rate': [0.25, 0.5, 1.0]
#     },

#     "Linear SVC": {
#         'select__k': [5000, 20000],
#         'clf': [LinearSVC(random_state=42, dual=False)],
#         'clf__penalty': ['l2'],
#         'clf__C': [0.01, 0.1, 1, 10],
#         'clf__max_iter': [2000, 5000, 10000]
#     }
# }

# # ================================
# # 4. Run GRID SEARCH for each model
# # ================================
# rows = []

# for model_name, grid_params in param_grids.items():
#     print(f"\n\n===== Running GridSearch for {model_name} =====")

#     grid = GridSearchCV(
#         pipeline,
#         grid_params,
#         cv=5,
#         scoring="accuracy",
#         n_jobs=-1,
#         verbose=1
#     )

#     grid.fit(X_train, y_train)
#     y_pred = grid.predict(X_test)

#     # metrics
#     acc = accuracy_score(y_test, y_pred)
#     precision, recall, f1, _ = precision_recall_fscore_support(
#         y_test, y_pred, average=None, labels=[0,1]
#     )

#     rows.append({
#         "Model": model_name,
#         "Best Params": grid.best_params_,
#         "Accuracy": acc,
#         "Precision_0": precision[0],
#         "Recall_0": recall[0],
#         "F1_0": f1[0],
#         "Precision_1": precision[1],
#         "Recall_1": recall[1],
#         "F1_1": f1[1]
#     })

# # ================================
# # 5. Save results
# # ================================
# results_df = pd.DataFrame(rows)

# pd.set_option('display.max_colwidth', None)
# print(results_df)

# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/CLF_model_comparison_results_ONEDOC.csv"
# results_df.to_csv(output_path, index=False)

# print(f"\nSaved results to CSV:\n{output_path}")
