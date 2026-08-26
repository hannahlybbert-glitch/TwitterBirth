# ============================================================================
# helpers.R — shared functions for all analysis scripts
# Source config.R and load packages before sourcing this file.
# Free variables (data_dir, XXX_SLUGS, needed_weeks, needed_machines,
#   MAROON, T_MIN, T_MAX, qualifying, n_clusters) are resolved from
#   the global environment at call time.
# ============================================================================

# Load duration parquet for one site (or sum of all XXX sites).
OTHER_XXX_COMBINED_SLUGS <- c("CHATURBATE.COM", "XHAMSTER.COM", "other_XXX_sites")

load_site_duration <- function(site_key) {
  if (site_key == "all_xxx") {
    lapply(XXX_SLUGS, function(s) {
      open_dataset(file.path(data_dir,
                             paste0("machine_aggregated_", s, ".parquet"))) |>
        filter(week_of_sample %in% needed_weeks,
               machine_id     %in% needed_machines) |>
        select(machine_id, week_of_sample, total_duration) |>
        collect()
    }) |>
      bind_rows() |>
      group_by(machine_id, week_of_sample) |>
      summarise(total_duration = sum(total_duration, na.rm = TRUE),
                .groups = "drop")
  } else if (site_key == "other_xxx_combined") {
    lapply(OTHER_XXX_COMBINED_SLUGS, function(s) {
      open_dataset(file.path(data_dir,
                             paste0("machine_aggregated_", s, ".parquet"))) |>
        filter(week_of_sample %in% needed_weeks,
               machine_id     %in% needed_machines) |>
        select(machine_id, week_of_sample, total_duration) |>
        collect()
    }) |>
      bind_rows() |>
      group_by(machine_id, week_of_sample) |>
      summarise(total_duration = sum(total_duration, na.rm = TRUE),
                .groups = "drop")
  } else {
    open_dataset(file.path(data_dir,
                           paste0("machine_aggregated_", site_key, ".parquet"))) |>
      filter(week_of_sample %in% needed_weeks,
             machine_id     %in% needed_machines) |>
      select(machine_id, week_of_sample, total_duration) |>
      collect()
  }
}

# p95 winsorization threshold from 2022 baseline (weeks 1-52) only,
# avoiding secular trends in session duration contaminating the cap.
compute_p95_2022 <- function(site_key) {
  dur <- if (site_key == "all_xxx") {
    lapply(XXX_SLUGS, function(s) {
      open_dataset(file.path(data_dir,
                             paste0("machine_aggregated_", s, ".parquet"))) |>
        filter(week_of_sample %in% 1:52, machine_id %in% needed_machines) |>
        select(machine_id, week_of_sample, total_duration) |>
        collect()
    }) |>
      bind_rows() |>
      group_by(machine_id, week_of_sample) |>
      summarise(total_duration = sum(total_duration, na.rm = TRUE), .groups = "drop")
  } else {
    open_dataset(file.path(data_dir,
                           paste0("machine_aggregated_", site_key, ".parquet"))) |>
      filter(week_of_sample %in% 1:52, machine_id %in% needed_machines) |>
      select(total_duration) |>
      collect()
  }
  quantile(dur$total_duration[dur$total_duration > 0], 0.95, na.rm = TRUE)
}

# Pre-build per-site XXX win_min wide table (called once in prepare_desktop.R / prepare_mobile.R).
build_xxx_win_wide <- function(needed_weeks, needed_machines) {
  cat("\nPre-building per-site XXX win_min (for all_xxx additive construction)...\n")
  t0 <- proc.time()
  xxx_win_prebuilt <- lapply(XXX_SLUGS, function(s) {
    t1    <- proc.time()
    p95_s <- compute_p95_2022(s)
    dur_s <- open_dataset(file.path(data_dir,
                                    paste0("machine_aggregated_", s, ".parquet"))) |>
      filter(week_of_sample %in% needed_weeks, machine_id %in% needed_machines) |>
      select(machine_id, week_of_sample, total_duration) |>
      collect()
    result <- dur_s |>
      mutate(win_min_s = pmin(total_duration, p95_s) / 60) |>
      select(machine_id, week_of_sample, win_min_s)
    names(result)[3] <- paste0("win_", gsub("[^A-Za-z0-9]", "_", s))
    cat(sprintf("  %s: p95 = %.1f min  (%.1fs)\n", s, p95_s / 60,
                (proc.time() - t1)[["elapsed"]]))
    result
  })
  result <- Reduce(
    function(a, b) full_join(a, b, by = c("machine_id", "week_of_sample")),
    xxx_win_prebuilt
  ) |>
    mutate(win_min_allxxx = rowSums(across(starts_with("win_")), na.rm = TRUE))
  cat(sprintf("Pre-build complete: %s rows  (%.1fs total)\n",
              format(nrow(result), big.mark = ","),
              (proc.time() - t0)[["elapsed"]]))
  result
}

