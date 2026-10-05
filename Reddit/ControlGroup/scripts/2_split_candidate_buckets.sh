#!/bin/bash
# Purpose: Step 2 stage 2 (split) -- one array task per bucket, writes per-author comment + submission files
# Run after 2_fetch_candidate_com_subs.sh finishes (see that file for the chained sbatch).

#SBATCH --partition=standard
#SBATCH --account=ksrini0
#SBATCH --time=02:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=1
#SBATCH --job-name=split_candidate_buckets
#SBATCH --output=logs/split_candidate_buckets_%A_%a.out
#SBATCH --error=logs/split_candidate_buckets_%A_%a.err
# 0-63 must match N_BUCKETS in 2a/2b
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
