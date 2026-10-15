"""
Compute accuracy, precision, recall, and F1 of the LLM prompt against the
handcoded truth column.

Reads ControlGroup/data/LLM/seed_tweets/test/handcoded_2016.csv, which contains
one row per handcoded tweet plus a trailing totals row (blank tweet_id) that is
dropped before scoring. In the LLM_anniversary_flag column, -99 means the
prompt did not produce a usable label for that tweet; both -99 and 0 are
treated as a negative (non-anniversary) prediction.
"""

from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "LLM" / "seed_tweets" / "test" / "handcoded_2016.csv"
TRUTH_COL = "Anniversary_Flag"
PRED_COL = "LLM_anniversary_flag_mini_T2"
MISSING_VALUE = -99


def main():
    df = pd.read_csv(DATA_PATH)
    df = df[df["tweet_id"].notna()]

    df[PRED_COL] = df[PRED_COL].replace(MISSING_VALUE, 0).fillna(0).astype(int)
    df[TRUTH_COL] = df[TRUTH_COL].astype(int)

    print(f"Loaded {len(df)} handcoded tweets from {DATA_PATH}\n")

    truth = df[TRUTH_COL]
    pred = df[PRED_COL]

    tp = ((pred == 1) & (truth == 1)).sum()
    tn = ((pred == 0) & (truth == 0)).sum()
    fp = ((pred == 1) & (truth == 0)).sum()
    fn = ((pred == 0) & (truth == 1)).sum()

    accuracy = (tp + tn) / len(df)
    precision = tp / (tp + fp) if (tp + fp) else float("nan")
    recall = tp / (tp + fn) if (tp + fn) else float("nan")
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else float("nan")

    print(f"{PRED_COL}:")
    print(f"  accuracy  = {accuracy:.3f} ({tp + tn}/{len(df)})")
    print(f"  precision = {precision:.3f} ({tp}/{tp + fp})")
    print(f"  recall    = {recall:.3f} ({tp}/{tp + fn})")
    print(f"  f1        = {f1:.3f}")
    print(f"  confusion matrix: TP={tp}  FP={fp}  TN={tn}  FN={fn}\n")


if __name__ == "__main__":
    main()
