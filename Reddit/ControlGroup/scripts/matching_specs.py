# Author: Hannah Lybbert
# Created: 2026-10-02
# Updated: 2026-10-05
# Purpose: Named matching specs for 4b/4c (outputs are named <SPEC>_*). Add a new spec rather than editing one already run.
#
# month_bins: months matched on; a multi-month bin is the sum of its months. A group's weight is split evenly across bins.
# weights: share per feature group, must sum to 1. Leave a group out to not match on it.

def monthly(first, last):
    return [[m] for m in range(first, last + 1)]


DEFAULTS = {
    "max_control_reuse": 5,
    "max_match_distance": None,
    "seed": 20260930,
}

EVEN_VOLUME_WEIGHTS = {
    "submissions":            0.20,
    "comments":               0.20,
    "designated_submissions": 0.20,
    "designated_comments":    0.20,
    "subreddit_breadth":      0.10,
    "account_age":            0.10,
}

COMMENT_HEAVY_WEIGHTS = {
    "submissions":            0.15,
    "comments":               0.25,
    "designated_submissions": 0.15,
    "designated_comments":    0.25,
    "subreddit_breadth":      0.10,
    "account_age":            0.10,
}

COMMENT_VERY_HEAVY_WEIGHTS = {
    "submissions":            0.10,
    "comments":               0.35,
    "designated_submissions": 0.10,
    "designated_comments":    0.35,
    "subreddit_breadth":      0.05,
    "account_age":            0.05,
}

COMMENT_DOMINANT_WEIGHTS = {
    "submissions":            0.03,
    "comments":               0.45,
    "designated_submissions": 0.03,
    "designated_comments":    0.45,
    "subreddit_breadth":      0.02,
    "account_age":            0.02,
}

COMMENT_DOMINANT_TEXT_WEIGHTS = {
    "submissions":            0.03,
    "comments":               0.40,
    "designated_submissions": 0.03,
    "designated_comments":    0.40,
    "subreddit_breadth":      0.02,
    "account_age":            0.02,
    "comment_length":         0.06,
    "submission_length":      0.04,
}

SPECS = {
    # Months -18..-1; all others use -10..-1 (COARSE_* = bins -1, -2..-4, -5..-7, -8..-10)
    "ORIGINAL": {
        "month_bins": monthly(-18, -1),
        "weights": {
            "submissions":            0.30,
            "comments":               0.30,
            "designated_submissions": 0.10,
            "designated_comments":    0.10,
            "subreddit_breadth":      0.10,
            "account_age":            0.05,
            "days_from":              0.05,
        },
    },
    "PRE10": {
        "month_bins": monthly(-10, -1),
        "weights": EVEN_VOLUME_WEIGHTS,
    },
    "COARSE": {
        "month_bins": [[-1], [-4, -3, -2], [-7, -6, -5], [-10, -9, -8]],
        "weights": EVEN_VOLUME_WEIGHTS,
    },
    "COM-HEAVY": {
        "month_bins": monthly(-10, -1),
        "weights": COMMENT_HEAVY_WEIGHTS,
    },
    "COARSE_COM-HEAVY": {
        "month_bins": [[-1], [-4, -3, -2], [-7, -6, -5], [-10, -9, -8]],
        "weights": COMMENT_HEAVY_WEIGHTS,
    },
    "COM-VERY-HEAVY": {
        "month_bins": monthly(-10, -1),
        "weights": COMMENT_VERY_HEAVY_WEIGHTS,
    },
    "COARSE_COM-VERY-HEAVY": {
        "month_bins": [[-1], [-4, -3, -2], [-7, -6, -5], [-10, -9, -8]],
        "weights": COMMENT_VERY_HEAVY_WEIGHTS,
    },
    "COM-DOM": {
        "month_bins": monthly(-10, -1),
        "weights": COMMENT_DOMINANT_WEIGHTS,
    },
    "COARSE_COM-DOM": {
        "month_bins": [[-1], [-4, -3, -2], [-7, -6, -5], [-10, -9, -8]],
        "weights": COMMENT_DOMINANT_WEIGHTS,
    },
    "COM-DOM_TEXT": {
        "month_bins": monthly(-10, -1),
        "weights": COMMENT_DOMINANT_TEXT_WEIGHTS,
    },
    "COARSE_COM-DOM_TEXT": {
        "month_bins": [[-1], [-4, -3, -2], [-7, -6, -5], [-10, -9, -8]],
        "weights": COMMENT_DOMINANT_TEXT_WEIGHTS,
    },
    # Diagnostic: comments only
    "ONLY_COM": {
        "month_bins": monthly(-10, -1),
        "weights": {"comments": 0.50, "designated_comments": 0.50},
    },
}


def get_spec(name):
    if name not in SPECS:
        raise SystemExit(f"Unknown spec '{name}'. Defined: {', '.join(SPECS)}")
    return {**DEFAULTS, **SPECS[name], "name": name}


def bin_label(months):
    lo, hi = -max(months), -min(months)
    return f"{lo}pre" if lo == hi else f"{lo}to{hi}pre"
