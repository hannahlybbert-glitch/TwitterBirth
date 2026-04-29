# Author: Hannah Lybbert
# Created: 02/20/2026
# Updated: 03/06/2026
# Purpose: Recovery script to get results from already completed batches

"""
Recovery script: fetch results from already-completed OpenAI birth detection batches
and save them to the output CSV without re-submitting anything.

Run this when get_reddit_births.py was interrupted after batch submission
but before results were downloaded.
"""

import os
import openai
import pandas as pd
import json
import re
from dotenv import load_dotenv

os.chdir("D:/TwitterBirth")

load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

INPUT_PATH  = "Reddit/data/intermediate/cleaned_raw/reddit_30k_sample.csv"
OUTPUT_PATH = "Reddit/data/LLM/birth_detection_large_sample.csv"
BATCH_IDS_PATH = "Reddit/data/json/batch_ids_birth.json"


def parse_birth_result(batch_id):
    try:
        batch_info = client.batches.retrieve(batch_id)
        status = batch_info.status
        print(f"Batch {batch_id} status: {status}")
        if status != "completed":
            print(f"  Skipping — not completed yet.")
            return None

        output_file_id = batch_info.output_file_id
        if not output_file_id:
            print(f"  No output file attached.")
            return None

        file_response = client.files.content(output_file_id)
        results = file_response.text

        parsed = []
        for line in results.splitlines():
            response = json.loads(line)
            post_id  = str(response.get("custom_id"))
            content  = response.get("response", {}).get("body", {}).get("choices", [])[0]["message"]["content"].strip()
            lines    = content.splitlines()

            flag_match      = re.search(r"^(-?\d+)", lines[0]) if len(lines) > 0 else None
            birth_flag      = int(flag_match.group(1)) if flag_match else -99

            days_match      = re.search(r"^(-?\d+)", lines[1]) if len(lines) > 1 else None
            days_from_birth = int(days_match.group(1)) if days_match else -999

            conf_match  = re.search(r"^(\d+)", lines[2]) if len(lines) > 2 else None
            confidence  = int(conf_match.group(1)) if conf_match else 0

            fem_match  = re.search(r"^(\d+)", lines[3]) if len(lines) > 3 else None
            p_female   = int(fem_match.group(1)) if fem_match else 50

            mal_match  = re.search(r"^(\d+)", lines[4]) if len(lines) > 4 else None
            p_male     = int(mal_match.group(1)) if mal_match else 50

            parsed.append({
                "id":              post_id,
                "birth_flag":      birth_flag,
                "days_from_birth": days_from_birth,
                "confidence":      confidence,
                "p_female":        p_female,
                "p_male":          p_male
            })

        print(f"  Parsed {len(parsed)} rows.")
        return pd.DataFrame(parsed)

    except Exception as e:
        print(f"Error parsing batch {batch_id}: {e}")
        return None


def get_batch_ids():
    """Load saved batch IDs, or fall back to listing recent completed batches."""
    if os.path.exists(BATCH_IDS_PATH):
        with open(BATCH_IDS_PATH, "r") as f:
            saved = json.load(f)
        ids = list(saved.values())
        print(f"Loaded {len(ids)} saved batch ID(s) from {BATCH_IDS_PATH}: {ids}")
        return ids

    # Fallback: scan recent batches from the API
    print("No saved batch IDs found. Scanning recent OpenAI batches for completed ones...")
    batches = client.batches.list(limit=20)
    completed = [b.id for b in batches.data if b.status == "completed"]
    print(f"Found {len(completed)} completed batch(es) in recent history.")
    if not completed:
        print("No completed batches found. Nothing to recover.")
    return completed


def main():
    batch_ids = get_batch_ids()
    if not batch_ids:
        return

    df = pd.read_csv(INPUT_PATH, encoding="utf-8", low_memory=False)
    df["id"] = df["id"].astype(str)

    all_results = []
    for batch_id in batch_ids:
        result_df = parse_birth_result(batch_id)
        if result_df is not None:
            all_results.append(result_df)

    if not all_results:
        print("No results could be recovered.")
        return

    df_birth = pd.concat(all_results, ignore_index=True)
    df_birth["id"] = df_birth["id"].astype(str)

    df_all = df[["id"]].copy()
    df_all = df_all.merge(df_birth, on="id", how="left")

    df_all["birth_flag"]      = df_all["birth_flag"].fillna(-99).astype(int)
    df_all["days_from_birth"] = df_all["days_from_birth"].fillna(-999).astype(int)
    df_all["confidence"]      = df_all["confidence"].fillna(0).astype(int)
    df_all["p_female"]        = df_all["p_female"].fillna(50).astype(int)
    df_all["p_male"]          = df_all["p_male"].fillna(50).astype(int)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df_all.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"\nResults saved to: {OUTPUT_PATH}")

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total records: {len(df_all):,}")
    print(f"  - Within 14-day window (1):  {(df_all['birth_flag'] == 1).sum():,}")
    print(f"  - Outside window / none (0): {(df_all['birth_flag'] == 0).sum():,}")
    print(f"  - Uncertain (-99):           {(df_all['birth_flag'] == -99).sum():,}")


if __name__ == "__main__":
    main()
