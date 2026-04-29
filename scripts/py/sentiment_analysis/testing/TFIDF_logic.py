### TFIDF LOGIC ###

# 1. Import needed libraries
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression, Lasso, LassoCV, Ridge, RidgeCV, RidgeClassifier, RidgeClassifierCV
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import classification_report, accuracy_score


# 2. Load in dataset
df = pd.read_csv("D:/TwitterBirth/data/sentiment_analysis/tweet_text_prepost_SAMPLE.csv")

# # 3. Define features 
# X = df['text'] # tweet text
# y = df['post'] # pre/post indicator 

# 3. Hold out 10%
X_temp, X_final, y_temp, y_final = train_test_split(
    df['text'], df['post'], test_size = 0.1, random_state = 42, stratify=df['post']
)

# 4. Train/Test split on 90% from above
X_train, X_test, y_train, y_test = train_test_split(
    X_temp, y_temp, test_size = 0.2, random_state = 42, stratify=y_temp)

# 5. Classifier Pipeline (TF-IDF & Logistic Regression)
pipeline = Pipeline([
    ('tfidf', TfidfVectorizer(
        lowercase = True,
        stop_words = 'english',
        max_features = 5000
    )),
    ('classifier', LogisticRegression(
        max_iter = 1000,
        penalty = 'l2',
        solver = 'saga'
    )),
    ('classifier', Lasso(
        max_iter = 1000,
        penalty = 'l1',
        solver = 'saga'
    ))
])

# 6. Fit the model
pipeline.fit(X_train, y_train)

# 7. Evaluate the model
y_predict = pipeline.predict(X_test)

print("Accuracy:", accuracy_score(y_test, y_predict))
print(classification_report(y_test, y_predict))





# 3. Store words & learn vocabulary from tweets (Initialize the TF-IDF Vectorizer)
vectorizer = TfidfVectorizer(
    lowercase=True,
    stop_words='english', # remove common English stop words
    max_features=5000 # keep only top 5000 important words
)

# 4. Convert words from #3 to vector 
# Fit vectorizer on the tweet text and transform text into TF-IDF vectors
X_tfidf = vectorizer.fit_transform(df['text'])





# #### LIKELY UNNECESSARY #####
# # 5. Convert the sparse TF-IDF matrix into a DataFrame
# # Get the list of words (features) from the vectorizer
# tfidf_df = pd.DataFrame(X_tfidf.toarray(),
#                         columns = vectorizer.get_feature_names_out())

# # 6. Concatenate with original columns
# final_df = pd.concat([df[['post', 'text']], tfidf_df], axis = 1)

# # 7. Save the vectorized output to a .csv
# final_df.to_csv("D:/TwitterBirth/data/sentiment_analysis/vectorized_tweet_text_SAMPLE.csv")


'''
TF + IDF = TF-IDF score
    higher scores --> greater importance
    represents the importance of each word across a collection of documents
'''


################ NOTES FROM VIDEO ######################
# # TERM FREQUENCY
#     # Counting how many time each word appears in the document
# def calculate_tf(document, word):
#     words = document.lower().split()
#     word_count = Counter(words)
#     return word_count[word.lower()]/len(words)

# # Inverse Document Frequency
#     # How rare or common a word is in the whole collection of documents 
#     # How many other documents contain this word (importance)
# def calculate_idf(word, docs):
#     num_documents = len(docs) + 1
#     num_documents_with_word = sum(1 for doc in docs if word.lower() in doc.lower()) + 1

#     return math.log(num_documents / num_documents_with_word)

