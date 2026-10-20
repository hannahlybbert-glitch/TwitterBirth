# Author: Hannah Lybbert
# Created: 2026-07-01
# Updated: 2026-10-16
# Purpose: Confusion matrix and TP/FP/TN/FN rates of the LLM anniversary flag against hand-coding

from pathlib import Path

import pandas as pd

DATA_DIR      = Path(__file__).resolve().parents[2] / "data/LLM/seed_tweets"
DATA_PATH     = DATA_DIR / "llm_anniversary_handcoded.csv"
ROUND2_PATH   = DATA_DIR / "llm_anniversary_handcoded_2.csv"  # random 100 with flag = 1, confidence >= 95
FULL_PATH     = DATA_DIR / "anniversary_tweets_RE_classified.csv"
TRUTH_COL     = "hancoded"           # 1 = true anniversary; 2 or blank = not
PRED_COL      = "anniversary_flag"   # 1 = anniversary; 0 = not; -99 = unparsed LLM response
CONF_COL      = "confidence"
MISSING_VALUE = -99
THRESHOLDS    = [90, 95, 100]        # LLM flag counts as 1 only if confidence >= threshold


# ----------------------------------------------------------------
# 1. Scoring
# ----------------------------------------------------------------
def rate(num, den):
    return f"{num / den:.3f} ({num}/{den})" if den else f"n/a (0/0)"


def score(df, label):
    truth = (df[TRUTH_COL] == 1).astype(int)
    pred  = (df[PRED_COL] == 1).astype(int)

    tp = int(((pred == 1) & (truth == 1)).sum())
    fp = int(((pred == 1) & (truth == 0)).sum())
    tn = int(((pred == 0) & (truth == 0)).sum())
    fn = int(((pred == 0) & (truth == 1)).sum())

    print(f"{label} (n = {len(df)})")
    print(f"  confusion matrix: TP={tp}  FP={fp}  TN={tn}  FN={fn}")
    print(f"  TP rate (recall)  = {rate(tp, tp + fn)}")
    print(f"  FP rate           = {rate(fp, fp + tn)}")
    print(f"  TN rate           = {rate(tn, tn + fp)}")
    print(f"  FN rate           = {rate(fn, fn + tp)}")
    print(f"  precision         = {rate(tp, tp + fp)}")
    print(f"  accuracy          = {rate(tp + tn, len(df))}\n")


def label(t):
    return "== 100" if t == 100 else f">= {t}"


# Hand-coded sample: same scoring, with flag = 1 only if confidence clears the threshold
def score_thresholds(df):
    truth = df[TRUTH_COL] == 1
    print("Hand-coded sample by confidence threshold")
    print(f"  {'confidence':<11}{'flagged':>8}{'TP':>5}{'FP':>5}{'TN':>5}{'FN':>5}"
          f"{'precision':>11}{'FP rate':>9}{'recall':>8}")
    for t in [0] + THRESHOLDS:
        pred = (df[PRED_COL] == 1) & (df[CONF_COL] >= t)
        tp, fp = int((pred & truth).sum()), int((pred & ~truth).sum())
        tn, fn = int((~pred & ~truth).sum()), int((~pred & truth).sum())
        prec = f"{tp / (tp + fp):.3f}" if tp + fp else "n/a"
        fpr  = f"{fp / (fp + tn):.3f}" if fp + tn else "n/a"
        rec  = f"{tp / (tp + fn):.3f}" if tp + fn else "n/a"
        name = "any" if t == 0 else label(t)
        print(f"  {name:<11}{tp + fp:>8}{tp:>5}{fp:>5}{tn:>5}{fn:>5}{prec:>11}{fpr:>9}{rec:>8}")
    print()


# Full sample: how many LLM-flagged anniversaries survive each threshold
def full_sample_thresholds():
    full = pd.read_csv(FULL_PATH, usecols=[PRED_COL, CONF_COL])
    pos = full[full[PRED_COL] == 1]
    print(f"Full sample ({FULL_PATH.name}): {len(full):,} tweets, {len(pos):,} flagged anniversaries")
    for t in THRESHOLDS:
        n = int((pos[CONF_COL] >= t).sum())
        print(f"  confidence {label(t):<7} {n:>7,}  ({n / len(pos):.1%} of flagged, {n / len(full):.1%} of all tweets)")
    print()


# Round 2: every tweet is LLM-flagged, so only precision / false positives can be measured
def score_round2():
    df = pd.read_csv(ROUND2_PATH, encoding_errors="replace")
    df = df[df["created_at"].notna()]
    # round 2 coding differs from round 1: blank = true anniversary, x = not
    codes = df[TRUTH_COL].fillna("").astype(str).str.strip().str.lower()
    true  = codes == ""
    conf  = pd.to_numeric(df[CONF_COL], errors="coerce")

    print(f"Round 2 ({ROUND2_PATH.name}, n = {len(df)}; all flag = 1, confidence >= 95)")
    print(f"  hand-codes: blank (true) = {int(true.sum())}, x (not) = {int((codes == 'x').sum())}")
    other = codes[~true & (codes != "x")]
    if len(other):
        print(f"  WARNING: {len(other)} unexpected codes counted as not-anniversary: {sorted(other.unique())}")
    for name, mask in [("confidence >= 95", conf >= 95), ("confidence 95-99", conf.between(95, 99)),
                       ("confidence == 100", conf == 100)]:
        tp = int((mask & true).sum())
        fp = int((mask & ~true).sum())
        print(f"  {name:<18} n = {tp + fp:>3}   TP = {tp:>3}   FP = {fp:>3}   precision = {rate(tp, tp + fp)}")
    print()


# ----------------------------------------------------------------
# 2. Main
# ----------------------------------------------------------------
def main():
    df = pd.read_csv(DATA_PATH, encoding_errors="replace")  # Excel CSVs aren't always UTF-8
    df = df[df["tweet_id"].notna()]  # drop blank trailing rows
    df[TRUTH_COL] = pd.to_numeric(df[TRUTH_COL], errors="coerce")
    df[PRED_COL]  = pd.to_numeric(df[PRED_COL], errors="coerce").fillna(MISSING_VALUE).astype(int)
    df[CONF_COL]  = pd.to_numeric(df[CONF_COL], errors="coerce").fillna(0)

    n_missing = int((df[PRED_COL] == MISSING_VALUE).sum())
    print(f"Loaded {len(df)} hand-coded tweets from {DATA_PATH}")
    print(f"  true anniversaries (hand-coded 1): {int((df[TRUTH_COL] == 1).sum())}")
    print(f"  LLM flag = {MISSING_VALUE} (unparsed): {n_missing}\n")

    score(df, f"All tweets ({MISSING_VALUE} counted as LLM = 0)")
    score(df[df[PRED_COL] != MISSING_VALUE], f"Parsed tweets only ({MISSING_VALUE} dropped)")
    score_thresholds(df)
    full_sample_thresholds()
    score_round2()


if __name__ == "__main__":
    main()
