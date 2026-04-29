# Author: Hannah Lybbert
# Created: 2026-03-31
# Updated: 2026-03-31
# Purpose: Plot log posts/user/month by subreddit for months -21 to -9 (control) / -21 to -10 (treatment)

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

ROOT             = Path(__file__).resolve().parents[5]
INPUT_CTRL_SAMP  = ROOT / "Reddit/raw/placebo_sample_posts.csv"
INPUT_CTRL_HIST  = ROOT / "Reddit/data/intermediate/births_and_posts/placebo_births_and_posts.csv"
INPUT_TREAT      = ROOT / "Reddit/data/final/births_and_posts_22k.csv"
OUTPUT_DIR       = ROOT / "Reddit/output/analysis/placebo"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

WINDOW_MIN       = -21
CTRL_WINDOW_MAX  = -9
TREAT_WINDOW_MAX = -9


# ----------------------------------------------------------------
# Helper: build mean log(posts+1) per subreddit per month
# ----------------------------------------------------------------
def build_subreddit_trends(post_history, author_subreddit_map, window_max):
    """
    For each (author, month) in the window, count posts in their assigned subreddit.
    Authors with 0 posts in a month contribute log(0+1)=0.
    Returns a DataFrame with columns: subreddit, month, mean_log_posts
    """
    months = list(range(WINDOW_MIN, window_max + 1))

    # Keep only posts in the assigned subreddit and within the window
    df = post_history.merge(author_subreddit_map, on="author", how="inner")
    df = df[df["subreddit_x"] == df["subreddit_y"]].copy()
    df = df.rename(columns={"subreddit_y": "assigned_subreddit"}).drop(columns=["subreddit_x"])
    df = df[
        (df["months_from_birth"] >= WINDOW_MIN) &
        (df["months_from_birth"] <= window_max)
    ]

    # Count posts per author per month (within assigned subreddit)
    post_counts = (
        df.groupby(["author", "assigned_subreddit", "months_from_birth"])
        .size()
        .reset_index(name="post_count")
    )

    # Build complete author x month grid (zeros for missing months)
    all_combos = (
        author_subreddit_map
        .assign(key=1)
        .merge(pd.DataFrame({"months_from_birth": months, "key": 1}), on="key")
        .drop(columns="key")
        .rename(columns={"subreddit": "assigned_subreddit"})
    )
    panel = all_combos.merge(
        post_counts, on=["author", "assigned_subreddit", "months_from_birth"], how="left"
    )
    panel["post_count"] = panel["post_count"].fillna(0)
    panel["log_posts"]  = np.log(panel["post_count"] + 1)

    # Average log posts across authors by subreddit and month
    trends = (
        panel.groupby(["assigned_subreddit", "months_from_birth"])["log_posts"]
        .mean()
        .reset_index()
        .rename(columns={"assigned_subreddit": "subreddit", "months_from_birth": "month"})
    )
    return trends

# ----------------------------------------------------------------
# Helper: plot multi-panel figure
# ----------------------------------------------------------------
def plot_panels(trends, subreddits, n_panels, window_max, title, output_path):
    """
    Plot subreddits split across n_panels in a 2-column grid.
    All panels share the same x and y axis range.
    """
    n_cols  = 2
    n_rows  = n_panels // n_cols
    chunk   = len(subreddits) // n_panels
    chunks  = [subreddits[i * chunk:(i + 1) * chunk] for i in range(n_panels - 1)]
    chunks.append(subreddits[(n_panels - 1) * chunk:])  # remainder goes in last panel

    fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 5 * n_rows), sharey=True)
    axes = axes.flatten()

    prop_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]

    for panel_idx, subs in enumerate(chunks):
        ax = axes[panel_idx]
        for color_idx, sub in enumerate(subs):
            data = trends[trends["subreddit"] == sub].sort_values("month")
            ax.plot(data["month"], data["log_posts"],
                    color=prop_cycle[color_idx % len(prop_cycle)],
                    linewidth=1.5, label=sub)
        ax.set_xlim(WINDOW_MIN, window_max)
        ax.set_xticks(range(WINDOW_MIN, window_max + 1, 3))
        ax.set_xlabel("Months from Birth")
        ax.set_ylabel("Mean log(posts + 1)")
        ax.legend(loc="upper right", fontsize=8)
        ax.grid(axis="y", linewidth=0.4, alpha=0.5)

    # Hide any unused axes
    for ax in axes[len(chunks):]:
        ax.set_visible(False)

    fig.suptitle(title, fontsize=13, y=1.01)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Saved: {output_path}")

