#!/bin/bash
# Draw the control-group candidate pool — cluster runner (Slurm array).
# Run from the Reddit project root:
#     sbatch ControlGroup/scripts/1_sample_candidate_pool.sh
#
# One array task per monthly RS_*.zst file: each task streams its file once and
# writes a chunk to
#     Reddit/ControlGroup/data/1_candidate_pool_chunks/chunk_RS_YYYY-MM.parquet
# Months outside the quota table (before 2010-09 / after its last month) are
# no-ops. A task whose chunk already exists is skipped, so a partly-finished
# array can be resubmitted as-is.
#
# After the array finishes, build the combined deliverable
#     Reddit/ControlGroup/data/1_candidate_pool.parquet
# with either (both cheap — ~154 small parquets):
#     python ControlGroup/scripts/1_sample_candidate_pool.py --combine-only         # login node
#     sbatch --dependency=afterok:<array_job_id> ...                                # dependent job

#SBATCH --partition=standard
#SBATCH --account=ksrini0
#SBATCH --time=04:00:00
#SBATCH --mem=16G
#SBATCH --cpus-per-task=1
#SBATCH --job-name=sample_candidate_pool
#SBATCH --output=logs/sample_candidate_pool_%A_%a.out
#SBATCH --error=logs/sample_candidate_pool_%A_%a.err
# Upper bound is deliberately generous — the archive is ~230 months and
# out-of-range tasks exit 0 cleanly. %20 caps concurrency so we don't hammer
# the shared filesystem.
#SBATCH --array=0-300%20

set -euo pipefail
shopt -s nullglob

# Full path to the TwitterBirth env's Python — don't rely on module/conda PATH
# ordering in a non-interactive batch shell (see process.sh for the war story).
PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3

# Cluster data layout (read by the .py via os.environ.get with repo-relative fallbacks).
export REDDIT_SUBMISSIONS_DIR=/nfs/turbo/si-ksrini/Reddit/raw/submissions
export TREATMENT_AUTHORS_CSV=/nfs/turbo/si-ksrini/Reddit/data/final/treatment_authors.csv
export BIRTH_DATE_DIST_CSV=/nfs/turbo/si-ksrini/Reddit/data/descriptives/date_birth_dist_full.csv
export CONTROLGROUP_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/ControlGroup/data

mkdir -p logs
: "${SLURM_ARRAY_TASK_ID:?must be run as a Slurm array job}"

mapfile -t FILES < <(ls "$REDDIT_SUBMISSIONS_DIR"/RS_*.zst 2>/dev/null | sort)
echo "Found ${#FILES[@]} submission files; this is array task $SLURM_ARRAY_TASK_ID"

F="${FILES[$SLURM_ARRAY_TASK_ID]:-}"
if [ -z "$F" ]; then
    echo "No file at index $SLURM_ARRAY_TASK_ID — nothing to do."
    exit 0
fi

# The .py doesn't self-skip in single-file mode, so guard here to keep the array
# resumable (a re-submitted array re-runs completed months otherwise).
CHUNK="$CONTROLGROUP_DATA_DIR/1_candidate_pool_chunks/chunk_$(basename "$F" .zst).parquet"
if [ -f "$CHUNK" ]; then
    echo "$(basename "$F"): chunk already exists — skipping."
    exit 0
fi

echo "============================================"
echo "Task $SLURM_ARRAY_TASK_ID -> $(basename "$F")"
echo "Started at: $(date)"
echo "============================================"

"$PYTHON" -u ControlGroup/scripts/1_sample_candidate_pool.py "$F"

echo ""
echo "Task $SLURM_ARRAY_TASK_ID done at: $(date)"