# Attach DVs (over60 and win_min) to a stacked panel that already has total_duration.
# Uses xxx_win_wide for XXX sites (additive construction preserving site separability).
attach_dvs <- function(df, site_key, xxx_win_wide) {
  if (site_key == "all_xxx") {
    df |>
      mutate(over60 = as.integer(!is.na(total_duration) & total_duration > 60)) |>
      left_join(select(xxx_win_wide, machine_id, week_of_sample, win_min_allxxx),
                by = c("machine_id", "week_of_sample")) |>
      mutate(win_min = coalesce(win_min_allxxx, 0)) |>
      select(-win_min_allxxx)

  } else if (site_key == "other_xxx_combined") {
    df |>
      mutate(over60 = as.integer(!is.na(total_duration) & total_duration > 60)) |>
      left_join(select(xxx_win_wide, machine_id, week_of_sample, win_other_xxx_combined),
                by = c("machine_id", "week_of_sample")) |>
      rename(win_min = win_other_xxx_combined) |>
      mutate(win_min = coalesce(win_min, 0))

  } else if (site_key %in% XXX_SLUGS) {
    win_col <- paste0("win_", gsub("[^A-Za-z0-9]", "_", site_key))
    df |>
      mutate(over60 = as.integer(!is.na(total_duration) & total_duration > 60)) |>
      left_join(select(xxx_win_wide, machine_id, week_of_sample, all_of(win_col)),
                by = c("machine_id", "week_of_sample")) |>
      rename(win_min = all_of(win_col)) |>
      mutate(win_min = coalesce(win_min, 0))

  } else {
    p95 <- compute_p95_2022(site_key)
    cat(sprintf("  p95 = %.1fs (%.1f min)\n", p95, p95 / 60))
    df |>
      mutate(
        over60  = as.integer(!is.na(total_duration) & total_duration > 60),
        win_min = pmin(replace(total_duration, is.na(total_duration), 0), p95) / 60
      )
  }
}

# Extract event-study coefficients from a fixest fit into a tidy data frame.
extract_coefs <- function(fit) {
  idx   <- grep("treated", names(coef(fit)))
  betas <- coef(fit)[idx]
  se_v  <- sqrt(diag(vcov(fit)))[idx]
  ci    <- confint(fit, level = 0.95)[idx, , drop = FALSE]
  coefs <- data.frame(
    rel_week = as.integer(regmatches(names(betas), regexpr("-?\\d+", names(betas)))),
    beta     = as.numeric(betas),
    se       = as.numeric(se_v),
    ci_lo    = ci[, 1],
    ci_hi    = ci[, 2],
    stringsAsFactors = FALSE
  )
  ref_row <- data.frame(rel_week = -1L, beta = 0, se = NA_real_, ci_lo = 0, ci_hi = 0)
  bind_rows(coefs, ref_row) |> arrange(rel_week)
}

# Pooled three-period TWFE spec.
# Returns list with fields:
#   beta_pre/se_pre/p_pre, beta_shortterm/se_shortterm/p_shortterm,
#   beta_longterm/se_longterm/p_longterm, n_obs, n_mc, r2_within
run_pooled <- function(df, dv) {
  df2 <- df |>
    mutate(
      pre       = as.integer(rel_week %in% PRE_WINDOW),
      shortterm = as.integer(rel_week %in% SHORT_WINDOW),
      longterm  = as.integer(rel_week %in% LONG_WINDOW)
    )
  fml <- as.formula(
    sprintf("%s ~ treated:pre + treated:shortterm + treated:longterm | machine_cohort + cohort_week", dv)
  )
  tryCatch({
    fit  <- feols(fml, data = df2, cluster = ~state, warn = FALSE, notes = FALSE)
    cf   <- coef(fit)
    se_v <- sqrt(diag(vcov(fit)))
    pv   <- 2 * pnorm(-abs(cf / se_v))
    list(
      beta_pre       = unname(cf["treated:pre"]),
      se_pre         = unname(se_v["treated:pre"]),
      p_pre          = unname(pv["treated:pre"]),
      beta_shortterm = unname(cf["treated:shortterm"]),
      se_shortterm   = unname(se_v["treated:shortterm"]),
      p_shortterm    = unname(pv["treated:shortterm"]),
      beta_longterm  = unname(cf["treated:longterm"]),
      se_longterm    = unname(se_v["treated:longterm"]),
      p_longterm     = unname(pv["treated:longterm"]),
      n_obs          = fit$nobs,
      n_mc           = n_distinct(df2$machine_cohort),
      r2_within      = unname(fit$r2["r2_within"])
    )
  }, error = function(e) {
    cat(sprintf("    ERROR: %s\n", conditionMessage(e)))
    list(beta_pre = NA_real_, se_pre = NA_real_, p_pre = NA_real_,
         beta_shortterm = NA_real_, se_shortterm = NA_real_, p_shortterm = NA_real_,
         beta_longterm  = NA_real_, se_longterm  = NA_real_, p_longterm  = NA_real_,
         n_obs = 0L, n_mc = 0L, r2_within = NA_real_)
  })
}

