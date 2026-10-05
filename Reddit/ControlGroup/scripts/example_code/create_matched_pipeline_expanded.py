"""
Create an expanded matched treatment/placebo author sample.

This is a script version of "Create Matched Pipeline Multidimensional" with a
priority-weighted match distance inspired by "Matching Diagnostics":

  - event-relative posting-volume blocks
  - active-week consistency within those blocks and overall
  - mean post length
  - share of posts with selftext
  - top-subreddit share
  - number of distinct subreddits posted in

By default this writes new files with the suffix "jul2023_content_priority_raw"
so the existing jul2023 outputs are not overwritten.

Usage:
    python create_matched_pipeline_expanded.py

Notebook-style tuning:
    import create_matched_pipeline_expanded as cmp
    volume_bins = cmp.make_volume_bins(-39, 0, 3)
    treatment_features, placebo_features = cmp.load_feature_frames(
        suffix="jul2023_content_priority_raw"
    )
    matched = cmp.match_from_feature_frames(
        treatment_features,
        placebo_features,
        volume_bins,
        block_on="birth_quarter",
    )
"""

from __future__ import annotations

import argparse
import gc
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial import cKDTree


ROOT = Path("/Users/karthiksrinivasan/Dropbox/Twitter Project (team)/data/Reddit")

SECS_PER_DAY = 86_400
SECS_PER_WEEK = 7 * SECS_PER_DAY
DEFAULT_CUTOFF = "2023-07-01"
DEFAULT_WINDOW_LO = -39
DEFAULT_WINDOW_HI = 0
DEFAULT_WINSOR_PCTILE = 0.95
DEFAULT_OUTPUT_SUFFIX = "jul2023_content_priority_raw"
DEFAULT_CHUNK_SIZE = 1_000_000
DEFAULT_RANDOM_SEED = 42
DEFAULT_NEIGHBOR_K = 200
DEFAULT_VOLUME_BINS = 3
DEFAULT_BLOCK_ON = "birth_quarter"
DEFAULT_MATCH_ORDER = "attachment_desc"
DEFAULT_ATTACHMENT_WEIGHT = 4.0
DEFAULT_WITH_REPLACEMENT = False
DEFAULT_MAX_PLACEBO_REUSE = None
DEFAULT_MAX_LOWER_ATTACHMENT_GAP = None
DEFAULT_DIRECTIONAL_CALIPER = None

NO_TEXT_MARKERS = {"", "[deleted]", "[removed]"}

CONTENT_PLATFORM_FEATURES = [
    "active_weeks",
    "mean_post_len",
    "share_with_text",
    "top_sub_share",
    "n_distinct_subs",
]
CONTENT_PLATFORM_WEIGHTS = {
    "active_weeks": 1.8,
    "mean_post_len": 2.2,
    "share_with_text": 2.8,
    "top_sub_share": 2.8,
    "n_distinct_subs": 2.2,
}
RAW_DIAGNOSTIC_FEATURES = [
    "recent_total",
    "active_weeks",
    "mean_post_len",
    "share_with_text",
    "top_sub_share",
    "n_distinct_subs",
]
ATTACHMENT_COMPONENT_WEIGHTS = {
    "recent_total": 0.8,
    "active_weeks": 1.4,
    "mean_post_len": 1.0,
    "share_with_text": 1.4,
    "top_sub_share": 1.6,
    "n_distinct_subs": -1.0,
}
DIRECTIONAL_ATTACHMENT_FEATURES = {
    "recent_total": 1.0,
    "active_weeks": 1.0,
    "mean_post_len": 1.0,
    "share_with_text": 1.0,
    "top_sub_share": 1.0,
    "n_distinct_subs": -1.0,
}


@dataclass(frozen=True)
class VolumeBin:
    count_feature: str
    active_feature: str
    lo: int
    hi: int
    count_weight: float
    active_weight: float


@dataclass
class PanelArtifacts:
    births: pd.DataFrame
    features: pd.DataFrame
    full18_authors: set[str]
    max_per_week: pd.Series


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compute expanded treatment/placebo author features and create a "
            "matched placebo sample."
        )
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="Reddit data directory.")
    parser.add_argument(
        "--cutoff",
        default=DEFAULT_CUTOFF,
        help="Drop authors whose event/start timestamp is on or after this date.",
    )
    parser.add_argument(
        "--window-lo",
        type=int,
        default=DEFAULT_WINDOW_LO,
        help="Lowest event-relative week included in pre-event features.",
    )
    parser.add_argument(
        "--window-hi",
        type=int,
        default=DEFAULT_WINDOW_HI,
        help="Highest event-relative week included in pre-event features.",
    )
    parser.add_argument(
        "--winsor-pctile",
        type=float,
        default=DEFAULT_WINSOR_PCTILE,
        help="Pooled max author-week percentile used to drop likely bots.",
    )
    parser.add_argument(
        "--output-suffix",
        default=DEFAULT_OUTPUT_SUFFIX,
        help="Suffix used for matched-author/post output CSV names.",
    )
    parser.add_argument(
        "--feature-suffix",
        default=None,
        help=(
            "Suffix used for treatment/placebo feature CSVs. Defaults to "
            "--output-suffix. Use this to reuse one feature cache while writing "
            "many matched-author outputs."
        ),
    )
    parser.add_argument(
        "--reuse-features",
        action="store_true",
        help="Skip raw submission scans and load treatment/placebo feature CSVs from --feature-suffix.",
    )
    parser.add_argument(
        "--features-only",
        action="store_true",
        help="Build or load feature CSVs, then stop before matching.",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=DEFAULT_CHUNK_SIZE,
        help="Rows per chunk when scanning submission CSVs.",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=DEFAULT_RANDOM_SEED,
        help="Seed used to shuffle treatment authors before greedy matching.",
    )
    parser.add_argument(
        "--neighbor-k",
        type=int,
        default=DEFAULT_NEIGHBOR_K,
        help=(
            "Initial number of nearest placebo neighbors to inspect for each "
            "treatment author. The search expands automatically if needed."
        ),
    )
    parser.add_argument(
        "--volume-bins",
        type=int,
        default=DEFAULT_VOLUME_BINS,
        help=(
            "Number of event-relative posting-period blocks to create across "
            "the matching window. The default is three roughly trimester-sized blocks."
        ),
    )
    parser.add_argument(
        "--block-on",
        choices=["birth_quarter", "birth_year", "none"],
        default=DEFAULT_BLOCK_ON,
        help=(
            "Exact blocking variable used before nearest-neighbor matching. "
            "Use 'none' or 'birth_year' if birth-quarter blocking is too restrictive."
        ),
    )
    parser.add_argument(
        "--match-order",
        choices=["attachment_desc", "random"],
        default=DEFAULT_MATCH_ORDER,
        help=(
            "Order treatment authors within each block. 'attachment_desc' matches "
            "the hardest/highest-attachment treated authors first so scarce "
            "high-attachment placebo authors are not spent on easier cases."
        ),
    )
    parser.add_argument(
        "--with-replacement",
        action="store_true",
        default=DEFAULT_WITH_REPLACEMENT,
        help=(
            "Allow the same placebo author to match multiple treatment authors. "
            "Treatment authors are still excluded if no candidate is within "
            "--max-match-distance or other calipers."
        ),
    )
    parser.add_argument(
        "--max-placebo-reuse",
        type=int,
        default=DEFAULT_MAX_PLACEBO_REUSE,
        help=(
            "Maximum times any one placebo author may be reused when "
            "--with-replacement is set. For example, 5 or 10 prevents one "
            "very central placebo author from dominating the matched sample."
        ),
    )
    parser.add_argument(
        "--attachment-weight",
        type=float,
        default=DEFAULT_ATTACHMENT_WEIGHT,
        help=(
            "Weight for the composite attachment score in the match distance. "
            "Set to 0 to disable the composite score."
        ),
    )
    parser.add_argument(
        "--attachment-caliper",
        type=float,
        default=None,
        help=(
            "Optional maximum absolute gap in composite attachment score. "
            "Treated authors without a placebo inside this common-support band "
            "are left unmatched."
        ),
    )
    parser.add_argument(
        "--max-lower-attachment-gap",
        type=float,
        default=DEFAULT_MAX_LOWER_ATTACHMENT_GAP,
        help=(
            "One-sided common-support rule. Reject a placebo candidate if its "
            "attachment_score is more than this amount below the treated author's "
            "score. Use 0 for 'placebo cannot be less attached'; try 0.05 or 0.10 "
            "for a small tolerance."
        ),
    )
    parser.add_argument(
        "--directional-caliper",
        type=float,
        default=DEFAULT_DIRECTIONAL_CALIPER,
        help=(
            "Optional one-sided per-feature caliper, in robust treatment-scale "
            "units. Rejects controls that are too low on recent_total, active_weeks, "
            "mean_post_len, share_with_text, or top_sub_share, or too high on "
            "n_distinct_subs."
        ),
    )
    parser.add_argument(
        "--max-match-distance",
        type=float,
        default=None,
        help=(
            "Optional maximum weighted standardized distance. Treatment authors "
            "whose best available placebo is farther away are left unmatched."
        ),
    )
    parser.add_argument(
        "--skip-refresh-post-files",
        action="store_true",
        help="Only write feature and matched-author files; skip matched post exports.",
    )
    return parser.parse_args()


