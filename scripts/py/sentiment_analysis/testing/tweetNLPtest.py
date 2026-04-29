# tweetNLPtest

## TweetNLP analyze
import os
import warnings
import tweetnlp
import pandas as pd
import numpy as np
import swifter
swifter.config.progress_bar = True 



# --- Ignore Warnings --- #
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message=".*use_auth_token.*")


# --- Data --- # 
# input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/topic_classifier_10k_t2.csv"
input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_mini_testing.csv"
output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/tweetnlp_MINItest.csv"


# -- Initialize Models -- #
# model_topic = tweetnlp.load_model('topic_classification', multi_label=False)
# model_sentiment = tweetnlp.load_model('sentiment')
# model_hate = tweetnlp.load_model('hate')
# model_offensive = tweetnlp.load_model('offensive')


# --- BUILD FUNCTIONS --- #

# Function for Tweet Topic Classification
def get_topic_classification(tweet):
    
    # Check if tweet is a string
    if not isinstance(tweet, str):
        return np.nan # return "." in stata
    try:
        topic_dict = model_topic.topic(tweet)
        # return topic_dict['label']
        if topic_dict is None:
            return np.nan
        if isinstance(topic_dict, dict):
            return topic_dict.get('label', np.nan)
        return topic_dict

    except Exception as e:
        print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
        return np.nan
    

# Function for Sentiment Analysis
def get_sentiment_scores(tweet):

    if not isinstance(tweet, str):
        return pd.Series([np.nan, np.nan, np.nan, np.nan], 
                         index=['label', 'prob_neg', 'prob_neu', 'prob_pos'])
    
    try:
        sentiment_dict = model_sentiment.sentiment(tweet, return_probability=True)
        # print(sentiment_dict)

        probs = sentiment_dict.get('probability', {})
        return pd.Series([
            sentiment_dict.get('label', np.nan),
            probs.get('negative', np.nan),
            probs.get('neutral', np.nan),
            probs.get('positive', np.nan),
        ], index=['sentiment', 'prob_neg', 'prob_neu', 'prob_pos'])
    
    except Exception as e:
        print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
        return pd.Series([np.nan, np.nan, np.nan, np.nan], 
                         index=['label', 'prob_neg', 'prob_neu', 'prob_pos'])


# Hate Speech Detection
def get_hate_speech_scores(tweet):

    if not isinstance(tweet, str):
        return pd.Series([np.nan, np.nan, np.nan], 
                         index=['label', 'prob_non_hate', 'prob_hate'])
    
    try:
        hate_dict = model_hate.hate(tweet, return_probability=True)
        # print(hate_dict)

        probs = hate_dict.get('probability', {})
        return pd.Series([
            hate_dict.get('label', np.nan),
            probs.get('non-hate', np.nan),
            probs.get('hate', np.nan),
        ], index=['hate_speech', 'prob_non_hate', 'prob_hate'])
    
    except Exception as e:
        print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
        return pd.Series([np.nan, np.nan, np.nan], 
                         index=['label', 'prob_non_hate', 'prob_hate'])


# Offensive Language Detection
def get_offensive_lang_scores(tweet):

    if not isinstance(tweet, str):
        return pd.Series([np.nan, np.nan, np.nan], 
                         index=['label', 'prob_non_offensive', 'prob_offensive'])
    
    try:
        offensive_dict = model_offensive.offensive(tweet, return_probability=True)
        # print(offensive_dict)

        probs = offensive_dict.get('probability', {})
        return pd.Series([
            offensive_dict.get('label', np.nan),
            probs.get('non-offensive', np.nan),
            probs.get('offensive', np.nan),
        ], index=['offensive_lang', 'prob_non_offensive', 'prob_offensive'])
    
    except Exception as e:
        print(f"⚠️ Error processing tweet: {tweet[:50]}... ({e})")
        return pd.Series([np.nan, np.nan, np.nan], 
                         index=['label', 'prob_non_offensive', 'prob_offensive'])



