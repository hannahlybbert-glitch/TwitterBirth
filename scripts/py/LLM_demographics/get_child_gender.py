import os
import openai
import pandas as pd
import json
import time
import re
import glob
from dotenv import load_dotenv

# Set working directory
os.chdir("D:/TwitterBirth")

# Load API key
load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# File paths
INPUT_PATH = f"data/cleaned/user_info_full_sample.dta"  # or .csv
# INPUT_PATH = f"data/testing/baby_gender_minisample.dta"  # or .csv
OUTPUT_PATH = f"data/raw/child_gender_prediction.dta"  # or .csv

# Constants
TOKENS_PER_PROMPT = 400  # estimate for child gender prompt
# ENQUEUED_TOKEN_LIMIT = 90_000  # Tier 1 limit for GPT-4o batch API
MAX_REQUESTS_PER_BATCH = 200

# Load DataFrame
if INPUT_PATH.endswith('.dta'):
    df = pd.read_stata(INPUT_PATH)
else:
    df = pd.read_csv(INPUT_PATH, encoding="utf-8")
# df = df.iloc[0:100].copy()  # for testing

# Ensure unique_id exists and is string type
assert 'unique_id' in df.columns, "unique_id column must exist in input data"
assert df["unique_id"].notna().all(), "unique_id column must not have missing values"
df["unique_id"] = df["unique_id"].astype(str)


############################# HELPER FUNCTIONS #############################

def clear_old_batches(task_name):
    jsonl_files = glob.glob(f"data/json/batch_requests_{task_name}_*.jsonl")
    for file in jsonl_files:
        os.remove(file)
    print(f"🧹 Cleared {len(jsonl_files)} old batch files for task: {task_name}")

def sanitize_text(text):
    """Clean text to avoid JSON encoding issues."""
    if pd.isna(text):
        return ""
    text = str(text)
    # Remove null bytes and other problematic characters
    text = text.replace('\x00', '').replace('\r', ' ').replace('\n', ' ')
    # Limit length to avoid token issues
    if len(text) > 2000:
        text = text[:2000]
    return text.strip()

def create_jsonl_files(task_name, prompt_function, input_columns):
    clear_old_batches(task_name)
    batch_index = 0
    total_requests = 0
    skipped_rows = 0

    for start in range(0, len(df), MAX_REQUESTS_PER_BATCH):
        batch_df = df.iloc[start:start + MAX_REQUESTS_PER_BATCH].copy()
        jsonl_filename = f"data/json/batch_requests_{task_name}_batch_{batch_index}.jsonl"
        batch_requests = 0

        with open(jsonl_filename, "w", encoding="utf-8") as f:
            for _, row in batch_df.iterrows():
                # Skip if text is missing or empty
                text_val = sanitize_text(row.get("text", ""))
                if not text_val:
                    skipped_rows += 1
                    continue

                # Sanitize all input data
                input_data = {}
                for col in input_columns:
                    input_data[col] = sanitize_text(row.get(col, ""))

                prompt = prompt_function(row["unique_id"], **input_data)
                f.write(json.dumps(prompt, ensure_ascii=False) + "\n")
                batch_requests += 1
                total_requests += 1

        print(f"Created JSONL: {jsonl_filename} ({batch_requests} requests)")
        batch_index += 1

    print(f"✓ Total requests created: {total_requests}")
    if skipped_rows > 0:
        print(f"⚠ Skipped rows (missing text): {skipped_rows}")


############################# PROMPTS #############################