# Interacted TWFE to test whether two mutually exclusive subgroups have
# different treatment effects. expr_g1/expr_g0 are quoted filter expressions
# (same form as subgroups list). Returns difference coefficients and p-values
# for short- and long-term windows. Fixed effects are fully interacted with the
# group indicator so each group gets its own cohort_week FEs.
run_diff_test <- function(df, dv, expr_g1, expr_g0) {
  df_g1 <- df |> filter(!!expr_g1) |> mutate(g = 1L)
  df_g0 <- df |> filter(!!expr_g0) |> mutate(g = 0L)

  bl_g1 <- mean(df_g1[[dv]][df_g1$treated == 1L & df_g1$rel_week %in% BASELINE_WINDOW], na.rm = TRUE)
  bl_g0 <- mean(df_g0[[dv]][df_g0$treated == 1L & df_g0$rel_week %in% BASELINE_WINDOW], na.rm = TRUE)

  df_g1 <- df_g1 |> mutate(across(all_of(dv), \(x) x / bl_g1))
  df_g0 <- df_g0 |> mutate(across(all_of(dv), \(x) x / bl_g0))

  df2   <- bind_rows(df_g1, df_g0) |>
    mutate(
      pre       = as.integer(rel_week %in% PRE_WINDOW),
      shortterm = as.integer(rel_week %in% SHORT_WINDOW),
      longterm  = as.integer(rel_week %in% LONG_WINDOW)
    )
  fml <- as.formula(sprintf(
    "%s ~ treated:pre + treated:shortterm + treated:longterm +
            treated:g:pre + treated:g:shortterm + treated:g:longterm |
            machine_cohort + cohort_week + g^cohort_week",
    dv
  ))
  tryCatch({
    fit  <- feols(fml, data = df2, cluster = ~state, warn = FALSE, notes = FALSE)
    cf   <- coef(fit)
    se_v <- sqrt(diag(vcov(fit)))
    pv   <- 2 * pnorm(-abs(cf / se_v))
    # fixest's name ordering for 3-way interactions is not guaranteed, so grep
    # for a coefficient whose name contains all three expected terms.
    pick <- function(v, terms) {
      nm <- names(v)[Reduce("&", lapply(terms, function(t) grepl(t, names(v), fixed = TRUE)))]
      if (length(nm) == 1L) unname(v[nm]) else {
        cat("    WARN: expected coef {", paste(terms, collapse = ":"), "} not found.",
            "Available:", paste(names(v), collapse = ", "), "\n")
        NA_real_
      }
    }
    list(
      beta_diff_st = pick(cf,   c("treated", ":g", "shortterm")),
      se_diff_st   = pick(se_v, c("treated", ":g", "shortterm")),
      p_diff_st    = pick(pv,   c("treated", ":g", "shortterm")),
      beta_diff_lt = pick(cf,   c("treated", ":g", "longterm")),
      se_diff_lt   = pick(se_v, c("treated", ":g", "longterm")),
      p_diff_lt    = pick(pv,   c("treated", ":g", "longterm"))
    )
  }, error = function(e) {
    cat(sprintf("    ERROR: %s\n", conditionMessage(e)))
    list(beta_diff_st = NA_real_, se_diff_st = NA_real_, p_diff_st = NA_real_,
         beta_diff_lt = NA_real_, se_diff_lt = NA_real_, p_diff_lt = NA_real_)
  })
}