# -------- RUN ANALYSES (batching) -------- #
if __name__ == '__main__':
    import math
    import torch

    # tune this based on your GPU/CPU memory
    BATCH_SIZE = 64

    # load models here (safe for Windows spawn)
    model_topic = tweetnlp.load_model('topic_classification')
    model_sentiment = tweetnlp.load_model('sentiment')
    model_hate = tweetnlp.load_model('hate')
    model_offensive = tweetnlp.load_model('offensive')

    # move underlying HF torch models to GPU if available
    try:
        if torch.cuda.is_available():
            for m in (model_topic, model_sentiment, model_hate, model_offensive):
                if hasattr(m, 'model') and hasattr(m.model, 'to'):
                    m.model.to('cuda')
    except Exception:
        pass

    # ---- DEBUG: inspect return formats (paste output here if unsure) ----
    sample_text = "I love pizza and sunny days"
    try:
        single = model_topic.topic(sample_text)
        print("DEBUG single topic output (repr):", repr(single))
        print("DEBUG single topic type:", type(single))
    except Exception as e:
        print("DEBUG single topic call error:", e)
    try:
        batch_sample = model_topic.topic([sample_text, "Rainy weather makes me sad"])
        print("DEBUG batch topic output type:", type(batch_sample))
        print("DEBUG batch topic repr (truncated):", repr(batch_sample)[:1000])
    except Exception as e:
        print("DEBUG batch topic call error:", e)

    # # also print available methods / signature to help mapping if needed
    # try:
    #     import inspect
    #     print("DEBUG model_topic methods:", [m for m in dir(model_topic) if not m.startswith('_')])
    #     if hasattr(model_topic, 'topic'):
    #         print("DEBUG signature model_topic.topic:", inspect.signature(model_topic.topic))
    #     if hasattr(model_topic, 'predict'):
    #         print("DEBUG signature model_topic.predict:", inspect.signature(model_topic.predict))
    # except Exception:
    #     pass
    # ---------------------------------------------------------------------

    df = pd.read_csv(input_path)
    texts = df['text'].astype(object).tolist()

    def try_call_batch(model, method, inputs, kwargs=None):
        kwargs = kwargs or {}
        fn = getattr(model, method)
        # First try true batch call (list input)
        try:
            out = fn(inputs, **kwargs)
            return out
        except Exception:
            # Fallback to per-item calls
            out = []
            for t in inputs:
                try:
                    out.append(fn(t, **kwargs))
                except Exception:
                    out.append(None)
            return out
        
    results = []
    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i+BATCH_SIZE]

        import re

        def clean_text_for_topic(s):
            if not isinstance(s, str):
                return ""
            s = s.strip()
            # remove URLs, mentions, stray hashes; collapse whitespace
            s = re.sub(r'http\S+|www\.\S+', '', s)
            s = re.sub(r'@\w+', '', s)
            s = s.replace('#', '')
            s = re.sub(r'\s+', ' ', s).strip()
            return s

        # Pre-clean batch to avoid model returning None for empty/URL-only strings
        batch_clean = [clean_text_for_topic(t) for t in batch]

        topic_out = []
        for idx, txt in enumerate(batch_clean):
            if txt == "":
                # keep original text for debug if you want
                print(f"DEBUG topic skipped (empty after clean) idx={i+idx} orig={repr(batch[idx])[:120]}")
                topic_out.append(None)
                continue

            # primary attempt: topic()
            try:
                res = model_topic.topic(txt)
                # if model returns None, try predict fallback below
                if res is not None:
                    topic_out.append(res)
                    continue
            except Exception as e:
                print(f"DEBUG topic() exception idx={i+idx}: {e} -- text={repr(txt)[:200]}")

            # fallback: try predict() if available
            if hasattr(model_topic, 'predict'):
                try:
                    res2 = model_topic.predict(txt)
                    topic_out.append(res2)
                    print(f"DEBUG topic.predict() used idx={i+idx}")
                    continue
                except Exception as e2:
                    print(f"DEBUG predict() exception idx={i+idx}: {e2} -- text={repr(txt)[:200]}")

            # final fallback: append None and log
            print(f"DEBUG topic result None idx={i+idx} text={repr(txt)[:200]}")
            topic_out.append(None)

        # keep using batched calls for the other models (sentiment/hate/off)
        sent_out = try_call_batch(model_sentiment, 'sentiment', batch, {'return_probability': True})
        hate_out = try_call_batch(model_hate, 'hate', batch, {'return_probability': True})
        off_out = try_call_batch(model_offensive, 'offensive', batch, {'return_probability': True})

        # normalize outputs to lists (existing behavior)
        if not isinstance(topic_out, (list, tuple)):
            topic_out = [topic_out] * len(batch)
        if not isinstance(sent_out, (list, tuple)):
            sent_out = [sent_out] * len(batch)
        if not isinstance(hate_out, (list, tuple)):
            hate_out = [hate_out] * len(batch)
        if not isinstance(off_out, (list, tuple)):
            off_out = [off_out] * len(batch)

        # # If topic_out contains Nones (because topic() raised), try a fallback to predict()
        # if isinstance(topic_out, (list, tuple)) and any(x is None for x in topic_out):
        #     if hasattr(model_topic, 'predict'):
        #         try:
        #             fallback = try_call_batch(model_topic, 'predict', batch)
        #             if not isinstance(fallback, (list, tuple)):
        #                 fallback = [fallback] * len(batch)
        #             topic_out = [t if t is not None else f for t, f in zip(topic_out, fallback)]
        #             print("DEBUG: used model_topic.predict() fallback for some items")
        #         except Exception as e:
        #             print("DEBUG: fallback predict failed:", e)

        # normalize outputs to lists
        if not isinstance(topic_out, (list, tuple)):
            topic_out = [topic_out] * len(batch)
        if not isinstance(sent_out, (list, tuple)):
            sent_out = [sent_out] * len(batch)
        if not isinstance(hate_out, (list, tuple)):
            hate_out = [hate_out] * len(batch)
        if not isinstance(off_out, (list, tuple)):
            off_out = [off_out] * len(batch)

        # Robust extractors to handle varying batch return formats
        def extract_label(item):
            if item is None:
                return np.nan
            # plain string
            if isinstance(item, str):
                return item
            # dict with direct 'label' or 'predicted_label' or 'class'
            if isinstance(item, dict):
                for k in ('label', 'predicted_label', 'class', 'result'):
                    v = item.get(k)
                    if isinstance(v, str):
                        return v
                    if isinstance(v, (list, tuple)) and v:
                        return v[0]
                # some versions return 'labels' as list of dicts: [{'label':..., 'score':...}, ...]
                labs = item.get('labels') or item.get('predictions') or item.get('results')
                if isinstance(labs, (list, tuple)) and labs:
                    first = labs[0]
                    if isinstance(first, dict):
                        return first.get('label') or first.get('class') or np.nan
                    return first
                # other nested possibilities
                inner = item.get('output') or item.get('outputs')
                if isinstance(inner, (str, dict, list, tuple)):
                    return extract_label(inner)
            # list/tuple -> inspect first element
            if isinstance(item, (list, tuple)) and item:
                return extract_label(item[0])
            return np.nan

        def extract_prob(item, key):
            if item is None:
                return np.nan
            if isinstance(item, dict):
                # probability might be dict, list, or single score
                for probs_key in ('probability', 'probabilities', 'probs', 'scores', 'scores_dict'):
                    probs = item.get(probs_key)
                    if isinstance(probs, dict):
                        # keys may be 'negative'/'neutral'/'positive' or 'non-hate'/'hate' etc.
                        # try direct key
                        if key in probs:
                            return probs.get(key, np.nan)
                        # maybe keys are different format: try lowercase matches
                        for k in probs:
                            if k.lower().replace(' ', '_') == key.lower().replace(' ', '_'):
                                return probs.get(k, np.nan)
                    if isinstance(probs, (list, tuple)) and probs:
                        first = probs[0]
                        if isinstance(first, dict):
                            if key in first:
                                return first.get(key, np.nan)
                            for k in first:
                                if k.lower().replace(' ', '_') == key.lower().replace(' ', '_'):
                                    return first.get(k, np.nan)
                # sometimes score is a single 'score' or 'confidence'
                for score_key in ('score', 'confidence', 'prob'):
                    v = item.get(score_key)
                    if isinstance(v, (int, float)):
                        return v
            if isinstance(item, (list, tuple)) and item:
                return extract_prob(item[0], key)
            return np.nan

        # Optional debug for first batch if labels are blank
        if i == 0:
            print("DEBUG sample topic_out[0] repr:", repr(topic_out[0])[:1000])
            print("DEBUG sample sent_out[0] repr:", repr(sent_out[0])[:1000])

        for j in range(len(batch)):
            to = topic_out[j]
            so = sent_out[j]
            ho = hate_out[j]
            oo = off_out[j]

            row = {
                'label': extract_label(to),
                'sentiment': extract_label(so),
                'prob_neg': extract_prob(so, 'negative'),
                'prob_neu': extract_prob(so, 'neutral'),
                'prob_pos': extract_prob(so, 'positive'),
                'hate_speech': extract_label(ho),
                'prob_non_hate': extract_prob(ho, 'non-hate'),
                'prob_hate': extract_prob(ho, 'hate'),
                'offensive_lang': extract_label(oo),
                'prob_non_offensive': extract_prob(oo, 'non-offensive'),
                'prob_offensive': extract_prob(oo, 'offensive'),
            }
            results.append(row)


    results_df = pd.DataFrame(results)
    out_df = pd.concat([df.reset_index(drop=True), results_df.reset_index(drop=True)], axis=1)
    out_df.to_csv(output_path, index=False)
    print("\n ✅ Tweet NLP complete. Output saved to:", output_path)





