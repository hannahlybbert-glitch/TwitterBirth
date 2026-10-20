# Author: Hannah Lybbert
# Created: 2026-10-16
# Updated: 2026-10-16
# Purpose: Re-parse the saved anniversary batch output (bare "0\n90" replies were dropped as -99) into anniversary_tweets_RE_classified.csv

import json
import re
from pathlib import Path

import pandas as pd

ROOT         = Path(__file__).resolve().parents[2]
CLASSIFIED   = ROOT / "data/LLM/seed_tweets/anniversary_tweets_classified.csv"
BATCH_OUTPUT = ROOT / "data/LLM/json/batch_6ad132e0a79481908cebf7981a0055b1_output.jsonl"
OUTPUT       = ROOT / "data/LLM/seed_tweets/anniversary_tweets_RE_classified.csv"

MISSING_VALUE = -99
# optional "1:" / "2:" line label, then the value
LINE_RE = re.compile(r"^\s*(?:\d+\s*:)?\s*(-?\d+)")


# ----------------------------------------------------------------
# 1. Parse batch output
# ----------------------------------------------------------------
def parse_line(lines, i, valid):
    if len(lines) <= i:
        return None
    m = LINE_RE.match(lines[i])
    if not m:
        return None
    v = int(m.group(1))
    return v if valid(v) else None


def parse_output(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            rec = json.loads(line)
            content = None
            resp = rec.get("response") or {}
            if resp.get("status_code") == 200:
                choices = resp.get("body", {}).get("choices", [])
                if choices:
                    content = choices[0]["message"]["content"]
            lines = [l for l in (content or "").strip().splitlines() if l.strip()]
            flag = parse_line(lines, 0, lambda v: v in (0, 1))
            conf = parse_line(lines, 1, lambda v: 0 <= v <= 100)
            rows.append({
                "tweet_id":         str(rec["custom_id"]),
                "anniversary_flag": MISSING_VALUE if flag is None else flag,
                "confidence":       0 if conf is None else conf,
                "llm_response":     content,
            })
    out = pd.DataFrame(rows)
    assert out["tweet_id"].is_unique, "duplicate custom_ids in batch output"
    return out


# ----------------------------------------------------------------
# 2. Merge onto the original classified file
# ----------------------------------------------------------------
def main():
    orig = pd.read_csv(CLASSIFIED, dtype={"tweet_id": str, "author_id": str})
    parsed = parse_output(BATCH_OUTPUT)
    print(f"Loaded {len(orig):,} classified tweets and {len(parsed):,} batch responses")

    df = orig.drop(columns=["anniversary_flag", "confidence"]).merge(parsed, on="tweet_id", how="left")
    df["anniversary_flag"] = df["anniversary_flag"].fillna(MISSING_VALUE).astype(int)
    df["confidence"]       = df["confidence"].fillna(0).astype(int)

    print(f"  no batch response:   {df['llm_response'].isna().sum():,}")
    print(f"  still {MISSING_VALUE} after re-parse: {(df['anniversary_flag'] == MISSING_VALUE).sum():,}")
    unparsed = df.loc[(df["anniversary_flag"] == MISSING_VALUE) & df["llm_response"].notna(), "llm_response"]
    if len(unparsed):
        print("  examples of unparsed responses:", unparsed.head(5).tolist())

    print("\nOriginal flag (rows) vs re-parsed flag (columns):")
    print(pd.crosstab(orig["anniversary_flag"], df["anniversary_flag"], margins=True).to_string())

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUTPUT, index=False, encoding="utf-8")
    print(f"\nSaved {len(df):,} rows to {OUTPUT}")


if __name__ == "__main__":
    main()
