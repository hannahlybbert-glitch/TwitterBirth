import pandas as pd
df = pd.read_csv("D:/TwitterBirth/Reddit/data/final/treatment_control_births_posts.csv")
df3 = df[df["full_18_pre"] == 1]
df3 = df3[(df3["months_from_birth"] >= -18) & (df3["months_from_birth"] <= 18)]

for treated, label in [(1, "TREATMENT"), (0, "CONTROL")]:
    n = df3[df3["treated"] == treated]["author"].nunique()
    ppm = df3[df3["treated"] == treated].groupby("months_from_birth")["id"].count().div(n)
    print(f"\n--- {label} (n={n:,}) ---")
    print(ppm.to_string())