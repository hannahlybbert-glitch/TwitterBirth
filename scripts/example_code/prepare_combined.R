# Author: Emily Davis, assisted by Claude
# Created: 2026-04-08
# Purpose: Load combined desktop+mobile aggregation outputs, build stacked panel
#          and per-site minutes wide table, and serialise to
#          data/intermediate_combined/ for downstream analysis scripts.
#
# Key differences from prepare_desktop.R / prepare_mobile.R:
#   1. Reads from data/Aggregation/desktop_mobile_machine_panel/ (the combined
#      files produced by 6_append_desktop_mobile_panels.py).
#   2. Demographics loaded from both desktop parquet and mobile CSV+lookup,
#      combined and tagged with mobile (0=desktop, 1=mobile).
#   3. Presence loaded from both desktop and mobile machine_week_presence.parquet,
#      combined and tagged with mobile.
#   4. The mobile column is carried through stacked_base so downstream scripts
#      can filter to mobile==0 or mobile==1 for device-specific analyses.
#   5. No analysis-layer winsorization: total_duration is already winsorized at
#      the session level in the aggregation pipeline (Script 2). Minutes are
#      computed as total_duration / 60 directly.
#
# Run once upfront. Saves:
#   data/intermediate_combined/stacked_panel.rds  — named list of shared objects
#   data/intermediate_combined/xxx_min_wide.rds   — per-site minutes wide table
#
# Usage:
#   Rscript code/analysis/prepare_combined.R

suppressPackageStartupMessages({
  library(arrow)
  library(dplyr)
  library(here)
})

source(here::here("code", "analysis", "_source", "config.R"))
source(here::here("code", "analysis", "_source", "helpers.R"))

# ============================================================================
# PATHS
# ============================================================================

project_root <- here::here()

data_dir_comb <- file.path(project_root, "data", "Aggregation", "desktop_mobile_machine_panel")
data_dir_desk <- file.path(project_root, "data", "Aggregation", "machine_panel")
data_dir_mob  <- file.path(project_root, "data", "Aggregation", "mobile_machine_panel")
int_dir_comb  <- file.path(project_root, "data", "intermediate_combined")

demo_file_desk      <- file.path(project_root, "data", "ProcessComscore",
                                  "full_demographics", "full_machine_person_demos.parquet")
demo_file_mob       <- file.path(project_root, "data", "ProcessComscore",
                                  "full_demographics", "full_mobile_demos.parquet")

# ============================================================================
# STATE LAWS
# ============================================================================

cat("Loading PH shutdown dates...\n")
laws <- read.csv(ph_shutdown_file, stringsAsFactors = FALSE, na.strings = c("", "NA"))
laws$date_PH_shutdown <- as.Date(laws$date_PH_shutdown)
treated_all <- sort(laws$state)
law_date    <- setNames(laws$date_PH_shutdown, laws$state)
qualifying  <- treated_all[!is.na(law_date[treated_all]) &
                            law_date[treated_all] < CUTOFF_DATE]
cat(sprintf("  Qualifying (%d): %s\n", length(qualifying),
            paste(qualifying, collapse = ", ")))

base_date <- as.Date("2022-01-01")
law_wos <- setNames(
  sapply(qualifying, function(s)
    as.integer(law_date[s] - base_date) %/% 7L + 1L),
  qualifying
)

# law_wos for ALL treated states (not just qualifying) so we can correctly
# exclude states whose laws fall within any cohort's event window.
treated_with_date <- treated_all[!is.na(law_date[treated_all])]
law_wos_all <- setNames(
  sapply(treated_with_date, function(s)
    as.integer(law_date[s] - base_date) %/% 7L + 1L),
  treated_with_date
)

# ============================================================================
# THRESHOLD FILTER (active only when ANALYSIS_MODE = threshold)
# Drop machines in regions where majority_share < 80% and at least one state
# in the DMA has any law date. excluded_regions is character(0) in all other
# modes, making the filter below a no-op.
# ============================================================================

if (.mode == "threshold") {
  cat("Building threshold exclusion list...\n")
  dma_states <- read.csv(
    file.path(project_root, "data", "ProcessAuxiliary", "DMA_County", "all_states_in_DMA.csv"),
    stringsAsFactors = FALSE
  )
  dma_states$any_treated <- sapply(dma_states$all_states, function(s) {
    any(trimws(strsplit(s, ",")[[1]]) %in% treated_with_date)
  })
  excluded_regions <- dma_states$comscore_market[
    dma_states$majority_share < 0.80 & dma_states$any_treated
  ]
  cat(sprintf("  %d regions excluded (majority_share < 80%% with a treated state)\n",
              length(excluded_regions)))
} else {
  excluded_regions <- character(0)
}

