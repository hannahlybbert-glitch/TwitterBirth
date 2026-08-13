* Author:  Hannah Lybbert
* Created: 08/192/2026
* Updated: 08/12/2026
* Purpose: Log original tweet volume around birth -- treatment vs. control

// do "$dofile/set_globals.do"

* Y-axis title
global ytitle_orig "Log Tweets: Treatment vs. Control"

* Control line color: light-medium gray, slightly darker than the CI band's gs10
global col_control "gs8"

* Load data
use "$final/volume_control_treatment_sample.dta", clear

gen log_og_tweets = log(og_qt_month_tweets + 1)


* ----------------------------------------------------------------
* FIGURE 1: Original Tweets, Treatment vs. Control
* ----------------------------------------------------------------
preserve
	collapse (mean) log_og_tweets        ///
	         (sd)   sd_var = log_og_tweets ///
	         (count) n     = log_og_tweets, ///
	         by(months_from_birth treated)

	gen se       = sd_var / sqrt(n)
	gen ci_lower = log_og_tweets - 1.96 * se
	gen ci_upper = log_og_tweets + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth if treated==1, lcolor($col_ci_main) lwidth($lw_ci)) ///
		(line log_og_tweets months_from_birth     if treated==1, lcolor($col_main)    lwidth($lw_main)) ///
		(line log_og_tweets months_from_birth     if treated==0, lcolor($col_control) lwidth($lw_main)) ///
		, $xline_birth ///
		  ytitle("$ytitle_orig", size($ytitle_size)) ///
		  $ylab ///
		  $xtitle_months ///
		  $xlab_months ///
		  legend(order(2 "Treatment" 3 "Control") $leg_pos_lr) ///
		  $region
	graph export "$vol_out/log_treat_control.$fig_format", replace
restore