# ----------------------------------------------------------------
# Control
# ----------------------------------------------------------------
print("=== CONTROL ===")
ctrl_sample = pd.read_csv(INPUT_CTRL_SAMP)
# One subreddit per author: use first observation
ctrl_assign = (
    ctrl_sample.sort_index()
    .groupby("author", sort=False)
    .first()
    .reset_index()[["author", "subreddit"]]
)
print(f"Control authors assigned: {len(ctrl_assign):,}")

ctrl_hist = pd.read_csv(INPUT_CTRL_HIST, low_memory=False)
ctrl_hist["months_from_birth"] = ctrl_hist["months_from_birth"].astype(float)
print(f"Control post history: {len(ctrl_hist):,} rows")

ctrl_trends = build_subreddit_trends(ctrl_hist, ctrl_assign, window_max=CTRL_WINDOW_MAX)
ctrl_subs   = sorted(ctrl_trends["subreddit"].unique())
print(f"Control subreddits with data: {len(ctrl_subs)}")

plot_panels(
    trends      = ctrl_trends,
    subreddits  = ctrl_subs,
    n_panels    = 4,
    window_max  = CTRL_WINDOW_MAX,
    title       = "Control: Mean log(posts+1) per user per month by subreddit (months -21 to -9)",
    output_path = OUTPUT_DIR / "log_posts_month_control_subreddits.jpg",
)

# Single plot with all 23 control subreddits, legend outside, ordered by avg log posts
ctrl_subs_ordered = (
    ctrl_trends.groupby("subreddit")["log_posts"]
    .mean()
    .sort_values(ascending=False)
    .index.tolist()
)
fig, ax = plt.subplots(figsize=(12, 6))
prop_cycle = plt.rcParams["axes.prop_cycle"].by_key()["color"]
for i, sub in enumerate(ctrl_subs_ordered):
    data = ctrl_trends[ctrl_trends["subreddit"] == sub].sort_values("month")
    ax.plot(data["month"], data["log_posts"],
            color=prop_cycle[i % len(prop_cycle)],
            linewidth=1.5, label=sub)
ax.set_xlim(WINDOW_MIN, CTRL_WINDOW_MAX)
ax.set_xticks(range(WINDOW_MIN, CTRL_WINDOW_MAX + 1, 3))
ax.set_xlabel("Months from Birth")
ax.set_ylabel("Mean log(posts + 1)")
ax.set_title("Control: Mean log(posts+1) per user per month by subreddit (months -21 to -9)")
ax.grid(axis="y", linewidth=0.4, alpha=0.5)
ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1), borderaxespad=0, fontsize=8)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "log_posts_month_control_subreddits_all.jpg", dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {OUTPUT_DIR / 'log_posts_month_control_subreddits_all.jpg'}")

# ----------------------------------------------------------------
# Treatment
# ----------------------------------------------------------------
print("\n=== TREATMENT ===")
treat = pd.read_csv(INPUT_TREAT, low_memory=False)

# Assign each author to the subreddit of their birth post
treat_assign = (
    treat[treat["birth_post"] == 1][["author", "subreddit"]]
    .drop_duplicates(subset="author")
    .reset_index(drop=True)
)
print(f"Treatment authors assigned: {len(treat_assign):,}")

treat_trends = build_subreddit_trends(treat, treat_assign, window_max=TREAT_WINDOW_MAX)
treat_subs   = sorted(treat_trends["subreddit"].unique())
print(f"Treatment subreddits with data: {len(treat_subs)}")

plot_panels(
    trends      = treat_trends,
    subreddits  = treat_subs,
    n_panels    = 2,
    window_max  = TREAT_WINDOW_MAX,
    title       = "Treatment: Mean log(posts+1) per user per month by subreddit (months -21 to -9)",
    output_path = OUTPUT_DIR / "log_posts_month_treatment_subreddits.jpg",
)