# ============================================================================
# DEMOGRAPHICS
# Load desktop and mobile (both parquet) separately, then combine. After
# remapping, both share: machine_id, state, gender, hoh_age,
# children_present, hh_income, mobile (0L = desktop, 1L = mobile).
# ============================================================================

cat("Loading desktop demographics...\n")
# Desktop hh_income has 8 categories; mobile has 6 (caps at "100k+").
# Recode desktop to the same 6-category labels used by mobile so that
# build_het_covariates sees a single consistent income variable.
recode_desktop_income <- function(x) {
  dplyr::case_when(
    x == "HHI US: Less than 25k"  ~ "HHI:Less than 25k",
    x == "HHI US: 25k-39.999k"    ~ "HHI:25k-39k",
    x == "HHI US: 40k-59.999k"    ~ "HHI:40k-59k",
    x == "HHI US: 60k-74.999k"    ~ "HHI:60k-74k",
    x == "HHI US: 75k-99.999k"    ~ "HHI:75k-99k",
    x %in% c("HHI US: 100k-149.999k",
             "HHI US: 150k-199.999k",
             "HHI US: 200k+")     ~ "HHI:100k+",
    TRUE                           ~ NA_character_
  )
}

demos_desk <- read_parquet(demo_file_desk,
    col_select = c("machine_id", "state", "have_demos", "gender", "hoh_age",
                   "children_present", "hh_income", "hh_size", "region")) |>
  filter(have_demos == 1L) |>
  distinct(machine_id, .keep_all = TRUE) |>
  filter(!state %in% EXCLUDE_STATES, !region %in% excluded_regions) |>
  mutate(machine_id = as.character(machine_id),
         mobile     = 0L,
         hh_income  = recode_desktop_income(hh_income)) |>
  select(machine_id, state, gender, hoh_age, children_present, hh_income, hh_size, mobile)

cat(sprintf("  %s desktop machines\n", format(nrow(demos_desk), big.mark = ",")))

cat("Loading mobile demographics...\n")
# Mobile hh_income uses "HHI USD:..." labels; recode to the same 6-category
# labels used by the recoded desktop variable above.
recode_mobile_income <- function(x) {
  dplyr::case_when(
    x == "HHI USD:Less than 25,000"  ~ "HHI:Less than 25k",
    x == "HHI USD:25,000 - 39,999"   ~ "HHI:25k-39k",
    x == "HHI USD:40,000 - 59,999"   ~ "HHI:40k-59k",
    x == "HHI USD:60,000 - 74,999"   ~ "HHI:60k-74k",
    x == "HHI USD:75,000 - 99,999"   ~ "HHI:75k-99k",
    x == "HHI USD:100,000 or more"   ~ "HHI:100k+",
    TRUE                              ~ NA_character_
  )
}

recode_mobile_hh_size <- function(x) {
  dplyr::case_when(
    x == "HH Size: 1"  ~ "HH Size:1",
    x == "HH Size: 2"  ~ "HH Size:2",
    x == "HH Size: 3"  ~ "HH Size:3",
    x == "HH Size: 4"  ~ "HH Size:4",
    x == "HH Size: 5+" ~ "HH Size:5 or More",
    TRUE               ~ NA_character_
  )
}

demos_mob <- read_parquet(demo_file_mob,
    col_select = c("machine_id", "state", "have_demos", "age", "gender",
                   "children_present", "hh_income", "hh_size", "region")) |>
  filter(have_demos == 1L) |>
  distinct(machine_id, .keep_all = TRUE) |>
  filter(!is.na(state), !state %in% EXCLUDE_STATES, !region %in% excluded_regions) |>
  mutate(
    machine_id = as.character(machine_id),
    mobile     = 1L,
    hoh_age = dplyr::case_when(
      age >= 18 & age <= 24 ~ "18-24",
      age >= 25 & age <= 34 ~ "25-34",
      age >= 35 & age <= 44 ~ "35-44",
      age >= 45 & age <= 54 ~ "45-54",
      age >= 55 & age <= 64 ~ "55-64",
      age >= 65              ~ "65 and Over",
      TRUE                   ~ NA_character_
    ),
    hh_income = recode_mobile_income(hh_income),
    hh_size   = recode_mobile_hh_size(hh_size)
  ) |>
  select(machine_id, state, gender, hoh_age, children_present, hh_income, hh_size, mobile)

cat(sprintf("  %s mobile machines\n", format(nrow(demos_mob), big.mark = ",")))


