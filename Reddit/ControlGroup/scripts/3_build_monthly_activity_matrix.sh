#!/bin/bash
# Purpose: Step 3 cluster runner -- one array task per bucket (run after step 2 finishes)
# Run from the Reddit project root: sbatch ControlGroup/scripts/3_build_monthly_activity_matrix.sh
# Then combine:
#     CONTROLGROUP_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/ControlGroup/data \
#       /home/hlybbert/.conda/envs/TwitterBirth/bin/python3 \
#       ControlGroup/scripts/3_build_monthly_activity_matrix.py --combine-only

#SBATCH --partition=standard
#SBATCH --account=ksrini0
#SBATCH --time=01:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=1
#SBATCH --job-name=build_candidate_volume
#SBATCH --output=logs/build_candidate_volume_%A_%a.out
#SBATCH --error=logs/build_candidate_volume_%A_%a.err
# 0-63 must match N_BUCKETS
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
