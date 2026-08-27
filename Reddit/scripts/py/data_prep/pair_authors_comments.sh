#!/bin/bash
# Pull treatment authors' full comment history — cluster runner (Slurm array).
# Run from the reddit project root:
#     sbatch scripts/py/data_prep/pair_authors_comments.sh
#
# One array task per monthly RC_*.zst file: each task streams its file once and
# writes a shard to
#     Reddit/data/intermediate/comments/treatment_author_comments/RC_YYYY-MM.csv
# Shards are resumable (a task whose shard already exists is a no-op), so a
# partly-finished array can be resubmitted as-is.
#
# After the array finishes, build the single combined deliverable with:
#     sbatch --dependency=afterok:<this_array_job_id> scripts/py/data_prep/pair_authors_comments_combine.sh
# (or just run `python scripts/py/data_prep/pair_authors_comments.py --combine-only`
#  on a login node once the shards are all there — it's cheap.)
#
# Prereq: Reddit/data/final/treatment_authors.csv must exist (build/authors.py).

#SBATCH --partition=standard
#SBATCH --account=ksrini0
#SBATCH --time=08:00:00
#SBATCH --mem=32G
#SBATCH --cpus-per-task=1
#SBATCH --job-name=pair_authors_comments
#SBATCH --output=logs/pair_authors_comments_%A_%a.out
#SBATCH --error=logs/pair_authors_comments_%A_%a.err
# Upper bound is deliberately generous — the archive is ~230 months and tasks
# with no matching file exit 0 cleanly. %20 caps concurrent tasks so we don't
# hammer the shared filesystem.
#SBATCH --array=0-300%20

set -euo pipefail
shopt -s nullglob

# Full path to the TwitterBirth env's Python — don't rely on module/conda PATH
# ordering in a non-interactive batch shell (see process.sh for the war story).
PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3

# Cluster data layout (no nested "Reddit/" folder here). Read by the .py via
# os.environ.get() with repo-relative fallbacks.
export REDDIT_COMMENTS_DIR=/nfs/turbo/si-ksrini/reddit/raw/comments
export TREATMENT_AUTHORS_CSV=/nfs/turbo/si-ksrini/reddit/data/final/treatment_authors.csv
export REDDIT_INTERMEDIATE_DIR=/nfs/turbo/si-ksrini/reddit/data/intermediate

mkdir -p logs

mapfile -t FILES < <(ls "$REDDIT_COMMENTS_DIR"/RC_*.zst 2>/dev/null | sort)
echo "Found ${#FILES[@]} comment files; this is array task $SLURM_ARRAY_TASK_ID"

F="${FILES[$SLURM_ARRAY_TASK_ID]:-}"
if [ -z "$F" ]; then
    echo "No file at index $SLURM_ARRAY_TASK_ID — nothing to do."
    exit 0
fi

echo "============================================"
echo "Task $SLURM_ARRAY_TASK_ID -> $(basename "$F")"
echo "Started at: $(date)"
echo "============================================"

"$PYTHON" scripts/py/data_prep/pair_authors_comments.py "$F"

echo ""
echo "Task $SLURM_ARRAY_TASK_ID done at: $(date)"