demos <- bind_rows(demos_desk, demos_mob)
cat(sprintf("  %s combined machines\n", format(nrow(demos), big.mark = ",")))
rm(demos_desk, demos_mob)

# ============================================================================
# PRESENCE PANEL
# Load desktop and mobile machine_week_presence.parquet separately, tag with
# mobile, combine, then inner-join with demos to attach state.
# ============================================================================

cat("Loading presence panel...\n")
t0 <- proc.time()

presence_desk <- read_parquet(file.path(data_dir_desk, "machine_week_presence.parquet")) |>
  mutate(machine_id = as.character(machine_id), mobile = 0L)

presence_mob <- read_parquet(file.path(data_dir_mob, "machine_week_presence.parquet")) |>
  mutate(machine_id = as.character(machine_id), mobile = 1L)

presence <- bind_rows(presence_desk, presence_mob) |>
  inner_join(select(demos, machine_id, state, mobile), by = c("machine_id", "mobile")) |>
  filter(!is.na(state), !state %in% EXCLUDE_STATES)

rm(presence_desk, presence_mob)

cat(sprintf("  %s rows | %s machines  (%.1fs)\n",
    format(nrow(presence), big.mark = ","),
    format(n_distinct(presence$machine_id), big.mark = ","),
    (proc.time() - t0)[["elapsed"]]))

# Never-treated states: in presence but have no law date at all.
# These are always valid controls for every cohort.
never_treated_states <- setdiff(unique(presence$state), names(law_wos_all))
cat(sprintf("  Never-treated: %d states\n", length(never_treated_states)))

week_dates <- data.frame(week_of_sample = sort(unique(presence$week_of_sample))) |>
  mutate(week_start_date = base_date + (week_of_sample - 1L) * 7L)

# ============================================================================
# BUILD STACKED PANEL
# Same cohort/window logic as prepare_desktop.R, with mobile carried through.
# ============================================================================

cat("\nBuilding stacked panel...\n")
t0 <- proc.time()

stacked_base <- lapply(qualifying, function(s) {
  wos_0        <- law_wos[[s]]
  window_weeks <- wos_0 + t_range

  # Cohort-specific control states:
  #   - Always include never-treated states (no law at all).
  #   - Include other treated states only if their law falls strictly AFTER
  #     the end of this cohort's event window (> wos_0 + T_MAX).
  #   - Exclude: s itself, states already treated before the window starts,
  #     and states that pass a law within the window [wos_0+T_MIN, wos_0+T_MAX].
  other_treated   <- setdiff(names(law_wos_all), s)
  valid_treated_controls <- other_treated[law_wos_all[other_treated] > wos_0 + T_MAX]
  cohort_controls <- c(never_treated_states, valid_treated_controls)

  presence |>
    filter(week_of_sample %in% window_weeks,
           state == s | state %in% cohort_controls) |>
    mutate(
      cohort   = s,
      rel_week = as.integer(week_of_sample - wos_0),
      treated  = as.integer(state == s)
    ) |>
    select(machine_id, week_of_sample, state, cohort, rel_week, treated, mobile)
}) |> bind_rows() |>
  mutate(
    machine_cohort = paste0(machine_id, "__", cohort),
    cohort_week    = paste0(cohort,     "__", week_of_sample)
  )

rm(presence)

# Merge demographic columns (join on machine_id + mobile to avoid cross-join
# in the unlikely case of a machine_id collision between device types)
demo_slim    <- demos |> select(machine_id, mobile, gender, hoh_age, children_present, hh_income, hh_size)
stacked_base <- stacked_base |> left_join(demo_slim, by = c("machine_id", "mobile"))
rm(demos, demo_slim)

cat(sprintf("Stacked: %s rows | %s machine\u00d7cohort | %s cohort\u00d7week | %d clusters  (%.1fs)\n",
    format(nrow(stacked_base),                           big.mark = ","),
    format(n_distinct(stacked_base$machine_cohort),      big.mark = ","),
    format(n_distinct(stacked_base$cohort_week),         big.mark = ","),
    n_distinct(stacked_base$state),
    (proc.time() - t0)[["elapsed"]]))

cat(sprintf("  Desktop machines: %s | Mobile machines: %s\n",
    format(n_distinct(stacked_base$machine_id[stacked_base$mobile == 0L]), big.mark = ","),
    format(n_distinct(stacked_base$machine_id[stacked_base$mobile == 1L]), big.mark = ",")))

needed_weeks    <- sort(unique(as.integer(outer(unname(law_wos), t_range, "+"))))
needed_machines <- unique(stacked_base$machine_id)
n_clusters      <- n_distinct(stacked_base$state)

