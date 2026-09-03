# Author: Hannah Lybbert
# Created: 2026-08-31
# Purpose: Descriptives for the treatment-author comment history.
#
#          Memory-efficient: instead of loading the multi-GB combined file
#          (data/intermediate/comments/treatment_author_comments.parquet — every
#          column stored as a string, so it explodes in memory), this streams the
#          per-month shards written by pair_authors_comments.py:
#              data/intermediate/comments/treatment_author_comments/treatment_RC_YYYY-MM.parquet
#          one month at a time, holding only compact accumulators:
#            * per-author running stats (~45k authors)
#            * small integer histograms for the per-author-per-month cuts
#            * a global subreddit-volume Counter
#          If the shard dir is missing it falls back to streaming the combined
#          file row group by row group, buffering one calendar month at a time.
#
#          Console report:
#            1. head (first 5 rows)
#            2. unique authors, incl. the "established before birth" restriction
#               (>=1 comment 18+ months before birth: min months_from_birth <= -18)
#            3. comments per author per calendar month (avg/median/min/max):
#               [3a] conditional on the author being active that month;
#               [3b] with zeros filled for every month from the author's earliest
#                    comment (treatment_author_earliest_comment.csv) through the
#                    last month in the data — months before their first comment
#                    are excluded from the denominator
#            4. unique subreddits per author — lifetime and per calendar month
#            5. extra cuts (lifetime volume, tenure, pre/post-birth split, ...)
#
#          Also writes an author-level table to
#            data/descriptives/treatment_comments/author_level.csv
#
# Paths: same override convention as pair_authors_comments.py, so this runs
#        unchanged on the cluster:
#          REDDIT_INTERMEDIATE_DIR  dir holding comments/treatment_author_comments[/ ]
#                                   (default: repo Reddit/data/intermediate)
#          TREATMENT_AUTHORS_CSV    path to treatment_authors.csv
#
# Usage:
#   python scripts/py/descriptives/treatment_comments_descriptives.py
#   python scripts/py/descriptives/treatment_comments_descriptives.py --max-months 6   # quick test
#   python scripts/py/descriptives/treatment_comments_descriptives.py --combined       # force single-file stream

import argparse
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

ROOT             = Path(__file__).resolve().parents[4]
INTERMEDIATE_DIR = Path(os.environ.get("REDDIT_INTERMEDIATE_DIR", ROOT / "Reddit/data/intermediate"))
AUTHORS_CSV      = Path(os.environ.get("TREATMENT_AUTHORS_CSV", ROOT / "Reddit/data/final/treatment_authors.csv"))

COMMENTS_DIR    = INTERMEDIATE_DIR / "comments"
SHARD_DIR       = COMMENTS_DIR / "treatment_author_comments"
COMBINED_PARQUET = COMMENTS_DIR / "treatment_author_comments.parquet"
EARLIEST_COMMENT_CSV = COMMENTS_DIR / "treatment_author_earliest_comment.csv"
OUTPUT_DIR      = INTERMEDIATE_DIR.parent / "descriptives" / "treatment_comments"

PREBIRTH_MONTHS = 18                       # restriction threshold, see PART 2
USE_COLS        = ["author", "months_from_birth", "created_utc", "subreddit", "id", "body"]
SHARD_RE        = re.compile(r"RC_(\d{4})-(\d{2})")

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 200)


# ================================================================
# helpers
# ================================================================
def banner(title):
    print("\n" + "=" * 78 + f"\n{title}\n" + "=" * 78, flush=True)


def month_ordinal(year, month):
    return year * 12 + (month - 1)


def _wq(vals, wts, q):
    """Nearest-rank weighted quantile. vals/wts need not be sorted."""
    vals = np.asarray(vals, float)
    wts  = np.asarray(wts, float)
    order = np.argsort(vals)
    vals, wts = vals[order], wts[order]
    cw = np.cumsum(wts)
    n = cw[-1]
    if n <= 0:
        return float("nan")
    k = int(np.searchsorted(cw, q * n, side="left"))
    return float(vals[min(k, len(vals) - 1)])


