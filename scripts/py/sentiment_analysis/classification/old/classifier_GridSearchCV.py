# -------- GRID SEARCH to find the best classification model ------------- #

# 1. Import needed libraries
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
import xgboost as xgb
from xgboost import XGBClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import classification_report, accuracy_score, precision_recall_fscore_support


# 2. Load in dataset
df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_prepost_balanced_SAMPLE.csv")
# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_prepost_balanced_nolink_10k.csv")
# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_prepost_balanced_SAMPLE_1mo_drop.csv")
# df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_prepost_balanced_SAMPLE_1mo_drop_nolink.csv")



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
        max_features=5000)),
    ('clf', LogisticRegression())  # placeholder, will swap models in via param_grid
])



# ------ GRID SEARCH - best performing model ------ #

# 5. Define parameter grid
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
    # # XGBoost
    # {
    #     'clf': [XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)],
    #     'clf__n_estimators': [100, 200],
    #     'clf__learning_rate': [0.1, 0.3],
    #     'clf__max_depth': [3, 5, 7],
    #     'clf__subsample': [0.8, 1.0]
    # }


# 6. Run GridSearchCV
grid = GridSearchCV(
    pipeline,
    param_grid,
    cv=5,                # 5-fold cross validation
    scoring='accuracy',  # could also use 'f1', 'roc_auc', etc.
    n_jobs=-1,           # use all CPU cores
    verbose=2
)

grid.fit(X_train, y_train)

# 7. Evaluate on test set
y_pred = grid.predict(X_test)
print("\n Best Parameters:", grid.best_params_)
print("Accuracy on Test:", accuracy_score(y_test, y_pred))
print(classification_report(y_test, y_pred))




#####################################################################################################

# # ------ GRID SEARCH (output all model's performance to .csv) ------ #

# # 5. Define Dictionary of Parameter Grids
# param_grids = {
#     "Logistic (L2)": {
#         'clf': [LogisticRegression(max_iter=10000, solver='saga')],
#         'clf__penalty': ['l2'],
#         'clf__C': [0.01, 0.1, 1, 10]       
#     },
#     "Logistic (L1)": {
#         'clf': [LogisticRegression(max_iter=10000, solver='saga')],
#         'clf__penalty': ['l1'],
#         'clf__C': [0.01, 0.1, 1, 10]        
#     },
#     "Logistic (elasticnet)": {
#         'clf': [LogisticRegression(max_iter=10000, solver='saga')],
#         'clf__penalty': ['elasticnet'],
#         'clf__l1_ratio': [0.25, 0.5, 0.75],
#         'clf__C': [0.01, 0.1, 1, 10]        
#     },
#     "Random Forest": {
#         'clf': [RandomForestClassifier(random_state=42)],
#         'clf__n_estimators': [100, 200],
#         'clf__max_depth': [10, 20, None]        
#     },
#     "Gradient Boosting": {
#         'clf': [GradientBoostingClassifier(random_state=42)],
#         'clf__n_estimators': [100, 200],
#         'clf__learning_rate': [0.5, 1.0], # sequential correction
#         'clf__max_depth': [3, 5, 7, 10] # tree depth
#     },
#     "AdaBoost": {
#         'clf': [AdaBoostClassifier(random_state=42)],
#         'clf__n_estimators': [25, 50, 100, 150, 200],
#         'clf__learning_rate': [0.1, 0.25, 0.5, 1.0]        
#     },
#     # "XGBoost": {
#     #     'clf': [XGBClassifier(use_label_encoder=False, eval_metric='logloss', random_state=42)],
#     #     'clf__n_estimators': [100, 200],
#     #     'clf__learning_rate': [0.1, 0.3],
#     #     'clf__max_depth': [3, 5, 7],
#     #     'clf__subsample': [0.8, 1.0]
#     # }
# }

# # 6. Run GridSearchCV for each model
# rows = []
# # results = {}

# for name, grid_params in param_grids.items():
#     grid = GridSearchCV(
#         pipeline,
#         grid_params,
#         cv=5,
#         scoring = "accuracy",
#         n_jobs = -1,
#         verbose= 0
#     )

#     # 6A. Run models and Evaluate on test set
#     grid.fit(X_train, y_train)
#     y_pred = grid.predict(X_test)

#     # 6B. Add classification report to a pandas DF
#     # Get per-class metrics
#     precision, recall, f1, _ = precision_recall_fscore_support(y_test, y_pred, average=None, labels=[0,1])

#     # Add row per model
#     rows.append({
#         "Model": name,
#         "Best Params": grid.best_params_,
#         "Accuracy": accuracy_score(y_test, y_pred),
#         "Precision_0": precision[0],
#         "Recall_0": recall[0],
#         "F1_0": f1[0],
#         "Precision_1": precision[1],
#         "Recall_1": recall[1],
#         "F1_1": f1[1],
#     })

# # 7. SAVE classification report
#     # Convert to DataFrame
# results_df = pd.DataFrame(rows)

# pd.set_option('display.max_colwidth', None)
# print(results_df)

# # Save to CSV
# results_df.to_csv("D:/TwitterBirth/data/sentiment_analysis/output/CLF_model_comparison_results_SAMPLE.csv", index=False)

# print("\nSaved results to CSV!")


# ####################### FINAL 10% HOLD OUT ########################
# final_rows = []
# for name, grid_params in param_grids.items():
#     grid = GridSearchCV(
#         pipeline,
#         grid_params,
#         cv=5,
#         scoring="accuracy",
#         n_jobs=-1,
#         verbose=0
#     )
#     grid.fit(X_train, y_train)

#     # Predict on the 10% holdout
#     y_final_pred = grid.predict(X_final)
#     precision, recall, f1, _ = precision_recall_fscore_support(y_final, y_final_pred, average=None, labels=[0,1])

#     final_rows.append({
#         "Model": name,
#         "Accuracy": accuracy_score(y_final, y_final_pred),
#         "Precision_0": precision[0],
#         "Recall_0": recall[0],
#         "F1_0": f1[0],
#         "Precision_1": precision[1],
#         "Recall_1": recall[1],
#         "F1_1": f1[1],
#     })
# final_results_df = pd.DataFrame(final_rows)
# final_results_df.to_csv("D:/TwitterBirth/data/sentiment_analysis/output/CLF_model_comparison_FINAL_HOLDOUT.csv", index=False)
# print("\nSaved final holdout results to CSV!")




#####################################################################################################





############## PREVIOUS NOTES #################

# results[name] = {
#     "best_params": grid.best_params_,
#     "accuracy": accuracy_score(y_test, y_pred),
#     "report": classification_report(y_test, y_pred, output_dict=False)
# }

# # 8. Print Summary Reports:
# for name, res in results.items():
#     print(f"\n === {name} ===")
#     print("Best Params:", res["best_params"])
#     print('Accuracy:', res["accuracy"])
#     print("Report: \n", res["report"])