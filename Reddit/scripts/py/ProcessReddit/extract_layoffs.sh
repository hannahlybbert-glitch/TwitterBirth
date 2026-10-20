#!/bin/bash
# Extract r/layoffs comments or submissions: Slurm array over monthly dumps, then combine into yearly files
# Run from the reddit project root (NOT with sbatch -- this script submits the jobs itself):
#   bash scripts/py/ProcessReddit/extract_layoffs.sh comments
#   bash scripts/py/ProcessReddit/extract_layoffs.sh submissions

set -euo pipefail
shopt -s nullglob

PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3
SCRIPT=scripts/py/ProcessReddit/extract_layoffs.py
SUBREDDIT=layoffs
RAW=/nfs/turbo/si-ksrini/Reddit/raw
export REDDIT_OUTPUT_DIR=/nfs/turbo/si-ksrini/Reddit/data/ProcessReddit
export PYTHONUNBUFFERED=1

KIND=${1:?usage: bash extract_layoffs.sh comments|submissions}
case "$KIND" in
    comments)    files=("$RAW"/comments/RC_*.zst) ;;
    submissions) files=("$RAW"/submissions/RS_*.zst) ;;
    *) echo "Unknown kind: $KIND (expected comments or submissions)" >&2; exit 1 ;;
esac
if [ ${#files[@]} -eq 0 ]; then
    echo "No $KIND files found under $RAW" >&2
    exit 1
fi

# ----------------------------------------------------------------
# Worker: one array task = one monthly dump
# ----------------------------------------------------------------
if [ -n "${SLURM_ARRAY_TASK_ID:-}" ]; then
    f="${files[$SLURM_ARRAY_TASK_ID]}"
    echo "[$KIND / r/$SUBREDDIT] task $SLURM_ARRAY_TASK_ID of ${#files[@]}: $f"
    "$PYTHON" "$SCRIPT" "$KIND" "$f" --subreddit "$SUBREDDIT"
    exit 0
fi

# ----------------------------------------------------------------
# Launcher: submit the array, then the combine step once every task succeeds
# ----------------------------------------------------------------
mkdir -p logs
COMMON=(--partition=standard --account=ksrini0 --cpus-per-task=1)

array_id=$(sbatch --parsable "${COMMON[@]}" \
    --array=0-$(( ${#files[@]} - 1 )) --time=06:00:00 --mem=8G \
    --job-name="${SUBREDDIT}_${KIND}" \
    --output="logs/${SUBREDDIT}_${KIND}_%A_%a.out" --error="logs/${SUBREDDIT}_${KIND}_%A_%a.err" \
    "$0" "$KIND")

combine_id=$(sbatch --parsable "${COMMON[@]}" \
    --dependency=afterok:"$array_id" --time=02:00:00 --mem=32G \
    --job-name="${SUBREDDIT}_${KIND}_combine" \
    --output="logs/${SUBREDDIT}_${KIND}_combine_%j.out" --error="logs/${SUBREDDIT}_${KIND}_combine_%j.err" \
    --wrap="$PYTHON $SCRIPT $KIND --combine --subreddit $SUBREDDIT")

echo "Submitted $KIND: array job $array_id (${#files[@]} files), combine job $combine_id (runs after all tasks succeed)"
