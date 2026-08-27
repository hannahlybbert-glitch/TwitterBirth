#!/bin/bash
# Combine step for pair_authors_comments — concatenates the per-month shards in
# Reddit/data/intermediate/comments/treatment_author_comments/ into the single
# deliverable Reddit/data/intermediate/comments/treatment_author_comments.csv
#
# Run from the reddit project root, after the array job finishes:
#     sbatch --dependency=afterok:<array_job_id> scripts/py/data_prep/pair_authors_comments_combine.sh
# This is light enough to just run on a login node instead:
#     python scripts/py/data_prep/pair_authors_comments.py --combine-only

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
export REDDIT_INTERMEDIATE_DIR=/nfs/turbo/si-ksrini/reddit/data/intermediate

mkdir -p logs

echo "Combining shards at: $(date)"
"$PYTHON" scripts/py/data_prep/pair_authors_comments.py --combine-only
echo "Done at: $(date)"