# Save a standard event-study plot (single-series TWFE).
# n_clusters defaults to global n_clusters; qualifying from global.
# y_limits: numeric vector of length 2 passed to scale_y_continuous(limits=),
#   or NULL to let ggplot choose automatically.
# y_breaks: numeric vector of break positions, or ggplot2::waiver() for auto.
save_event_study_plot <- function(coefs, site_label, dv_label, y_label,
                                   slug, dv_slug, out_dir,
                                   baseline_mean = NULL, n_clusters = NULL,
                                   y_limits = NULL, y_breaks = ggplot2::waiver(),
                                   panel_label = NULL, empty = FALSE) {
  if (is.null(n_clusters)) n_clusters <- get("n_clusters", envir = globalenv())
  n_cohorts <- length(get("qualifying", envir = globalenv()))

  p <- ggplot(coefs, aes(x = rel_week)) +
    geom_hline(yintercept = 0, linetype = "dashed", linewidth = 0.5) +
    geom_vline(xintercept = 0, linetype = "dashed", color = "gray50", linewidth = 0.5)

  coefs_show <- if (empty) coefs[coefs$rel_week < 0L, ] else coefs
  p <- p +
    geom_errorbar(data = coefs_show, aes(ymin = ci_lo, ymax = ci_hi), width = 0.3,
                  color = MAROON, linewidth = 0.6) +
    geom_line(data = coefs_show,  aes(y = beta), color = MAROON, linewidth = 0.9) +
    geom_point(data = coefs_show, aes(y = beta), color = MAROON, size = 2)

  p <- p +
    scale_x_continuous(limits = c(T_MIN, T_MAX), breaks = seq(T_MIN, T_MAX, by = 4)) +
    scale_y_continuous(limits = y_limits, breaks = y_breaks) +
    labs(
      x        = "Weeks relative to Pornhub shutdown date",
      y        = y_label,
      title    = if (!is.null(panel_label))
                   sprintf("Panel %s — %s", panel_label, site_label)
                 else
                   sprintf("Stacked TWFE — %s  (%s)", site_label, dv_label),
      subtitle = sprintf(
        "Machine×cohort + cohort×week FE  |  SE clustered by state (%d clusters, %d cohorts)",
        n_clusters, n_cohorts)
    ) +
    theme_bw() +
    theme(
      panel.grid.minor = element_blank(),
      panel.border     = element_blank(),
      axis.line        = element_line(color = "black", linewidth = 0.4),
      plot.title       = element_text(size = 17),
      plot.subtitle    = element_text(size = 8, color = "gray40"),
      axis.title       = element_text(size = 14),
      axis.text        = element_text(size = 13)
    )

  if (!is.null(baseline_mean)) {
    p <- p + annotate("text", x = 0.25, y = 0,
                      label = sprintf("(mean = %.3f)", baseline_mean),
                      hjust = 0, vjust = 1.6, size = 11 / .pt, color = "gray40")
  }

  path <- file.path(out_dir, sprintf("%s_%s.png", slug, dv_slug))
  ggsave(path, p, width = 9, height = 4.5, dpi = 300)
  invisible(p)
}

# Format a coefficient and SE as "β (SE)".  Returns "—" for NA.
fmt_coef <- function(beta, se) {
  if (is.na(beta)) return("\u2014")
  sprintf("%.4f (%.4f)", beta, se)
}

