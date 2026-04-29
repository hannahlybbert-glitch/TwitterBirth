import pandas as pd
import os
import openai
import time
from dotenv import load_dotenv
from tqdm import tqdm
import sys
import time

# Set working directory (temporary change for this script)
os.chdir("/Users/rorylawson/Desktop/TwitterBirth")

# Verify it's set correctly
print(f"Current Working Directory: {os.getcwd()}")

# Load API Key
load_dotenv(dotenv_path="config/.env")  # ✅ Load only once
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Date range for filenames
begin_date = "2025_02_17"
end_date = "2025_02_24"

# Load Data
file_path = f"data/testing/classified_text_{begin_date}-{end_date}.csv"
if not os.path.exists(file_path):
    print(f"Error: File '{file_path}' not found. Make sure it is in the correct directory.")
    sys.exit(1)

df = pd.read_csv(file_path, encoding="utf-8")

# Keep only tweets with pictures
# Filter only tweets that are classified as birth announcements and have pictures
pics_df = df[(df["has_picture"] == 1) & (df["text_classification"] == 1)].copy()
pics_df = pics_df[["query_id", "tweet_id", "media_url", "has_picture"]]

# Check if DataFrame is empty
if pics_df.empty:
    print("Error: No tweets with pictures found. Exiting.")
    sys.exit(1)

# Ensure necessary columns exist
required_columns = {"query_id", "tweet_id", "media_url", "has_picture"}
if not required_columns.issubset(df.columns):
    raise ValueError(f"Tweet CSV must contain columns: {required_columns}")

# Enable tqdm progress tracking
tqdm.pandas()

# Function to classify an image
def classify_image(image_url):
    """Classifies an image using GPT-4V and returns 1 (birth announcement) or 0 (not a birth announcement)."""
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo",
            messages=[
                {"role": "system", "content": "You are an expert image classifier for identifying birth announcement images."},
                {"role": "user", "content": [
                    {"type": "text", "text": "Does this image likely represent a birth announcement? Respond with '1' for Yes or '0' for No."},
                    {"type": "image_url", "image_url": {"url": image_url, "detail": "low"}}  # ✅ Corrected structure
                ]}
            ]
        )

        # Extract classification result
        result = response.choices[0].message.content.strip()
        
        # Ensure valid output (should be "1" or "0")
        return "1" if result == "1" else "0"
    
    except openai.RateLimitError as e:
        print(f"Quota exceeded error: {e}. Stopping classification.")
        raise  # Re-raise to stop further classification

    except openai.OpenAIError as e:
        print(f"❌ OpenAI API Error: {e}")
        return "Error"  # Return error so we can debug failed classifications

# Apply image classification with progress tracking
start_time = time.time()
print("🔍 Classifying images...")
pics_df["pic_classification"] = pics_df["media_url"].progress_apply(classify_image)

# Merge classification results back into the original DataFrame
df = df.merge(pics_df[["tweet_id", "pic_classification"]], on="tweet_id", how="left")

# Fill non-picture tweets with NA
df["pic_classification"] = df["pic_classification"].apply(lambda x: x if pd.notna(x) else "NA")

# Save results
output_file = f"data/testing/classified_pics_{begin_date}-{end_date}.csv"
df.to_csv(output_file, index=False, encoding="utf-8")

end_time = time.time()
elapsed_time = end_time - start_time

print(f"✅ Classification completed in {elapsed_time:.2f} seconds.. Results saved to: {output_file}")

# begin_date = "2025_02_16"
# end_date = "2025_02_23"

df = pd.read_csv(f"data/testing/classified_pics_{begin_date}-{end_date}.csv", encoding="utf-8")

hand_code = df[(df["pic_classification"] == 1) | ((df["text_classification"] == 1) & (df["has_picture"] == 0)) ]

hand_code_path = f"data/testing/to_hand_code_{begin_date}-{end_date}.csv"
hand_code.to_csv(hand_code_path, encoding = "utf-8", index = False)

print(len(hand_code), "tweets made it through classification")
print(f"✅ Tweets saved to: {hand_code_path}")





# # Single image classification for testing purposes
# # Extract first image URL for testing
# image_url = pics_df["media_url"].iloc[0]  # ✅ Using `.iloc[0]` ensures it's a single value
# print(f"Testing Image URL: {image_url}")

# # OpenAI API Call for Image Classification
# try:
#     response = client.chat.completions.create(
#         model="gpt-4-turbo",
#         messages=[
#             {"role": "system", "content": "You are an expert image classifier for identifying birth announcement images."},
#             {"role": "user", "content": [
#                 {"type": "text", "text": "Does this image likely represent a birth announcement? Respond with 'Yes' or 'No'."},
#                 {"type": "image_url", "image_url": {"url": image_url, "detail": "low"}}  # ✅ Fixed format
#             ]}
#         ]
#     )

#     # Extract and print the response
#     result = response.choices[0].message.content
#     print(f"🖼️ Image Classification Result: {result}")

# except openai.OpenAIError as e:
#     print(f"❌ OpenAI API Error: {e}")


