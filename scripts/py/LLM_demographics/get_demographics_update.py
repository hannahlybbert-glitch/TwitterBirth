import os
import openai
import pandas as pd
import json
import time
import re
import glob
from dotenv import load_dotenv

# Set working directory
os.chdir("D:/TwitterBirth") #H:: Changed working directory to match my own (Rory's old dir "E:/TwitterBirth")

# Load API key
load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# File path
# Either YEAR = 2018 or 2013_2017
YEAR = "2018"
INPUT_PATH = f"data/raw/user_info_{YEAR}.csv" # H:: maybe create copy and use that path just in case
OUTPUT_PATH = f"data/raw/user_info_with_demographics_{YEAR}.csv"

# Constants
TOKENS_PER_PROMPT = 550  # estimate
ENQUEUED_TOKEN_LIMIT = 40_000_000 # This will depend on account tier and model used
MAX_REQUESTS_PER_BATCH = ENQUEUED_TOKEN_LIMIT // TOKENS_PER_PROMPT

# Load DataFrame
df = pd.read_csv(INPUT_PATH, encoding="utf-8")
# df = df.iloc[0:10].copy()  # for testing

if 'unique_id' not in df.columns:
    print("Creating date_birth and unique_id variables")
    # fill in missing values with 0 for "days_from"
    df["days_from"] = df["days_from"].fillna(0)

    # Convert post date
    df["created_at_dt"] = pd.to_datetime(df["created_at"])

    # subtract days_from for birth announcements that are not same day as actual birth
    df["date_birth_dt"] = df["created_at_dt"] + pd.to_timedelta(df["days_from"], unit="D")

    # Save birth date as a string (needed for unique_id and output)
    df["date_birth"] = df["date_birth_dt"].dt.strftime("%Y-%m-%dT%H:%M:%S.000Z")

    # Create a unique ID per birth (author_id + date of birth)
    df["author_id"] = df["author_id"].astype(str).str.strip()
    df["unique_id"] = df["author_id"] + "_" + df["date_birth"]


# check if there is a unique_id variable. If not, then create it. Everything should run by unique id instead of by author id.
df["unique_id"] = df["unique_id"].astype(str)


def clear_old_batches(task_name):
    jsonl_files = glob.glob(f"data/json/batch_requests_{task_name}_*.jsonl")
    for file in jsonl_files:
        os.remove(file)
    print(f"🧹 Cleared {len(jsonl_files)} old batch files for task: {task_name}")

def create_jsonl_files(task_name, prompt_function, input_columns):
    clear_old_batches(task_name)
    batch_index = 0

    for start in range(0, len(df), MAX_REQUESTS_PER_BATCH):
        batch_df = df.iloc[start:start + MAX_REQUESTS_PER_BATCH].copy()
        jsonl_filename = f"data/json/batch_requests_{task_name}_batch_{batch_index}.jsonl"

        with open(jsonl_filename, "w", encoding="utf-8") as f:
            for _, row in batch_df.iterrows():
                input_data = {col: row.get(col, "") for col in input_columns}
                prompt = prompt_function(row["unique_id"], **input_data)
                f.write(json.dumps(prompt, ensure_ascii=False) + "\n")

        print(f"Created JSONL: {jsonl_filename} ({len(batch_df)} requests)")
        batch_index += 1


############################# PROMPTS #############################


# prompt for getting gender using name, description, and profile image
def get_gender_prompt(unique_id, name, username, description, profile_image_url):
    name = name or ""
    username = username or ""
    description = description or ""
    profile_image_url = profile_image_url or ""

    return {
        "custom_id": str(unique_id),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "Determine the likely gender of a Twitter user \n"
                        "based on their name, username, profile description, and profile image.\n"
                        "Use cautious, evidence-based reasoning."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"User information:\n"
                                f"- Name: {name}\n"
                                f"- Username: {username}\n"
                                f"- Description: {description}\n\n"
                                "Instructions:\n"
                                "1. If the name is clearly associated with a specific gender (e.g., Angela, John), use that as your primary signal.\n"
                                "2. Use the description and username for secondary clues (e.g., pronouns, 'mom', 'husband').\n"
                                "3. Examine the profile image **only if it clearly shows a real human face**. Ignore logos, cartoons, pets, or vague photos.\n"
                                "4. If the image is ambiguous, blurry, indirect, or only shows clothing or context (e.g., a person from behind), do NOT override the textual cues.\n"
                                "5. If the name and description suggest one gender and the image is unclear or weak, stick with the name/description.\n"
                                "6. If the image fails to load or is missing, do NOT guess based on image alone. Rely only on name and description.\n"
                                "7. If all signals are unclear, return `-99`.\n\n"
                                "Respond with only ONE of the following:\n"
                                "- 1 → Likely Female\n"
                                "- 0 → Likely Male\n"
                                "- -99 → Gender is uncertain or cannot be determined\n\n"
                                "Final answer (number only):"
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": profile_image_url,
                                "detail": "auto"
                            }
                        }
                    ]
                }
            ]
        }
    }


