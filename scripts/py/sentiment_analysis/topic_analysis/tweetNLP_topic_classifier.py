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

# Dynamically determine optimal batch size based on available VRAM
def get_optimal_batch_size(device, model, tokenizer, target_vram_usage=0.8):
    """
    Estimate optimal batch size based on available GPU memory.
    Only runs if CUDA is available.
    """
    if device.type != "cuda":
        return 128  # Use default for CPU
    
    try:
        # Get available VRAM
        total_vram = torch.cuda.get_device_properties(device).total_memory / 1e9  # GB
        
        # Test different batch sizes starting from 512
        for test_batch in [512, 256, 128]:
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
            
            # Create dummy batch and test memory usage
            dummy_batch = ["This is a test sentence."] * test_batch
            try:
                enc = tokenizer(
                    dummy_batch,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=128,
                    return_token_type_ids=False
                ).to(device)
                
                with torch.no_grad():
                    _ = model(**enc).logits
                
                used_memory = torch.cuda.max_memory_allocated(device) / 1e9  # GB
                if used_memory < total_vram * target_vram_usage:
                    print(f"✅ Optimal batch size: {test_batch} (using {used_memory:.2f}GB/{total_vram:.2f}GB VRAM)")
                    return test_batch
            except Exception:
                continue
        
        return 128  # Fallback
    except Exception as e:
        print(f"⚠️ Could not determine optimal batch size: {e}. Using default 128.")
        return 128

# ID family label index
id2label = model.config.id2label
FAMILY_IDX = [i for i, lbl in id2label.items() if "family" in lbl.lower()]
assert len(FAMILY_IDX) == 1, f"Expected one family label, got {FAMILY_IDX}"
FAMILY_IDX = FAMILY_IDX[0]

input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_FULL.csv"
output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/NLP_topic_classifier_FULL.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/NLP_topic_classifier_10k_chatedit.csv"
# input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_10kSAMPLE.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/NLP_topic_classifier_10k.csv"
# input_path = "D:/TwitterBirth/data/sentiment_analysis/tweet_text_handcode.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/NLP_topic_classifier100.csv"
# output_path = "D:/TwitterBirth/data/sentiment_analysis/output/tweetNLP/classification_10k.csv"


# ---------- Unified Classification Function (Single Pass) ---------- #
def classify_tweets(texts, batch_size=128, threshold=0.5):
    """
    Single-pass classification: processes tweets once to get both family and topic predictions.
    
    Optimizations:
    - Single forward pass (avoid 2x processing)
    - Minimal GPU transfers
    - Generator-based approach reduces memory overhead
    
    Args:
        texts: list of strings
        batch_size: batch size for inference
        threshold: threshold for family classification
        
    Returns:
        family_probs: array of family probabilities (N,)
        family_flags: binary flags (N,)
        topic_labels: array of topic label strings (N,)
    """
    if len(texts) == 0:
        L = model.config.num_labels
        return (
            np.empty((0,)),
            np.empty((0,), dtype=int),
            np.empty((0,), dtype=object)
        )
    
    all_family_probs = []
    all_topic_labels = []
    
    # Process in batches with single forward pass
    for i in tqdm(range(0, len(texts), batch_size), desc="Classifying tweets"):
        batch = texts[i:i + batch_size]
        
        # Tokenize with optimized settings (no token_type_ids needed for RoBERTa)
        enc = tokenizer(
            batch,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=128,
            return_token_type_ids=False  # Not needed for RoBERTa, saves memory
        ).to(device)  # Single transfer to device
        
        with torch.no_grad():
            logits = model(**enc).logits  # Single forward pass (bsz, num_labels)
        
        # Convert logits to probabilities once
        probs = torch.sigmoid(logits).cpu().numpy()  # (bsz, num_labels)
        
        # Extract family probabilities
        all_family_probs.extend(probs[:, FAMILY_IDX])
        
        # Extract topic labels (highest probability)
        topic_indices = probs.argmax(axis=1)
        topic_labels = [id2label[int(idx)] for idx in topic_indices]
        all_topic_labels.extend(topic_labels)
    
    # Convert to numpy arrays
    family_probs = np.asarray(all_family_probs)
    family_flags = (family_probs > threshold).astype(np.int8)  # Use int8 to save memory
    topic_labels = np.asarray(all_topic_labels, dtype=object)
    
    return family_probs, family_flags, topic_labels



# ---------- Run Classification Function ---------- #
def classify_file(input_path, output_path, text_column="text",
                  batch_size=None, threshold=0.5):
    """
    Reads file, classifies tweets, writes CSV with optimized batch processing.
    
    Args:
        input_path: Path to input CSV
        output_path: Path to output CSV
        text_column: Name of column containing text
        batch_size: Batch size (auto-tuned if None)
        threshold: Threshold for family classification
    """
    import time
    
    # Load file
    print(f"📂 Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    print(f"   Loaded {len(df):,} rows")

    if text_column not in df.columns:
        raise KeyError(f"Column '{text_column}' not found in input file.")

    # Auto-tune batch size if not specified
    if batch_size is None:
        print("🔧 Auto-tuning batch size based on GPU memory...")
        batch_size = get_optimal_batch_size(device, model, tokenizer)
    
    # Prepare texts (minimal memory overhead)
    texts = df[text_column].fillna("").astype(str).tolist()
    
    # Run unified classifier (single pass for both family and topic)
    print(f"🚀 Classifying {len(texts):,} tweets (batch_size={batch_size})...")
    start_time = time.time()
    
    fam_probs, fam_flags, topic_labels = classify_tweets(
        texts,
        batch_size=batch_size,
        threshold=threshold
    )
    
    elapsed = time.time() - start_time
    tweets_per_sec = len(texts) / elapsed
    print(f"   ⏱️  Completed in {elapsed:.1f}s ({tweets_per_sec:.0f} tweets/sec)")

    # Append results
    df["family_prob"] = fam_probs
    df["family_flag"] = fam_flags
    df["topic"] = topic_labels

    # Save results
    print(f"💾 Saving results to {output_path}...")
    df.to_csv(output_path, index=False)
    print(f"✅ Done! Results saved.")



# ------------ EXECUTE ------------ #
if __name__ == "__main__":
    classify_file(
        input_path=input_path,
        output_path=output_path,
        text_column="text",   # change if your column name is different
        batch_size=None,      # Auto-tune based on GPU memory (set to int for manual control)
        threshold=0.5
    )