# # -------- RUN ANALYSES (optimized) -------- #
# import math
# import multiprocessing
# from multiprocessing import Pool

# # Optional: how many parallel worker processes to use (set to 1 to disable multiprocessing)
# # WORKERS will be determined inside __main__ to avoid running before spawn on Windows.

# def init_worker():
#     # each worker loads its own copy of the models once
#     global model_topic, model_sentiment, model_hate, model_offensive
#     import tweetnlp
#     model_topic = tweetnlp.load_model('topic_classification')
#     model_sentiment = tweetnlp.load_model('sentiment')
#     model_hate = tweetnlp.load_model('hate')
#     model_offensive = tweetnlp.load_model('offensive')
#     # try to move underlying torch models to GPU if available
#     try:
#         import torch
#         if torch.cuda.is_available():
#             for m in (model_topic, model_sentiment, model_hate, model_offensive):
#                 if hasattr(m, 'model') and hasattr(m.model, 'to'):
#                     m.model.to('cuda')
#     except Exception:
#         pass

# def process_text(text):
#     # helper executed inside worker process (must be top-level for pickling)
#     return {
#         'label': get_topic_classification(text),
#         **get_sentiment_scores(text).to_dict(),
#         **get_hate_speech_scores(text).to_dict(),
#         **get_offensive_lang_scores(text).to_dict()
#     }