def get_race_prompt(unique_id, name, profile_image_url):
    name = name or ""
    profile_image_url = profile_image_url or ""

    return {
        "custom_id": str(unique_id),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a classification assistant. Your task is to infer the likely race or ethnicity \n"
                        "of a Twitter user based on their name and profile image. Use cautious, evidence-based reasoning."
                    )
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                f"Name: {name}\n\n"
                                "Instructions:\n"
                                "1. Examine the profile image carefully. Only use the image if it clearly shows a real person.\n"
                                "2. Consider whether the name is commonly associated with a specific racial or ethnic group.\n"
                                "3. Combine visual and name-based evidence to form a judgment.\n"
                                "4. If either signal is ambiguous, err on the side of uncertainty.\n\n"
                                "Think step by step:\n"
                                "- Does the image clearly depict a person? What features can be observed?\n"
                                "- Is the name strongly associated with a particular racial or ethnic group?\n"
                                "- Do the image and name reinforce or contradict each other?\n"
                                "- What is the most cautious, reasonable classification?\n\n"
                                "Final classification:\n"
                                "- 1 = Black\n"
                                "- 2 = White\n"
                                "- 3 = Asian\n"
                                "- 4 = Hispanic\n"
                                "- 5 = Other\n"
                                "- -99 = Uncertain or image not usable\n\n"
                                "Respond with only ONE number based on your reasoning."
                            )
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": profile_image_url,
                                "detail": "auto"
                            }
                        }
                    ]
                }
            ]
        }
    }


def get_occupation_prompt(unique_id, description):
    description = description or ""

    return {
        "custom_id": str(unique_id),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an occupation classifier. Based on a Twitter user's profile description, assign them to one of the following broad occupation categories."
                        "Think through your reasoning step-by-step and realize that more often than not, there will be no information about their occupation in their description."
                        "If you cannot tell what their occupation is, enter -99."
                        "Respond ONLY with the category number.\n\n"
                        "1 = Education (e.g., teacher, professor)\n"
                        "2 = Healthcare (e.g., nurse, doctor, therapist)\n"
                        "3 = Tech / Engineering (e.g., software, data, IT)\n"
                        "4 = Business / Finance (e.g., marketing, consultant, accountant)\n"
                        "5 = Government / Law (e.g., civil servant, attorney, military)\n"
                        "6 = Media / Arts (e.g., journalist, writer, musician)\n"
                        "7 = Service / Retail (e.g., waiter, driver, sales)\n"
                        "8 = Student (e.g., undergrad, grad student)\n"
                        "9 = Other\n"
                        "-99 = Uncertain"
                    )
                },
                {
                    "role": "user",
                    "content": f"Profile description: {description}\n\nCategory number only:"
                }
            ]
        }
    }



def get_children_prompt(unique_id, text):
    text = text or ""

    return {
        "custom_id": str(unique_id),
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": "gpt-4-turbo",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are an assistant tasked with inferring what number child is being referenced in a birth announcement tweet. \n\n"
                        "For example, we want to know based on a tweet, if a birth announcement tweet is referring to the birth of someone's first child, or their thrid child, etc."
                        "Return an exact number ONLY if the number is explicitly stated"
                        "Acceptable evidence includes:\n"
                        "- An ordinal reference clearly indicating the child's number (e.g., 'we had our second baby').\n"
                        "- A sibling reference that allows precise inference (e.g., 'she met her big brother' = two children).\n\n"
                        "Be cautious. Do NOT guess from vague plural words or generic statements."
                        "If there is any ambiguity or uncertainty, please enter your answer as -99. Make sure that is it negative 99\n\n"
                    )
                },
                {
                    "role": "user",
                    "content": f"Tweet: {text}\n\n Think through your reasoning step-by-step. What number child is the birth referenced in the tweet? Respond with a single number (e.g., 1, 2, 3) only if it is explicitly stated. If it is not very clear what number respond with -99."
                }
            ]
        }
    }


