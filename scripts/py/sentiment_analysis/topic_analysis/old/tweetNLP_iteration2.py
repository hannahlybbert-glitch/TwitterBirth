# Iteration


import os
import warnings
import tweetnlp
import pandas as pd
import numpy as np
import re
from multiprocessing import Pool, cpu_count
import multiprocessing

swifter_enabled = False
try:
    import swifter
    swifter.config.progress_bar = True
    swifter_enabled = True
except Exception:
    pass

os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
warnings.filterwarnings("ignore", message=".*use_auth_token.*")

input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_mini_testing.csv"
output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/tweetnlp_MINItest_it2.csv"

# Tunables
WORKERS = max(1, min(4, cpu_count() - 1))  # try 1..4 by default; lower if memory is tight
CHUNK_SIZE = 5000        # number of rows per chunk passed to each worker (tune)
BATCH_SIZE = 128         # batch size for sentiment/hate/off calls inside a worker
cuda_move = True         # set False if you don't want to move models to GPU

# Globals for worker-loaded models
model_topic = None
model_sentiment = None
model_hate = None
model_offensive = None

def init_worker():
    "Initializer for Pool workers — loads models once per worker."
    global model_topic, model_sentiment, model_hate, model_offensive
    import tweetnlp, torch
    model_topic = tweetnlp.load_model('topic_classification')      # preserve original behavior
    model_sentiment = tweetnlp.load_model('sentiment')
    model_hate = tweetnlp.load_model('hate')
    model_offensive = tweetnlp.load_model('offensive')
    if cuda_move:
        try:
            if torch.cuda.is_available():
                for m in (model_topic, model_sentiment, model_hate, model_offensive):
                    if hasattr(m, 'model') and hasattr(m.model, 'to'):
                        m.model.to('cuda')
        except Exception:
            pass

def clean_text_for_topic(s):
    if not isinstance(s, str):
        return ""
    s = s.strip()
    s = re.sub(r'http\S+|www\.\S+', '', s)
    s = re.sub(r'@\w+', '', s)
    s = s.replace('#', '')
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def try_batch_call(model, method, inputs, kwargs=None):
    "Try list input (batch) then fall back to per-item calls; returns list aligned to inputs."
    kwargs = kwargs or {}
    fn = getattr(model, method)
    # try batch
    try:
        out = fn(inputs, **kwargs)
        # If single dict returned for entire list, try to expand
        if not isinstance(out, (list, tuple)):
            out = [out] * len(inputs)
        return list(out)
    except Exception:
        # per-item fallback
        out = []
        for t in inputs:
            try:
                out.append(fn(t, **kwargs))
            except Exception:
                out.append(None)
        return out

def safe_topic_call(text):
    "Call topic per-item with cleaning and fallback to predict(); returns raw model output or None."
    txt = clean_text_for_topic(text)
    if txt == "":
        return None
    try:
        res = model_topic.topic(txt)
        if res is not None:
            return res
    except Exception:
        pass
    # fallback to predict if available
    if hasattr(model_topic, 'predict'):
        try:
            return model_topic.predict(txt)
        except Exception:
            return None
    return None

def extract_label(item):
    "Extract a single label string or np.nan from various possible model outputs."
    if item is None:
        return np.nan
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        for k in ('label', 'predicted_label', 'class', 'result'):
            v = item.get(k)
            if isinstance(v, str):
                return v
            if isinstance(v, (list, tuple)) and v:
                return v[0]
        labs = item.get('labels') or item.get('predictions') or item.get('results')
        if isinstance(labs, (list, tuple)) and labs:
            first = labs[0]
            if isinstance(first, dict):
                return first.get('label') or first.get('class') or np.nan
            return first
        inner = item.get('output') or item.get('outputs')
        if isinstance(inner, (str, dict, list, tuple)):
            return extract_label(inner)
    if isinstance(item, (list, tuple)) and item:
        return extract_label(item[0])
    return np.nan

def extract_prob(item, key):
    "Extract probability for `key` from model output or np.nan."
    if item is None:
        return np.nan
    if isinstance(item, dict):
        for probs_key in ('probability', 'probabilities', 'probs', 'scores'):
            probs = item.get(probs_key)
            if isinstance(probs, dict):
                if key in probs:
                    return probs.get(key, np.nan)
                # try normalized key matching
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
        for score_key in ('score', 'confidence', 'prob'):
            v = item.get(score_key)
            if isinstance(v, (int, float)):
                return v
    if isinstance(item, (list, tuple)) and item:
        return extract_prob(item[0], key)
    return np.nan

def process_chunk(rows):
    """
    rows: list of (index, text)
    returns: list of dicts with index + result columns
    """
    indices = [r[0] for r in rows]
    texts = [r[1] for r in rows]

    # topic: do per-item safe calls (preserves original behavior)
    topic_out = [safe_topic_call(t) for t in texts]

    # sentiment/hate/offensive: attempt batched call (faster)
    sent_out = try_batch_call(model_sentiment, 'sentiment', texts, {'return_probability': True})
    hate_out = try_batch_call(model_hate, 'hate', texts, {'return_probability': True})
    off_out = try_batch_call(model_offensive, 'offensive', texts, {'return_probability': True})

    results = []
    for idx, t, to, so, ho, oo in zip(indices, texts, topic_out, sent_out, hate_out, off_out):
        row = {
            'index': idx,
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
    return results

if __name__ == '__main__':
    # Windows-safe multiprocessing
    multiprocessing.freeze_support()

    print(f"Using WORKERS={WORKERS}, CHUNK_SIZE={CHUNK_SIZE}, BATCH_SIZE={BATCH_SIZE}, cuda_move={cuda_move}")

    # Read once
    df = pd.read_csv(input_path)
    texts = df['text'].astype(object).tolist()
    n = len(texts)

    # Prepare row chunks (list of lists of (index, text))
    chunks = []
    for start in range(0, n, CHUNK_SIZE):
        sub = [(i, texts[i]) for i in range(start, min(start + CHUNK_SIZE, n))]
        chunks.append(sub)

    # Parallel map
    all_results = []
    if WORKERS == 1:
        init_worker()  # load models in main process
        for c in chunks:
            all_results.extend(process_chunk(c))
    else:
        with Pool(processes=WORKERS, initializer=init_worker) as pool:
            for res in pool.imap_unordered(process_chunk, chunks):
                all_results.extend(res)

    # Build results DataFrame and merge to original
    res_df = pd.DataFrame(all_results).set_index('index').sort_index()
    # Ensure all rows present
    for col in ['label','sentiment','prob_neg','prob_neu','prob_pos',
                'hate_speech','prob_non_hate','prob_hate',
                'offensive_lang','prob_non_offensive','prob_offensive']:
        if col not in res_df.columns:
            res_df[col] = np.nan
    res_df = res_df.reindex(range(n)).reset_index(drop=True)

    out_df = pd.concat([df.reset_index(drop=True), res_df.reset_index(drop=True)], axis=1)
    out_df.to_csv(output_path, index=False)
    print("✅ Tweet NLP complete. Output saved to:", output_path)
# ...existing code...