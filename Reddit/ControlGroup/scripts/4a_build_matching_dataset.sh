#!/bin/bash
# Stack treatment + candidate authors into the matching dataset -- cluster runner (single job).
# Must run AFTER both:
#   - 3_build_monthly_activity_matrix.sh + its --combine-only step (3a/3b candidate files)
#   - scripts/py/volume/run_treatment_volume_matrix.sh (treatment_{submission,comment}_volume.parquet)
#
# Run from the Reddit project root:
#     sbatch ControlGroup/scripts/4a_build_matching_dataset.sh
# or chain it after the treatment volume job:
#     sbatch --dependency=afterok:<treatment_volume_job_id> ControlGroup/scripts/4a_build_matching_dataset.sh
#
# Writes:
#     $CONTROLGROUP_DATA_DIR/4a_matching_dataset.parquet
#     $CONTROLGROUP_DATA_DIR/test/4a_matching_dataset_test.parquet   (100 + 100 sample for testing 4b)

#SBATCH --partition=standard
#SBATCH --account=ksrini0
#SBATCH --time=00:30:00
#SBATCH --mem=8G
#SBATCH --cpus-per-task=1
#SBATCH --job-name=build_matching_dataset
#SBATCH --output=logs/build_matching_dataset_%j.out
#SBATCH --error=logs/build_matching_dataset_%j.err

set -euo pipefail

PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3

# Cluster data layout (read by the .py via os.environ.get with repo-relative fallbacks).
export CONTROLGROUP_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/ControlGroup/data
export VOLUME_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/data/volume
export TREATMENT_AUTHORS_CSV=/nfs/turbo/si-ksrini/Reddit/data/final/treatment_authors.csv

mkdir -p logs

echo "Building matching dataset at: $(date)"
"$PYTHON" -u ControlGroup/scripts/4a_build_matching_dataset.py
echo "Done at: $(date)"
