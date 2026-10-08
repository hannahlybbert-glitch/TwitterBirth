# Author: Hannah Lybbert
# Updated: 2026-10-05
# Purpose: One-time cleanup -- move flat per_author_candidates/ files into bNNN/ bucket subfolders (safe to rerun)

import os
import re
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(os.environ.get("CONTROLGROUP_DATA_DIR", ROOT / "Reddit/ControlGroup/data"))
PER_AUTHOR_DIR = DATA_DIR / "per_author_candidates"

N_BUCKETS = 256   # ~1,560 authors per bucket (increased from 63 on 10/6/2026 to scale with 400k candidate authors), matches 2a/2b

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