# ============================================================================
# BALANCED MACHINE×COHORT SET
# ============================================================================

cat("\nBuilding balanced machine×cohort set (all 25 event-window weeks required)...\n")
t0 <- proc.time()
n_weeks_required <- length(t_range)
balanced_mcs <- stacked_base |>
  group_by(machine_cohort) |>
  summarise(n_weeks = n_distinct(week_of_sample), .groups = "drop") |>
  filter(n_weeks == n_weeks_required) |>
  pull(machine_cohort)
cat(sprintf("  Balanced: %s of %s machine\u00d7cohort pairs (%.1f%%)  (%.1fs)\n",
    format(length(balanced_mcs),                    big.mark = ","),
    format(n_distinct(stacked_base$machine_cohort), big.mark = ","),
    100 * length(balanced_mcs) / n_distinct(stacked_base$machine_cohort),
    (proc.time() - t0)[["elapsed"]]))

# ============================================================================
# BUILD XXX MINUTES WIDE TABLE
# No analysis-layer winsorization. total_duration is already winsorized at the
# session level in the aggregation pipeline (Script 2, per-month P95 across all
# sessions). Minutes = total_duration / 60.
#
# Column naming mirrors xxx_win_wide from prepare_desktop/mobile.R so that all
# downstream scripts (run_regressions.R, diagnostics.R, etc.) work unchanged:
#   win_PORNHUB_COM, win_CHATURBATE_COM, ..., win_min_allxxx
# The "win_" prefix here means "the minutes column for that site", not that
# analysis-layer winsorization was applied.
# ============================================================================

cat("\nPre-building per-site XXX minutes wide table...\n")
t0 <- proc.time()

xxx_win_wide <- {
  per_site <- lapply(XXX_SLUGS, function(s) {
    t1 <- proc.time()
    dur_s <- open_dataset(file.path(data_dir_comb,
                                    paste0("machine_aggregated_", s, ".parquet"))) |>
      filter(week_of_sample %in% needed_weeks, machine_id %in% needed_machines) |>
      select(machine_id, week_of_sample, total_duration) |>
      collect()
    result <- dur_s |>
      mutate(win_s = total_duration / 60) |>
      select(machine_id, week_of_sample, win_s)
    col_name <- paste0("win_", gsub("[^A-Za-z0-9]", "_", s))
    names(result)[3] <- col_name
    cat(sprintf("  %s  (%.1fs)\n", s, (proc.time() - t1)[["elapsed"]]))
    result
  })
  Reduce(
    function(a, b) full_join(a, b, by = c("machine_id", "week_of_sample")),
    per_site
  ) |>
    mutate(
    win_min_allxxx         = rowSums(across(starts_with("win_")), na.rm = TRUE),
    win_other_xxx_combined = rowSums(
      across(c(win_CHATURBATE_COM, win_XHAMSTER_COM, win_other_XXX_sites)),
      na.rm = TRUE
    )
  )
}

cat(sprintf("Wide table: %s rows  (%.1fs total)\n",
            format(nrow(xxx_win_wide), big.mark = ","),
            (proc.time() - t0)[["elapsed"]]))

# ============================================================================
# SAVE RDS FILES
# ============================================================================

dir.create(int_dir_comb, recursive = TRUE, showWarnings = FALSE)

panel_path <- file.path(int_dir_comb, "stacked_panel.rds")
saveRDS(
  list(
    stacked_base         = stacked_base,
    week_dates           = week_dates,
    needed_weeks         = needed_weeks,
    needed_machines      = needed_machines,
    law_wos              = law_wos,
    law_wos_all          = law_wos_all,
    law_date             = law_date,
    qualifying           = qualifying,
    n_clusters           = n_clusters,
    never_treated_states = never_treated_states,
    balanced_mcs         = balanced_mcs
  ),
  panel_path
)
cat(sprintf("\nSaved: %s  (%.1f MB)\n",
    panel_path, file.size(panel_path) / 1e6))

win_path <- file.path(int_dir_comb, "xxx_win_wide.rds")
saveRDS(xxx_win_wide, win_path)
cat(sprintf("Saved: %s  (%.1f MB)\n",
    win_path, file.size(win_path) / 1e6))

het_path <- file.path(int_dir_comb, "het_covs.rds")
saveRDS(build_het_covariates(stacked_base, xxx_win_wide), het_path)
cat(sprintf("Saved: %s  (%.1f MB)\n",
    het_path, file.size(het_path) / 1e6))

cat("\nAll done.\n")
