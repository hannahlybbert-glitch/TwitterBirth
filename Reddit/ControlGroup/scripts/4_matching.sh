#!/bin/bash
# Step 4: build the matching dataset (4a), then match (4b) -- cluster runner (single job).
# Comment out 4a below once 4a_matching_dataset.parquet is built, so reruns only match.
# 4a must run AFTER both:
#   - 3_build_monthly_activity_matrix.sh + its --combine-only step (3a/3b candidate files)
#   - scripts/py/volume/run_treatment_volume_matrix.sh (treatment_{submission,comment}_volume.parquet)
#
# 4b/4c run once per spec in SPECS below (names defined in matching_specs.py). Edit
# the list to choose which matching versions to (re)run.
#
# Run from the Reddit project root:
#     sbatch ControlGroup/scripts/4_matching.sh           # full data
#     sbatch ControlGroup/scripts/4_matching.sh --test    # 4a test sample (100 + 100)
# (arguments are passed to 4b and 4c; 4a always writes both the full and test files)
#
# Writes (per spec; test mode adds a _test suffix and writes into a test/ subfolder
# of each folder below):
#     4a: $CONTROLGROUP_DATA_DIR/4a_matching_dataset.parquet
#         $CONTROLGROUP_DATA_DIR/test/4a_matching_dataset_test.parquet
#     4b: $CONTROLGROUP_DATA_DIR/4_matching/<SPEC>_matched_pairs.parquet
#         $CONTROLGROUP_DATA_DIR/4_matching/<SPEC>_balance.csv
#         $CONTROLGROUP_DATA_DIR/4_matching/<SPEC>_spec.json
#     4c: Reddit/ControlGroup/output/matching/<SPEC>_pretrends.png

#SBATCH --partition=standard
#SBATCH --account=ksrini0
#SBATCH --time=05:00:00
#SBATCH --mem=24G
#SBATCH --cpus-per-task=8        # 4b's up-front neighbor query runs in parallel (workers=-1)
#SBATCH --job-name=matching
#SBATCH --output=logs/matching_%j.out
#SBATCH --error=logs/matching_%j.err

set -euo pipefail

PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3

# Cluster data layout (read by the .py via os.environ.get with repo-relative fallbacks).
export CONTROLGROUP_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/ControlGroup/data
export VOLUME_DATA_DIR=/nfs/turbo/si-ksrini/Reddit/data/volume
export TREATMENT_AUTHORS_CSV=/nfs/turbo/si-ksrini/Reddit/data/final/treatment_authors.csv

mkdir -p logs

# # Step 4a: build the matching dataset
# echo "4a: building matching dataset at: $(date)"
# "$PYTHON" -u ControlGroup/scripts/4a_build_matching_dataset.py

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
