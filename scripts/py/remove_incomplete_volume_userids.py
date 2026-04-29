import pandas as pd
from datetime import datetime
import os
import csv

# File path
csv_file = "data/raw/retweet_reply_volume_by_user_2013_2017.csv"

# Load dataset
df = pd.read_csv(csv_file, encoding="utf-8")

# Remove rows where date wasn't fetched
df = df[df["date"] != "No Data"]

# Parse date columns
df["begin_date_dt"] = pd.to_datetime(df["begin_date"])
df["end_date_dt"] = pd.to_datetime(df["end_date"])
df["date_dt"] = pd.to_datetime(df["date"])

# Compute expected number of days per unique_id
df["expected_days"] = (df["end_date_dt"] - df["begin_date_dt"]).dt.days + 1

# Count actual number of unique days observed per unique_id
actual_days = df.groupby("unique_id")["date_dt"].nunique().reset_index()
actual_days.rename(columns={"date_dt": "actual_days"}, inplace=True)

# Merge actual_days back into main DataFrame
df = df.merge(actual_days, on="unique_id", how="left")

# Identify incomplete unique_ids
incomplete_ids = df[df["actual_days"] < df["expected_days"]]["unique_id"].unique()

# Filter out rows from incomplete unique_ids
df_cleaned = df[~df["unique_id"].isin(incomplete_ids)]

# Drop temporary computation columns
df_cleaned = df_cleaned.drop(columns=["begin_date_dt", "end_date_dt", "date_dt", "expected_days", "actual_days"])

# Save filtered data back to file
with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
    writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(df_cleaned.columns)
    writer.writerows(df_cleaned.itertuples(index=False, name=None))

print(f"✅ Filtered data saved to {csv_file}")




# import pandas as pd
# from datetime import datetime
# from dateutil.relativedelta import relativedelta
# import os
# import csv

# # File path
# csv_file = "data/raw/retweet_reply_volume_by_user_2013_2017.csv"

# # Load dataset
# df = pd.read_csv(csv_file, encoding="utf-8")

# # Remove the ones we can't get data for
# df = df[df["date"] != "No Data"]

# # Create new datetime variables (do NOT overwrite original timestamps)
# df["begin_date_dt"] = pd.to_datetime(df["begin_date"])
# df["end_date_dt"] = pd.to_datetime(df["end_date"])
# df["date_dt"] = pd.to_datetime(df["date"])

# # Compute expected days per user
# df["expected_days"] = (df["end_date_dt"] - df["begin_date_dt"]).dt.days + 1

# # Count actual days of volume data per author_id
# actual_days = df.groupby("author_id")["date_dt"].nunique().reset_index()
# actual_days.rename(columns={"date_dt": "actual_days"}, inplace=True)

# # Merge expected and actual days
# df = df.merge(actual_days, on="author_id", how="left")

# # Identify incomplete users
# incomplete_users = df[df["actual_days"] < df["expected_days"]]["author_id"].unique()

# # Remove incomplete users
# df_cleaned = df[~df["author_id"].isin(incomplete_users)]

# # Drop temporary variables so output matches original format
# df_cleaned = df_cleaned.drop(columns=["begin_date_dt", "end_date_dt", "date_dt", "expected_days", "actual_days"])

# # **Save the filtered data in the correct CSV format**
# with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
#     writer = csv.writer(file, delimiter=",", quotechar='"', quoting=csv.QUOTE_ALL)
    
#     # Write headers
#     writer.writerow(df_cleaned.columns)
    
#     # Write data without unnecessary output
#     writer.writerows(df_cleaned.itertuples(index=False, name=None))

# print(f"✅ Filtered data saved to {csv_file}")
