#!/bin/bash
# Split candidate comment/submission chunks into per-author files -- cluster runner
# (Slurm array), stage 2 of 2. Must run AFTER every task in 2_fetch_candidate_com_subs.sh
# has finished (it reads chunks written by every month, across the whole fetch array).
#
# Typical submission, chained with a dependency:
#     FETCH_JOBID=$(sbatch --parsable ControlGroup/scripts/2_fetch_candidate_com_subs.sh)
#     sbatch --dependency=afterok:$FETCH_JOBID ControlGroup/scripts/2_split_candidate_buckets.sh
#
# One array task per hash bucket (0-63): each task reads that bucket's chunks across
# every month for BOTH comments and submissions, and writes the per-author files:
#     Reddit/ControlGroup/data/per_author_candidates/{author}_comments.parquet
#     Reddit/ControlGroup/data/per_author_candidates/{author}_submissions.parquet
#
# A bucket already marked split (for a given type) is skipped, so a partly-finished
# array can be resubmitted as-is (the .py doesn't self-skip in --bucket mode -- see
# 1_sample_candidate_pool.sh for the same pattern).

#SBATCH --partition=standard
#SBATCH --account=ksrini0
#SBATCH --time=02:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=1
#SBATCH --job-name=split_candidate_buckets
#SBATCH --output=logs/split_candidate_buckets_%A_%a.out
#SBATCH --error=logs/split_candidate_buckets_%A_%a.err
# N_BUCKETS in both 2a/2b is 64 -- keep this in sync if that constant ever changes.
# %16 caps concurrency since every task writes ~1,500 small files to the same dir.
#SBATCH --array=0-63%16

set -euo pipefail

PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3

export CONTROLGROUP_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/ControlGroup/data

: "${SLURM_ARRAY_TASK_ID:?must be run as a Slurm array job}"

B=$SLURM_ARRAY_TASK_ID
BNNN=$(printf "%03d" "$B")

COMMENT_MARKER="$CONTROLGROUP_DATA_DIR/2a_candidate_comment_chunks/.split_done_b${BNNN}"
SUBMISSION_MARKER="$CONTROLGROUP_DATA_DIR/2b_candidate_submission_chunks/.split_done_b${BNNN}"

echo "============================================"
echo "Task $SLURM_ARRAY_TASK_ID -> bucket $BNNN"
echo "Started at: $(date)"
echo "============================================"

if [ -f "$COMMENT_MARKER" ]; then
    echo "bucket $BNNN: comments already split -- skipping."
else
    "$PYTHON" -u ControlGroup/scripts/2a_fetch_candidate_comments.py --split-only --bucket "$B"
fi

if [ -f "$SUBMISSION_MARKER" ]; then
    echo "bucket $BNNN: submissions already split -- skipping."
else
    "$PYTHON" -u ControlGroup/scripts/2b_fetch_candidate_submissions.py --split-only --bucket "$B"
fi

echo ""
echo "Task $SLURM_ARRAY_TASK_ID done at: $(date)"
