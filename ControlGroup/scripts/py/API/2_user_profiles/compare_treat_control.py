# Author: Hannah Lybbert
# Purpose: Compare control (anniversary profiles_filtered) vs. treatment
#          (sample_authors) accounts on account age, followers, following,
#          tweet count, and average weekly tweets.

import os
from datetime import date

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..")))

CONTROL_PATH   = "ControlGroup/data/2_user_profiles/anniversary/test/profiles_filtered.csv"
# TREATMENT_PATH = "data/testing/sample_authors.csv"
TREATMENT_PATH = "data/testing/sample_authors_2013.csv"


# Control accounts aren't tied to a frozen snapshot the way treatment is here, so
# control age / avg_weekly_tweets is always computed as of today, whenever this
# script is run.
CONTROL_REF_DATE = pd.Timestamp(date.today(), tz="UTC")

# lifetime_posts in sample_authors.csv is a frozen snapshot: 2013-2017 births were
# scraped 7/17/2025, 2018 births were scraped 4/15/2025. Treatment age / avg_weekly_tweets
# must be computed as of whichever date matches each row's birth-tweet cohort, so the
# comparison against control's avg_weekly_tweets is apples-to-apples.
TREATMENT_REF_DATE_2013_2017 = pd.Timestamp("2025-07-17", tz="UTC")
TREATMENT_REF_DATE_2018      = pd.Timestamp("2025-04-15", tz="UTC")

METRICS = ["account_age_years", "followers_count", "following_count", "tweet_count", "avg_weekly_tweets"]

OUTPUT_PATH      = "ControlGroup/output/descriptives/compare_users.md"
HISTOGRAM_PATH   = "ControlGroup/output/descriptives/compare_users_histograms.png"


def load_control(path):
    df = pd.read_csv(path)
    created = pd.to_datetime(df["account_created_at"], utc=True, errors="coerce")
    age_weeks = (CONTROL_REF_DATE - created).dt.days / 7
    tweet_count = pd.to_numeric(df["tweet_count"], errors="coerce")

    return pd.DataFrame({
        "account_age_years": (CONTROL_REF_DATE - created).dt.days / 365.25,
        "followers_count":   pd.to_numeric(df["followers_count"], errors="coerce"),
        "following_count":   pd.to_numeric(df["following_count"], errors="coerce"),
        "tweet_count":       tweet_count,
        "avg_weekly_tweets": tweet_count / age_weeks,
    })


def load_treatment(path):
    df = pd.read_csv(path)
    created = pd.to_datetime(df["user_created_at"], format="%d%b%Y", utc=True, errors="coerce")
    birth_tweet_year = pd.to_datetime(df["date_birth_tweet"], format="%d%b%Y", errors="coerce").dt.year
    ref_date = pd.to_datetime(
        pd.Series(
            np.where(birth_tweet_year == 2018, TREATMENT_REF_DATE_2018, TREATMENT_REF_DATE_2013_2017),
            index=df.index,
        ),
        utc=True,
    )
    age_weeks = (ref_date - created).dt.days / 7
    lifetime_posts = pd.to_numeric(df["lifetime_posts"], errors="coerce")

    return pd.DataFrame({
        "account_age_years": (ref_date - created).dt.days / 365.25,
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
    print(f"Control account_age_years and avg_weekly_tweets computed as of {CONTROL_REF_DATE.date()}")
    print(f"Treatment account_age_years and avg_weekly_tweets computed as of {TREATMENT_REF_DATE_2013_2017.date()} (2013-2017 births) "
          f"or {TREATMENT_REF_DATE_2018.date()} (2018 births)\n")

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
