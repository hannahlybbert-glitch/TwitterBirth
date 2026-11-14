# Author: Hannah Lybbert
# Created: 2026-11-04
# Updated: 2026-11-04
# Purpose: Check that the get_post_volume.py parts cover every input author once, then combine them

import json
import os
import sys

import pandas as pd

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

TEST_MODE = False   # set False for full run

N_PARTS = 2

_base_profiles = "ControlGroup/data/2_user_profiles"
_base_volume   = "ControlGroup/data/3_post_volume"

if TEST_MODE:
    INPUT_CSV  = f"{_base_profiles}/profiles_filtered_test.csv"
    OUTPUT_DIR = f"{_base_volume}/test_100"
    FILE_NAME  = "post_volume.csv"
else:
    INPUT_CSV  = f"{_base_profiles}/profiles_filtered.csv"
    OUTPUT_DIR = _base_volume
    FILE_NAME  = "post_volume.parquet"


def read_volume(path):
    return pd.read_csv(path) if TEST_MODE else pd.read_parquet(path)


def main():
    # 1. Stop if any part has not finished
    part_dirs = [f"{OUTPUT_DIR}/part_{part}" for part in range(N_PARTS)]
    required  = [f"{d}/{name}" for d in part_dirs for name in ("progress.json", FILE_NAME)]
    not_found = [path for path in required if not os.path.exists(path)]
    if not_found:
        sys.exit("Parts not finished, missing:\n  " + "\n  ".join(not_found))

    # 2. Check authors against the input list
    part_ids = []
    for part_dir in part_dirs:
        with open(f"{part_dir}/progress.json") as f:
            part_ids.append(set(json.load(f)["completed_author_ids"]))

    input_ids = set(pd.read_csv(INPUT_CSV, dtype=str, usecols=["author_id"])["author_id"])
    done_ids  = set().union(*part_ids)
    n_overlap = sum(len(ids) for ids in part_ids) - len(done_ids)
    n_missing = len(input_ids - done_ids)
    n_extra   = len(done_ids - input_ids)

    print(f"Input authors: {len(input_ids):,}")
    for part, ids in enumerate(part_ids):
        print(f"  Part {part} complete: {len(ids):,}")
    if n_overlap or n_missing or n_extra:
        sys.exit(f"Check failed: {n_overlap:,} in both parts, {n_missing:,} missing, {n_extra:,} not in input")

    # 3. Combine and drop rows repeated by a resumed job
    df = pd.concat([read_volume(f"{d}/{FILE_NAME}") for d in part_dirs], ignore_index=True)
    n_rows = len(df)
    df = df.drop_duplicates(subset=["author_id", "date"])
    print(f"Rows: {n_rows:,}  (dropped {n_rows - len(df):,} duplicates)")

    # Authors can be complete with no rows if the API returned no buckets
    row_ids = {str(author_id) for author_id in df["author_id"].unique()}
    if row_ids - done_ids:
        sys.exit(f"Check failed: {len(row_ids - done_ids):,} authors have rows but are not marked complete")
    print(f"Complete authors with no rows: {len(done_ids - row_ids):,}")

    # 4. Save
    output_path = f"{OUTPUT_DIR}/{FILE_NAME}"
    if TEST_MODE:
        df.to_csv(output_path, index=False)
    else:
        df.to_parquet(output_path, index=False)
    print(f"Output saved to {output_path}")


if __name__ == "__main__":
    main()
