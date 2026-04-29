import os
import openai
import pandas as pd
import re
import time
import sys
import emoji
from tqdm import tqdm
from dotenv import load_dotenv
from collections import Counter
import time

# Load API Key
load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define majority voting parameter
N = 1  # Change this value to control majority voting. n=1 disables it.

begin_date = "2025_02_17"
end_date = "2025_02_24"

# Set working directory (temporary change for this script)
os.chdir("/Users/rorylawson/Desktop/TwitterBirth")

# Verify it's set correctly
print(f"Current Working Directory: {os.getcwd()}")

# Ensure file exists
file_path = f"data/testing/query_results_{begin_date}-{end_date}.csv"
if not os.path.exists(file_path):
    
    print(f"Error: File '{file_path}' not found. Make sure it is in the correct directory.")
    sys.exit(1)

original_df = pd.read_csv(file_path, encoding="utf-8")  #.iloc[0:10] - this can filter for the first 10 obs
df = original_df[["query_id","tweet_id","text"]].copy()

# Check if DataFrame is empty
if df.empty:
    print("Error: The CSV file is empty. Exiting.")
    sys.exit(1)

# Check for correct column name
expected_column = "text"
if expected_column not in df.columns:
    print(f"Error: Column '{expected_column}' not found. Available columns: {df.columns.tolist()}")
    sys.exit(1)

# Enable tqdm progress tracking
tqdm.pandas()

# Preprocess text (keeping all emojis)
def preprocess_text(text):
    text = str(text).strip()
    text = re.sub(r"http\S+|www\S+|@\S+", "", text)  # Remove links and mentions
    text = re.sub(r"[^a-zA-Z0-9\s.,!?'/:-\U0001F600-\U0001F64F]", "", text)  # Keep all emojis
    text = re.sub(r"\s+", " ", text).strip()  # Remove extra spaces
    return text.lower()

# Chain of Thought (CoT) Reasoning Prompt with Emoji Interpretation
def get_chain_of_thought_prompt(text):
    return f"""
You are an expert classifier tasked with determining if a tweet is a birth announcement.

A tweet should be classified as a birth announcement if it meets ANY of the following criteria:
✔ Explicitly announces the recent birth of the tweeter's own child (within approximately one week).
✔ Mentions the child's birth date, birth time, baby's name, weight, or birth-related emojis (👶, 🍼) in a personal context.
✔ Clearly references their child's age in terms of a milestone closely tied to birth (e.g., "[baby name] turned 6 months today!" or "Happy 1st birthday to my baby!"), provided the referenced birth occurred within approximately the last 2 years.

A tweet is NOT a birth announcement if it meets ANY of the following criteria:
❌ Congratulates someone else on their baby's birth (e.g., friend, sibling, relative).
❌ Is posted by a business, organization, or brand account.
❌ Refers to the birth of an animal or pet.
❌ Refers clearly to a child's birth that occurred more than approximately 2 years ago.
❌ Contains no explicit or implicit references to childbirth.

---

### Tweet to classify:
{text}

Think step by step. Based on the criteria above, is this tweet a birth announcement?

**Final Answer:** Respond with ONLY "1" (Birth Announcement) or "0" (Not a Birth Announcement).
"""