# if __name__ == '__main__':
#     # Required on Windows to safely spawn child processes
#     multiprocessing.freeze_support()

#     WORKERS = max(1, min(4, multiprocessing.cpu_count() - 1))
#     print(f"\n 🚀 Using {WORKERS} worker(s) for processing.")

#     # If running single-process, load models here (so they are available to get_* functions).
#     if WORKERS == 1:
#         import tweetnlp
#         model_topic = tweetnlp.load_model('topic_classification', multi_label=False)
#         model_sentiment = tweetnlp.load_model('sentiment')
#         model_hate = tweetnlp.load_model('hate')
#         model_offensive = tweetnlp.load_model('offensive')
#         # try GPU move if desired
#         try:
#             import torch
#             if torch.cuda.is_available():
#                 for m in (model_topic, model_sentiment, model_hate, model_offensive):
#                     if hasattr(m, 'model') and hasattr(m.model, 'to'):
#                         m.model.to('cuda')
#         except Exception:
#             pass

#     # read once
#     df = pd.read_csv(input_path)
#     texts = df['text'].astype(object).tolist()

#     if WORKERS == 1:
#         # single-process loop
#         results = [process_text(t) for t in texts]
#     else:
#         # parallel processing: each worker loads models once (via init_worker)
#         with Pool(processes=WORKERS, initializer=init_worker) as pool:
#             results = pool.map(process_text, texts)

