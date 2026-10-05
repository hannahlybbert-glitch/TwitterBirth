# Author: Hannah Lybbert
# Created: 2026-10-02
# Purpose: Named matching specifications for steps 4b/4c. Every output of a run starts
#          with its spec name (<SPEC>_matched_pairs.parquet, <SPEC>_balance.csv,
#          <SPEC>_spec.json, <SPEC>_pretrends.png), so past matching methods stay on
#          disk side by side. Spec names are ALL CAPS (e.g. COARSE_COM-HEAVY).
#
# Rule: once a spec has been run, don't edit it -- add a new one. 4b also writes the
# resolved spec to <SPEC>_spec.json as a record of exactly what was used.
#
# Spec fields:
#   month_bins          list of month groups (months_from_birth, negative). Each bin
#                       becomes one feature per volume type: a single month uses the
#                       existing column (sub_3pre); a multi-month bin is the SUM of its
#                       months (sub_2to4pre). A group's weight is split evenly across
#                       its bins.
#   weights             share of total weight per feature group (must sum to 1).
#                       Groups: submissions, comments, designated_submissions,
#                       designated_comments, subreddit_breadth, account_age, days_from.
#                       Leave a group out to not match on it.
#   max_control_reuse   max treatment authors one control can match
#   max_match_distance  optional caliper (weighted std units); None = always take the nearest
#   seed                treatment match order

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

SPECS = {
    # First version (2026-09-30): 18 monthly bins, volume-heavy weights, days_from matched.
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
    # 2026-10-02: only months -10..-1 (fewer features to match), no days_from,
    # volume groups weighted evenly.
    "PRE10": {
        "month_bins": monthly(-10, -1),
        "weights": EVEN_VOLUME_WEIGHTS,
    },
    # 2026-10-02: PRE10 with months coarsened to -1, -2..-4, -5..-7, -8..-10.
    # COARSE_* specs use these bins; all other non-ORIGINAL specs are monthly -10..-1.
    "COARSE": {
        "month_bins": [[-1], [-4, -3, -2], [-7, -6, -5], [-10, -9, -8]],
        "weights": EVEN_VOLUME_WEIGHTS,
    },
    # 2026-10-02: PRE10 / COARSE matched comments poorly -> shift weight toward comments.
    "COM-HEAVY": {
        "month_bins": monthly(-10, -1),
        "weights": COMMENT_HEAVY_WEIGHTS,
    },
    "COARSE_COM-HEAVY": {
        "month_bins": [[-1], [-4, -3, -2], [-7, -6, -5], [-10, -9, -8]],
        "weights": COMMENT_HEAVY_WEIGHTS,
    },
    # 2026-10-02: push further toward comments (35/35 comments, 10/10 submissions,
    # 5/5 breadth/account age).
    "COM-VERY-HEAVY": {
        "month_bins": monthly(-10, -1),
        "weights": COMMENT_VERY_HEAVY_WEIGHTS,
    },
    "COARSE_COM-VERY-HEAVY": {
        "month_bins": [[-1], [-4, -3, -2], [-7, -6, -5], [-10, -9, -8]],
        "weights": COMMENT_VERY_HEAVY_WEIGHTS,
    },
    # 2026-10-02: comments dominant (45/45 comments, 3/3 submissions, 2/2 breadth/account age).
    "COM-DOM": {
        "month_bins": monthly(-10, -1),
        "weights": COMMENT_DOMINANT_WEIGHTS,
    },
    "COARSE_COM-DOM": {
        "month_bins": [[-1], [-4, -3, -2], [-7, -6, -5], [-10, -9, -8]],
        "weights": COMMENT_DOMINANT_WEIGHTS,
    },
    # 2026-10-02: diagnostic -- match on comments only (50 all comments, 50 designated
    # comments), months -10..-1 monthly. Upper bound on how well comments can match.
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
