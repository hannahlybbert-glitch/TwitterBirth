#!/bin/bash
# Purpose: Step 4 runner -- 4a (uncomment when rebuilding), then 4b + 4c for each spec in SPECS
# Run from the Reddit project root:
#     sbatch ControlGroup/scripts/4_matching.sh           # full data
#     sbatch ControlGroup/scripts/4_matching.sh --test    # 100 + 100 test sample

#SBATCH --partition=standard
#SBATCH --account=ksrini0
#SBATCH --time=05:00:00
#SBATCH --mem=24G
#SBATCH --cpus-per-task=8
#SBATCH --job-name=matching
#SBATCH --output=logs/matching_%j.out
#SBATCH --error=logs/matching_%j.err

set -euo pipefail

PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3

# Cluster paths
export CONTROLGROUP_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/ControlGroup/data
export VOLUME_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/data/volume
export TREATMENT_AUTHORS_CSV=/nfs/turbo/si-ksrini/Reddit/data/final/treatment_authors.csv

mkdir -p logs

# # Step 4a: build the matching dataset
# echo "4a: building matching dataset at: $(date)"
# "$PYTHON" -u ControlGroup/scripts/4a_build_matching_dataset.py

# Specs to run (defined in matching_specs.py)
SPECS=(ORIGINAL PRE10 COARSE COM-HEAVY COARSE_COM-HEAVY COM-VERY-HEAVY COARSE_COM-VERY-HEAVY
       COM-DOM COARSE_COM-DOM ONLY_COM)

for SPEC in "${SPECS[@]}"; do
    # Step 4b: match treatment authors to candidate controls
    echo ""
    echo "4b [$SPEC]: matching at: $(date)"
    "$PYTHON" -u ControlGroup/scripts/4b_match_authors.py --spec "$SPEC" "$@"

    # Step 4c: plot matched pre-birth trends
    echo ""
    echo "4c [$SPEC]: plotting at: $(date)"
    "$PYTHON" -u ControlGroup/scripts/4c_plot_matched_pretrends.py --spec "$SPEC" "$@"
done

echo "Done at: $(date)"
