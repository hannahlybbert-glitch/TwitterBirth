#!/bin/bash
# Author: Hannah Lybbert
# Created: 2026-11-03
# Purpose: Run get_post_volume.py on the cluster; resubmit to resume from progress.json
# Run from the TwitterBirth root: mkdir -p logs && sbatch --export=ALL,PART=0 ControlGroup/scripts/API/3_post_volume/main_volume.sh
# PART selects the API key: ~/.x_token_0 or ~/.x_token_1

#SBATCH --partition=standard
#SBATCH --account=ksrini0

#SBATCH --job-name=xAPIvolume
#SBATCH --time=14-00:00:00
#SBATCH --mem=4G
#SBATCH --cpus-per-task=1
#SBATCH --output=logs/xAPIvolume%j.log
#SBATCH --error=logs/xAPIvolume%j.err
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=hlybbert@umich.edu

# Full path -- module/conda PATH is unreliable in batch jobs
PYTHON=/home/hlybbert/.conda/envs/TwitterBirth/bin/python3
export X_API_BEARER_TOKEN=$(cat ~/.x_token_"$PART")

set -euo pipefail

# --- Preflight: fail now, not days in ---
: "${PART:?PART is not set, submit with sbatch --export=ALL,PART=0 or PART=1}"
: "${X_API_BEARER_TOKEN:?token is empty, check ~/.x_token_$PART}"
"$PYTHON" -c "import requests, pandas, dateutil, dotenv, pyarrow"

# --- Run (-u so the log updates live) ---
echo "Started at: $(date)"
"$PYTHON" -u ControlGroup/scripts/API/3_post_volume/get_post_volume.py --part "$PART"
echo "Finished at: $(date)"
