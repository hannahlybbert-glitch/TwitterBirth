#!/bin/bash
# Master script for combined analysis pipeline with updated estimation data
# Run from project root: sbatch code/analysis/make_combined.sh
#
# Data prep (prepare_combined.R) creates data/intermediate_combined/, which is
# shared by make_desktop.sh and make_mobile.sh. Run this first if starting fresh.

#SBATCH --partition=caslake
#SBATCH --account=pi-mattbrownecon

#SBATCH --job-name=analysis_pipeline_combined
#SBATCH --output=logs/analysis_combined_%j.out
#SBATCH --error=logs/analysis_combined_%j.err
#SBATCH --time=01:00:00
#SBATCH --mem=64G

source /software/python-anaconda-2022.05-el8-x86_64/etc/profile.d/conda.sh
conda activate age-verification

set -euo pipefail

export ANALYSIS_MODE=combined

echo "============================================"
echo "ANALYSIS PIPELINE (COMBINED)"
echo "Started at: $(date)"
echo "============================================"

# echo ""
# echo "=== prepare_combined.R ==="
# Rscript code/analysis/prepare_combined.R

# echo ""
# echo "=== run_regressions.R (combined) ==="
# RUN_MODE=combined Rscript code/analysis/run_regressions.R

# echo ""
# echo "=== compare_time_series.py ==="
# python code/analysis/compare_time_series.py

# echo ""
# echo "=== create_regression_table.R ==="
# Rscript code/analysis/create_regression_table.R

# echo ""
# echo "=== create_event_study_plots.R ==="
# Rscript code/analysis/create_event_study_plots.R

# echo ""
# echo "=== create_decomposition_plots.R ==="
# Rscript code/analysis/create_decomposition_plots.R

# echo ""
# echo "=== create_summary_table.R ==="
# Rscript code/analysis/create_summary_table.R

# echo ""
# echo "=== create_het_main_regressions.R ==="
# Rscript code/analysis/create_het_main_regressions.R

# echo ""
# echo "=== create_het_main_figures.R ==="
# Rscript code/analysis/create_het_main_figures.R

# echo ""
# echo "=== create_het_table.R ==="
# Rscript code/analysis/create_het_table.R

# echo ""
# echo "=== create_decomp_plots2_pres.R ==="
# Rscript code/analysis/create_decomp_plots2_pres.R

# echo ""
# echo "=== determine_avg_state_share.py ==="
# python code/analysis/determine_avg_state_share.py


# # ----------- CONSUMER EDGE ANALYSIS ------------- #
# echo ""
# echo "=== prepare_combined_CE.R ==="
# Rscript code/analysis/prepare_combined_CE.R

# echo ""
# echo "=== run_regressions_CE.R (combined) ==="
# RUN_MODE=combined Rscript code/analysis/run_regressions_CE.R

# echo ""
# echo "=== create_regression_table_CE.R ==="
# Rscript code/analysis/create_regression_table_CE.R

echo ""
echo "=== create_event_study_plots_CE.R ==="
Rscript code/analysis/create_event_study_plots_CE.R

# echo ""
# echo "=== create_main_regression_table.R ==="
# Rscript code/analysis/create_main_regression_table.R


# # ---------- EXTENSIVE MARGIN ANALYSIS -------------- #

# # Extensive-margin analysis (all_xxx only). Estimates pooled short/long ATT per
# # weekly-seconds threshold, then plots the ST/LT effects against the threshold
# # on the x-axis. (regressions must run before the figure.)
# echo ""
# echo "=== create_extensive_margin_regressions.R ==="
# Rscript code/analysis/create_extensive_margin_regressions.R

# echo ""
# echo "=== create_extensive_margin_figure.R ==="
# Rscript code/analysis/create_extensive_margin_figure.R

# # Bin decomposition (all_xxx only): partitions weekly minutes into
# # mutually-exclusive duration bins (a la Cengiz et al.) and estimates the
# # pooled long-run ATT per bin. Prep step must run before the regressions.
# echo ""
# echo "=== prepare_extensive_margin_bins_mb.R ==="
# Rscript code/analysis/prepare_extensive_margin_bins_mb.R

# echo ""
# echo "=== create_extensive_margin_regressions_mb.R ==="
# Rscript code/analysis/create_extensive_margin_regressions_mb.R

# echo ""
# echo "=== create_extensive_margin_figure_mb.R ==="
# Rscript code/analysis/create_extensive_margin_figure_mb.R

# # State-level forest plots (Pornhub, XVideos, XNXX, All XXX; win_min).
# # Per-state short/long ATT with an Overall reference row at the top.
# echo ""
# echo "=== create_state_forest_plot.R ==="
# Rscript code/analysis/create_state_forest_plot.R

# # Leave-one-out robustness: overall ATT re-estimated dropping each treated
# # state's cohort (valid state clustering, 14 treated clusters each).
# echo ""
# echo "=== create_state_loo_plot.R ==="
# Rscript code/analysis/create_state_loo_plot.R

# # Kids-vs-age-of-head horserace (desktop, All XXX, win_min).
# echo ""
# echo "=== create_het_kids_age_horserace.R ==="
# Rscript code/analysis/create_het_kids_age_horserace.R

# # Long-run event studies (~6 months, balanced panel of 11 states; 4 main sites).
# # Self-contained: rebuilds the stacked panel for the wider window.
# echo ""
# echo "=== create_longrun_event_study.R ==="
# Rscript code/analysis/create_longrun_event_study.R

echo ""
echo "============================================"
echo "ANALYSIS PIPELINE (COMBINED) COMPLETE"
echo "Finished at: $(date)"
echo "============================================"



# Old code:
# echo ""
# echo "=== create_normalized_het_regressions.R (~5-10 min) ==="
# Rscript code/analysis/create_normalized_het_regressions.R

# echo ""
# echo "=== create_heterogeneity_plots.R ==="
# Rscript code/analysis/create_heterogeneity_plots.R

# echo ""
# echo "=== create_normalized_het_table.R ==="
# Rscript code/analysis/create_normalized_het_table.R

# echo ""
# echo "=== create_normalized_het_figures.R ==="
# Rscript code/analysis/create_normalized_het_figures.R

# echo ""
# echo "=== create_demo_summary_tables.R ==="
# Rscript code/analysis/create_demo_summary_tables.R

# echo ""
# echo "=== machine_xxx_2022_sum_table.R ==="
# Rscript code/analysis/machine_xxx_2022_sum_table.R