# Classification function with majority voting (toggleable)
def classify_with_majority_voting(text, n=N):
    if not text or len(text.split()) < 3:
        return "0"  # Assume "Not a Birth Announcement" for very short tweets

    responses = []
    
    for _ in range(n):
        prompt = get_chain_of_thought_prompt(text)
        try:
            response = client.chat.completions.create(
                model="gpt-4-turbo",
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response.choices[0].message.content.strip()

            # Extract only the final classification (last "1" or "0" in response)
            match = re.findall(r"\b(1|0)\b", answer)
            if match:
                responses.append(match[-1])  # Get the last instance of 1 or 0
            else:
                print(f"Unexpected response: {answer}")

        except openai.RateLimitError as e:
            print(f"Quota exceeded error: {e}. Stopping classification.")
            raise  # Re-raise to stop further classification

        except openai.OpenAIError as e:
            print(f"Error: {e}. Retrying...")
            time.sleep(2)

    if n == 1:
        return responses[0] if responses else "Error"

    # Determine classification based on `n`
    count_1 = responses.count("1")
    count_0 = responses.count("0")

    if n % 2 == 0:  # Even n → Require MORE than 50% agreement
        return "1" if count_1 > (n // 2) else "0"
    else:  # Odd n → Majority rule
        return "1" if count_1 > count_0 else "0"

# Apply classification with progress tracking
# df = df.head(10) # applies it over only 10 observations
start_time = time.time()
df["processed_text"] = df["text"].progress_apply(preprocess_text)
df["text_classification"] = df["processed_text"].progress_apply(lambda x: classify_with_majority_voting(x, N))

# merge back in with original df
df = df.drop(columns = ["text"]) # drop original column text
merged_df = pd.merge(df, original_df, on = ['query_id','tweet_id'], how = 'inner')


# Save results
merged_df.to_csv(f"data/testing/classified_text_{begin_date}-{end_date}.csv", index=False, encoding="utf-8")

print(f"✅ Classification complete. Results saved to 'classified_text_{begin_date}-{end_date}.csv'.")
end_time = time.time()
elapsed_time = end_time - start_time
print(f"⏱️ Classification completed in {elapsed_time:.2f} seconds.")



# import os
# import openai
# import pandas as pd
# import re
# import time
# import emoji
# import sys
# from tqdm import tqdm
# from dotenv import load_dotenv
# from collections import Counter

# # Load API Key
# load_dotenv(dotenv_path="config/.env")
# client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # Ensure file exists
# file_path = "data/testing/tweets_to_classify.csv"
# if not os.path.exists(file_path):
#     print(f"Error: File '{file_path}' not found. Make sure it is in the correct directory.")
#     sys.exit(1)

# df = pd.read_csv(file_path, encoding="utf-8")

# # Check if DataFrame is empty
# if df.empty:
#     print("Error: The CSV file is empty. Exiting.")
#     sys.exit(1)

# # Check for correct column name
# expected_column = "text"
# if expected_column not in df.columns:
#     print(f"Error: Column '{expected_column}' not found. Available columns: {df.columns.tolist()}")
#     sys.exit(1)

# # Enable tqdm progress tracking
# tqdm.pandas()

# # Preprocess text
# def preprocess_text(text):
#     text = str(text).strip()
#     text = re.sub(r"http\S+|www\S+|@\S+", "", text)  # Remove links and mentions
#     text = re.sub(r"[^a-zA-Z0-9\s.,!?']", "", text)  # Remove special characters but keep apostrophes
#     text = emoji.replace_emoji(text, "")  # Remove emojis
#     text = re.sub(r"\s+", " ", text).strip()  # Remove extra spaces
#     return text.lower()

# # Few-shot learning prompt optimized for high recall
# def get_few_shot_prompt(text):
#     return f"""
# You are an expert classifier that determines whether a tweet is a birth announcement.

# A birth announcement meets these criteria:
# - The tweet is from the account holder.
# - It mentions the birth of the account holder's child. This could mean the account holder themselves gave birth, or their partner/spouse gave birth.

# The following do not count as birth announcements:
# - Announcements of an adoption or miscarriage
# - Tweets from a company or organization's account (e.g sports team, hospital, NGO) announcing the birth of someone's child.
# - Tweets announcing that the account holder's friend or non-romantic relative (e.g. Aunt, Uncle, Nephew, Sibling) gave birth.

# A birth announcement might also include:
# - Phrases like "we welcomed," "introducing," "mom and baby are doing well," "our baby," "our little one," "proud to announce," "blessed to share," "welcome to the world [baby name]", or similar expressions.
# - Timestamps or specific time of day for when the child was born
# - Measurements of weight and or height of the child

# **If you are uncertain, classify it as a birth announcement. The goal is to minimize false negatives.**

# Now, determine whether the following tweet within the three backticks is a birth announcement.

# ```{text}```

# Respond with ONLY "1" (Birth Announcement) or "0" (Not a Birth Announcement). No explanations.
# """

# # Majority voting classifier with bias toward recall
# def classify_with_majority_voting(text, n=5):
#     if not text or len(text.split()) < 3:
#         return "0"  # Assume "Not a Birth Announcement" for very short tweets

#     responses = []
    
#     for _ in range(n):
#         prompt = get_few_shot_prompt(text)
#         try:
#             response = client.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 messages=[{"role": "user", "content": prompt}]
#             )
#             answer = response.choices[0].message.content.strip()

#             # Extract only the first number
#             match = re.search(r"\b(1|0)\b", answer)
#             if match:
#                 responses.append(match.group(1))
#             else:
#                 print(f"Unexpected response: {answer}")

#         except openai.OpenAIError as e:
#             print(f"Error: {e}. Retrying...")
#             time.sleep(2)

#     if responses:
#         count_1 = responses.count("1")
#         count_0 = responses.count("0")

#         # Prioritize recall: If at least 3/5 calls say "1", classify as a birth announcement
#         if count_1 >= 3:
#             return "1"
#         else:
#             return "0"
    
#     return "Error"

# # Apply preprocessing and classification with progress tracking
# df["text"] = df["text"].progress_apply(preprocess_text)
# df["classification"] = df["text"].progress_apply(classify_with_majority_voting)

# # Save results
# df.to_csv("data/testing/classified_tweetsv3.csv", index=False, encoding="utf-8")

# print("Classification complete. Results saved to 'classified_tweetsv3.csv'.")





# import os
# import openai
# import pandas as pd
# import re
# import time
# import emoji
# import sys
# from tqdm import tqdm
# from dotenv import load_dotenv
# from collections import Counter

# # Load API Key
# load_dotenv(dotenv_path="config/.env")
# client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # Ensure file exists
# file_path = "data/testing/tweets_to_classify.csv"
# if not os.path.exists(file_path):
#     print(f"Error: File '{file_path}' not found. Make sure it is in the correct directory.")
#     sys.exit(1)

# df = pd.read_csv(file_path, encoding="utf-8")

# # Check if DataFrame is empty
# if df.empty:
#     print("Error: The CSV file is empty. Exiting.")
#     sys.exit(1)

# # Check for correct column name
# expected_column = "text"
# if expected_column not in df.columns:
#     print(f"Error: Column '{expected_column}' not found. Available columns: {df.columns.tolist()}")
#     sys.exit(1)

# # Enable tqdm progress tracking
# tqdm.pandas()

# # Preprocess text
# def preprocess_text(text):
#     text = str(text).strip()
#     text = re.sub(r"http\S+|www\S+|@\S+", "", text)  # Remove links and mentions
#     text = re.sub(r"[^a-zA-Z0-9\s.,!?']", "", text)  # Remove special characters but keep apostrophes
#     text = emoji.replace_emoji(text, "")  # Remove emojis
#     text = re.sub(r"\s+", " ", text).strip()  # Remove extra spaces
#     return text.lower()

# # Few-shot learning prompt
# def get_few_shot_prompt(text):
#     return f"""
# You are an expert classifier that determines whether a tweet is a birth announcement.

# A birth announcement meets these criteria:
# - The tweet is from the account holder, not someone else congratulating them.
# - It mentions the birth of the account holder's child (not a pet or relative).
# - It might include phrases like "we welcomed," "introducing," or "our baby."
# - It is not about a grandchild, an adoption, or a tweet from an organization.

# ### Examples:

# Tweet: "We just welcomed our beautiful baby girl into the world!"  
# Classification: 1

# Tweet: "Congrats to my sister on the birth of her son!"  
# Classification: 0

# Tweet: "Excited to announce the birth of our little one. Meet baby Noah!"  
# Classification: 1

# Tweet: "Happy to share that my wife gave birth to a healthy baby boy!"  
# Classification: 1

# Tweet: "Sending love to my friend who just had a baby!"  
# Classification: 0

# Now, determine whether the following tweet within the three backticks is a birth announcement.

# ```{text}```

# Respond with ONLY "1" (Birth Announcement) or "0" (Not a Birth Announcement). No explanations.
# """

# # Majority voting classifier (runs classification multiple times and selects most common result)
# def classify_with_majority_voting(text, n=3):
#     if not text or len(text.split()) < 3:
#         return "0"  # Assume "Not a Birth Announcement" for very short tweets

#     responses = []
    
#     for _ in range(n):
#         prompt = get_few_shot_prompt(text)
#         try:
#             response = client.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 messages=[{"role": "user", "content": prompt}]
#             )
#             answer = response.choices[0].message.content.strip()

#             # Extract only the first number
#             match = re.search(r"\b(1|0)\b", answer)
#             if match:
#                 responses.append(match.group(1))
#             else:
#                 print(f"Unexpected response: {answer}")

#         except openai.OpenAIError as e:
#             print(f"Error: {e}. Retrying...")
#             time.sleep(2)

#     if responses:
#         # Return the most common classification
#         return Counter(responses).most_common(1)[0][0]
#     return "Error"

# # Validation step - a second GPT check to confirm the classification
# def validate_classification(text, predicted_label):
#     validation_prompt = f"""
# You previously classified this tweet as {predicted_label}:

# "{text}"

# Confirm if this classification is correct:
# - Reply "Correct" if the classification is accurate.
# - Reply "Incorrect" if it should be the opposite.
# """

#     try:
#         response = client.chat.completions.create(
#             model="gpt-3.5-turbo",
#             messages=[{"role": "user", "content": validation_prompt}]
#         )
#         validation_response = response.choices[0].message.content.strip()

#         if "Incorrect" in validation_response:
#             return "0" if predicted_label == "1" else "1"  # Flip the label if incorrect
#     except openai.OpenAIError as e:
#         print(f"Error during validation: {e}")

#     return predicted_label  # Return the original classification if no issues

# # Apply preprocessing and classification with progress tracking
# df["text"] = df["text"].progress_apply(preprocess_text)
# df["initial_classification"] = df["text"].progress_apply(classify_with_majority_voting)
# df["final_classification"] = df.progress_apply(lambda row: validate_classification(row["text"], row["initial_classification"]), axis=1)

# # Save results
# df.to_csv("data/testing/classified_tweetsv2.csv", index=False, encoding="utf-8")

# print("Classification complete. Results saved to 'classified_tweetsv2.csv'.")


# import os
# import openai
# import pandas as pd
# import re
# import time
# import emoji
# import sys
# from tqdm import tqdm
# from dotenv import load_dotenv


# # Load API Key
# load_dotenv(dotenv_path="config/.env")
# client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# # Ensure file exists
# file_path = "data/testing/tweets_to_classify.csv"
# if not os.path.exists(file_path):
#     print(f"Error: File '{file_path}' not found. Make sure it is in the correct directory.")
#     sys.exit(1)  # Exit if the file is missing

# df = pd.read_csv(file_path, encoding="utf-8")

# # Check if DataFrame is empty
# if df.empty:
#     print("Error: The CSV file is empty. Exiting.")
#     sys.exit(1)

# # Check for correct column name and rename if necessary
# expected_column = "text"
# if expected_column not in df.columns:
#     print(f"Error: Column '{expected_column}' not found. Available columns: {df.columns.tolist()}")
#     sys.exit(1)

# # Enable tqdm progress tracking
# tqdm.pandas()

# # Preprocess text
# def preprocess_text(text):
#     text = str(text).strip()
#     text = re.sub(r"http\S+|www\S+|@\S+", "", text)  # Remove links and mentions
#     text = re.sub(r"[^a-zA-Z0-9\s.,!?]", "", text)  # Remove special characters
#     text = emoji.replace_emoji(text, "")  # Remove emojis
#     text = re.sub(r"\s+", " ", text).strip()  # Remove extra spaces
#     return text.lower()

# # Classify tweets with retry handling
# def classify_text(text):
#     if not text or len(text.split()) < 3:
#         return ""  # Assume "Not a Birth Announcement"

#     prompt = f"""
#     Classify the following tweet as one of the following categories:

#     1. Birth Announcement
#     0. Not a Birth Announcement

#     Tweet: "{text}"

#     Respond with ONLY the category number.
#     To qualify as a birth announcement, it should be the account holder's child.
#     This could mean the account holder physically gave birth, or their spouse/partner gave birth.
#     Tweets that do not qualify:
#     The birth of a grandchild of the account holder,
#     an adoption,
#     a tweet from an organization (hospital, company, sports team) that announces that other people gave birth.
#     """

#     for attempt in range(3):  # Retry up to 3 times
#         try:
#             response = client.chat.completions.create(
#                 model="gpt-3.5-turbo",
#                 messages=[{"role": "user", "content": prompt}]
#             )
#             answer = response.choices[0].message.content.strip()

#             # Extract only the first number (if the response contains extra text)
#             match = re.search(r"\b(1|0)\b", answer)
#             if match:
#                 return match.group(1)  # Return only the number (1 or 0)
#             else:
#                 print(f"Unexpected response: {answer}. Retrying...")

#         except openai.OpenAIError as e:
#             print(f"Error: {e}, retrying ({attempt + 1}/3)...")
#             time.sleep(2)

#     return "Error"

# # Apply preprocessing and classification with progress tracking
# df["text"] = df["text"].progress_apply(preprocess_text)
# df["is_birth_announcement"] = df["text"].progress_apply(classify_text)

# # Save results
# df.to_csv("data/testing/classified_tweets.csv", index=False, encoding="utf-8")

# print("Classification complete. Results saved to 'classified_tweetsv1.csv'.")
