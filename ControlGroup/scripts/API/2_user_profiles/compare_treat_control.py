# Author: Hannah Lybbert
# Purpose: Compare control (anniversary profiles_filtered) vs. treatment
#          (sample_authors) accounts on account age, followers, following,
#          tweet count, and average weekly tweets.

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")))

CONTROL_PATH   = "ControlGroup/data/user_profiles/anniversary/test/profiles_filtered.csv"
# TREATMENT_PATH = "data/testing/sample_authors.csv"
TREATMENT_PATH = "data/testing/sample_authors_2013.csv"


# lifetime_posts in sample_authors.csv was scraped in April 2025, so account
# age / avg_weekly_tweets for the treatment group is calculated as of that date.
TREATMENT_REF_DATE = pd.Timestamp("2025-07-17", tz="UTC")

METRICS = ["account_age_years", "followers_count", "following_count", "tweet_count", "avg_weekly_tweets"]

OUTPUT_PATH      = "ControlGroup/output/descriptives/compare_users.md"
HISTOGRAM_PATH   = "ControlGroup/output/descriptives/compare_users_histograms.png"


def load_control(path):
    df = pd.read_csv(path)
    created = pd.to_datetime(df["account_created_at"], utc=True, errors="coerce")

    return pd.DataFrame({
        "account_age_years": (TREATMENT_REF_DATE - created).dt.days / 365.25,
        "followers_count":   pd.to_numeric(df["followers_count"], errors="coerce"),
        "following_count":   pd.to_numeric(df["following_count"], errors="coerce"),
        "tweet_count":       pd.to_numeric(df["tweet_count"], errors="coerce"),
        "avg_weekly_tweets": pd.to_numeric(df["avg_weekly_tweets"], errors="coerce"),
    })


def load_treatment(path):
    df = pd.read_csv(path)
    created = pd.to_datetime(df["user_created_at"], format="%d%b%Y", utc=True, errors="coerce")
    age_weeks = (TREATMENT_REF_DATE - created).dt.days / 7
    lifetime_posts = pd.to_numeric(df["lifetime_posts"], errors="coerce")

    return pd.DataFrame({
        "account_age_years": (TREATMENT_REF_DATE - created).dt.days / 365.25,
        "followers_count":   pd.to_numeric(df["followers_count"], errors="coerce"),
        "following_count":   pd.to_numeric(df["following_count"], errors="coerce"),
        "tweet_count":       lifetime_posts,
        "avg_weekly_tweets": lifetime_posts / age_weeks,
    })


def stats_row(metric, group, series):
    series = series.dropna()
    p95, p99 = series.quantile([0.95, 0.99])
    return f"| {metric} | {group} | {series.mean():.1f} | {series.median():.1f} | {series.std():.1f} | {series.min():.1f} | {series.max():.1f} | {p95:.1f} | {p99:.1f} |"


def print_stats(group, series):
    series = series.dropna()
    p95, p99 = series.quantile([0.95, 0.99])
    print(f"    {group:<10} n={len(series):<5} mean={series.mean():>10.1f}  median={series.median():>10.1f}  sd={series.std():>10.1f}  min={series.min():>10.1f}  max={series.max():>10.1f}  p95={p95:>10.1f}  p99={p99:>10.1f}")


# def plot_histograms(control, treatment, path):
#     fig, axes = plt.subplots(2, 3, figsize=(15, 8))
#     axes = axes.flatten()

#     for ax, metric in zip(axes, METRICS):
#         control_vals   = control[metric].dropna()
#         treatment_vals = treatment[metric].dropna()
#         combined       = pd.concat([control_vals, treatment_vals])

#         # clip the view to the control group's range (up to its 95th percentile) so
#         # control outliers don't wash out the bars; treatment is left unclipped
#         lo, hi = control_vals.min(), control_vals.quantile(0.95)
#         bins   = np.linspace(combined.min(), combined.max(), 31)

#         ax.hist(control_vals,   bins=bins, alpha=0.6, density=True, label="Control")
#         ax.hist(treatment_vals, bins=bins, alpha=0.6, density=True, label="Treatment")
#         ax.set_xlim(lo, hi)
#         ax.set_title(metric)
#         ax.set_ylabel("Density")
#         ax.legend()

#     axes[-1].axis("off")
#     fig.tight_layout()

#     os.makedirs(os.path.dirname(path), exist_ok=True)
#     fig.savefig(path, dpi=150)
#     plt.close(fig)


def main():
    control   = load_control(CONTROL_PATH)
    treatment = load_treatment(TREATMENT_PATH)

    print(f"Control (anniversary, n={len(control)}):   {CONTROL_PATH}")
    print(f"Treatment (sample_authors, n={len(treatment)}): {TREATMENT_PATH}")
    print(f"Treatment account age / avg_weekly_tweets computed as of {TREATMENT_REF_DATE.date()}\n")

    lines = ["| Metric | Group | Mean | Median | SD | Min | Max | P95 | P99 |", "|---|---|---|---|---|---|---|---|---|"]
    for metric in METRICS:
        print(f"{metric}:")
        print_stats("control", control[metric])
        print_stats("treatment", treatment[metric])
        print()

        lines.append(stats_row(metric, "Control", control[metric]))
        lines.append(stats_row(metric, "Treatment", treatment[metric]))

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote comparison table ({len(control)} control, {len(treatment)} treatment) to {OUTPUT_PATH}")

    # plot_histograms(control, treatment, HISTOGRAM_PATH)
    # print(f"Wrote histogram panel to {HISTOGRAM_PATH}")


if __name__ == "__main__":
    main()