def get_child_gender_prompt(unique_id, text, description):
    """
    Generate prompt to predict child gender from birth announcement tweet.

    Args:
        unique_id: Unique identifier for this birth
        text: Tweet text announcing the birth
        description: User's bio/description

    Returns:
        Dictionary formatted for OpenAI batch API
    """
    text = text or ""
    description = description or ""

    return {
        "custom_id": str(unique_id),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4o-mini",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a classifier that determines the gender of a newborn child "
                        "based on a birth announcement tweet and the user's bio.\n\n"
                        "Follow this multi-step approach in order:\n\n"
                        "STEP 1: Check for gendered indicators in the TWEET TEXT\n"
                        "Look for specific phrases:\n"
                        "- Direct terms: 'baby boy', 'baby girl', 'little boy', 'little girl'\n"
                        "- Family terms: 'son', 'daughter', 'prince', 'princess'\n"
                        "- Announcements: \"it's a girl!\", \"it's a boy!\", 'she is here', 'he is here'\n"
                        "- Titles: 'miss', 'mister', 'mr', 'ms'\n"
                        "- Pronouns: 'she/her/hers' = girl, 'he/him/his' = boy\n"
                        "- Hashtags: #babyboy, #babygirl, #mydaughter, #myson, etc.\n"
                        "- Sibling references (NEWBORN only): 'little sister', 'little brother', "
                        "'baby sister', 'baby brother', 'younger sister', 'younger brother'\n"
                        "  * IGNORE: 'big brother/sister', 'older brother/sister' (which refer to existing children)\n\n"
                        "STEP 2: Check for gendered indicators in the BIO/DESCRIPTION\n"
                        "Look for phrases indicating the gender of all children:\n"
                        "- 'girl mom', 'boy mom', 'girl dad', 'boy dad'\n"
                        "- For example, 'Mamma to two lovely ladies', 'Daddy to three boys'\n"
                        "- 'Father of daughters', 'Mom to the best girls'\n\n"
                        "STEP 3: Use clearly gendered NAMES in the tweet text\n"
                        "If the name is clearly associated with a specific gender (e.g., Angela, John):\n"
                        "- Clearly female: Olivia, Sophia, Emma, Isabella, Emily, etc.\n"
                        "- Clearly male: David, Michael, James, William, Alexander, etc.\n"
                        "- IGNORE ambiguous names: Alex, Taylor, Jordan, Riley, etc. unless a pronoun is present that indicates the gender of the child.\n\n"
                        "STEP 4: Use name indicators in the BIO (use caution)\n"
                        "Only if ALL children mentioned in the bio are clearly the same gender:\n"
                        "- Example: 'Mum to Evelyn Rose and Olivia-Rae' (both female → assume newborn is female)\n"
                        "- Example: 'Dad to Jack and Emma' (mixed genders → DO NOT USE)\n\n"
                        "CONFIDENCE SCORING:\n"
                        "- High confidence (90-100): Direct terms from Step 1\n"
                        "- Medium confidence (60-89): Names from Step 3 or bio patterns from Step 2\n"
                        "- Low confidence (40-59): Ambiguous names or weak signals\n"
                        "- Uncertain (0-39): No clear signals → return -99\n\n"
                        "Allow some flexibility for borderline cases (e.g., name 'Kennedy' with supporting context)."
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Tweet: {text}\n\n"
                        f"Bio/Description: {description}\n\n"
                        "Based on this birth announcement, what is the gender of the child?\n\n"
                        "Respond with ONLY ONE of the following:\n"
                        "- 1 → Likely Female\n"
                        "- 0 → Likely Male\n"
                        "- -99 → Gender is uncertain or cannot be determined\n\n"
                        "Then on the next line, provide your confidence (0-100).\n\n"
                        "Format:\n"
                        "[gender number]\n"
                        "[confidence number]\n\n"
                        "Final answer:"
                    )
                }
            ]
        }
    }


############################# BATCH PROCESSING #############################

def submit_batch_job(jsonl_filename):
    try:
        file_upload = client.files.create(file=open(jsonl_filename, "rb"), purpose="batch")
        file_id = file_upload.id
        response = client.batches.create(input_file_id=file_id, endpoint="/v1/chat/completions", completion_window="24h")
        return response.id
    except Exception as e:
        print(f"Error submitting batch job for {jsonl_filename}: {e}")
        return None

def wait_for_queue(max_active=2, sleep_time=60):
    """
    Wait until the number of active batches drops below max_active.
    Active = queued, in_progress, or validating.
    """
    while True:
        try:
            batches = client.batches.list(limit=20)

            active = [
                b for b in batches.data
                if b.status in ["queued", "in_progress", "validating"]
            ]

            print(f"Active batches in queue: {len(active)}")

            if len(active) < max_active:
                break

            print("⏳ Waiting for queue capacity...")
            time.sleep(sleep_time)

        except Exception as e:
            print(f"Error checking queue: {e}")
            time.sleep(sleep_time)

def check_batch_status(batch_id, task_name):
    while True:
        try:
            job_status = client.batches.retrieve(batch_id)
            status = job_status.status
            print(f"[{task_name}] Batch {batch_id} status: {status}")
            if status in ["completed", "failed", "cancelled"]:
                return status
            time.sleep(30)
        except Exception as e:
            print(f"Error checking status: {e}")
            return None