def output_paths(root: Path, suffix: str) -> dict[str, Path]:
    return {
        "treatment_features": root / f"treatment_match_features_{suffix}.csv",
        "placebo_features": root / f"placebo_match_features_{suffix}.csv",
        "matched_authors": root / f"matched_authors_{suffix}.csv",
        "matched_treatment_posts": root / f"matched_placebo_treatment_posts_{suffix}.csv",
        "matched_submissions": root / f"matched_placebo_submissions_{suffix}.csv",
    }


def print_volume_bins(volume_bins: list[VolumeBin]) -> None:
    print("volume bins for matching:")
    for spec in volume_bins:
        print(
            f"  weeks [{spec.lo}, {spec.hi}]: "
            f"{spec.count_feature} weight={spec.count_weight:.2f}; "
            f"{spec.active_feature} weight={spec.active_weight:.2f}"
        )


def week_label(week: int) -> str:
    if week < 0:
        return f"m{abs(week)}"
    if week > 0:
        return f"p{week}"
    return "0"


def make_volume_bins(window_lo: int, window_hi: int, n_bins: int) -> list[VolumeBin]:
    if window_hi < window_lo:
        raise ValueError(f"window_hi must be >= window_lo; got {window_hi} < {window_lo}")

    weeks = np.arange(window_lo, window_hi + 1)
    n_bins = min(max(n_bins, 1), len(weeks))
    chunks = [chunk for chunk in np.array_split(weeks, n_bins) if len(chunk) > 0]
    count_weights = np.linspace(1.4, 1.8, num=len(chunks))
    active_weights = np.linspace(1.0, 1.3, num=len(chunks))

    bins = []
    for chunk, count_weight, active_weight in zip(chunks, count_weights, active_weights):
        lo = int(chunk[0])
        hi = int(chunk[-1])
        suffix = f"w{week_label(lo)}_w{week_label(hi)}"
        bins.append(
            VolumeBin(
                count_feature=f"posts_{suffix}",
                active_feature=f"active_weeks_{suffix}",
                lo=lo,
                hi=hi,
                count_weight=float(count_weight),
                active_weight=float(active_weight),
            )
        )
    return bins


def matching_features(volume_bins: list[VolumeBin]) -> list[str]:
    features = []
    for spec in volume_bins:
        features.extend([spec.count_feature, spec.active_feature])
    features.extend(CONTENT_PLATFORM_FEATURES)
    return features


def feature_weights(volume_bins: list[VolumeBin]) -> dict[str, float]:
    weights = {}
    for spec in volume_bins:
        weights[spec.count_feature] = spec.count_weight
        weights[spec.active_feature] = spec.active_weight
    weights.update(CONTENT_PLATFORM_WEIGHTS)
    return weights


def diagnostic_features(volume_bins: list[VolumeBin]) -> list[str]:
    features = []
    for spec in volume_bins:
        features.extend([spec.count_feature, spec.active_feature])
    features.extend(RAW_DIAGNOSTIC_FEATURES)
    return features


def load_births(path: Path, cutoff_ts: float, label: str) -> pd.DataFrame:
    births = pd.read_csv(path, dtype={"author": str})
    births["birth_utc"] = pd.to_numeric(births["birth_utc"], errors="coerce")
    births = births.dropna(subset=["author", "birth_utc"])
    births = births[births["birth_utc"] < cutoff_ts][["author", "birth_utc"]]
    births = births.drop_duplicates("author", keep="first").reset_index(drop=True)
    print(f"{label} authors after cutoff: {len(births):,}")
    return births


def combine_grouped_series(
    pieces: list[pd.Series], nlevels: int, dtype: str = "float64"
) -> pd.Series:
    if not pieces:
        return pd.Series(dtype=dtype)
    out = pd.concat(pieces)
    return out.groupby(level=list(range(nlevels))).sum()


def empty_author_series(name: str, dtype: str = "float64") -> pd.Series:
    return pd.Series(dtype=dtype, name=name, index=pd.Index([], name="author"))


