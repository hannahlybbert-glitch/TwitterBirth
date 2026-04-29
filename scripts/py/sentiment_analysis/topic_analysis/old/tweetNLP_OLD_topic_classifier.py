# Tweet NLP topic classification

import numpy as np
import pandas as pd
import torch
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# ---------- Load Model & Tokenizer ---------- #
MODEL_NAME = "cardiffnlp/twitter-roberta-base-dec2021-tweet-topic-multi-all"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, problem_type="multi_label_classification")
# model_topic = tweetnlp.load_model('topic_classification', multi_label=False)


# GPU
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
# device = torch.device("cpu")
model.eval()

# ID family label index
id2label = model.config.id2label
FAMILY_IDX = [i for i, lbl in id2label.items() if "family" in lbl.lower()]
assert len(FAMILY_IDX) == 1, f"Expected one family label, got {FAMILY_IDX}"
FAMILY_IDX = FAMILY_IDX[0]

input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_FULL.csv"
output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/NLP_topic_classifier_FULL.csv"
# input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/NLP_topic_classifier_10k.csv"
# input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_handcode.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/NLP_topic_classifier100.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/classification_10k.csv"


# ---------- Family Classification Function ---------- #
def classify_family_tweets(texts, batch_size=128, threshold=0.5, return_all_probs=True):
    """
    texts: list of strings
    Outputs:
      - family_probs: shape (N,)
      - family_flags: shape (N,), binary
      - all_probs: optional (N, L)
    """
    if len(texts) == 0:
        if return_all_probs:
            L = model.config.num_labels
            return (
                np.empty((0,)),
                np.empty((0,), dtype=int),
                np.empty((0, L))
            )
        else:
            return np.empty((0,)), np.empty((0,), dtype=int)
        

    all_family_probs = []
    all_probs = [] if return_all_probs else None

    for i in tqdm(range(0, len(texts), batch_size)):
        batch = texts[i:i + batch_size]

        enc = tokenizer(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128
        ).to(device)

        # Move inputs to GPU/CPU device
        enc = {k: v.to(device) for k, v in enc.items()}
        # enc = enc

        with torch.no_grad():
            logits = model(**enc).logits   # shape (bsz, num_labels)

        # Convert logits -> probabilities -> CPU -> numpy
        probs = torch.sigmoid(logits).cpu().numpy()
        # probs = torch.sigmoid(logits).numpy()


        # Collect family column
        all_family_probs.extend(probs[:, FAMILY_IDX])

        # Collect all label probabilities (optional)
        if return_all_probs:
            all_probs.append(probs)

    family_probs = np.array(all_family_probs)
    family_flags = (family_probs > threshold).astype(int)

    if return_all_probs:
        all_probs = np.concatenate(all_probs, axis=0)
        return family_probs, family_flags, all_probs

    return family_probs, family_flags


# ---------- MULTI topic Classification Function ---------- #
def classify_topics(texts, batch_size=128):
    if len(texts) == 0:
        return []

    all_topic_labels = []

    for i in tqdm(range(0, len(texts), batch_size)):
        batch = texts[i:i + batch_size]

        enc = tokenizer(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128
        ).to(device)

        with torch.no_grad():
            logits = model(**enc).logits

        probs = torch.sigmoid(logits).cpu().numpy()

        # highest-probability label index
        topic_idx = probs.argmax(axis=1)

        # convert index → label name
        topic_labels = [id2label[int(j)] for j in topic_idx]

        all_topic_labels.extend(topic_labels)

    return np.array(all_topic_labels)



# ---------- Run Classification Function ---------- #
def classify_file(input_path, output_path, text_column="text",
                  batch_size=128, threshold=0.5):
    """
    Reads file, classifies tweets, writes CSV or Parquet.
    """

    # Load file automatically based on extension
    df = pd.read_csv(input_path)

    if text_column not in df.columns:
        raise KeyError(f"Column '{text_column}' not found in input file.")

    texts = df[text_column].fillna("").astype(str).tolist()

    # Run classifier
    fam_probs, fam_flags = classify_family_tweets(
        texts,
        batch_size=batch_size,
        threshold=threshold,
        return_all_probs=False  # saving only family signal
    )

    topic_labels = classify_topics(texts, batch_size=batch_size)

    # Append results
    df["family_prob"] = fam_probs
    df["family_flag"] = fam_flags
    df["topic"] = topic_labels


    df.to_csv(output_path, index=False)
    print(f"\n✅ Saved results to: {output_path}")



# ------------ EXECUTE ------------ #
if __name__ == "__main__":
    classify_file(
        input_path=input_path,
        output_path=output_path,
        text_column="text",   # change if your column name is different
        batch_size=128,
        threshold=0.5
    )





# # Function for Tweet Topic Classification
# def get_topic_classification(tweet):
    
#     # Check if tweet is a string
#     if not isinstance(tweet, str):
#         return np.nan # return "." in stata
#     try:
#         topic_dict = model.topic(tweet)
#         # print tests
#         # print(topic_dict)
        
#         return topic_dict['label']

#     except Exception as e:
#         print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
#         return np.nan