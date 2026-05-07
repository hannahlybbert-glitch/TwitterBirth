* Author:  Hannah Lybbert
* Created: 02/19/2026
* Updated: 02/23/2026
* Purpose: Log original tweet volume around birth
* Output:  original_tweets.png, original_tweets_gender.png

do "$dofile/set_globals.do"

* Y-axis title
global ytitle_orig "Log Original Tweets"

* Load data
use "$final/ogqt_volume_analysis_sample.dta", clear
gen log_og_tweets = log(og_qt_month_tweets + 1)


* ----------------------------------------------------------------
* FIGURE 1: Original Tweets (Overall)
* ----------------------------------------------------------------
preserve
	collapse (mean) log_og_tweets        ///
	         (sd)   sd_var = log_og_tweets ///
	         (count) n     = log_og_tweets, ///
	         by(months_from_birth)

	gen se       = sd_var / sqrt(n)
	gen ci_lower = log_og_tweets - 1.96 * se
	gen ci_upper = log_og_tweets + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth, lcolor($col_ci_main) lwidth($lw_ci)) ///
		(line log_og_tweets months_from_birth,     lcolor($col_main)    lwidth($lw_main)) ///
		, $xline_birth ///
		  ytitle("$ytitle_orig", size($ytitle_size)) ///
		  $ylab ///
		  $xtitle_months ///
		  $xlab_months ///
		  $leg_off ///
		  $region
	graph export "$vol_out/log_original_tweets.$fig_format", replace
restore


* ----------------------------------------------------------------
* FIGURE 2: Original Tweets by Gender
* ----------------------------------------------------------------
preserve
	collapse (mean) log_og_tweets        ///
	         (sd)   sd_var = log_og_tweets ///
	         (count) n     = log_og_tweets, ///
	         by(months_from_birth female)

	gen se       = sd_var / sqrt(n)
	gen ci_lower = log_og_tweets - 1.96 * se
	gen ci_upper = log_og_tweets + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth if female==1, lcolor($col_ci_female) lwidth($lw_ci)) ///
		(rcap ci_upper ci_lower months_from_birth if female==0, lcolor($col_ci_male)   lwidth($lw_ci)) ///
		(line log_og_tweets months_from_birth     if female==1, lcolor($col_female)    lwidth($lw_main)) ///
		(line log_og_tweets months_from_birth     if female==0, lcolor($col_male)      lwidth($lw_main)) ///
		, $xline_birth ///
		  ytitle("$ytitle_orig", size($ytitle_size)) ///
		  $ylab ///
		  $xtitle_months ///
		  $xlab_months ///
		  $leg_gender ///
		  $region
	graph export "$vol_out/log_original_tweets_gender.$fig_format", replace
restore
