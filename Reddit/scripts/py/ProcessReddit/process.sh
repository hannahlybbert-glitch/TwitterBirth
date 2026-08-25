#!/bin/bash
# Reddit submissions descriptives pipeline — cluster runner
# Run from the reddit project root: sbatch scripts/py/ProcessReddit/process.sh
# Loops over every RS_*.zst file in $REDDIT_SUBMISSIONS_DIR (per-file step is
# resumable — files already profiled are skipped, so it's safe to resubmit
# if this run doesn't finish within the time limit), then aggregates all
# per-file outputs into macro-level descriptives.

#SBATCH --partition=standard
#SBATCH --account=ksrini0

#SBATCH --job-name=reddit_submissions_descriptives
#SBATCH --output=logs/reddit_descriptives_%j.out
#SBATCH --error=logs/reddit_descriptives_%j.err
#SBATCH --time=48:00:00
#SBATCH --mem=96G
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

# Site-specific data locations — read by 1_/2_ via os.environ.get(), with a
# repo-relative fallback for local runs. Update these if paths change.
export REDDIT_SUBMISSIONS_DIR=/nfs/turbo/si-ksrini/reddit/raw/submissions
export REDDIT_OUTPUT_DIR=/nfs/turbo/si-ksrini/reddit/output/ProcessReddit

echo "============================================"
echo "REDDIT SUBMISSIONS DESCRIPTIVES PIPELINE"
echo "Started at: $(date)"
echo "============================================"

# echo ""
# echo "Step 1: Profiling submissions files in $REDDIT_SUBMISSIONS_DIR"
# echo "(resumable — already-profiled files are skipped)"
# files=("$REDDIT_SUBMISSIONS_DIR"/RS_*.zst)
# echo "Found ${#files[@]} files"
# for f in "${files[@]}"; do
#     echo ""
#     echo "  -> $(basename "$f")"
#     "$PYTHON" scripts/py/ProcessReddit/1_profile_submissions_file.py "$f"
# done

echo ""
echo "Step 2: Aggregating per-file results into macro-level descriptives..."
"$PYTHON" scripts/py/ProcessReddit/2_aggregate_submissions_descriptives.py

echo ""
echo "============================================"
echo "PIPELINE COMPLETE"
echo "Finished at: $(date)"
echo "============================================"