# Submits batch job to ChatGPT API
def submit_batch_job(jsonl_filename):
    try:
        file_upload = client.files.create(file=open(jsonl_filename, "rb"), purpose="batch")
        file_id = file_upload.id
        response = client.batches.create(input_file_id=file_id, endpoint="/v1/chat/completions", completion_window="24h")
        return response.id
    except Exception as e:
        print(f"Error submitting batch job for {jsonl_filename}: {e}")
        return None

# Checks the status of current batch every 5 minutes
def check_batch_status(batch_id, task_name):
    while True:
        try:
            job_status = client.batches.retrieve(batch_id)
            status = job_status.status
            print(f"[{task_name}] Batch {batch_id} status: {status}")
            if status in ["completed", "failed", "cancelled"]:
                return status
            time.sleep(30) # sleeps for 30 seconds before checking status again (put to 300 for larger batches if you want)
        except Exception as e:
            print(f"Error checking status: {e}")
            return None

# Retreives classification answer from ChatGPT output
def parse_result(batch_id, column_name, regex_pattern=r"-?\d+", default_value=-99, cast_fn=int):
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

            match = re.search(regex_pattern, content)
            value = cast_fn(match.group(0)) if match else default_value

            parsed.append({"unique_id": unique_id, column_name: value})

        return pd.DataFrame(parsed)

    except Exception as e:
        print(f"Error parsing {column_name} results: {e}")
        return None

# 
def submit_and_process_batches(task_name, column_name, regex_pattern, default_value, cast_fn=int):
    batch_index = 0
    all_results = []

    while True:
        jsonl_filename = f"data/json/batch_requests_{task_name}_batch_{batch_index}.jsonl"
        if not os.path.exists(jsonl_filename):
            break

        batch_id = submit_batch_job(jsonl_filename)
        if batch_id:
            status = check_batch_status(batch_id, task_name)
            if status == "completed":
                result_df = parse_result(
                    batch_id=batch_id,
                    column_name=column_name,
                    regex_pattern=regex_pattern,
                    default_value=default_value,
                    cast_fn=cast_fn
                )
                if result_df is not None:
                    all_results.append(result_df)

        batch_index += 1

    if all_results:
        final_df = pd.concat(all_results, ignore_index=True)
        final_df["unique_id"] = final_df["unique_id"].astype(str)
        return final_df
    else:
        return pd.DataFrame(columns=["unique_id", column_name])

# Run all of the functions
def main():
    # Create all JSONL files up front
    create_jsonl_files("gender", get_gender_prompt, ["name", "username", "description", "profile_image_url"])
    create_jsonl_files("race", get_race_prompt, ["name","profile_image_url"])
    create_jsonl_files("occupation", get_occupation_prompt, ["description"])
    create_jsonl_files("children", get_children_prompt, ["text"])

    # Submit and process results
    df_gender = submit_and_process_batches("gender", "female", r"\b-?1\b|\b0\b", -99, int)
    df_race = submit_and_process_batches("race", "race", r"\b-?1\b|[2-5]", -99, int)
    df_occupation = submit_and_process_batches("occupation", "occupation", r"\b(10|[1-9])\b", -99, int)
    df_children = submit_and_process_batches("children", "num_children", r"\d+", -99, int)

    # Merge all together
    df_gender["unique_id"] = df_gender["unique_id"].astype(str)
    df_race["unique_id"] = df_race["unique_id"].astype(str)
    df_occupation["unique_id"] = df_occupation["unique_id"].astype(str)
    df_children["unique_id"] = df_children["unique_id"].astype(str)

    df_final = (
        df
        .merge(df_gender, on = "unique_id", how="left")
        .merge(df_race, on="unique_id", how="left")
        .merge(df_occupation, on="unique_id", how="left")
        .merge(df_children, on="unique_id", how="left")
    )

    df_final.to_csv(OUTPUT_PATH, index=False, encoding="utf-8")
    print(f"Final merged file saved to: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

