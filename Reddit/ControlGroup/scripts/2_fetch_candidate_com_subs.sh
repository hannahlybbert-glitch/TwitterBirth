#!/bin/bash
# Purpose: Step 2 stage 1 (fetch) -- one array task per RC_*/RS_*.zst month (comments first, then submissions)
# Run from the Reddit project root, then chain stage 2:
#     FETCH_JOBID=$(sbatch --parsable ControlGroup/scripts/2_fetch_candidate_com_subs.sh)
#     sbatch --dependency=afterok:$FETCH_JOBID ControlGroup/scripts/2_split_candidate_buckets.sh

#SBATCH --partition=standard
#SBATCH --account=ksrini0
#SBATCH --time=05:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=1
#SBATCH --job-name=fetch_candidate_com_subs
#SBATCH --output=logs/fetch_candidate_com_subs_%A_%a.out
#SBATCH --error=logs/fetch_candidate_com_subs_%A_%a.err
# generous upper bound (extra tasks exit cleanly); %20 caps concurrency
#SBATCH --array=0-500%20

set -euo pipefail
shopt -s nullglob

# Full path -- module/conda PATH is unreliable in batch jobs
PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3

# Cluster paths
export REDDIT_COMMENTS_DIR=/nfs/turbo/si-ksrini/Reddit/raw/comments
export REDDIT_SUBMISSIONS_DIR=/nfs/turbo/si-ksrini/Reddit/raw/submissions
export CONTROLGROUP_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/ControlGroup/data

: "${SLURM_ARRAY_TASK_ID:?must be run as a Slurm array job}"

mapfile -t RC_FILES < <(ls "$REDDIT_COMMENTS_DIR"/RC_*.zst 2>/dev/null | sort)
mapfile -t RS_FILES < <(ls "$REDDIT_SUBMISSIONS_DIR"/RS_*.zst 2>/dev/null | sort)
N_RC=${#RC_FILES[@]}
N_RS=${#RS_FILES[@]}
TOTAL=$((N_RC + N_RS))
echo "Found $N_RC comment file(s) + $N_RS submission file(s) = $TOTAL total; this is array task $SLURM_ARRAY_TASK_ID"

if [ "$SLURM_ARRAY_TASK_ID" -ge "$TOTAL" ]; then
    echo "No file at index $SLURM_ARRAY_TASK_ID (only $TOTAL total) -- nothing to do."
    exit 0
fi

if [ "$SLURM_ARRAY_TASK_ID" -lt "$N_RC" ]; then
    F="${RC_FILES[$SLURM_ARRAY_TASK_ID]}"
    SCRIPT="2a_fetch_candidate_comments.py"
    PREFIX="RC"
    CHUNK_DIR="$CONTROLGROUP_DATA_DIR/2a_candidate_comment_chunks"
else
    F="${RS_FILES[$((SLURM_ARRAY_TASK_ID - N_RC))]}"
    SCRIPT="2b_fetch_candidate_submissions.py"
    PREFIX="RS"
    CHUNK_DIR="$CONTROLGROUP_DATA_DIR/2b_candidate_submission_chunks"
fi

# Skip months already done
MONTH="$(basename "$F" .zst | sed "s/^${PREFIX}_//")"
MARKER="$CHUNK_DIR/.done_$MONTH"
if [ -f "$MARKER" ]; then
    echo "$(basename "$F"): already fetched -- skipping."
    exit 0
fi

echo "============================================"
echo "Task $SLURM_ARRAY_TASK_ID -> $SCRIPT $(basename "$F")"
echo "Started at: $(date)"
echo "============================================"

"$PYTHON" -u "ControlGroup/scripts/$SCRIPT" "$F"

echo ""
echo "Task $SLURM_ARRAY_TASK_ID done at: $(date)"
