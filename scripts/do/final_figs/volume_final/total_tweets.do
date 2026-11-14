* Author:  Hannah Lybbert
* Created: 02/19/2026
* Updated: 02/23/2026
* Purpose: Log total tweet volume around birth
* Output:  total_tweets.png, total_tweets_gender.png

* TODO (flagged 2026-11-11): SE/CI BUG — FINAL FIGURES, FIX BEFORE USING.
*   Data are author-day rows, so collapsing straight to months counts each author ~30x
*   -> n = author-days, CIs ~5.5x too narrow (means are fine).
*   Fix: after line creating ltotal_month_tweets, add
*     collapse (first) ltotal_month_tweets female, by(author_id months_from_birth)
*   Affected: Figure 3 and Figure 4 (marked "TODO SE BUG" below).

do "$dofile/set_globals.do"

* Y-axis title
global ytitle_total "Log Total Tweets"

* Load data
use "$final/tweet_volume_analysis_sample.dta", clear
gen ltotal_month_tweets = log(total_month_tweets + 1)


* ----------------------------------------------------------------
* FIGURE 3: Total Tweets (Overall)
* ----------------------------------------------------------------
preserve
	* TODO SE BUG: n = author-days, not authors (see header)
	collapse (mean) ltotal_month_tweets        ///
	         (sd)   sd_var = ltotal_month_tweets ///
	         (count) n     = ltotal_month_tweets, ///
	         by(months_from_birth)

	gen se       = sd_var / sqrt(n)
	gen ci_lower = ltotal_month_tweets - 1.96 * se
	gen ci_upper = ltotal_month_tweets + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth,  lcolor($col_ci_main) lwidth($lw_ci)) ///
		(line ltotal_month_tweets months_from_birth, lcolor($col_main)    lwidth($lw_main)) ///
		, $xline_birth ///
		  ytitle("$ytitle_total", size($ytitle_size)) ///
		  $ylab ///
		  $xtitle_months ///
		  $xlab_months ///
		  $leg_off ///
		  $region
	graph export "$vol_out/log_total_tweets.$fig_format", replace
restore


* ----------------------------------------------------------------
* FIGURE 4: Total Tweets by Gender
* ----------------------------------------------------------------
preserve
	* TODO SE BUG: n = author-days, not authors (see header)
	collapse (mean) ltotal_month_tweets        ///
	         (sd)   sd_var = ltotal_month_tweets ///
	         (count) n     = ltotal_month_tweets, ///
	         by(months_from_birth female)

	gen se       = sd_var / sqrt(n)
	gen ci_lower = ltotal_month_tweets - 1.96 * se
	gen ci_upper = ltotal_month_tweets + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth  if female==1, lcolor($col_ci_female) lwidth($lw_ci)) ///
		(rcap ci_upper ci_lower months_from_birth  if female==0, lcolor($col_ci_male)   lwidth($lw_ci)) ///
		(line ltotal_month_tweets months_from_birth if female==1, lcolor($col_female)    lwidth($lw_main)) ///
		(line ltotal_month_tweets months_from_birth if female==0, lcolor($col_male)      lwidth($lw_main)) ///
		, $xline_birth ///
		  ytitle("$ytitle_total", size($ytitle_size)) ///
		  $ylab ///
		  $xtitle_months ///
		  $xlab_months ///
		  $leg_gender ///
		  $region
	graph export "$vol_out/log_total_tweets_gender.$fig_format", replace
restore
