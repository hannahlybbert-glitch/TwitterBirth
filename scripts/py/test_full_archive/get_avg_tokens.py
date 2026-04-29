import json
import pandas as pd

# Define file path
file_path = "/Users/rorylawson/Desktop/TwitterBirth/data/json/batch_67c156eae840819083a79569b71cab65_output.jsonl"

# Read JSONL file and store token counts
token_counts = []

with open(file_path, "r", encoding="utf-8") as f:
    for line in f:
        response = json.loads(line)
        response_data = response.get("response", {})
        status_code = response_data.get("status_code")

        if status_code == 200:
            body = response_data.get("body", {})
            usage = body.get("usage", {})
            total_tokens = usage.get("total_tokens", 0)
            token_counts.append(total_tokens)

# Convert to DataFrame
df = pd.DataFrame(token_counts, columns=["total_tokens"])

# Display DataFrame and compute average
print(df)
print(f"Average tokens per request: {df['total_tokens'].mean():.2f}")
