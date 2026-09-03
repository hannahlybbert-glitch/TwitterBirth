#!/bin/bash
# Runner for treatment_comments_descriptives.py — cluster (Slurm) or login node.
#
# Streams the per-month shards in
#   Reddit/data/intermediate/comments/treatment_author_comments/treatment_RC_YYYY-MM.parquet
# one month at a time (the combined single file is too big to load), prints the
# descriptive report to the job's .out, and writes an author-level table to
#   Reddit/data/descriptives/treatment_comments/author_level.csv
#
# Run from the Reddit project root:
#     sbatch scripts/py/descriptives/run_treatment_comments_descriptives.sh
# Light enough to run directly on a login node instead:
#     python scripts/py/descriptives/treatment_comments_descriptives.py

#SBATCH --partition=standard
#SBATCH --account=ksrini0
#SBATCH --time=02:00:00
#SBATCH --mem=64G
#SBATCH --cpus-per-task=1
#SBATCH --job-name=treatment_comments_descriptives
#SBATCH --output=logs/treatment_comments_descriptives_%j.out
#SBATCH --error=logs/treatment_comments_descriptives_%j.err

set -euo pipefail

# Full path to the env's Python — don't rely on module/conda PATH ordering in a
# non-interactive batch shell (see process.sh for the war story).
PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3

# Cluster data layout. Read by the .py via os.environ.get() with repo-relative
# fallbacks; the .py only needs the intermediate dir + the authors csv.
export REDDIT_INTERMEDIATE_DIR=/nfs/turbo/si-ksrini/Reddit/data/intermediate
export TREATMENT_AUTHORS_CSV=/nfs/turbo/si-ksrini/Reddit/data/final/treatment_authors.csv

mkdir -p logs

echo "============================================"
echo "TREATMENT COMMENTS DESCRIPTIVES"
echo "Started at: $(date)"
echo "============================================"

"$PYTHON" scripts/py/descriptives/treatment_comments_descriptives.py "$@"

echo ""
echo "Done at: $(date)"