def parse_child_gender_result(batch_id):
    """
    Parse child gender batch results and extract both gender and confidence.

    Returns:
        DataFrame with unique_id, baby_girl, and gender_confidence
    """
    try:
        batch_info = client.batches.retrieve(batch_id)
        output_file_id = batch_info.output_file_id
        if not output_file_id:
            print(f"No output file for batch {batch_id}")
            return None

        file_response = client.files.content(output_file_id)
        results = file_response.text

        parsed = []
        for line in results.splitlines():
            response = json.loads(line)
            unique_id = str(response.get("custom_id"))
            content = response.get("response", {}).get("body", {}).get("choices", [])[0]["message"]["content"].strip()

            # Extract gender (first line: -99, 0, or 1)
            gender_match = re.search(r"^(-?\d+)", content, re.MULTILINE)
            gender = int(gender_match.group(1)) if gender_match else -99

            # Extract confidence (second line: 0-100)
            confidence_match = re.search(r"\n(\d+)\s*$", content)
            confidence = int(confidence_match.group(1)) if confidence_match else 0

            parsed.append({
                "unique_id": unique_id,
                "baby_girl": gender,
                "gender_confidence": confidence
            })

        return pd.DataFrame(parsed)

    except Exception as e:
        print(f"Error parsing child_gender results: {e}")
        return None

def submit_and_process_batches(task_name):
    batch_index = 0
    all_results = []

    while True:
        jsonl_filename = f"data/json/batch_requests_{task_name}_batch_{batch_index}.jsonl"
        if not os.path.exists(jsonl_filename):
            break

        # ✅ WAIT before submitting the next batch
        wait_for_queue(max_active=2)

        print(f"🚀 Submitting batch {batch_index}")
        batch_id = submit_batch_job(jsonl_filename)

        if batch_id:
            status = check_batch_status(batch_id, task_name)

            if status == "completed":
                result_df = parse_child_gender_result(batch_id)
                if result_df is not None:
                    all_results.append(result_df)

            elif status == "failed":
                print(f"❌ Batch {batch_id} failed — consider retrying later.")

        batch_index += 1

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        final_df["unique_id"] = final_df["unique_id"].astype(str)
        return final_df
    else:
        return pd.DataFrame(columns=["unique_id", "baby_girl", "gender_confidence"])


def main():
    # Create JSONL files
    create_jsonl_files("child_gender", get_child_gender_prompt, ["text", "description"])

    # Submit and process results
    df_child_gender = submit_and_process_batches("child_gender")

    # Merge with original df to ensure all rows are included
    # Rows without text will have missing predictions, fill with -99
    df_all = df[["unique_id"]].copy()
    df_all = df_all.merge(df_child_gender, on="unique_id", how="left")

    # Fill missing predictions with -99 (uncertain) and 0 (no confidence)
    df_all.loc[:, "baby_girl"] = df_all["baby_girl"].fillna(-99).astype(int)
    df_all.loc[:, "gender_confidence"] = df_all["gender_confidence"].fillna(0).astype(int)

    # Save output (only unique_id, baby_girl, gender_confidence)
    if OUTPUT_PATH.endswith('.dta'):
        df_all.to_stata(OUTPUT_PATH, write_index=False)
    else:
        df_all.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"✓ Results saved to: {OUTPUT_PATH}")

    # Summary statistics
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total records: {len(df_all)}")

    print(f"\nChild gender predictions:")
    print(f"  - Boy (0): {(df_all['baby_girl'] == 0).sum()}")
    print(f"  - Girl (1): {(df_all['baby_girl'] == 1).sum()}")

    # Count -99 from missing text vs. GPT uncertainty
    uncertain_total = (df_all['baby_girl'] == -99).sum()
    missing_text = (df_all['gender_confidence'] == 0).sum()  # Missing text = 0 confidence
    gpt_uncertain = uncertain_total - missing_text

    print(f"  - Uncertain (-99): {uncertain_total}")
    print(f"      → Missing text: {missing_text}")
    print(f"      → GPT uncertain: {gpt_uncertain}")

    print(f"\nConfidence score distribution (all records):")
    print(f"  - No confidence (0 - missing text): {(df_all['gender_confidence'] == 0).sum()}")
    print(f"  - Very low (1-39): {((df_all['gender_confidence'] >= 1) & (df_all['gender_confidence'] < 40)).sum()}")
    print(f"  - Low (40-59): {((df_all['gender_confidence'] >= 40) & (df_all['gender_confidence'] < 60)).sum()}")
    print(f"  - Medium (60-89): {((df_all['gender_confidence'] >= 60) & (df_all['gender_confidence'] < 90)).sum()}")
    print(f"  - High (90-100): {(df_all['gender_confidence'] >= 90).sum()}")

    # Stats excluding missing text
    df_predicted = df_all[df_all['gender_confidence'] > 0]
    if len(df_predicted) > 0:
        print(f"\nConfidence statistics (excluding missing text):")
        print(f"  - Mean: {df_predicted['gender_confidence'].mean():.1f}")
        print(f"  - Median: {df_predicted['gender_confidence'].median():.1f}")


if __name__ == "__main__":
    main()
