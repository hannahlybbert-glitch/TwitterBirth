#!/bin/bash
# Reddit submissions descriptives pipeline — cluster runner
# Run from project root: sbatch Reddit/scripts/py/ProcessReddit/process.sh
# Profiles every RS_*.zst file in Reddit/raw/submissions (per-file step is
# resumable — files already profiled are skipped, so it's safe to resubmit
# if this run doesn't finish within the time limit), then aggregates all
# per-file outputs into macro-level descriptives.

#SBATCH --partition=caslake
#SBATCH --account=si-ksrini

#SBATCH --job-name=reddit_submissions_descriptives
#SBATCH --output=logs/reddit_descriptives_%j.out
#SBATCH --error=logs/reddit_descriptives_%j.err
#SBATCH --time=48:00:00
#SBATCH --mem=64G
#SBATCH --cpus-per-task=1

set -euo pipefail

# TODO: confirm --partition / --account above are right for this project
# (copied from scripts/example_code/master.sh) and set the correct conda
# env below — needs pandas, pyarrow, and zstandard installed.
# module unload python
# module load python/anaconda-2024.10
# conda activate twitterproj

echo "============================================"
echo "REDDIT SUBMISSIONS DESCRIPTIVES PIPELINE"
echo "Started at: $(date)"
echo "============================================"

echo ""
echo "Step 1: Profiling all submissions files (resumable — already-profiled files are skipped)..."
python3 Reddit/scripts/py/ProcessReddit/1_profile_submissions_file.py

echo ""
echo "Step 2: Aggregating per-file results into macro-level descriptives..."
python3 Reddit/scripts/py/ProcessReddit/2_aggregate_submissions_descriptives.py

echo ""
echo "============================================"
echo "PIPELINE COMPLETE"
echo "Finished at: $(date)"
echo "============================================"
