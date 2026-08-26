# ============================================================================
# config.R — universal constants for all analysis scripts
# Source this file after loading library(here).
# ============================================================================

suppressPackageStartupMessages(library(here))

project_root <- here::here()

# Switch all data/output paths based on ANALYSIS_MODE env var.
#
# Supported values:
#   desktop          (default) — original desktop-only pipeline
#   mobile                     — original mobile-only pipeline
#   combined                   — desktop+mobile combined, all machines
#   desktop_combined           — combined panel, desktop machines only (mobile==0)
#   mobile_combined            — combined panel, mobile machines only  (mobile==1)
#
# The three combined modes all read from intermediate_combined/ and
# desktop_mobile_machine_panel/. Output destinations:
#   combined         → output/analysis/combined/
#   desktop_combined → output/analysis/          (same path as desktop)
#   mobile_combined  → output/analysis/mobile/   (same path as mobile)

.mode <- Sys.getenv("ANALYSIS_MODE", unset = "desktop")

if (.mode == "mobile") {
  data_dir          <- file.path(project_root, "data", "Aggregation", "mobile_machine_panel")
  demo_file         <- file.path(project_root, "data", "ProcessComscore", "mobile_characteristics.csv")
  state_lookup_file <- file.path(project_root, "data", "Aggregation", "mobile_to_state_lookup.parquet")
  int_dir           <- file.path(project_root, "data", "intermediate_mobile")
  out_base          <- file.path(project_root, "output", "analysis", "mobile")

} else if (.mode %in% c("combined", "desktop_combined", "mobile_combined", "final", "single_user", "threshold")) {
  data_dir <- file.path(project_root, "data", "Aggregation", "desktop_mobile_machine_panel")
  int_dir  <- file.path(project_root, "data", "intermediate_combined")
  out_base <- switch(.mode,
    combined         = file.path(project_root, "output", "analysis", "combined"),
    desktop_combined = file.path(project_root, "output", "analysis"),
    mobile_combined  = file.path(project_root, "output", "analysis", "mobile"),
    final            = file.path(project_root, "output", "analysis", "final"),
    single_user      = file.path(project_root, "output", "analysis", "single_user"),
    threshold        = file.path(project_root, "output", "analysis", "threshold")
  )

} else {
  # Default: desktop
  data_dir  <- file.path(project_root, "data", "Aggregation", "machine_panel")
  demo_file <- file.path(project_root, "data", "ProcessComscore",
                         "full_demographics", "full_machine_person_demos.parquet")
  int_dir   <- file.path(project_root, "data", "intermediate")
  out_base  <- file.path(project_root, "output", "analysis")
}

# When running a device-specific combined mode, downstream scripts filter
# stacked_base to this value of the mobile column. NULL means no filter.
MOBILE_FILTER <- switch(.mode,
  desktop_combined = 0L,
  mobile_combined  = 1L,
  NULL  # combined, final, desktop, mobile, single_user: no filter
)

# In single_user mode, drop shared-device machines (gender == "Shared").
# All mobile machines pass through (one user per device by definition);
# desktop is restricted to machines assigned to a single named person.
SINGLE_USER_FILTER <- .mode == "single_user"

ph_shutdown_file <- file.path(project_root, "raw", "statelaws", "phshutdown_dates.csv")
out_int_dir      <- file.path(out_base, "intermediate")

EXCLUDE_STATES <- c("DC", "XX", "ZZ")
CUTOFF_DATE    <- as.Date("2024-11-24")
T_MIN <- -16L; T_MAX <- 8L
t_range <- T_MIN:T_MAX

MAROON <- "#8c1515"
NAVY   <- "#0B3954"

XXX_SLUGS <- c("PORNHUB.COM", "CHATURBATE.COM", "XHAMSTER.COM",
               "XNXX.COM",   "XVIDEOS.COM",    "other_XXX_sites")

COMPARISON_SITE_KEYS <- c("Netflix Inc.", "Reddit", "Twitter",
                           "ONLYFANS.COM", "New York Times Digital")

# Canonical site list (used by run_regressions, output scripts)
SITES_FULL <- list(
  list(key = "all_xxx",                  label = "All XXX",                slug = "all_xxx"),
  list(key = "PORNHUB.COM",              label = "Pornhub",                slug = "PORNHUB_COM"),
  list(key = "XVIDEOS.COM",              label = "XVideos",                slug = "XVIDEOS_COM"),
  list(key = "XHAMSTER.COM",             label = "xHamster",               slug = "XHAMSTER_COM"),
  list(key = "XNXX.COM",                 label = "XNXX",                   slug = "XNXX_COM"),
  list(key = "CHATURBATE.COM",           label = "Chaturbate",             slug = "CHATURBATE_COM"),
  list(key = "other_XXX_sites",          label = "Other XXX",              slug = "other_XXX"),
  list(key = "other_xxx_combined",       label = "Other XXX (combined)",   slug = "other_xxx_combined"),
  list(key = "all_other_sites",          label = "All other sites",        slug = "all_other"),
  list(key = "VPNclean",                 label = "VPN (clean)",            slug = "VPNclean"),
  list(key = "allVPN",                   label = "All VPN",                slug = "allVPN"),
  list(key = "Netflix Inc.",             label = "Netflix",                slug = "Netflix_Inc"),
  list(key = "Reddit",                   label = "Reddit",                 slug = "Reddit"),
  list(key = "Twitter",                  label = "Twitter",                slug = "Twitter"),
  list(key = "ONLYFANS.COM",             label = "OnlyFans",               slug = "ONLYFANS_COM"),
  list(key = "New York Times Digital",   label = "New York Times",         slug = "NYT_Digital")
)

# VPN-only override — used by make_vpn.sh (set VPN_ONLY=1) to skip re-running
# adult XXX sites that were already produced in a prior pipeline run.
if (identical(Sys.getenv("VPN_ONLY"), "1")) {
  SITES_FULL <- SITES_FULL[sapply(SITES_FULL, `[[`, "key") %in%
                             c("VPNclean", "allVPN", "all_other_sites")]
}
BAL_SITES <- SITES_FULL[sapply(SITES_FULL, `[[`, "key") %in%
               c("all_xxx", "PORNHUB.COM", "XVIDEOS.COM")]

# DV definitions (key, short label, y-axis label)
DV_METADATA <- list(
  over60  = list(short   = "Pr(>60s)",
                 y_label = "Change in Pr(>60s)",
                 title   = "Pr(>60s on site)"),
  win_min = list(short   = "Win. min/machine (p95)",
                 y_label = "Change in weekly minutes per machine",
                 title   = "Winsorized min/machine/week (p95)")
)
dvs <- names(DV_METADATA)

# Pooled spec period windows (main regressions)
PRE_WINDOW   <- -16:-5   # placebo pre-period
SHORT_WINDOW <-   0:3    # short-term ATT
LONG_WINDOW  <-   4:8    # long-term ATT

# Reference period for the extensive-margin bin decomposition
# (prepare_extensive_margin_bins_mb.R, create_extensive_margin_regressions_mb.R):
# used both to define the quintile cutoffs and the baseline bin shares. Matt's
# choice -- the immediate pre-treatment weeks, not the full placebo PRE_WINDOW.
BIN_REF_WINDOW <- -4:-1
