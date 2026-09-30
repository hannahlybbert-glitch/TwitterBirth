#!/bin/bash
# Build the treatment-side monthly volume matrix -- cluster runner (single job).
# Must run AFTER treatment_author_comments.parquet exists
# (scripts/py/data_prep/comments/1_pair_author_comments.sh + 2_aggregate_author_comments.sh).
#
# Run from the Reddit project root:
#     sbatch scripts/py/volume/run_treatment_volume_matrix.sh
# or chain it after the comments combine job:
#     sbatch --dependency=afterok:<combine_job_id> scripts/py/volume/run_treatment_volume_matrix.sh
#
# Writes:
#     $VOLUME_DATA_DIR/treatment_submission_volume.parquet
#     $VOLUME_DATA_DIR/treatment_comment_volume.parquet
#
# Memory: the .py loads author + months_from_birth for every treatment comment
# into pandas at once -- bump --mem if the job OOMs.

#SBATCH --partition=standard
#SBATCH --account=ksrini0
#SBATCH --time=02:00:00
#SBATCH --mem=64G
#SBATCH --cpus-per-task=1
#SBATCH --job-name=build_treatment_volume
#SBATCH --output=logs/build_treatment_volume_%j.out
#SBATCH --error=logs/build_treatment_volume_%j.err

set -euo pipefail

PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3

# Cluster data layout (no nested "Reddit/" folder here). Read by the .py via
# os.environ.get() with repo-relative fallbacks.
export BIRTHS_AND_POSTS_CSV=/nfs/turbo/si-ksrini/Reddit/data/final/births_and_posts_FULL.csv
export TREATMENT_COMMENTS_PARQUET=/nfs/turbo/si-ksrini/Reddit/data/intermediate/comments/treatment_author_comments.parquet
export VOLUME_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/data/volume

mkdir -p logs

echo "Building treatment volume matrix at: $(date)"
"$PYTHON" -u scripts/py/volume/build_treatment_volume_matrix.py
echo "Done at: $(date)"