def summarize_array(label, a):
    a = np.asarray(a, float)
    a = a[~np.isnan(a)]
    if a.size == 0:
        print(f"{label}\n    (no data)")
        return
    print(
        f"{label}\n"
        f"    n      = {a.size:,}\n"
        f"    mean   = {a.mean():,.2f}\n"
        f"    median = {np.median(a):,.2f}\n"
        f"    min    = {a.min():,.2f}\n"
        f"    max    = {a.max():,.2f}\n"
        f"    p90/p95/p99 = {np.quantile(a, .9):,.1f} / {np.quantile(a, .95):,.1f} / {np.quantile(a, .99):,.1f}"
    )


def summarize_hist(label, counter, note=""):
    if not counter:
        print(f"{label}\n    (no data)")
        return
    vals = np.array(sorted(counter), float)
    wts  = np.array([counter[int(v)] for v in vals], float)
    n = wts.sum()
    mean = float((vals * wts).sum() / n)
    print(
        f"{label}\n"
        f"    n      = {int(n):,}\n"
        f"    mean   = {mean:,.2f}\n"
        f"    median = {_wq(vals, wts, .5):,.2f}\n"
        f"    min    = {vals[0]:,.2f}\n"
        f"    max    = {vals[-1]:,.2f}\n"
        f"    p90/p95/p99 = {_wq(vals, wts, .9):,.1f} / {_wq(vals, wts, .95):,.1f} / {_wq(vals, wts, .99):,.1f}"
        f"  [nearest-rank{'; ' + note if note else ''}]"
    )


# ================================================================
# month-chunk iterator: yields (label 'YYYY-MM', month_ordinal, DataFrame)
# ================================================================
def iter_month_chunks(use_combined, max_months):
    shards = sorted(SHARD_DIR.glob("treatment_RC_*.parquet")) if SHARD_DIR.exists() else []

    if shards and not use_combined:
        if max_months:
            shards = shards[:max_months]
        print(f"Streaming {len(shards):,} monthly shards from {SHARD_DIR}", flush=True)
        for f in shards:
            m = SHARD_RE.search(f.name)
            y, mo = int(m.group(1)), int(m.group(2))
            yield f"{y:04d}-{mo:02d}", month_ordinal(y, mo), pd.read_parquet(f, columns=USE_COLS)
        return

    # fallback: stream the combined file, buffering consecutive same-month row groups
    if not COMBINED_PARQUET.exists():
        raise SystemExit(
            f"No shards in {SHARD_DIR} and no combined file at {COMBINED_PARQUET}.\n"
            f"Run pair_authors_comments.py first, or set REDDIT_INTERMEDIATE_DIR."
        )
    print(f"Streaming row groups from {COMBINED_PARQUET} (no shard dir found)", flush=True)
    pf = pq.ParquetFile(COMBINED_PARQUET)
    buf, buf_key, emitted = [], None, 0
    for i in range(pf.num_row_groups):
        df = pf.read_row_group(i, columns=USE_COLS).to_pandas()
        ep = pd.to_numeric(df["created_utc"], errors="coerce")
        per = pd.to_datetime(ep, unit="s", errors="coerce").dt.to_period("M")
        mode = per.mode(dropna=True)
        key = str(mode.iloc[0]) if len(mode) else buf_key or "1970-01"
        if buf_key is None or key == buf_key:
            buf.append(df)
            buf_key = buf_key or key
        else:
            y, mo = map(int, buf_key.split("-"))
            yield buf_key, month_ordinal(y, mo), pd.concat(buf, ignore_index=True)
            emitted += 1
            if max_months and emitted >= max_months:
                return
            buf, buf_key = [df], key
    if buf:
        y, mo = map(int, buf_key.split("-"))
        yield buf_key, month_ordinal(y, mo), pd.concat(buf, ignore_index=True)


