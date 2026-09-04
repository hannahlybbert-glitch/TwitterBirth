#!/bin/bash
# Master script for the Reddit control-group pipeline.
# Run from the Reddit project root: sbatch ControlGroup/scripts/master.sh
# Comment/uncomment steps below as they are completed.

#SBATCH --partition=standard
#SBATCH --account=ksrini0

#SBATCH --job-name=control_group_reddit
#SBATCH --output=logs/control_group_reddit_%j.out
#SBATCH --error=logs/control_group_reddit_%j.err
#SBATCH --time=24:00:00      # ~10-14h serial over ~154 monthly RS_*.zst; ceiling (chunks are resumable)
#SBATCH --mem=16G            # peak ~3G on the largest months; headroom for high-volume years
#SBATCH --cpus-per-task=1

set -euo pipefail

# Full path to the TwitterBirth env's Python (don't rely on module/conda PATH in a
# non-interactive batch shell). -u keeps stdout unbuffered so per-month progress
# lines stream to the log as they happen.
PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3

# Cluster data layout (read by the .py via os.environ.get with repo-relative fallbacks).
export REDDIT_SUBMISSIONS_DIR=/nfs/turbo/si-ksrini/Reddit/raw/submissions
export TREATMENT_AUTHORS_CSV=/nfs/turbo/si-ksrini/Reddit/data/final/treatment_authors.csv
export BIRTH_DATE_DIST_CSV=/nfs/turbo/si-ksrini/Reddit/data/descriptives/date_birth_dist_full.csv
export CONTROLGROUP_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/ControlGroup/data

mkdir -p logs

echo "============================================"
echo "MASTER CONTROL PIPELINE"
echo "Started at: $(date)"
echo "============================================"

# Step 1: Draw random candidate authors
echo ""
"$PYTHON" -u ControlGroup/scripts/1_sample_candidate_pool.py

# # Step 2a: Fetch candidate authors' comment history
# echo ""
# "$PYTHON" -u ControlGroup/scripts/2a_fetch_candidate_comments.py

# # Step 2b: Fetch candidate authors' submission history
# echo ""
# "$PYTHON" -u ControlGroup/scripts/2b_fetch_candidate_submissions.py

echo ""
echo "============================================"
echo "PIPELINE COMPLETE"
echo "Finished at: $(date)"
echo "============================================"
