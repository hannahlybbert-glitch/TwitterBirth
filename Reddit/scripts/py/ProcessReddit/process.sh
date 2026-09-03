#!/bin/bash
# Reddit descriptives pipeline — cluster runner (submissions + comments)
# Run from the reddit project root: sbatch scripts/py/ProcessReddit/process.sh
#
# Set MODE below to "submissions" or "comments" to pick which pipeline runs.
# Loops over every RS_*.zst / RC_*.zst file in the matching raw dir (the
# per-file step is resumable — files already profiled are skipped, so it's
# safe to resubmit if a run doesn't finish within the time limit), aggregates
# per-file outputs into macro-level descriptives, then builds condensed
# monthly/yearly rollups for easier digestion.
#
# NOTE on resources: Slurm parses #SBATCH lines statically at submit time,
# before any bash below runs — MODE can't drive --time/--mem the way it
# drives the python calls further down. Comments files run ~5x larger than
# submissions files for the same month (2.3GB vs 444MB compressed for
# 2012-12), so when you flip MODE, also flip which resource block below is
# commented out.

#SBATCH --partition=standard
#SBATCH --account=ksrini0

# --- Resources for MODE=submissions (uncomment this pair, comment the comments pair below) ---
# #SBATCH --time=48:00:00
# #SBATCH --mem=96G

# --- Resources for MODE=comments (uncomment this pair, comment the submissions pair above) ---
#SBATCH --time=120:00:00
#SBATCH --mem=128G

#SBATCH --job-name=reddit_descriptives
#SBATCH --output=logs/reddit_descriptives_%j.out
#SBATCH --error=logs/reddit_descriptives_%j.err
#SBATCH --cpus-per-task=1

set -euo pipefail
shopt -s nullglob

# Call the TwitterBirth env's Python by its full path instead of relying on
# `module load` + `conda activate` to win a PATH-ordering race in a
# non-interactive batch shell — that raced the wrong way last time (module's
# python3.10 ran instead of the env's python3.11, even though `conda
# activate` reported success), causing an ImportError for a package that
# was actually installed, just in the environment that didn't end up running.
PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3

# Slurm sends stdout to a file, where Python block-buffers its prints and the log
# looks frozen for long stretches. Force line-buffered output so each file's
# progress shows up as it happens.
export PYTHONUNBUFFERED=1

# ============================================================
# MODE toggle — "submissions" or "comments". Remember to also flip the
# matching #SBATCH resource block above.
# ============================================================
# MODE=submissions
MODE=comments

# Site-specific output location — read by 1_/2_/3_ via os.environ.get(), with
# a repo-relative fallback for local runs. Shared by both modes; each mode's
# scripts write to their own submissions_descriptives/ or comments_descriptives/
# subfolder under here. Update this if the path changes.
export REDDIT_OUTPUT_DIR=/nfs/turbo/si-ksrini/Reddit/data/ProcessReddit

echo "============================================"
echo "REDDIT DESCRIPTIVES PIPELINE ($MODE)"
echo "Started at: $(date)"
echo "============================================"

if [ "$MODE" = "submissions" ]; then
    export REDDIT_SUBMISSIONS_DIR=/nfs/turbo/si-ksrini/Reddit/raw/submissions

    echo ""
    echo "Step 1: Profiling submissions files in $REDDIT_SUBMISSIONS_DIR"
    echo "(resumable — a file that already has all three per-file outputs is skipped,"
    echo " so a restart picks up at the first unprofiled month)"
    per_file_dir="$REDDIT_OUTPUT_DIR/submissions_descriptives/per_file"
    files=("$REDDIT_SUBMISSIONS_DIR"/RS_*.zst)
    echo "Found ${#files[@]} files"
    for f in "${files[@]}"; do
        stem=$(basename "$f" .zst)
        if [ -f "$per_file_dir/${stem}__summary.json" ] \
           && [ -f "$per_file_dir/${stem}__subreddit_stats.csv" ] \
           && [ -f "$per_file_dir/${stem}__subreddit_authors.parquet" ]; then
            echo "  -> ${stem}.zst  already profiled, skipping"
            continue
        fi
        echo ""
        echo "  -> ${stem}.zst  ($(date '+%H:%M:%S'))"
        "$PYTHON" scripts/py/ProcessReddit/1_profile_submissions_file.py "$f"
    done

    echo ""
    echo "Step 2: Aggregating per-file results into macro-level descriptives..."
    "$PYTHON" scripts/py/ProcessReddit/2_aggregate_submissions_descriptives.py

    echo ""
    echo "Step 3: Building condensed monthly/yearly rollups (avg posts/author, yearly top subreddits)..."
    "$PYTHON" scripts/py/ProcessReddit/3_monthly_and_yearly_submissions_rollups.py

elif [ "$MODE" = "comments" ]; then
    export REDDIT_COMMENTS_DIR=/nfs/turbo/si-ksrini/Reddit/raw/comments

    echo ""
    echo "Step 1: Profiling comments files in $REDDIT_COMMENTS_DIR"
    echo "(resumable — a file that already has all three per-file outputs is skipped,"
    echo " so a restart picks up at the first unprofiled month)"
    per_file_dir="$REDDIT_OUTPUT_DIR/comments_descriptives/per_file"
    files=("$REDDIT_COMMENTS_DIR"/RC_*.zst)
    echo "Found ${#files[@]} files"
    for f in "${files[@]}"; do
        stem=$(basename "$f" .zst)
        if [ -f "$per_file_dir/${stem}__summary.json" ] \
           && [ -f "$per_file_dir/${stem}__subreddit_stats.csv" ] \
           && [ -f "$per_file_dir/${stem}__subreddit_authors.parquet" ]; then
            echo "  -> ${stem}.zst  already profiled, skipping"
            continue
        fi
        echo ""
        echo "  -> ${stem}.zst  ($(date '+%H:%M:%S'))"
        "$PYTHON" scripts/py/ProcessReddit/1_profile_comments_file.py "$f"
    done

    echo ""
    echo "Step 2: Aggregating per-file results into macro-level descriptives..."
    "$PYTHON" scripts/py/ProcessReddit/2_aggregate_comments_descriptives.py

    echo ""
    echo "Step 3: Building condensed monthly/yearly rollups (avg comments/author, yearly top subreddits)..."
    "$PYTHON" scripts/py/ProcessReddit/3_monthly_and_yearly_comments_rollups.py

else
    echo "Unknown MODE: $MODE (expected 'submissions' or 'comments')" >&2
    exit 1
fi

echo ""
echo "============================================"
echo "PIPELINE COMPLETE"
echo "Finished at: $(date)"
echo "============================================"
