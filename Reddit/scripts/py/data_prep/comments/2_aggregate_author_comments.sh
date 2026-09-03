#!/bin/bash
# Combine step for pair_authors_comments — concatenates the per-month shards in
# Reddit/data/intermediate/comments/treatment_author_comments/ into the single
# deliverable Reddit/data/intermediate/comments/treatment_author_comments.parquet
#
# Run from the reddit project root, after the array job finishes:
#     sbatch --dependency=afterok:<array_job_id> scripts/py/data_prep/comments/2_aggregate_author_comments.sh
# This is light enough to just run on a login node instead:
#     python scripts/py/data_prep/comments/pair_authors_comments.py --combine-only

#SBATCH --partition=standard
#SBATCH --account=ksrini0
#SBATCH --time=02:00:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=1
#SBATCH --job-name=pair_authors_comments_combine
#SBATCH --output=logs/pair_authors_comments_combine_%j.out
#SBATCH --error=logs/pair_authors_comments_combine_%j.err

set -euo pipefail

PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3
# combine() still loads treatment_authors.csv (for the earliest-comment summary),
# so set it here too — matches 1_pair_author_comments.sh and doesn't rely on the
# .py's repo-relative fallback.
export TREATMENT_AUTHORS_CSV=/nfs/turbo/si-ksrini/Reddit/data/final/treatment_authors.csv
export REDDIT_INTERMEDIATE_DIR=/nfs/turbo/si-ksrini/Reddit/data/intermediate

mkdir -p logs

echo "Combining shards at: $(date)"
"$PYTHON" scripts/py/data_prep/comments/pair_authors_comments.py --combine-only
echo "Done at: $(date)"
