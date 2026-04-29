import os
import pandas as pd
import requests
import openai
from deepface import DeepFace
from tqdm import tqdm
from dotenv import load_dotenv
from collections import Counter
import time

# Set working directory (temporary change for this script)
os.chdir("/Users/rorylawson/Desktop/TwitterBirth")

# Verify it's set correctly
print(f"Current Working Directory: {os.getcwd()}")

# Load API Key
load_dotenv(dotenv_path="config/.env")  # ✅ Load only once
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Input and Output CSV Paths
INPUT_CSV = "data/testing/query_test.csv"
OUTPUT_CSV = "data/testing/profile_classifications.csv"

# Function to get probability from DeepFace
def get_gender_probability_from_image(image_url):
    try:
        response = DeepFace.analyze(img_path=image_url, actions=['gender'], enforce_detection=False)
        gender_prediction = response[0]["dominant_gender"]
        gender_confidence = response[0]["gender"]  # DeepFace provides % confidence

        # Convert DeepFace output to probability (Female: 1.0, Male: 0.0)
        female_prob = gender_confidence.get("Woman", 0.0) / 100  # Convert to 0-1 scale
        male_prob = gender_confidence.get("Man", 0.0) / 100

        if female_prob > male_prob:
            return female_prob  # Probability it’s female
        elif male_prob > female_prob:
            return 0.0  # 100% male
        else:
            return -99  # Uncertain / Other
    except Exception as e:
        print(f"⚠️ Error analyzing image {image_url}: {e}")
        return -99  # Uncertain / Other

# Function to get probability from text description
def get_gender_probability_from_text(description):
    if not description or description.strip() == "":
        return -99  # No bio = "Other"

    prompt = f"""Based on the following user profile description, estimate the probability that the user is female.
    
    Description: "{description}"
    
    Respond with a single number between 0 and 1, where:
    - 1.0 means 100% certain the user is female.
    - 0.0 means 100% certain the user is male.
    - -99 means it's unclear or "Other".
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": "You estimate gender probabilities from user bios."},
                      {"role": "user", "content": prompt}],
            temperature=0
        )
        return float(response["choices"][0]["message"]["content"].strip())
    except Exception as e:
        print(f"⚠️ Error in text-based gender classification: {e}")
        return -99  # Error case

# Function to classify occupation
def classify_occupation(username, description):
    if not description or description.strip() == "":
        description = "No description provided."

    prompt = f"""Based on the following Twitter profile details, classify the likely occupation:
    
    Username: {username}
    Description: {description}
    
    Respond with the most probable occupation (e.g., 'Software Engineer', 'Student', 'Doctor', 'Artist', 'Unemployed', etc.).
    If unknown, respond with 'Unknown'.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4-turbo",
            messages=[{"role": "system", "content": "You classify user occupations."},
                      {"role": "user", "content": prompt}],
            temperature=0
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"⚠️ Error in occupation classification: {e}")
        return "Unknown"

# Load CSV file
df = pd.read_csv(INPUT_CSV)

# Ensure required columns exist
required_columns = ["username", "description", "profile_image_url"]
if not all(col in df.columns for col in required_columns):
    print(f"❌ Error: CSV must contain columns {required_columns}")
    exit(1)

# Add empty columns for classification results
df["gender_probability"] = -99  # Default to -99 (uncertain)
df["occupation"] = "Unknown"  # Default to "Unknown"

# Process each profile and update the DataFrame
for index, row in df.iterrows():
    username = row["username"]
    description = row["description"]
    profile_image_url = row["profile_image_url"]

    print(f"Processing {username}...")

    # Get gender probability from image and text
    image_gender_prob = get_gender_probability_from_image(profile_image_url)
    text_gender_prob = get_gender_probability_from_text(description)

    # Use text-based probability if available, otherwise fallback to image
    if text_gender_prob != -99:
        final_gender_prob = text_gender_prob
    else:
        final_gender_prob = image_gender_prob

    # Classify occupation
    occupation = classify_occupation(username, description)

    # Update DataFrame
    df.at[index, "gender_probability"] = final_gender_prob
    df.at[index, "occupation"] = occupation

# Save updated DataFrame back to CSV
df.to_csv(OUTPUT_CSV, index=False)

print(f"✅ Classification complete! Updated data saved to {OUTPUT_CSV}")