# ================================================================
# main
# ================================================================
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--combined", action="store_true", help="stream the single combined file instead of the shards")
    ap.add_argument("--max-months", type=int, default=None, help="only process the first N months (quick test)")
    args = ap.parse_args()

    # ---- PART 1: head ------------------------------------------------------
    banner("PART 1 — head (first 5 rows, all columns)")
    head_src = COMBINED_PARQUET if COMBINED_PARQUET.exists() else next(
        iter(sorted(SHARD_DIR.glob("treatment_RC_*.parquet"))), None
    )
    if head_src is None:
        raise SystemExit(f"Nothing to read under {COMMENTS_DIR}")
    pf_head = pq.ParquetFile(head_src)
    head_df = pa.Table.from_batches([next(pf_head.iter_batches(batch_size=5))]).to_pandas()
    print(head_df.to_string())
    print(f"\n(head read from {head_src.name}; that file has {pf_head.metadata.num_rows:,} rows, "
          f"{pf_head.metadata.num_row_groups} row groups, {pf_head.metadata.num_columns} columns)")

    # ---- accumulators ---------------------------------------------------------
    # per author: [n_comments, n_months_active, first_ord, last_ord, min_mfb, max_mfb]
    AUTH      = {}
    AUTH_SUBS = {}                              # author -> set of (interned) subreddit names
    SUB_POOL  = {}                              # intern subreddit strings so the sets share objects

    comments_per_month_hist = Counter()        # comments-in-a-month -> # of (author, month) cells
    subs_per_month_hist     = Counter()        # distinct subs-in-a-month -> # of (author, month) cells
    sub_volume              = Counter()        # subreddit -> total comments
    months_spanned          = set()
    bucket_authors          = defaultdict(set) # floor(months_from_birth) -> set of authors active then

    n_rows = n_bad_epoch = n_null_mfb = n_dup_ids_in_grp = 0
    n_body_deleted = n_body_blank = 0
    c_pre = c_post = 0
    epoch_min = np.inf
    epoch_max = -np.inf
    mfb_min = np.inf
    mfb_max = -np.inf
    max_m_ord = -(10 ** 9)                     # latest calendar month seen (for the [3b] window end)
    DELETED = {"[deleted]", "[removed]"}

    # ---- stream ------------------------------------------------------------
    for i, (label, m_ord, df) in enumerate(iter_month_chunks(args.combined, args.max_months), 1):
        df = df[df["author"].notna()]
        if df.empty:
            continue
        n_rows += len(df)
        max_m_ord = max(max_m_ord, m_ord)

        # intern this month's subreddits, then map to shared objects
        subs = df["subreddit"]
        for s in subs.dropna().unique():
            SUB_POOL.setdefault(s, s)
        sub_i = subs.map(SUB_POOL)

        epoch = pd.to_numeric(df["created_utc"], errors="coerce")
        n_bad_epoch += int(epoch.isna().sum())
        if epoch.notna().any():
            epoch_min = min(epoch_min, float(epoch.min()))
            epoch_max = max(epoch_max, float(epoch.max()))
        per = pd.to_datetime(epoch, unit="s", errors="coerce").dt.to_period("M")
        months_spanned.update(str(p) for p in per.dropna().unique())

        mfb = pd.to_numeric(df["months_from_birth"], errors="coerce").astype("float64")
        n_null_mfb += int(mfb.isna().sum())
        if mfb.notna().any():
            mfb_min = min(mfb_min, float(np.nanmin(mfb)))
            mfb_max = max(mfb_max, float(np.nanmax(mfb)))
        c_pre  += int((mfb < 0).sum())
        c_post += int((mfb >= 0).sum())

        body = df["body"]
        n_body_deleted += int(body.isin(DELETED).sum())
        n_body_blank   += int(body.fillna("").astype(str).str.strip().eq("").sum())
        n_dup_ids_in_grp += int(df["id"].duplicated().sum())

        sub_volume.update(sub_i.dropna().value_counts().to_dict())

        work = pd.DataFrame({"author": df["author"].to_numpy(),
                             "sub": sub_i.to_numpy(),
                             "mfb": mfb.to_numpy()})
        gb = work.groupby("author", sort=False)

        for author, c in gb.size().items():
            rec = AUTH.get(author)
            if rec is None:
                AUTH[author] = [int(c), 1, m_ord, m_ord, np.nan, np.nan]
                AUTH_SUBS[author] = set()
            else:
                rec[0] += int(c)
                rec[1] += 1
                rec[3] = m_ord
            comments_per_month_hist[int(c)] += 1

        for author, k in gb["sub"].nunique().items():
            subs_per_month_hist[int(k)] += 1

        gmin = gb["mfb"].min()
        gmax = gb["mfb"].max()
        for author, v in gmin.items():
            if pd.notna(v):
                rec = AUTH[author]
                rec[4] = v if np.isnan(rec[4]) else min(rec[4], v)
        for author, v in gmax.items():
            if pd.notna(v):
                rec = AUTH[author]
                rec[5] = v if np.isnan(rec[5]) else max(rec[5], v)

        for author, sset in gb["sub"].agg(lambda s: frozenset(s.dropna())).items():
            AUTH_SUBS[author].update(sset)

        bwork = work[["author"]].copy()
        bwork["b"] = np.floor(work["mfb"].to_numpy())
        bwork = bwork.dropna(subset=["b"])
        for b, grp in bwork.groupby("b")["author"]:
            bucket_authors[int(b)].update(grp.unique())

        if i % 24 == 0:
            print(f"  ... {i} months, {n_rows:,} comments, {len(AUTH):,} authors so far", flush=True)

    if not AUTH:
        raise SystemExit("No comments found in any month.")

    # ---- finalize per-author arrays -------------------------------------------
    authors  = list(AUTH)
    arr      = np.array([AUTH[a] for a in authors], dtype=float)   # (N, 6)
    n_comments      = arr[:, 0]
    n_months_active = arr[:, 1]
    first_ord       = arr[:, 2]
    last_ord        = arr[:, 3]
    min_mfb         = arr[:, 4]
    max_mfb         = arr[:, 5]
    tenure          = last_ord - first_ord + 1
    subs_lifetime   = np.array([len(AUTH_SUBS[a]) for a in authors], dtype=float)
    n_authors       = len(authors)

    # ---- OVERVIEW -----------------------------------------------------------
    banner("OVERVIEW")
    print(f"rows (comments)          : {n_rows:,}")
    print(f"unique authors           : {n_authors:,}")
    print(f"unique subreddits        : {len(sub_volume):,}")
    if np.isfinite(epoch_min):
        print(f"comment date range       : {pd.Timestamp(epoch_min, unit='s')}  ->  {pd.Timestamp(epoch_max, unit='s')}")
    print(f"calendar months spanned  : {len(months_spanned):,}")
    print(f"birth-relative month rng : {mfb_min:.0f}  ->  {mfb_max:.0f}")
    print(f"unparseable created_utc  : {n_bad_epoch:,} ({n_bad_epoch / n_rows:.2%})")
    print(f"null months_from_birth   : {n_null_mfb:,} ({n_null_mfb / n_rows:.2%})")
    print(f"dup comment ids (within a row group; not a global check) : {n_dup_ids_in_grp:,}")
    print(f"body == [deleted]/[removed]: {n_body_deleted / n_rows:.2%}")
    print(f"body blank                : {n_body_blank / n_rows:.2%}")

    if AUTHORS_CSV.exists():
        roster = (
            pd.read_csv(AUTHORS_CSV, usecols=["author"])
            .dropna(subset=["author"]).drop_duplicates(subset="author")
        )
        seen = set(authors)
        have = int(roster["author"].isin(seen).sum())
        print(f"\ntreatment roster         : {len(roster):,} authors")
        print(f"  with >=1 comment here  : {have:,} ({have / len(roster):.1%})")
        print(f"  with zero comments     : {len(roster) - have:,}")
    else:
        print(f"\n(treatment roster not found at {AUTHORS_CSV} — skipping coverage check)")

    # ---- PART 2 ----------------------------------------------------------------
    banner(f"PART 2 — unique authors (restriction: a comment >= {PREBIRTH_MONTHS} months before birth)")
    n_restricted = int(np.sum(min_mfb <= -PREBIRTH_MONTHS))    # NaN compares False
    print(f"all unique authors                                         : {n_authors:,}")
    print(f"restricted (min months_from_birth <= -{PREBIRTH_MONTHS})               : "
          f"{n_restricted:,} ({n_restricted / n_authors:.1%})")

    # ---- PART 3 ----------------------------------------------------------------
    banner("PART 3 — comments per author per calendar month")
    summarize_hist("[3a] conditional on the author being active that month", comments_per_month_hist)

    # [3b] denominator: an author is "in the sample" for every calendar month from
    # their earliest-ever comment month (from treatment_author_earliest_comment.csv)
    # through the last calendar month present in the data — inclusive, zeros filled.
    # Months before an author's first comment are NOT counted.
    if EARLIEST_COMMENT_CSV.exists():
        ec = pd.read_csv(EARLIEST_COMMENT_CSV, usecols=["author", "earliest_comment_epoch"])
        ec_dt = pd.to_datetime(ec["earliest_comment_epoch"], unit="s", errors="coerce")
        entry_by_author = dict(zip(ec["author"], (ec_dt.dt.year * 12 + ec_dt.dt.month - 1)))
        n_from_csv = sum(a in entry_by_author and pd.notna(entry_by_author[a]) for a in authors)
        print(f"    [3b] entry month from {EARLIEST_COMMENT_CSV.name} for "
              f"{n_from_csv:,}/{n_authors:,} authors (rest fall back to first observed comment month)")
    else:
        entry_by_author = {}
        print(f"    [3b] {EARLIEST_COMMENT_CSV.name} not found — using each author's first observed comment month")

    entry_ord = np.array(
        [entry_by_author.get(a, np.nan) for a in authors], dtype=float
    )
    entry_ord = np.where(np.isnan(entry_ord), first_ord, entry_ord)      # fallback
    window_len = np.maximum(max_m_ord - entry_ord + 1, n_months_active)  # >= active, guards odd cases

    total_window = int(window_len.sum())
    total_active = int(n_months_active.sum())
    total_gap    = total_window - total_active
    hist_3b = Counter(comments_per_month_hist)
    hist_3b[0] += total_gap
    last_month_lbl = f"{int(max_m_ord // 12):04d}-{int(max_m_ord % 12) + 1:02d}"
    summarize_hist(f"[3b] from each author's earliest comment month through {last_month_lbl} "
                   f"(zeros filled; pre-entry months excluded)", hist_3b)
    print(f"    (author-months in denominator: {total_window:,}; "
          f"share with zero comments: {total_gap / total_window:.1%})")

    # ---- PART 4 ----------------------------------------------------------------
    banner("PART 4 — unique subreddits per author")
    summarize_array("[4a] distinct subreddits over the author's whole comment history", subs_lifetime)
    summarize_hist("[4b] distinct subreddits per active calendar month", subs_per_month_hist)

    # ---- PART 5 ----------------------------------------------------------------
    banner("PART 5 — extra cuts")
    summarize_array("[5a] comments per author (lifetime, heavy-tailed)", n_comments)
    summarize_array("[5b] active calendar months per author", n_months_active)
    summarize_array("[5c] observed tenure (first..last active month, in months)", tenure)
    summarize_array("[5d] first comment's months_from_birth (how far back history reaches)", min_mfb)
    summarize_array("[5e] last comment's months_from_birth (how long after birth we see them)", max_mfb)

    n_any_pre  = int(np.sum(min_mfb < 0))
    n_any_post = int(np.sum(max_mfb >= 0))
    n_both     = int(np.sum((min_mfb < 0) & (max_mfb >= 0)))
    tot = c_pre + c_post
    print("\n[5f] pre/post birth split")
    print(f"    comments before birth (mfb < 0) : {c_pre:,} ({c_pre / tot:.1%})")
    print(f"    comments at/after birth (mfb>=0) : {c_post:,} ({c_post / tot:.1%})")
    print(f"    authors with any pre-birth comment  : {n_any_pre:,}")
    print(f"    authors with any post-birth comment : {n_any_post:,}")
    print(f"    authors observed on both sides      : {n_both:,}")

    print("\n[5g] unique authors active at each birth-relative month (event-time coverage)")
    for m in range(-24, 25, 3):
        print(f"    month {m:>4} : {len(bucket_authors.get(m, ())):,} authors")

    print("\n[5h] top 15 subreddits by comment volume")
    for name, cnt in sub_volume.most_common(15):
        print(f"    {name:<30} {cnt:,}")

    # ---- author-level table --------------------------------------------------
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    entry_lbl = [f"{int(o // 12):04d}-{int(o % 12) + 1:02d}" if np.isfinite(o) else pd.NA
                 for o in entry_ord]
    out = pd.DataFrame({
        "author":                authors,
        "n_comments":            n_comments.astype("int64"),
        "n_months_active":       n_months_active.astype("int64"),
        "tenure_months":         np.where(np.isnan(tenure), pd.NA, tenure),
        "entry_month":           entry_lbl,                                  # [3b] window start
        "months_in_sample":      window_len.astype("int64"),                # [3b] denominator per author
        "zero_comment_months":   (window_len - n_months_active).astype("int64"),
        "n_subreddits_lifetime": subs_lifetime.astype("int64"),
        "min_months_from_birth": np.where(np.isnan(min_mfb), pd.NA, min_mfb),
        "max_months_from_birth": np.where(np.isnan(max_mfb), pd.NA, max_mfb),
    })
    out_csv = OUTPUT_DIR / "author_level.csv"
    out.to_csv(out_csv, index=False)
    print(f"\nSaved author-level table ({len(out):,} rows) -> {out_csv}")


if __name__ == "__main__":
    main()
