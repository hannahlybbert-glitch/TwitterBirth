# Author: Hannah Lybbert
# Purpose: Merge profiles_filtered.csv (from filter_profiles.py) with the
#          matching seed tweet info (anniversaries_extracted.csv) and save
#          a single user_info.dta for Stata analysis.

import os

import pandas as pd

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")))

FILTER_NAME = "anniversary"   # must match the value used elsewhere in the pipeline; set "" for default pull
TEST_MODE   = True            # set False for full run

_base_profiles = "ControlGroup/data/2_user_profiles"
if FILTER_NAME:
    _base_profiles = f"{_base_profiles}/{FILTER_NAME}"

OUTPUT_DIR = f"{_base_profiles}/test" if TEST_MODE else _base_profiles

_base_seed = "ControlGroup/data/LLM/seed_tweets"
ANNIVERSARIES_CSV = f"{_base_seed}/test/anniversaries_extracted_test.csv" if TEST_MODE else f"{_base_seed}/anniversaries_extracted.csv"

PROFILES_CSV  = f"{OUTPUT_DIR}/profiles_filtered.csv"
USER_INFO_DTA = f"{OUTPUT_DIR}/user_info.dta"


def main():
    profiles = pd.read_csv(PROFILES_CSV)

    anniversaries = pd.read_csv(ANNIVERSARIES_CSV)
    anniversaries = anniversaries.drop_duplicates(subset="author_id")
    anniversaries = anniversaries.drop(columns=["created_at"])  # duplicate of profiles' seed_tweet_date

    # left join on profiles_filtered so every filtered author is kept, and anniversary
    # info is attached only for authors who are actually in profiles_filtered
    df = profiles.merge(anniversaries, on="author_id", how="left")

    # Stata .dta can't write timezone-aware datetimes as native Stata dates, and the cleaning
    # .do files expect a plain ISO string (they parse dates via date(substr(var,1,10), "YMD")),
    # so write these out as strings rather than native Stata datetimes.
    df["seed_tweet_date"]    = pd.to_datetime(df["seed_tweet_date"], utc=True, errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    df["account_created_at"] = pd.to_datetime(df["account_created_at"], utc=True, errors="coerce").dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df.to_stata(USER_INFO_DTA, write_index=False, version=118)  # v118 = UTF-8, avoids latin-1 errors on bio/tweet text

    n_matched = df["tweet_id"].notna().sum()
    print(f"Kept all {len(df):,} filtered profiles; {n_matched:,} matched to a seed tweet")
    print(f"Saved to {USER_INFO_DTA}")


if __name__ == "__main__":
    main()