# ----------------------------------------------------------------
# Side-by-side comparison: control vs treatment, y capped at 0.06
# ----------------------------------------------------------------
Y_CAP          = 0.03
CTRL_AVG_MAX   = 0.025

ctrl_avg = ctrl_trends.groupby("subreddit")["log_posts"].mean()
ctrl_subs_comparison = ctrl_avg[ctrl_avg < CTRL_AVG_MAX].sort_values(ascending=False).index.tolist()

treat_subs_ordered = (
    treat_trends.groupby("subreddit")["log_posts"]
    .mean()
    .sort_values(ascending=False)
    .index.tolist()
)

fig, (ax_ctrl, ax_treat) = plt.subplots(1, 2, figsize=(18, 6), sharey=True)

for i, sub in enumerate(ctrl_subs_comparison):
    data = ctrl_trends[ctrl_trends["subreddit"] == sub].sort_values("month")
    ax_ctrl.plot(data["month"], data["log_posts"],
                 color=prop_cycle[i % len(prop_cycle)],
                 linewidth=1.5, label=sub)
ax_ctrl.set_xlim(WINDOW_MIN, CTRL_WINDOW_MAX)
ax_ctrl.set_ylim(0, Y_CAP)
ax_ctrl.set_xticks(range(WINDOW_MIN, CTRL_WINDOW_MAX + 1, 3))
ax_ctrl.set_xlabel("Months from Birth")
ax_ctrl.set_ylabel("Mean log(posts + 1)")
ax_ctrl.set_title("Control")
ax_ctrl.grid(axis="y", linewidth=0.4, alpha=0.5)
ax_ctrl.legend(loc="upper left", bbox_to_anchor=(0, -0.18), ncol=3, fontsize=7, borderaxespad=0)
print(f"Comparison figure — control subreddits included (avg < {CTRL_AVG_MAX}): {ctrl_subs_comparison}")

for i, sub in enumerate(treat_subs_ordered):
    data = treat_trends[treat_trends["subreddit"] == sub].sort_values("month")
    ax_treat.plot(data["month"], data["log_posts"],
                  color=prop_cycle[i % len(prop_cycle)],
                  linewidth=1.5, label=sub)
ax_treat.set_xlim(WINDOW_MIN, TREAT_WINDOW_MAX)
ax_treat.set_xticks(range(WINDOW_MIN, TREAT_WINDOW_MAX + 1, 3))
ax_treat.set_xlabel("Months from Birth")
ax_treat.set_title("Treatment")
ax_treat.grid(axis="y", linewidth=0.4, alpha=0.5)
ax_treat.legend(loc="upper left", bbox_to_anchor=(0, -0.18), ncol=3, fontsize=7, borderaxespad=0)

fig.suptitle("Mean log(posts+1) per user per month by subreddit (months -21 to -9)", fontsize=13)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / "log_posts_month_comparison_subreddits.jpg", dpi=150, bbox_inches="tight")
plt.close()
print(f"Saved: {OUTPUT_DIR / 'log_posts_month_comparison_subreddits.jpg'}")

# ----------------------------------------------------------------
# CSV summary: avg log posts across period per subreddit
# ----------------------------------------------------------------
treat_avg = (
    treat_trends.groupby("subreddit")["log_posts"]
    .mean()
    .sort_values(ascending=False)
    .reset_index()
    .rename(columns={"subreddit": "t_subreddit", "log_posts": "t_avg"})
)
ctrl_avg_df = (
    ctrl_avg
    .sort_values(ascending=False)
    .reset_index()
    .rename(columns={"subreddit": "c_subreddit", "log_posts": "c_avg"})
)

summary = pd.concat([treat_avg, ctrl_avg_df], axis=1)[["t_subreddit", "t_avg", "c_subreddit", "c_avg"]]
summary["t_avg"] = summary["t_avg"].round(4)
summary["c_avg"] = summary["c_avg"].round(4)

csv_path = OUTPUT_DIR / "subreddit_avg_log_posts_pre_pregnancy.csv"
summary.to_csv(csv_path, index=False)
print(f"Saved: {csv_path}")
print(summary.to_string())