def post_text_features(window: pd.DataFrame) -> pd.DataFrame:
    title = window["title"].fillna("").astype(str)
    selftext = window["selftext"].fillna("").astype(str).str.strip()
    has_text = ~selftext.str.lower().isin(NO_TEXT_MARKERS)
    selftext_for_length = selftext.mask(~has_text, "")

    out = window[["author"]].copy()
    out["post_len"] = title.str.len().to_numpy() + selftext_for_length.str.len().to_numpy()
    out["has_text"] = has_text.astype(int).to_numpy()
    return out


def build_panel_artifacts(
    submissions_csv: Path,
    births: pd.DataFrame,
    label: str,
    window_lo: int,
    window_hi: int,
    volume_bins: list[VolumeBin],
    chunk_size: int,
) -> PanelArtifacts:
    birth_lookup = births.set_index("author")["birth_utc"]
    eligible_authors = set(birth_lookup.index)

    full18_authors: set[str] = set()
    global_week_counts: list[pd.Series] = []
    window_week_counts: list[pd.Series] = []
    window_author_sums: list[pd.DataFrame] = []
    subreddit_counts: list[pd.Series] = []

    usecols = ["author", "created_utc", "subreddit", "title", "selftext"]
    dtypes = {
        "author": str,
        "subreddit": str,
        "title": str,
        "selftext": str,
    }

    print(f"\nScanning {label} submissions: {submissions_csv}")
    rows_read = 0
    rows_kept = 0
    rows_in_window = 0

    for chunk_num, chunk in enumerate(
        pd.read_csv(
            submissions_csv,
            usecols=usecols,
            dtype=dtypes,
            chunksize=chunk_size,
            on_bad_lines="skip",
        ),
        start=1,
    ):
        rows_read += len(chunk)
        chunk = chunk[chunk["author"].isin(eligible_authors)].copy()
        if chunk.empty:
            if chunk_num % 10 == 0:
                print(f"  {label}: processed {rows_read:,} rows; kept {rows_kept:,}")
            continue

        chunk["created_utc"] = pd.to_numeric(chunk["created_utc"], errors="coerce")
        chunk = chunk.dropna(subset=["created_utc"])
        if chunk.empty:
            continue

        chunk["birth_utc"] = chunk["author"].map(birth_lookup)
        chunk["weeks"] = ((chunk["created_utc"] - chunk["birth_utc"]) / SECS_PER_WEEK).round()
        chunk = chunk.dropna(subset=["weeks"])
        chunk["weeks"] = chunk["weeks"].astype(int)

        rows_kept += len(chunk)
        full18_authors.update(chunk.loc[chunk["weeks"] <= -78, "author"].unique())
        global_week_counts.append(chunk.groupby(["author", "weeks"]).size())

        in_window = chunk["weeks"].between(window_lo, window_hi)
        if in_window.any():
            window = chunk.loc[in_window, usecols + ["weeks"]].copy()
            rows_in_window += len(window)

            window_week_counts.append(window.groupby(["author", "weeks"]).size())

            text_stats = post_text_features(window)
            author_sums = (
                text_stats.groupby("author")
                .agg(
                    window_posts=("author", "size"),
                    post_len_sum=("post_len", "sum"),
                    has_text_sum=("has_text", "sum"),
                )
                .astype({"window_posts": "int64", "post_len_sum": "int64", "has_text_sum": "int64"})
            )
            window_author_sums.append(author_sums)

            window["subreddit_clean"] = window["subreddit"].fillna("").astype(str).str.strip()
            with_sub = window[window["subreddit_clean"] != ""]
            if not with_sub.empty:
                subreddit_counts.append(with_sub.groupby(["author", "subreddit_clean"]).size())

        if chunk_num % 10 == 0:
            print(
                f"  {label}: processed {rows_read:,} rows; "
                f"kept {rows_kept:,}; in window {rows_in_window:,}"
            )

    all_week_counts = combine_grouped_series(global_week_counts, nlevels=2, dtype="int64")
    if all_week_counts.empty:
        max_per_week = empty_author_series("max_per_week", dtype="int64")
    else:
        max_per_week = all_week_counts.groupby(level="author").max()
    print(f"{label} authors with full_18_pre: {len(full18_authors):,} / {len(births):,}")
    print(f"{label} max-per-week describe:")
    print(max_per_week.describe())

    features = assemble_features(
        births=births,
        window_week_counts=window_week_counts,
        window_author_sums=window_author_sums,
        subreddit_counts=subreddit_counts,
        label=label,
        window_lo=window_lo,
        window_hi=window_hi,
        volume_bins=volume_bins,
    )

    del global_week_counts, window_week_counts, window_author_sums, subreddit_counts
    gc.collect()

    return PanelArtifacts(
        births=births,
        features=features,
        full18_authors=full18_authors,
        max_per_week=max_per_week,
    )


