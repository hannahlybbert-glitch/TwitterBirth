# Author: Hannah Lybbert
# Created: 02/27/2026
# Updated: 02/27/2026
# Purpose: Evaluate LLM birth detection accuracy against handcoded 100-post sample

import os
import pandas as pd

os.chdir("D:/TwitterBirth")

# File paths
# LLM_PATH      = "Reddit/data/LLM/test_samples/birth_detection_100.csv"
# LLM_PATH      = "Reddit/data/LLM/test_samples/birth_detection_100_T2.csv"
# LLM_PATH      = "Reddit/data/LLM/test_samples/birth_detection_2nd_100.csv"
# LLM_PATH = "Reddit/data/LLM/test_samples/birth_detection_parenting_100.csv"
LLM_PATH = "Reddit/data/LLM/test_samples/birth_detection_parenting_100_full.csv"

# HANDCODE_PATH = "Reddit/data/handcode/reddit_test_sample_handcoded.csv"
# HANDCODE_PATH = "Reddit/data/handcode/reddit_2nd_test_sample_handcoded.csv"
# HANDCODE_PATH = "Reddit/data/handcode/reddit_parenting_test_sample_handcoded.csv"
HANDCODE_PATH = "Reddit/data/handcode/reddit_parenting_100_sample_handcoded(2).csv"

OUTPUT_PATH   = "Reddit/data/LLM/performance/llm_accuracy_comparison_parenting_100.csv"

# Load data
df_llm = pd.read_csv(LLM_PATH, encoding="utf-8")
df_hc  = pd.read_csv(HANDCODE_PATH, encoding="utf-8")

df_llm["id"] = df_llm["id"].astype(str)
df_hc["id"]  = df_hc["id"].astype(str)

# Merge on id
df = df_hc[["id", "birth_flag", "female"]].merge(
    df_llm[["id", "birth_flag", "days_from_birth", "confidence", "p_female", "p_male"]],
    on="id", how="inner", suffixes=("_hc", "_llm")
)
print(f"Merged {len(df)} records\n")

# Binarize LLM gender: p_female > 50 → 1, p_male > 50 → 0, tied → -99 (uncertain)
df["female_llm"] = df.apply(
    lambda r: 1 if r["p_female"] > 50 else (0 if r["p_male"] > 50 else -99),
    axis=1
)


############################# HELPER FUNCTIONS #############################

def confusion_matrix_stats(tp, fp, fn, tn):
    total     = tp + fp + fn + tn
    accuracy  = (tp + tn) / total if total > 0 else None
    precision = tp / (tp + fp)    if (tp + fp) > 0 else None
    recall    = tp / (tp + fn)    if (tp + fn) > 0 else None
    f1        = (2 * precision * recall / (precision + recall)
                 if precision and recall and (precision + recall) > 0 else None)
    return accuracy, precision, recall, f1

def print_confusion_matrix(tp, fp, fn, tn, label=""):
    print(f"  {'':20s}  Handcode=1  Handcode=0")
    print(f"  {'LLM=1':20s}  {tp:>10}  {fp:>10}")
    print(f"  {'LLM=0':20s}  {fn:>10}  {tn:>10}")

def fmt(val):
    return f"{val:.3f}" if val is not None else "N/A"


############################# BIRTH FLAG ACCURACY #############################

print("=" * 60)
print("BIRTH FLAG ACCURACY")
print("=" * 60)

# Summarize LLM predictions
llm_flag_counts = df["birth_flag_llm"].value_counts().to_dict()
print(f"\nLLM birth_flag distribution:")
print(f"  1   (within window): {llm_flag_counts.get(1,  0):>4}")
print(f"  0   (outside):       {llm_flag_counts.get(0,  0):>4}")
print(f"  -99 (uncertain):     {llm_flag_counts.get(-99, 0):>4}")

# Compare on all rows — treat LLM -99 as incorrect
df["birth_flag_llm_binary"] = df["birth_flag_llm"].apply(lambda x: 1 if x == 1 else 0)

tp = ((df["birth_flag_llm_binary"] == 1) & (df["birth_flag_hc"] == 1)).sum()
fp = ((df["birth_flag_llm_binary"] == 1) & (df["birth_flag_hc"] == 0)).sum()
fn = ((df["birth_flag_llm_binary"] == 0) & (df["birth_flag_hc"] == 1)).sum()
tn = ((df["birth_flag_llm_binary"] == 0) & (df["birth_flag_hc"] == 0)).sum()

accuracy, precision, recall, f1 = confusion_matrix_stats(tp, fp, fn, tn)

print(f"\nConfusion matrix (LLM -99 treated as 0):")
print_confusion_matrix(tp, fp, fn, tn)
print(f"\n  Accuracy:  {fmt(accuracy)}")
print(f"  Precision: {fmt(precision)}")
print(f"  Recall:    {fmt(recall)}")
print(f"  F1:        {fmt(f1)}")

