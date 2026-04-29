* Author:  Hannah Lybbert
* Created: 02/19/2026
* Updated: 02/23/2026
* Purpose: Log retweet and reply volume around birth — overall and by gender

* Output:  log_rt_replies.jpg, log_rt_replies_gender.jpg

do "$dofile/set_globals.do"
di "$ylab"
di "$xlab_months"


* Y-axis title
global ytitle_rt "Log Retweets and Replies"

* Load data
use "$volume_analysis/tweet_volume_analysis_sample.dta", clear
gen lrt_rp_month_tweets = log(rt_rp_month_tweets + 1)
di "$ylab"
di "$xlab_months"

* ----------------------------------------------------------------
* FIGURE 1: Retweets and Replies (Overall)
* ----------------------------------------------------------------
preserve
	collapse (mean) lrt_rp_month_tweets        ///
	         (sd)   sd_var = lrt_rp_month_tweets ///
	         (count) n     = lrt_rp_month_tweets, ///
	         by(months_from_birth)

	gen se       = sd_var / sqrt(n)
	gen ci_lower = lrt_rp_month_tweets - 1.96 * se
	gen ci_upper = lrt_rp_month_tweets + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth,   lcolor($col_ci_main) lwidth($lw_ci)) ///
		(line lrt_rp_month_tweets months_from_birth, lcolor($col_main)    lwidth($lw_main)) ///
		, $xline_birth ///
		  ytitle("$ytitle_rt", size($ytitle_size)) ///
		  $ylab ///
		  $xtitle_months ///
		  $xlab_months ///
		  $leg_off ///
		  $region
	graph export "$vol_out/log_rt_replies.$fig_format", replace
restore


* ----------------------------------------------------------------
* FIGURE 2: Retweets and Replies by Gender
* ----------------------------------------------------------------
preserve
	collapse (mean) lrt_rp_month_tweets        ///
	         (sd)   sd_var = lrt_rp_month_tweets ///
	         (count) n     = lrt_rp_month_tweets, ///
	         by(months_from_birth female)

	gen se       = sd_var / sqrt(n)
	gen ci_lower = lrt_rp_month_tweets - 1.96 * se
	gen ci_upper = lrt_rp_month_tweets + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth    if female==1, lcolor($col_ci_female) lwidth($lw_ci)) ///
		(rcap ci_upper ci_lower months_from_birth    if female==0, lcolor($col_ci_male)   lwidth($lw_ci)) ///
		(line lrt_rp_month_tweets months_from_birth  if female==1, lcolor($col_female)    lwidth($lw_main)) ///
		(line lrt_rp_month_tweets months_from_birth  if female==0, lcolor($col_male)      lwidth($lw_main)) ///
		, $xline_birth ///
		  ytitle("$ytitle_rt", size($ytitle_size)) ///
		  $ylab ///
		  $xtitle_months ///
		  $xlab_months ///
		  $leg_gender ///
		  $region
	graph export "$vol_out/log_rt_replies_gender.$fig_format", replace
restore
