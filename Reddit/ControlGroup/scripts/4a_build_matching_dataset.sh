#!/bin/bash
# Purpose: Step 4a runner on its own (4_matching.sh can also run it). Needs step 3 + treatment volume files.
# Run from the Reddit project root: sbatch ControlGroup/scripts/4a_build_matching_dataset.sh

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

# Cluster paths
export CONTROLGROUP_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/ControlGroup/data
export VOLUME_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/data/volume
export TREATMENT_AUTHORS_CSV=/nfs/turbo/si-ksrini/Reddit/data/final/treatment_authors.csv

mkdir -p logs

echo "Building matching dataset at: $(date)"
"$PYTHON" -u ControlGroup/scripts/4a_build_matching_dataset.py
echo "Done at: $(date)"
