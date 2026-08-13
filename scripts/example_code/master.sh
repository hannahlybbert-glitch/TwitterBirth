#!/bin/bash
# Master script for Comscore merge pipeline
# Run from project root: ./code/ProcessComscore/master.sh
# Processes all months from 202201 to 202412 (36 months)

#SBATCH --partition=caslake
#SBATCH --account=pi-mattbrownecon

#SBATCH --job-name=merge_pipeline
#SBATCH --output=logs/merge_%j.out
#SBATCH --error=logs/merge_%j.err
#SBATCH --time=04:00:00
#SBATCH --mem=64G

set -euo pipefail

# # Load required module. (recent version of python good at handling parquet.)
# module unload python
# module load python/anaconda-2024.10
# conda activate age-verification

echo "============================================"
echo "MERGE PIPELINE."
echo "Started at: $(date)"
echo "============================================"

# # Step 1: Create machine characteristics
# echo ""
# echo "Creating machine characteristics..."
# python3 code/ProcessComscore/create_machine_characteristics.py

# Steps 3 + 5 only: regenerate web_characteristics with vpn_clean_site flag,
# then remerge into sessions. Steps 2 and 4 are unchanged; steps 1, 6, 7 not needed.
# for year in 2022 2023 2024; do
#     for month in 01 02 03 04 05 06 07 08 09 10 11 12; do
#         MONTH_ID="${year}${month}"

#         echo ""
#         echo "============================================"
#         echo "Processing month: ${MONTH_ID}"
#         echo "============================================"

        # # Step 2: Create crosswalk (unchanged — skip)
        # echo "Creating crosswalk..."
        # python3 code/ProcessComscore/create_crosswalk_file.py ${MONTH_ID}

        # # Step 3: Create web characteristics (adds vpn_clean_site column)
        # echo "Creating web characteristics..."
        # python3 code/ProcessComscore/create_web_characteristics.py ${MONTH_ID}

        # # Step 4: Create machine state lookup (unchanged — skip)
        # echo "Creating machine state lookup..."
        # python3 code/ProcessComscore/create_machine_state_lookup.py ${MONTH_ID}

        # # Step 5: Merge into sessions (picks up new vpn_clean_site column)
        # echo "Merging all data into sessions..."
        # python3 code/ProcessComscore/merge_into_sessions.py ${MONTH_ID}
#     done
# done

# # Step 6: Build full demographic reference files (unchanged — skip)
# echo ""
# echo "Building full demographics..."
# python3 code/ProcessComscore/create_full_demographics.py

# # Step 7: Merge person demographics onto machine demographics (unchanged — skip)
# echo ""
# echo "Merging full demographics..."
# python3 code/ProcessComscore/merge_full_demographics.py

# Diagnostic: check machine vs. person file coverage across all months
echo ""
echo "Checking machine/person coverage..."
python3 code/ProcessComscore/check_machine_person_coverage.py

echo ""
echo "============================================"
echo "PIPELINE COMPLETE"
echo "Finished at: $(date)"
echo "============================================"
