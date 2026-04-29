# Author: Hannah Lybbert
# Created: 02/25/2026
# Updated: 02/25/2026
# Purpose: Synchronous birth detection for prompt testing on the 100-row sample

import os
import openai
import pandas as pd
import re
import time
from dotenv import load_dotenv

# Set working directory
os.chdir("D:/TwitterBirth")

# Load API key
load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# File paths — sync script always runs on the test sample only
INPUT_PATH  = "Reddit/data/intermediate/cleaned_raw/test_samples/reddit_test_100_sample.csv"
OUTPUT_PATH = "Reddit/data/LLM/test_samples/birth_detection_100.csv"

# Constants
SLEEP_BETWEEN_CALLS = 0.2  # seconds between requests — stays well under Tier 1 rate limit

# Load DataFrame
df = pd.read_csv(INPUT_PATH, encoding="utf-8", low_memory=False)
df["id"] = df["id"].astype(str)
print(f"Loaded {len(df)} rows from {INPUT_PATH}")


############################# HELPER FUNCTIONS #############################

def sanitize_text(text):
    """Clean text to avoid encoding issues."""
    if pd.isna(text):
        return ""
    text = str(text)
    text = text.replace('\x00', '').replace('\r', ' ').replace('\n', ' ')
    if len(text) > 2000:
        text = text[:2000]
    return text.strip()


############################# PROMPT #############################

SYSTEM_PROMPT = (
    "Classify a Reddit post on two tasks:\n\n"

    "TASK 1 — BIRTH FLAG\n"
    "Did the author post within 14 days (before or after) of having a baby?\n"
    "VALID subjects: the author ('I am 39 weeks pregnant', 'I'm 4 days postpartum') "
    "or their spouse/partner ('my wife is 38 weeks pregnant', 'my husband and I just had our baby').\n"
    "INVALID: any other person — sister, mother, friend, nephew, etc.\n"
    "Timing must be PRESENT TENSE ('I am', 'my wife is'), not past ('I was', 'she was').\n"
    "Calculate days_from_birth (birth = 40 weeks):\n"
    "- 'X weeks pregnant' → (X−40)×7  |  'X+Y' → ((X−40)×7)−Y\n"
    "- 'X days postpartum/pp' → X  |  'X weeks postpartum' → X×7\n"
    "- 'baby is X days/weeks old' → X or X×7\n"
    "Flag as 1 only if −14 ≤ days_from_birth ≤ 14.\n\n"

    "TASK 2 — POSTER GENDER (p_female, p_male, each 0-100, summing to 100)\n"
    "Strong female signals: author is pregnant/postpartum, gave birth, is breastfeeding/nursing, "
    "refers to self as mom/mother/mum, mentions her husband/boyfriend.\n"
    "Strong male signals: author's wife/girlfriend is pregnant or postpartum, "
    "author refers to self as dad/father, says 'I will become a father'.\n"
    "Weaker signals: 'my partner' (ambiguous — use other cues); "
    "note 'my wife' could indicate a same-sex female couple.\n"
    "If no gender cues exist: p_female=50, p_male=50.\n\n"

    "Respond on exactly five lines:\n"
    "Line 1: birth_flag (1=within window, 0=not, -99=uncertain)\n"
    "Line 2: days_from_birth (integer, or -999 if N/A)\n"
    "Line 3: confidence (0-100)\n"
    "Line 4: p_female (0-100)\n"
    "Line 5: p_male (0-100)"
)


############################# CLASSIFICATION #############################

# Calls OpenAI API synchronously and returns parsed result for one post
def classify_post(post_id, title, selftext):
    user_content = (
        f"Title: {title}\n\n"
        f"Post: {selftext}\n\n"
        "[birth_flag]\n[days_from_birth]\n[confidence]\n[p_female]\n[p_male]"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_content}
        ]
    )

    content = response.choices[0].message.content.strip()
    lines   = content.splitlines()

    flag_match = re.search(r"^(-?\d+)", lines[0]) if len(lines) > 0 else None
    days_match = re.search(r"^(-?\d+)", lines[1]) if len(lines) > 1 else None
    conf_match = re.search(r"^(\d+)",   lines[2]) if len(lines) > 2 else None
    fem_match  = re.search(r"^(\d+)",   lines[3]) if len(lines) > 3 else None
    mal_match  = re.search(r"^(\d+)",   lines[4]) if len(lines) > 4 else None

    return {
        "id":              str(post_id),
        "birth_flag":      int(flag_match.group(1)) if flag_match else -99,
        "days_from_birth": int(days_match.group(1)) if days_match else -999,
        "confidence":      int(conf_match.group(1)) if conf_match else 0,
        "p_female":        int(fem_match.group(1))  if fem_match  else 50,
        "p_male":          int(mal_match.group(1))  if mal_match  else 50,
    }


# Run classification on all rows
def main():
    results = []

    for _, row in df.iterrows():
        title    = sanitize_text(row.get("title",    ""))
        selftext = sanitize_text(row.get("selftext", ""))

        if not title and not selftext:
            results.append({
                "id": row["id"], "birth_flag": -99, "days_from_birth": -999,
                "confidence": 0, "p_female": 50, "p_male": 50
            })
            continue

        try:
            result = classify_post(row["id"], title, selftext)
            results.append(result)
        except Exception as e:
            print(f"ERROR — id={row['id']}: {e}")
            results.append({
                "id": row["id"], "birth_flag": -99, "days_from_birth": -999,
                "confidence": 0, "p_female": 50, "p_male": 50
            })

        time.sleep(SLEEP_BETWEEN_CALLS)

    # Save results
    df_out = pd.DataFrame(results)
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    df_out.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")

    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total records: {len(df_out):,}")

    print(f"\nBirth flag predictions:")
    print(f"  - Within 14-day window (1):  {(df_out['birth_flag'] == 1).sum():,}")
    print(f"  - Outside window / none (0): {(df_out['birth_flag'] == 0).sum():,}")
    print(f"  - Uncertain (-99):           {(df_out['birth_flag'] == -99).sum():,}")

    flagged = df_out[df_out["birth_flag"] == 1]
    if len(flagged) > 0:
        print(f"\nDays from birth distribution (flagged posts only):")
        print(f"  - Prenatal  (< 0): {(flagged['days_from_birth'] < 0).sum():,}")
        print(f"  - Day of    (= 0): {(flagged['days_from_birth'] == 0).sum():,}")
        print(f"  - Postnatal (> 0): {(flagged['days_from_birth'] > 0).sum():,}")
        print(f"  - Mean days_from_birth: {flagged['days_from_birth'].mean():.1f}")

    print(f"\nConfidence distribution (all records):")
    print(f"  - No confidence (0): {(df_out['confidence'] == 0).sum():,}")
    print(f"  - Low (1-39):        {((df_out['confidence'] >= 1)  & (df_out['confidence'] < 40)).sum():,}")
    print(f"  - Medium (40-89):    {((df_out['confidence'] >= 40) & (df_out['confidence'] < 90)).sum():,}")
    print(f"  - High (90-100):     {(df_out['confidence'] >= 90).sum():,}")

    print(f"\nPoster gender distribution (all records):")
    print(f"  - Likely female (p_female > 50): {(df_out['p_female'] > 50).sum():,}")
    print(f"  - Likely male   (p_male   > 50): {(df_out['p_male']   > 50).sum():,}")
    print(f"  - Uncertain     (p_female = 50): {(df_out['p_female'] == 50).sum():,}")

    print(f"\nResults saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