# Build per-machine×cohort pre-period heterogeneity covariates for spec 3.
# Requires stacked_base to have hh_income (loaded in prepare.R).
# Returns a data frame with one row per machine×cohort.
# past_xxx_bin: bin 1 = zero pre-period all-XXX minutes;
#               bins 2-6 = quintiles of positive all-XXX minutes distribution.
build_het_covariates <- function(stacked_base, xxx_win_wide) {
  cat("\nBuilding heterogeneity covariates (pre-period characteristics)...\n")
  t0 <- proc.time()

  pre_mc <- stacked_base |>
    filter(rel_week < 0L) |>
    select(machine_cohort, machine_id, week_of_sample)

  # --- Past XXX activity: bin 1 = never, bins 2-6 = quintiles of positive ---
  vol_agg <- pre_mc |>
    left_join(select(xxx_win_wide, machine_id, week_of_sample, win_min_allxxx),
              by = c("machine_id", "week_of_sample")) |>
    group_by(machine_cohort) |>
    summarise(pre_allxxx_min = sum(coalesce(win_min_allxxx, 0), na.rm = TRUE),
              .groups = "drop") |>
    mutate(
      past_xxx_bin = factor(
        ifelse(pre_allxxx_min == 0,
               1L,
               ntile(ifelse(pre_allxxx_min > 0, pre_allxxx_min, NA_real_), 5) + 1L),
        levels = 1:6
      )
    )

  cat(sprintf("  past_xxx_bin dist: %s\n",
              paste(tabulate(vol_agg$past_xxx_bin, nbins = 6), collapse = " / ")))

  # --- Static demo covariates (kids, age_bin, inc_tercile) ---
  demo_mc <- stacked_base |>
    distinct(machine_cohort, children_present, hoh_age, hh_income)

  # Income: ordered factor, cut into terciles
  income_levels <- sort(unique(na.omit(demo_mc$hh_income)))
  cat(sprintf("  Income levels (%d): %s\n", length(income_levels),
              paste(income_levels, collapse = "; ")))
  inc_num    <- as.integer(factor(demo_mc$hh_income, levels = income_levels))
  inc_breaks <- quantile(inc_num, probs = c(0, 1/3, 2/3, 1), na.rm = TRUE)

  demo_mc <- demo_mc |>
    mutate(
      kids       = as.integer(children_present == "Children:Yes"),
      age_bin    = factor(
                    dplyr::case_when(
                      hoh_age %in% c("18-24", "25-34")        ~ "18-34",
                      hoh_age %in% c("35-44", "45-54")        ~ "35-54",
                      hoh_age %in% c("55-64", "65 and Over")  ~ "55+",
                      TRUE ~ NA_character_
                    ), levels = c("18-34", "35-54", "55+")),
      inc_tercile = factor(
        findInterval(as.integer(factor(hh_income, levels = income_levels)),
                     inc_breaks, rightmost.closed = TRUE),
        levels = 1:3, labels = c("low", "mid", "high")
      )
    ) |>
    select(machine_cohort, kids, age_bin, inc_tercile)

  # --- Past visitor per site: any pre-period minutes > 0 ---
  win_cols_j <- paste0("win_", gsub("[^A-Za-z0-9]", "_", XXX_SLUGS))
  past_visitor_agg <- pre_mc |>
    left_join(select(xxx_win_wide, machine_id, week_of_sample, all_of(win_cols_j)),
              by = c("machine_id", "week_of_sample")) |>
    group_by(machine_cohort) |>
    summarise(
      across(all_of(win_cols_j),
             ~ as.integer(any(!is.na(.x) & .x > 0)),
             .names = "past_visitor_{.col}"),
      .groups = "drop"
    )
  names(past_visitor_agg) <- sub("past_visitor_win_", "past_visitor_",
                                  names(past_visitor_agg))

  result <- vol_agg |>
    select(machine_cohort, past_xxx_bin) |>
    left_join(past_visitor_agg, by = "machine_cohort") |>
    left_join(demo_mc,          by = "machine_cohort")

  cat(sprintf("  Het covariates: %s machine\u00d7cohort (%.1fs)\n",
              format(nrow(result), big.mark = ","),
              (proc.time() - t0)[["elapsed"]]))
  result
}

# Spec 3: fully interacted pooled TWFE (eqn:heterogeneity in draft.tex).
# het_covs: output of build_het_covariates().
# Race excluded: not in full_machine_person_demos.parquet.
# past_xxx_bin: 6-level factor (1=never, 2-6=quintiles of positive all-XXX minutes).
run_interacted <- function(df, dv, het_covs) {
  df2 <- df |>
    left_join(het_covs, by = "machine_cohort") |>
    mutate(
      pre       = as.integer(rel_week %in% PRE_WINDOW),
      shortterm = as.integer(rel_week %in% SHORT_WINDOW),
      longterm  = as.integer(rel_week %in% LONG_WINDOW)
    )

  fml_str <- paste0(
    dv,
    " ~ treated:pre + treated:shortterm + treated:longterm",
    " + treated:pre:past_xxx_bin + treated:shortterm:past_xxx_bin + treated:longterm:past_xxx_bin",
    " + treated:pre:kids + treated:shortterm:kids + treated:longterm:kids",
    " + treated:pre:inc_tercile + treated:shortterm:inc_tercile + treated:longterm:inc_tercile",
    " + treated:pre:age_bin + treated:shortterm:age_bin + treated:longterm:age_bin",
    " | machine_cohort + cohort_week"
  )

  feols(as.formula(fml_str), data = df2, cluster = ~state, warn = FALSE, notes = FALSE)
}