def assemble_features(
    births: pd.DataFrame,
    window_week_counts: list[pd.Series],
    window_author_sums: list[pd.DataFrame],
    subreddit_counts: list[pd.Series],
    label: str,
    window_lo: int,
    window_hi: int,
    volume_bins: list[VolumeBin],
) -> pd.DataFrame:
    week_counts = combine_grouped_series(window_week_counts, nlevels=2, dtype="int64")
    if week_counts.empty:
        recent_total = empty_author_series("recent_total")
        active_weeks = empty_author_series("active_weeks")
    else:
        wc = week_counts.rename("n_posts").reset_index()
        recent_total = wc.groupby("author")["n_posts"].sum().rename("recent_total")
        active_weeks = wc[wc["n_posts"] > 0].groupby("author").size().rename("active_weeks")

    volume_bin_series = []
    if week_counts.empty:
        for spec in volume_bins:
            volume_bin_series.append(empty_author_series(spec.count_feature))
            volume_bin_series.append(empty_author_series(spec.active_feature))
    else:
        for spec in volume_bins:
            in_bin = wc["weeks"].between(spec.lo, spec.hi)
            if in_bin.any():
                bin_counts = wc.loc[in_bin].groupby("author")["n_posts"].sum().rename(spec.count_feature)
                active_counts = wc.loc[in_bin].groupby("author").size().rename(spec.active_feature)
            else:
                bin_counts = empty_author_series(spec.count_feature)
                active_counts = empty_author_series(spec.active_feature)
            volume_bin_series.append(bin_counts)
            volume_bin_series.append(active_counts)

    if window_author_sums:
        author_sums = pd.concat(window_author_sums).groupby(level=0).sum()
        author_sums["mean_post_len"] = author_sums["post_len_sum"] / author_sums["window_posts"]
        author_sums["share_with_text"] = author_sums["has_text_sum"] / author_sums["window_posts"]
    else:
        author_sums = pd.DataFrame(
            columns=["window_posts", "post_len_sum", "has_text_sum", "mean_post_len", "share_with_text"],
            index=pd.Index([], name="author"),
        )

    sub_counts = combine_grouped_series(subreddit_counts, nlevels=2, dtype="int64")
    if sub_counts.empty:
        n_distinct_subs = empty_author_series("n_distinct_subs")
        top_sub_share = empty_author_series("top_sub_share")
    else:
        sub_totals = sub_counts.groupby(level="author").sum()
        n_distinct_subs = sub_counts.groupby(level="author").size().rename("n_distinct_subs")
        top_sub_share = (sub_counts.groupby(level="author").max() / sub_totals).rename("top_sub_share")

    starts = pd.to_datetime(births["birth_utc"], unit="s", utc=True).dt.tz_convert(None)
    quarters = starts.dt.to_period("Q")

    feat = births[["author", "birth_utc"]].copy()
    feat["birth_quarter"] = quarters.astype(str)
    feat["birth_year"] = starts.dt.year.astype(str)

    feat = (
        feat.merge(recent_total, on="author", how="left")
        .merge(active_weeks, on="author", how="left")
        .merge(n_distinct_subs, on="author", how="left")
        .merge(top_sub_share, on="author", how="left")
        .merge(author_sums[["mean_post_len", "share_with_text"]], on="author", how="left")
    )
    for series in volume_bin_series:
        feat = feat.merge(series, on="author", how="left")

    feat["recent_total"] = pd.to_numeric(feat["recent_total"], errors="coerce").fillna(0).astype(int)
    feat["active_weeks"] = pd.to_numeric(feat["active_weeks"], errors="coerce").fillna(0).astype(int)
    feat["n_distinct_subs"] = pd.to_numeric(feat["n_distinct_subs"], errors="coerce").fillna(0).astype(int)
    feat["top_sub_share"] = pd.to_numeric(feat["top_sub_share"], errors="coerce").fillna(0.0)
    feat["mean_post_len"] = pd.to_numeric(feat["mean_post_len"], errors="coerce").fillna(0.0)
    feat["share_with_text"] = pd.to_numeric(feat["share_with_text"], errors="coerce").fillna(0.0)

    for spec in volume_bins:
        feat[spec.count_feature] = (
            pd.to_numeric(feat[spec.count_feature], errors="coerce").fillna(0).astype(int)
        )
        feat[spec.active_feature] = (
            pd.to_numeric(feat[spec.active_feature], errors="coerce").fillna(0).astype(int)
        )

    print(f"\n{label} expanded features describe:")
    print(feat[diagnostic_features(volume_bins)].describe())
    return feat