# Also report accuracy excluding LLM uncertain rows
df_certain = df[df["birth_flag_llm"] != -99].copy()
if len(df_certain) > 0:
    tp2 = ((df_certain["birth_flag_llm"] == 1) & (df_certain["birth_flag_hc"] == 1)).sum()
    fp2 = ((df_certain["birth_flag_llm"] == 1) & (df_certain["birth_flag_hc"] == 0)).sum()
    fn2 = ((df_certain["birth_flag_llm"] == 0) & (df_certain["birth_flag_hc"] == 1)).sum()
    tn2 = ((df_certain["birth_flag_llm"] == 0) & (df_certain["birth_flag_hc"] == 0)).sum()
    accuracy2, precision2, recall2, f12 = confusion_matrix_stats(tp2, fp2, fn2, tn2)
    print(f"\nExcluding LLM uncertain (-99) rows (n={len(df_certain)}):")
    print_confusion_matrix(tp2, fp2, fn2, tn2)
    print(f"\n  Accuracy:  {fmt(accuracy2)}")
    print(f"  Precision: {fmt(precision2)}")
    print(f"  Recall:    {fmt(recall2)}")
    print(f"  F1:        {fmt(f12)}")

# Disagreements on birth flag
df_disagree_birth = df[df["birth_flag_llm_binary"] != df["birth_flag_hc"]].copy()
if len(df_disagree_birth) > 0:
    print(f"\nDisagreements ({len(df_disagree_birth)} rows):")
    for _, row in df_disagree_birth.iterrows():
        print(f"  id={row['id']}  hc={int(row['birth_flag_hc'])}  llm={int(row['birth_flag_llm'])}  conf={int(row['confidence'])}")


############################# GENDER ACCURACY #############################

print("\n" + "=" * 60)
print("GENDER ACCURACY")
print("=" * 60)

# Only compare rows where both are determinate
df_gender = df[(df["female"] != -99) & (df["female_llm"] != -99)].copy()

llm_gender_counts = df["female_llm"].value_counts().to_dict()
print(f"\nLLM gender distribution (all 100 rows):")
print(f"  1   (female):    {llm_gender_counts.get(1,   0):>4}")
print(f"  0   (male):      {llm_gender_counts.get(0,   0):>4}")
print(f"  -99 (uncertain): {llm_gender_counts.get(-99, 0):>4}")

hc_gender_counts = df["female"].value_counts().to_dict()
print(f"\nHandcoded gender distribution (all 100 rows):")
print(f"  1   (female):    {hc_gender_counts.get(1,   0):>4}")
print(f"  0   (male):      {hc_gender_counts.get(0,   0):>4}")
print(f"  -99 (uncertain): {hc_gender_counts.get(-99, 0):>4}")

print(f"\nComparable rows (both determinate): n={len(df_gender)}")

if len(df_gender) > 0:
    tp = ((df_gender["female_llm"] == 1) & (df_gender["female"] == 1)).sum()
    fp = ((df_gender["female_llm"] == 1) & (df_gender["female"] == 0)).sum()
    fn = ((df_gender["female_llm"] == 0) & (df_gender["female"] == 1)).sum()
    tn = ((df_gender["female_llm"] == 0) & (df_gender["female"] == 0)).sum()

    accuracy, precision, recall, f1 = confusion_matrix_stats(tp, fp, fn, tn)

    print(f"\nConfusion matrix:")
    print(f"  {'':20s}  Handcode=F  Handcode=M")
    print(f"  {'LLM=Female':20s}  {tp:>10}  {fp:>10}")
    print(f"  {'LLM=Male':20s}  {fn:>10}  {tn:>10}")
    print(f"\n  Accuracy:  {fmt(accuracy)}")
    print(f"  Precision: {fmt(precision)}")
    print(f"  Recall:    {fmt(recall)}")
    print(f"  F1:        {fmt(f1)}")

    df_disagree_gender = df_gender[df_gender["female_llm"] != df_gender["female"]].copy()
    if len(df_disagree_gender) > 0:
        print(f"\nDisagreements ({len(df_disagree_gender)} rows):")
        for _, row in df_disagree_gender.iterrows():
            print(f"  id={row['id']}  hc={'F' if row['female']==1 else 'M'}  llm={'F' if row['female_llm']==1 else 'M'}  p_female={int(row['p_female'])}  p_male={int(row['p_male'])}")


############################# SAVE COMPARISON CSV #############################

df_out = df[["id", "birth_flag_hc", "birth_flag_llm", "birth_flag_llm_binary",
             "days_from_birth", "confidence", "female", "p_female", "p_male", "female_llm"]].copy()
df_out["birth_flag_match"]  = (df_out["birth_flag_llm_binary"] == df_out["birth_flag_hc"]).astype(int)
df_out["gender_match"]      = df_out.apply(
    lambda r: int(r["female_llm"] == r["female"])
              if r["female"] != -99 and r["female_llm"] != -99 else -99,
    axis=1
)

os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
df_out.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
print(f"\n\nComparison CSV saved to: {OUTPUT_PATH}")
