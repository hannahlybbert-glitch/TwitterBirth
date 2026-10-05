#!/bin/bash
# Purpose: Step 1 cluster runner -- one array task per monthly RS_*.zst (skips months already done)
# Run from the Reddit project root: sbatch ControlGroup/scripts/1_sample_candidate_pool.sh
# Then combine: python ControlGroup/scripts/1_sample_candidate_pool.py --combine-only

#SBATCH --partition=standard
#SBATCH --account=ksrini0
#SBATCH --time=04:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=1
#SBATCH --job-name=sample_candidate_pool
#SBATCH --output=logs/sample_candidate_pool_%A_%a.out
#SBATCH --error=logs/sample_candidate_pool_%A_%a.err
# generous upper bound (extra tasks exit cleanly); %20 caps concurrency
#SBATCH --array=0-300%20

set -euo pipefail
shopt -s nullglob

# Full path -- module/conda PATH is unreliable in batch jobs
PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3

# Cluster paths
export REDDIT_SUBMISSIONS_DIR=/nfs/turbo/si-ksrini/Reddit/raw/submissions
export TREATMENT_AUTHORS_CSV=/nfs/turbo/si-ksrini/Reddit/data/final/treatment_authors.csv
export BIRTH_DATE_DIST_CSV=/nfs/turbo/si-ksrini/Reddit/data/descriptives/date_birth_dist_full.csv
export CONTROLGROUP_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/ControlGroup/data
export ALL_AUTHORS_DIR=/nfs/turbo/si-ksrini/Reddit/data/all_authors

mkdir -p logs
: "${SLURM_ARRAY_TASK_ID:?must be run as a Slurm array job}"

mapfile -t FILES < <(ls "$REDDIT_SUBMISSIONS_DIR"/RS_*.zst 2>/dev/null | sort)
echo "Found ${#FILES[@]} submission files; this is array task $SLURM_ARRAY_TASK_ID"

F="${FILES[$SLURM_ARRAY_TASK_ID]:-}"
if [ -z "$F" ]; then
    echo "No file at index $SLURM_ARRAY_TASK_ID — nothing to do."
    exit 0
fi

# Skip months already done
MONTH="$(basename "$F" .zst | sed 's/^RS_//')"
CHUNK="$CONTROLGROUP_DATA_DIR/1_candidate_pool_chunks/chunk_$(basename "$F" .zst).parquet"
ALL_AUTHORS="$ALL_AUTHORS_DIR/${MONTH}_RS_authors.parquet"
if [ -f "$CHUNK" ] && [ -f "$ALL_AUTHORS" ]; then
    echo "$(basename "$F"): chunk + all_authors already exist — skipping."
    exit 0
fi

echo "============================================"
echo "Task $SLURM_ARRAY_TASK_ID -> $(basename "$F")"
echo "Started at: $(date)"
echo "============================================"

"$PYTHON" -u ControlGroup/scripts/1_sample_candidate_pool.py "$F"

echo ""
echo "Task $SLURM_ARRAY_TASK_ID done at: $(date)"
