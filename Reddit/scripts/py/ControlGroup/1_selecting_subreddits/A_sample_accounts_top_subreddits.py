# Author: Hannah Lybbert
# Created: 2026-07-27
# Purpose: Sample ~100 authors from each top treatment subreddit and their matched
#          control subreddits, to use as candidate control-group accounts.

import pandas as pd
from pathlib import Path

ROOT        = Path(__file__).resolve().parents[5]
OUTPUT_PATH = ROOT / "Reddit/data/ControlGroup/1_subreddits/sampled_accounts_top_subreddits.csv"

SAMPLE_SIZE = 100

# Top subreddits treatment users post in (from other_treatment_subreddits.py),
# excluding subreddits that are themselves birth/parenting related.
top_subreddits = [
    "AskReddit",
    "aww",
    "funny",
    "pics",
    "namenerds",
    "legaladvice",
    "personalfinance",
    "cats",
    "mildlyinteresting",
    "Showerthoughts",
    "AskDocs",
    "TryingForABaby",
    "explainlikeimfive",
    "gardening",
    "HomeImprovement",
    "gaming",
]

# Subreddits matched to the treatment subreddits, either by type of person or by
# average log posts per month (see analysis/placebo/subreddit_matching.py).
matched_subreddits = [
    "running",
    "careerguidance",
    "Baking",
    "Adulting",
    "millenials",  # NOTE: this is the way it is spelled on Reddit, not "millennials"
    "GenZ",
    "GradSchool",
]


# ----------------------------------------------------------------
# Placeholder: pull SAMPLE_SIZE authors who have posted in `subreddit`
# ----------------------------------------------------------------
def sample_accounts(subreddit, n=SAMPLE_SIZE):
    """
    TODO: replace with real sampling logic.
    Must return a DataFrame with at least an "author" column containing
    up to `n` unique authors who have posted in `subreddit`.
    """
    raise NotImplementedError("Sampling logic not yet implemented")


# ----------------------------------------------------------------
# Sample accounts for every subreddit in our two lists
# ----------------------------------------------------------------
all_samples = []
for group_name, subreddits in [("top", top_subreddits), ("matched", matched_subreddits)]:
    for subreddit in subreddits:
        print(f"Sampling {SAMPLE_SIZE} accounts from r/{subreddit}...")
        sampled = sample_accounts(subreddit, SAMPLE_SIZE)
        sampled["subreddit"] = subreddit
        sampled["subreddit_group"] = group_name
        all_samples.append(sampled)

sampled_accounts = pd.concat(all_samples, ignore_index=True)

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
sampled_accounts.to_csv(OUTPUT_PATH, index=False)
print(f"Saved {len(sampled_accounts):,} sampled accounts to {OUTPUT_PATH}")