# Author: Hannah Lybbert
# Created: 2026-09-18
# Purpose: One-time cleanup -- move the files already sitting flat in
#          per_author_candidates/ into per-bucket subfolders (bNNN/), so the
#          directory stays browsable. A flat ~200k-entry directory chokes
#          OnDemand's web file browser with proxy timeouts, even though the
#          filesystem/data itself is fine (`ls -f | wc -l` works instantly from
#          a terminal -- this is a browsing problem, not a data problem).
#
# Bucket assignment matches bucket_of() in 2a_fetch_candidate_comments.py /
# 2b_fetch_candidate_submissions.py: hash(author) % N_BUCKETS. An author's
# comments and submissions files land in the same bucket folder, since the
# bucket only depends on the author name. Going forward, split_bucket() in both
# scripts writes new files directly into these subfolders -- this script only
# handles files written before that change existed.
#
# Safe to rerun: only touches files sitting directly in per_author_candidates/
# (never files already inside a bNNN/ subfolder), so if a fetch/split job is
# still writing new flat files concurrently, just run this again afterward to
# catch stragglers.
#
# Usage (from this file's directory, Reddit/ControlGroup/scripts/):
#   python reorganize_per_author_candidates.py
#
# Paths can be overridden:
#   CONTROLGROUP_DATA_DIR  (default: repo Reddit/ControlGroup/data)

import os
import re
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("CONTROLGROUP_DATA_DIR", ROOT / "Reddit/ControlGroup/data"))
PER_AUTHOR_DIR = DATA_DIR / "per_author_candidates"

N_BUCKETS = 64   # must match N_BUCKETS in 2a_fetch_candidate_comments.py / 2b_...

SUFFIX_RE = re.compile(r"_(comments|submissions)\.parquet$")


def bucket_of(author):
    return zlib.crc32(author.encode("utf-8")) % N_BUCKETS


def main():
    for b in range(N_BUCKETS):
        (PER_AUTHOR_DIR / f"b{b:03d}").mkdir(parents=True, exist_ok=True)

    files = [p for p in PER_AUTHOR_DIR.iterdir() if p.is_file() and SUFFIX_RE.search(p.name)]
    print(f"Found {len(files):,} flat files to reorganize in {PER_AUTHOR_DIR}")

    moved = 0
    for p in files:
        author = SUFFIX_RE.sub("", p.name)
        b = bucket_of(author)
        p.rename(PER_AUTHOR_DIR / f"b{b:03d}" / p.name)
        moved += 1
        if moved % 20_000 == 0:
            print(f"  ... moved {moved:,}/{len(files):,}")

    print(f"Done. Moved {moved:,} files into {N_BUCKETS} bucket subfolders under {PER_AUTHOR_DIR}")


if __name__ == "__main__":
    main()
