## Practicing TF-IDF

from sklearn.feature_extraction import TfidfVectorizer

corpus = [
    "The cat chased the mouse.",
    "I love eating fresh apples.",
    "The weather today is sunny and warm.",
    "She reads a book every night.",
    "A fast car zoomed down the road.",
    "He enjoys playing soccer with friends.",
    "The bakery sells delicious bread.",
    "Our dog barked loudly at the mailman."
]

v = TfidfVectorizer()
transformed_output = v.fit_transform(corpus)
print(v.vocabulary)