#     # attach results and save once
#     results_df = pd.DataFrame(results)
#     df = pd.concat([df.reset_index(drop=True), results_df.reset_index(drop=True)], axis=1)

#     # write output only once
#     df.to_csv(output_path, index=False)
#     print("\n ✅ Tweet NLP complete. Output saved to:", output_path)

# # ...existing code...



# # -------- RUN ANALYSES -------- #

# df = pd.read_csv(input_path)

# # --- Topic Classification --- #
# df['label'] = df['text'].swifter.apply(get_topic_classification)
# # df[['label']] = df['text'].swifter.apply(lambda x: pd.Series(get_topic_classification(x)))

# print("\n ✅ Topic classification complete.")


# # --- Sentiment Analysis --- #
# sentiment_results = df['text'].swifter.apply(get_sentiment_scores)
# df = pd.concat([df, sentiment_results], axis=1)
# df.to_csv(output_path, index=False)

# print("\n ✅ Sentiment Analysis complete.")


# # --- Hate Speech  --- #
# hate_results = df['text'].swifter.apply(get_hate_speech_scores)
# df = pd.concat([df, hate_results], axis=1)
# df.to_csv(output_path, index=False)

# print("\n ✅ Hate Speech Analysis complete.")


# # --- Offensive Language  --- #
# offensive_results = df['text'].swifter.apply(get_offensive_lang_scores)
# df = pd.concat([df, offensive_results], axis=1)
# df.to_csv(output_path, index=False)

# print("\n ✅ Offensive Language Analysis complete.")


# # --- All Analyses Complete --- #
# print("\n ✅ Tweet NLP complete. Output saved to:", output_path)





# # --- Maybe needed ----- #
#         if not isinstance(topic_out, (list, tuple)):
#             topic_out = [topic_out] * len(batch)
#         if not isinstance(sent_out, (list, tuple)):
#             sent_out = [sent_out] * len(batch)
#         if not isinstance(hate_out, (list, tuple)):
#             hate_out = [hate_out] * len(batch)
#         if not isinstance(off_out, (list, tuple)):
#             off_out = [off_out] * len(batch)

#         for j in range(len(batch)):
#             to = topic_out[j]
#             so = sent_out[j]
#             ho = hate_out[j]
#             oo = off_out[j]

#             def safe_label(d):
#                 if d is None: return np.nan
#                 if isinstance(d, dict): return d.get('label', np.nan)
#                 return d

#             def safe_prob(d, key):
#                 if not isinstance(d, dict): return np.nan
#                 probs = d.get('probability', {}) or {}
#                 return probs.get(key, np.nan)

#             row = {
#                 'label': safe_label(to),
#                 'sentiment': safe_label(so),
#                 'prob_neg': safe_prob(so, 'negative'),
#                 'prob_neu': safe_prob(so, 'neutral'),
#                 'prob_pos': safe_prob(so, 'positive'),
#                 'hate_speech': safe_label(ho),
#                 'prob_non_hate': safe_prob(ho, 'non-hate'),
#                 'prob_hate': safe_prob(ho, 'hate'),
#                 'offensive_lang': safe_label(oo),
#                 'prob_non_offensive': safe_prob(oo, 'non-offensive'),
#                 'prob_offensive': safe_prob(oo, 'offensive'),
#             }
#             results.append(row)