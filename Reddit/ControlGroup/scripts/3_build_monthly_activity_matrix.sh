#!/bin/bash
# Assign placebo births and build the 18-month pre-birth volume vectors + matching
# features -- cluster runner (Slurm array).
# Must run AFTER 2_split_candidate_buckets.sh has finished (reads the per-author
# files under per_author_candidates/bNNN/), and after
# scripts/py/descriptives/full_sample_descriptives.py has written days_from_dist_full.csv.
#
# Run from the Reddit project root:
#     sbatch ControlGroup/scripts/3_build_monthly_activity_matrix.sh
#
# One array task per bucket folder (0-63): each writes
#     Reddit/ControlGroup/data/3_candidate_volume_chunks/{comments,submissions}_bNNN.parquet
#
# Once every task has finished, combine the chunks into the deliverables
# (3a_candidate_comment_volume.parquet / 3b_candidate_submission_volume.parquet)
# and print the funnel. This is small (64 files, ~100k rows) -- fine to run directly:
#     CONTROLGROUP_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/ControlGroup/data \
#       /home/hlybbert/.conda/envs/TwitterBirth/bin/python3 \
#       ControlGroup/scripts/3_build_monthly_activity_matrix.py --combine-only
#
# A bucket already marked done is skipped, so a partly-finished array can be
# resubmitted as-is (the .py doesn't self-skip in single-bucket mode).

#SBATCH --partition=standard
#SBATCH --account=ksrini0
#SBATCH --time=01:00:00
#SBATCH --mem=16G           # holds one bucket's full lifetime activity (~1,500 authors) in memory
#SBATCH --cpus-per-task=1
#SBATCH --job-name=build_candidate_volume
#SBATCH --output=logs/build_candidate_volume_%A_%a.out
#SBATCH --error=logs/build_candidate_volume_%A_%a.err
# N_BUCKETS in 3_build_monthly_activity_matrix.py is 64 -- keep this in sync.
# %16 caps concurrency since every task reads ~3,000 small files off the same share.
#SBATCH --array=0-63%16

set -euo pipefail

PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3

export CONTROLGROUP_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/ControlGroup/data
export DAYS_FROM_DIST_CSV=/nfs/turbo/si-ksrini/Reddit/data/descriptives/days_from_dist_full.csv

: "${SLURM_ARRAY_TASK_ID:?must be run as a Slurm array job}"

B=$SLURM_ARRAY_TASK_ID
BNNN=$(printf "%03d" "$B")

MARKER="$CONTROLGROUP_DATA_DIR/3_candidate_volume_chunks/.done_b${BNNN}"

echo "============================================"
echo "Task $SLURM_ARRAY_TASK_ID -> bucket $BNNN"
echo "Started at: $(date)"
echo "============================================"

if [ -f "$MARKER" ]; then
    echo "bucket $BNNN: already built -- skipping."
else
    "$PYTHON" -u ControlGroup/scripts/3_build_monthly_activity_matrix.py "$B"
fi

echo ""
echo "Task $SLURM_ARRAY_TASK_ID done at: $(date)"
