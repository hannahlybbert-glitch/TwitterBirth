import openai
from dotenv import load_dotenv
import os

# Change to project root directory
os.chdir("D:/TwitterBirth")

# Load API key from correct path
load_dotenv(dotenv_path="config/.env")
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Get the batch details
batch = client.batches.retrieve("batch_698baafffbf48190b23892be5f09dbd9")
print(f"Status: {batch.status}")
print(f"Failed at: {batch.failed_at}")
print(f"Error file ID: {batch.error_file_id}")
print(f"Request counts: {batch.request_counts}")

# If there's an error file, download it
if batch.error_file_id:
    error_content = client.files.content(batch.error_file_id)
    print("\n" + "="*60)
    print("ERROR DETAILS:")
    print("="*60)
    print(error_content.text[:2000])  # First 2000 chars