def apply_author_filters(
    treatment: PanelArtifacts,
    placebo: PanelArtifacts,
    winsor_pctile: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    pooled = pd.concat([treatment.max_per_week, placebo.max_per_week], ignore_index=True)
    cap = int(np.ceil(pooled.quantile(winsor_pctile)))
    print(
        f"\npooled p{int(winsor_pctile * 100)} cap "
        f"(across full submission history): {cap} posts/author-week"
    )

    treatment_bots = set(treatment.max_per_week[treatment.max_per_week > cap].index)
    placebo_bots = set(placebo.max_per_week[placebo.max_per_week > cap].index)
    print(f"  treatment bots dropped: {len(treatment_bots):,}")
    print(f"  placebo   bots dropped: {len(placebo_bots):,}")

    treatment_keep = treatment.full18_authors - treatment_bots
    placebo_keep = placebo.full18_authors - placebo_bots
    print("\nafter both filters (full_18_pre AND not bot in any week):")
    print(f"  treatment: {len(treatment_keep):,} / {len(treatment.births):,}")
    print(f"  placebo:   {len(placebo_keep):,} / {len(placebo.births):,}")

    treatment_features = treatment.features[treatment.features["author"].isin(treatment_keep)].reset_index(drop=True)
    placebo_features = placebo.features[placebo.features["author"].isin(placebo_keep)].reset_index(drop=True)
    return treatment_features, placebo_features


def build_feature_frames(
    root: Path = ROOT,
    cutoff: str = DEFAULT_CUTOFF,
    window_lo: int = DEFAULT_WINDOW_LO,
    window_hi: int = DEFAULT_WINDOW_HI,
    volume_bins: list[VolumeBin] | None = None,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    winsor_pctile: float = DEFAULT_WINSOR_PCTILE,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Slow stage: scan raw submission CSVs and return filtered feature frames."""
    if volume_bins is None:
        volume_bins = make_volume_bins(window_lo, window_hi, DEFAULT_VOLUME_BINS)

    cutoff_ts = pd.Timestamp(cutoff).timestamp()
    treatment_births = load_births(root / "treatment_author_birth_dates.csv", cutoff_ts, "treatment")
    placebo_births = load_births(root / "candidate_placebo_birth_dates.csv", cutoff_ts, "placebo")

    treatment = build_panel_artifacts(
        submissions_csv=root / "births_2_3M_submissions.csv",
        births=treatment_births,
        label="treatment",
        window_lo=window_lo,
        window_hi=window_hi,
        volume_bins=volume_bins,
        chunk_size=chunk_size,
    )
    placebo = build_panel_artifacts(
        submissions_csv=root / "candidate_placebo_submissions.csv",
        births=placebo_births,
        label="placebo",
        window_lo=window_lo,
        window_hi=window_hi,
        volume_bins=volume_bins,
        chunk_size=chunk_size,
    )

    return apply_author_filters(
        treatment=treatment,
        placebo=placebo,
        winsor_pctile=winsor_pctile,
    )


def save_feature_frames(
    treatment_features: pd.DataFrame,
    placebo_features: pd.DataFrame,
    root: Path = ROOT,
    suffix: str = DEFAULT_OUTPUT_SUFFIX,
) -> None:
    output = output_paths(root, suffix)
    print("\nfinal feature file row counts:")
    print(f"  treatment: {len(treatment_features):,}")
    print(f"  placebo:   {len(placebo_features):,}")
    treatment_features.to_csv(output["treatment_features"], index=False)
    placebo_features.to_csv(output["placebo_features"], index=False)
    print(f"Saved -> {output['treatment_features']}")
    print(f"Saved -> {output['placebo_features']}")


def load_feature_frames(
    root: Path = ROOT,
    suffix: str = DEFAULT_OUTPUT_SUFFIX,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fast stage: load already-computed feature frames for repeated matching."""
    output = output_paths(root, suffix)
    dtype = {
        "author": str,
        "birth_quarter": str,
        "birth_year": str,
    }
    print(f"Loading treatment features -> {output['treatment_features']}")
    treatment_features = pd.read_csv(output["treatment_features"], dtype=dtype)
    print(f"Loading placebo features   -> {output['placebo_features']}")
    placebo_features = pd.read_csv(output["placebo_features"], dtype=dtype)
    print(f"Loaded treatment: {len(treatment_features):,} | placebo: {len(placebo_features):,}")
    return treatment_features, placebo_features


def require_feature_columns(
    treatment: pd.DataFrame,
    placebo: pd.DataFrame,
    columns: list[str],
) -> None:
    treatment_missing = [column for column in columns if column not in treatment.columns]
    placebo_missing = [column for column in columns if column not in placebo.columns]
    if treatment_missing or placebo_missing:
        pieces = []
        if treatment_missing:
            pieces.append(f"treatment missing {treatment_missing}")
        if placebo_missing:
            pieces.append(f"placebo missing {placebo_missing}")
        raise ValueError(
            "Feature cache is incompatible with this matching configuration: "
            + "; ".join(pieces)
            + ". Rebuild features with matching --window-* / --volume-bins settings."
        )


def clipped_robust_component(
    treatment: pd.DataFrame,
    df: pd.DataFrame,
    feature: str,
    clip: float = 3.0,
) -> pd.Series:
    values = pd.to_numeric(df[feature], errors="coerce")
    treatment_values = pd.to_numeric(treatment[feature], errors="coerce")
    center = treatment_values.median()
    q25 = treatment_values.quantile(0.25)
    q75 = treatment_values.quantile(0.75)
    scale = (q75 - q25) / 1.349
    if not np.isfinite(scale) or scale <= 0:
        scale = treatment_values.std()
    if not np.isfinite(scale) or scale <= 0:
        scale = 1.0
    return ((values - center) / scale).clip(-clip, clip).fillna(0.0)


def add_attachment_scores(
    treatment: pd.DataFrame,
    placebo: pd.DataFrame,
    component_weights: dict[str, float] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Add a one-dimensional score for platform/content attachment.

    Positive components mean "more attached / more treatment-like"; negative
    component weights reverse variables where lower values indicate a more
    core-community style, such as distinct subreddit count.
    """
    if component_weights is None:
        component_weights = ATTACHMENT_COMPONENT_WEIGHTS

    required = list(component_weights)
    require_feature_columns(treatment, placebo, required)

    treatment_scored = treatment.copy()
    placebo_scored = placebo.copy()
    denom = sum(abs(weight) for weight in component_weights.values())

    for target_df, source_df in [
        (treatment_scored, treatment),
        (placebo_scored, placebo),
    ]:
        score = pd.Series(0.0, index=target_df.index)
        for feature, weight in component_weights.items():
            score = score + weight * clipped_robust_component(
                treatment=treatment,
                df=source_df,
                feature=feature,
            ).to_numpy()
        target_df["attachment_score"] = score / denom

    print("\nattachment_score describe:")
    print("  treatment:")
    print(treatment_scored["attachment_score"].describe())
    print("  placebo:")
    print(placebo_scored["attachment_score"].describe())
    return treatment_scored, placebo_scored


def weighted_standardized_matrix(
    df: pd.DataFrame,
    features: list[str],
    center: pd.Series,
    scale: pd.Series,
    weights: dict[str, float],
) -> np.ndarray:
    standardized = ((df[features] - center) / scale).to_numpy(dtype=float)
    weight_vec = np.sqrt(np.array([weights.get(feature, 1.0) for feature in features], dtype=float))
    return standardized * weight_vec


def fit_robust_standardizer(df: pd.DataFrame, features: list[str]) -> tuple[pd.Series, pd.Series]:
    center = df[features].median()
    q25 = df[features].quantile(0.25)
    q75 = df[features].quantile(0.75)
    iqr_scale = (q75 - q25) / 1.349
    fallback_scale = df[features].std()
    scale = iqr_scale.where(iqr_scale > 0, fallback_scale)
    scale = scale.replace(0, 1.0).fillna(1.0)
    return center, scale


def nearest_unused(
    tree: cKDTree,
    point: np.ndarray,
    placebo_authors: np.ndarray,
    used_placebo: set[str],
    placebo_reuse_counts: dict[str, int] | None,
    max_placebo_reuse: int | None,
    initial_k: int,
    max_match_distance: float | None,
    target_attachment: float | None = None,
    placebo_attachment: np.ndarray | None = None,
    attachment_caliper: float | None = None,
    max_lower_attachment_gap: float | None = None,
    target_directional_values: np.ndarray | None = None,
    placebo_directional_values: np.ndarray | None = None,
    directional_signs: np.ndarray | None = None,
    directional_scales: np.ndarray | None = None,
    directional_caliper: float | None = None,
) -> tuple[str | None, float | None]:
    if len(placebo_authors) == 0:
        return None, None

    k = min(max(initial_k, 1), len(placebo_authors))
    while True:
        distances, indices = tree.query(point, k=k, workers=-1)
        distances = np.atleast_1d(distances)
        indices = np.atleast_1d(indices)

        for distance, idx in zip(distances, indices):
            if np.isinf(distance):
                continue
            if max_match_distance is not None and float(distance) > max_match_distance:
                return None, None
            if (
                attachment_caliper is not None
                and target_attachment is not None
                and placebo_attachment is not None
            ):
                attachment_gap = abs(float(placebo_attachment[int(idx)]) - target_attachment)
                if attachment_gap > attachment_caliper:
                    continue
            if (
                max_lower_attachment_gap is not None
                and target_attachment is not None
                and placebo_attachment is not None
            ):
                lower_gap = target_attachment - float(placebo_attachment[int(idx)])
                if lower_gap > max_lower_attachment_gap:
                    continue
            if (
                directional_caliper is not None
                and target_directional_values is not None
                and placebo_directional_values is not None
                and directional_signs is not None
                and directional_scales is not None
            ):
                candidate_values = placebo_directional_values[int(idx)]
                shortfall = directional_signs * (target_directional_values - candidate_values)
                allowed_shortfall = directional_caliper * directional_scales
                if np.any(shortfall > allowed_shortfall):
                    continue
            author = placebo_authors[int(idx)]
            if author not in used_placebo:
                if (
                    max_placebo_reuse is not None
                    and placebo_reuse_counts is not None
                    and placebo_reuse_counts.get(str(author), 0) >= max_placebo_reuse
                ):
                    continue
                return str(author), float(distance)

        if k >= len(placebo_authors):
            return None, None
        k = min(k * 2, len(placebo_authors))


def match_authors(
    treatment: pd.DataFrame,
    placebo: pd.DataFrame,
    features: list[str],
    weights: dict[str, float],
    raw_balance_features: list[str],
    block_on: str,
    match_order: str,
    with_replacement: bool,
    max_placebo_reuse: int | None,
    random_seed: int,
    neighbor_k: int,
    max_match_distance: float | None,
    attachment_caliper: float | None,
    max_lower_attachment_gap: float | None,
    directional_caliper: float | None,
) -> pd.DataFrame:
    print(f"\nTreatment: {len(treatment):,} | Placebo: {len(placebo):,}")
    overlap = set(treatment["author"]) & set(placebo["author"])
    print(f"overlap between treatment and placebo authors: {len(overlap):,} (should be 0 or small)")

    center, scale = fit_robust_standardizer(treatment, features)
    balance_sig = treatment[features].std().replace(0, 1.0).fillna(1.0)

    rng = np.random.default_rng(random_seed)
    forbidden_placebo = set(treatment["author"])
    used_placebo: set[str] = set()
    placebo_reuse_counts: dict[str, int] = {}
    all_matches: list[dict[str, object]] = []
    print(f"pre-excluded {len(forbidden_placebo):,} treatment authors from placebo pool")
    print(f"matching with replacement: {with_replacement}")
    if with_replacement and max_placebo_reuse is not None:
        print(f"maximum reuse per placebo author: {max_placebo_reuse:,}")
    print("\nweighted matching features:")
    for feature in features:
        print(f"  {feature}: weight={weights.get(feature, 1.0):.2f}")
    if max_match_distance is not None:
        print(f"maximum weighted match distance: {max_match_distance:.3f}")
    if attachment_caliper is not None:
        print(f"maximum absolute attachment_score gap: {attachment_caliper:.3f}")
    if max_lower_attachment_gap is not None:
        print(f"maximum one-sided lower attachment_score gap: {max_lower_attachment_gap:.3f}")

    directional_features = []
    directional_signs = None
    directional_scales = None
    if directional_caliper is not None:
        directional_features = [
            feature
            for feature in DIRECTIONAL_ATTACHMENT_FEATURES
            if feature in treatment.columns and feature in placebo.columns
        ]
        if not directional_features:
            raise ValueError("No directional-caliper features are available in both feature frames.")
        _, directional_scale_series = fit_robust_standardizer(treatment, directional_features)
        directional_signs = np.array(
            [DIRECTIONAL_ATTACHMENT_FEATURES[feature] for feature in directional_features],
            dtype=float,
        )
        directional_scales = directional_scale_series[directional_features].to_numpy(dtype=float)
        print(f"one-sided directional caliper: {directional_caliper:.3f} robust-scale units")
        for feature, sign, scale in zip(directional_features, directional_signs, directional_scales):
            direction_label = "not too low" if sign > 0 else "not too high"
            print(f"  {feature}: {direction_label}; raw scale={scale:.3f}")

    if block_on == "none":
        treatment_blocks = pd.Series(["all"] * len(treatment), index=treatment.index)
        placebo_blocks = pd.Series(["all"] * len(placebo), index=placebo.index)
    else:
        treatment_blocks = treatment[block_on]
        placebo_blocks = placebo[block_on]

    blocks = sorted(treatment_blocks.dropna().unique())
    print(f"blocks to match on {block_on}: {len(blocks)}")

    for block in blocks:
        t_q = treatment[treatment_blocks == block]
        blocked_authors = forbidden_placebo if with_replacement else (forbidden_placebo | used_placebo)
        p_q = placebo[
            (placebo_blocks == block)
            & (~placebo["author"].isin(blocked_authors))
        ]

        if len(p_q) == 0 or len(t_q) == 0:
            print(f"  {block}: t={len(t_q):,} p={len(p_q):,} - skipping")
            continue

        t_q = t_q.sample(frac=1, random_state=int(rng.integers(1 << 31)))
        if match_order == "attachment_desc" and "attachment_score" in t_q.columns:
            t_q = t_q.sort_values("attachment_score", ascending=False, kind="mergesort")
        t_q = t_q.reset_index(drop=True)
        p_q = p_q.reset_index(drop=True)
        placebo_authors = p_q["author"].to_numpy()
        placebo_lookup_cols = ["birth_quarter", "birth_utc"]
        if "attachment_score" in p_q.columns:
            placebo_lookup_cols.append("attachment_score")
        placebo_birth_lookup = p_q.set_index("author")[placebo_lookup_cols]
        placebo_attachment = (
            p_q["attachment_score"].to_numpy(dtype=float)
            if "attachment_score" in p_q.columns
            else None
        )
        placebo_directional_values = (
            p_q[directional_features].to_numpy(dtype=float)
            if directional_features
            else None
        )
        tree = cKDTree(weighted_standardized_matrix(p_q, features, center, scale, weights))
        t_points = weighted_standardized_matrix(t_q, features, center, scale, weights)

        matched_in_q = 0
        unmatched_in_q = 0

        for i, point in enumerate(t_points):
            unavailable_authors = forbidden_placebo if with_replacement else (forbidden_placebo | used_placebo)
            cand, distance = nearest_unused(
                tree=tree,
                point=point,
                placebo_authors=placebo_authors,
                used_placebo=unavailable_authors,
                placebo_reuse_counts=placebo_reuse_counts if with_replacement else None,
                max_placebo_reuse=max_placebo_reuse if with_replacement else None,
                initial_k=neighbor_k,
                max_match_distance=max_match_distance,
                target_attachment=(
                    float(t_q.loc[i, "attachment_score"])
                    if "attachment_score" in t_q.columns
                    else None
                ),
                placebo_attachment=placebo_attachment,
                attachment_caliper=attachment_caliper,
                max_lower_attachment_gap=max_lower_attachment_gap,
                target_directional_values=(
                    t_q.loc[i, directional_features].to_numpy(dtype=float)
                    if directional_features
                    else None
                ),
                placebo_directional_values=placebo_directional_values,
                directional_signs=directional_signs,
                directional_scales=directional_scales,
                directional_caliper=directional_caliper,
            )
            if cand is None or distance is None:
                unmatched_in_q += 1
                continue

            p_match = placebo_birth_lookup.loc[cand]
            match_row = {
                "treatment_author": t_q.loc[i, "author"],
                "placebo_author": cand,
                "match_distance": distance,
                "match_block": block,
                "birth_quarter": t_q.loc[i, "birth_quarter"],
                "birth_utc": t_q.loc[i, "birth_utc"],
                "placebo_birth_quarter": p_match["birth_quarter"],
                "placebo_birth_utc": p_match["birth_utc"],
            }
            if "attachment_score" in t_q.columns and "attachment_score" in p_match.index:
                match_row["treatment_attachment_score"] = t_q.loc[i, "attachment_score"]
                match_row["placebo_attachment_score"] = p_match["attachment_score"]
                match_row["attachment_score_gap"] = (
                    t_q.loc[i, "attachment_score"] - p_match["attachment_score"]
                )
            all_matches.append(match_row)
            used_placebo.add(cand)
            placebo_reuse_counts[cand] = placebo_reuse_counts.get(cand, 0) + 1
            matched_in_q += 1

        print(
            f"  {block}: t={len(t_q):,} p_avail={len(p_q):,} "
            f"matched={matched_in_q:,} unmatched={unmatched_in_q:,}"
        )

    matched = pd.DataFrame(
        all_matches,
        columns=[
            "treatment_author",
            "placebo_author",
            "match_distance",
            "match_block",
            "birth_quarter",
            "birth_utc",
            "placebo_birth_quarter",
            "placebo_birth_utc",
            "treatment_attachment_score",
            "placebo_attachment_score",
            "attachment_score_gap",
        ],
    )
    print_match_diagnostics(
        matched=matched,
        treatment=treatment,
        placebo=placebo,
        match_features=features,
        raw_balance_features=raw_balance_features,
        match_sig=balance_sig,
        with_replacement=with_replacement,
    )

    assert matched["treatment_author"].nunique() == len(matched), "1-to-1 violated"
    if not with_replacement:
        assert matched["placebo_author"].nunique() == len(matched), "1-to-1 violated"
    assert (set(matched["treatment_author"]) & set(matched["placebo_author"])) == set(), (
        "treatment and placebo author sets overlap in matched pairs"
    )
    return matched


def match_from_feature_frames(
    treatment_features: pd.DataFrame,
    placebo_features: pd.DataFrame,
    volume_bins: list[VolumeBin],
    block_on: str = DEFAULT_BLOCK_ON,
    match_order: str = DEFAULT_MATCH_ORDER,
    with_replacement: bool = DEFAULT_WITH_REPLACEMENT,
    max_placebo_reuse: int | None = DEFAULT_MAX_PLACEBO_REUSE,
    random_seed: int = DEFAULT_RANDOM_SEED,
    neighbor_k: int = DEFAULT_NEIGHBOR_K,
    max_match_distance: float | None = None,
    attachment_weight: float = DEFAULT_ATTACHMENT_WEIGHT,
    attachment_caliper: float | None = None,
    max_lower_attachment_gap: float | None = DEFAULT_MAX_LOWER_ATTACHMENT_GAP,
    directional_caliper: float | None = DEFAULT_DIRECTIONAL_CALIPER,
    weights: dict[str, float] | None = None,
) -> pd.DataFrame:
    """Fast stage: rerun matching using in-memory feature frames."""
    match_features = matching_features(volume_bins)
    raw_balance_features = diagnostic_features(volume_bins)
    if weights is None:
        weights = feature_weights(volume_bins)

    required = ["author", "birth_quarter", "birth_year", "birth_utc"] + sorted(
        set(match_features + raw_balance_features)
    )
    require_feature_columns(treatment_features, placebo_features, required)

    if (
        attachment_weight > 0
        or match_order == "attachment_desc"
        or attachment_caliper is not None
        or max_lower_attachment_gap is not None
    ):
        treatment_features, placebo_features = add_attachment_scores(
            treatment_features,
            placebo_features,
        )
        if attachment_weight > 0:
            match_features = match_features + ["attachment_score"]
            raw_balance_features = raw_balance_features + ["attachment_score"]
            weights = {**weights, "attachment_score": attachment_weight}

    return match_authors(
        treatment=treatment_features,
        placebo=placebo_features,
        features=match_features,
        weights=weights,
        raw_balance_features=raw_balance_features,
        block_on=block_on,
        match_order=match_order,
        with_replacement=with_replacement,
        max_placebo_reuse=max_placebo_reuse,
        random_seed=random_seed,
        neighbor_k=neighbor_k,
        max_match_distance=max_match_distance,
        attachment_caliper=attachment_caliper,
        max_lower_attachment_gap=max_lower_attachment_gap,
        directional_caliper=directional_caliper,
    )


def save_matched_authors(
    matched: pd.DataFrame,
    output_csv: Path,
    with_replacement: bool = DEFAULT_WITH_REPLACEMENT,
) -> None:
    matched.to_csv(output_csv, index=False)
    print(f"\nSaved -> {output_csv}")

    check = pd.read_csv(
        output_csv,
        dtype={"treatment_author": str, "placebo_author": str},
    )
    assert len(check) == len(matched), f"CSV roundtrip lost rows: {len(check)} vs {len(matched)}"
    assert check["treatment_author"].nunique() == len(check), "CSV roundtrip broke treatment uniqueness"
    if not with_replacement:
        assert check["placebo_author"].nunique() == len(check), "CSV roundtrip broke placebo uniqueness"
    print(
        f"roundtrip check passed: {len(check):,} rows, "
        f"{check['treatment_author'].nunique():,} unique treatment, "
        f"{check['placebo_author'].nunique():,} unique placebo"
    )


def print_match_diagnostics(
    matched: pd.DataFrame,
    treatment: pd.DataFrame,
    placebo: pd.DataFrame,
    match_features: list[str],
    raw_balance_features: list[str],
    match_sig: pd.Series,
    with_replacement: bool,
) -> None:
    print(f"\nTotal matched pairs: {len(matched):,}")
    if matched.empty:
        print("No matched pairs were created.")
        return

    print(f"  unique treatment authors: {matched['treatment_author'].nunique():,}")
    print(f"  unique placebo authors:   {matched['placebo_author'].nunique():,}")
    print(f"  treatment authors unmatched: {len(treatment) - len(matched):,}")
    if with_replacement:
        reuse_counts = matched["placebo_author"].value_counts()
        print(f"  placebo reuse allowed: yes")
        print(f"  max matches for one placebo author: {reuse_counts.max():,}")
        print(f"  placebo authors reused >1 time: {(reuse_counts > 1).sum():,}")
        top_reused = reuse_counts.head(10).rename_axis("author").reset_index(name="n_matches")
        reusable_features = [
            feature
            for feature in raw_balance_features
            if feature in placebo.columns
        ]
        cols = ["author"] + reusable_features
        print("  top reused placebo authors:")
        print(top_reused.merge(placebo[cols], on="author", how="left").to_string(index=False))
    else:
        print("  placebo reuse allowed: no")

    print("\nmatch_distance describe (std units):")
    print(matched["match_distance"].describe())
    print("  percentiles:")
    for p in [50, 75, 90, 95, 99, 99.9]:
        print(f"    p{p}: {matched['match_distance'].quantile(p / 100):.3f}")
    print(
        f"  matches with dist > 1.0 std: {(matched['match_distance'] > 1.0).sum():,} "
        f"({(matched['match_distance'] > 1.0).mean() * 100:.2f}%)"
    )

    block_col = "match_block" if "match_block" in matched.columns else "birth_quarter"
    print(f"\nmatch quality by {block_col} (median + p95 distance):")
    qstats = matched.groupby(block_col)["match_distance"].agg(
        n="count",
        median_dist="median",
        p95_dist=lambda x: x.quantile(0.95),
    )
    print(qstats.to_string())

    print("\nweighted-distance feature balance check (matched pairs only):")
    print_balance_table(matched, treatment, placebo, match_features, match_sig)

    raw_features = [feature for feature in raw_balance_features if feature in treatment.columns and feature in placebo.columns]
    raw_sig = treatment[raw_features].std().replace(0, 1.0).fillna(1.0)
    print("\ninterpretable raw-feature balance check (matched pairs only):")
    print_balance_table(matched, treatment, placebo, raw_features, raw_sig)
    print("  std_diff = (t_mean - p_mean) / treatment_std; |std_diff| < 0.1 is well-balanced")


def print_balance_table(
    matched: pd.DataFrame,
    treatment: pd.DataFrame,
    placebo: pd.DataFrame,
    features: list[str],
    sig: pd.Series,
) -> None:
    if not features:
        print("  no features available")
        return

    mt = matched.merge(
        treatment[["author"] + features],
        left_on="treatment_author",
        right_on="author",
    ).drop(columns="author")
    mp = matched.merge(
        placebo[["author"] + features],
        left_on="placebo_author",
        right_on="author",
    ).drop(columns="author")
    balance = pd.DataFrame(
        {
            "feature": features,
            "treatment_mean": [mt[f].mean() for f in features],
            "placebo_mean": [mp[f].mean() for f in features],
            "std_diff": [(mt[f].mean() - mp[f].mean()) / sig[f] for f in features],
        }
    )
    print(balance.to_string(index=False))


def write_filtered_csv_by_authors(
    input_csv: Path,
    output_csv: Path,
    authors: set[str],
    chunk_size: int,
    label: str,
) -> None:
    first_chunk = True
    total_rows = 0
    total_authors: set[str] = set()

    print(f"\nWriting {label}: {input_csv} -> {output_csv}")
    for chunk in pd.read_csv(
        input_csv,
        chunksize=chunk_size,
        dtype={"author": str},
        on_bad_lines="skip",
    ):
        filtered = chunk[chunk["author"].isin(authors)]
        if filtered.empty:
            continue

        filtered.to_csv(output_csv, mode="w" if first_chunk else "a", header=first_chunk, index=False)
        first_chunk = False
        total_rows += len(filtered)
        total_authors.update(filtered["author"].dropna().unique())

    if first_chunk:
        columns = pd.read_csv(input_csv, nrows=0).columns
        pd.DataFrame(columns=columns).to_csv(output_csv, index=False)

    print(f"  rows written: {total_rows:,}")
    print(f"  unique authors written: {len(total_authors):,}")


def refresh_matched_post_files(
    root: Path,
    matched: pd.DataFrame,
    output: dict[str, Path],
    chunk_size: int,
) -> None:
    matched_authors = set(matched["placebo_author"])
    print(f"\nmatched placebo authors: {len(matched_authors):,}")

    write_filtered_csv_by_authors(
        input_csv=root / "candidate_placebo_treatment_posts.csv",
        output_csv=output["matched_treatment_posts"],
        authors=matched_authors,
        chunk_size=chunk_size,
        label="matched placebo treatment posts",
    )
    write_filtered_csv_by_authors(
        input_csv=root / "candidate_placebo_submissions.csv",
        output_csv=output["matched_submissions"],
        authors=matched_authors,
        chunk_size=chunk_size,
        label="matched placebo submissions",
    )

    print("\nmatched post-file diagnostics:")
    mt_authors = set(
        pd.read_csv(output["matched_treatment_posts"], usecols=["author"], dtype={"author": str})["author"]
    )
    ms_authors = set(
        pd.read_csv(output["matched_submissions"], usecols=["author"], dtype={"author": str})["author"]
    )
    print(f"  expected unique authors: {len(matched_authors):,}")
    print(f"  treatment-post authors:  {len(mt_authors):,}")
    print(f"  submission authors:      {len(ms_authors):,}")
    print(f"  authors with NO treatment post: {len(matched_authors - mt_authors):,}")
    print(f"  authors with NO submissions:    {len(matched_authors - ms_authors):,}")

    per_author = (
        pd.read_csv(output["matched_submissions"], usecols=["author"], dtype={"author": str})
        .groupby("author")
        .size()
    )
    if not per_author.empty:
        print(
            f"  posts/author: median={per_author.median():.0f}, "
            f"p10={per_author.quantile(0.1):.0f}, "
            f"p90={per_author.quantile(0.9):.0f}, "
            f"max={per_author.max():,}"
        )


def main() -> None:
    args = parse_args()
    root = args.root
    match_output = output_paths(root, args.output_suffix)
    feature_suffix = args.feature_suffix or args.output_suffix
    volume_bins = make_volume_bins(args.window_lo, args.window_hi, args.volume_bins)
    print_volume_bins(volume_bins)

    if args.reuse_features:
        treatment_features, placebo_features = load_feature_frames(
            root=root,
            suffix=feature_suffix,
        )
    else:
        treatment_features, placebo_features = build_feature_frames(
            root=root,
            cutoff=args.cutoff,
            window_lo=args.window_lo,
            window_hi=args.window_hi,
            volume_bins=volume_bins,
            chunk_size=args.chunk_size,
            winsor_pctile=args.winsor_pctile,
        )
        save_feature_frames(
            treatment_features=treatment_features,
            placebo_features=placebo_features,
            root=root,
            suffix=feature_suffix,
        )

    if args.features_only:
        print("\nStopping before matching because --features-only was set.")
        return

    matched = match_from_feature_frames(
        treatment_features=treatment_features,
        placebo_features=placebo_features,
        volume_bins=volume_bins,
        block_on=args.block_on,
        match_order=args.match_order,
        with_replacement=args.with_replacement,
        max_placebo_reuse=args.max_placebo_reuse,
        random_seed=args.random_seed,
        neighbor_k=args.neighbor_k,
        max_match_distance=args.max_match_distance,
        attachment_weight=args.attachment_weight,
        attachment_caliper=args.attachment_caliper,
        max_lower_attachment_gap=args.max_lower_attachment_gap,
        directional_caliper=args.directional_caliper,
    )
    save_matched_authors(
        matched,
        match_output["matched_authors"],
        with_replacement=args.with_replacement,
    )

    if args.skip_refresh_post_files:
        print("\nSkipping matched post-file refresh because --skip-refresh-post-files was set.")
    else:
        refresh_matched_post_files(
            root=root,
            matched=matched,
            output=match_output,
            chunk_size=args.chunk_size,
        )


if __name__ == "__main__":
    main()
