* Author:  Hannah Lybbert
* Created: 02/20/2026
* Updated: 02/23/2026
* Purpose: Extensive margin — share of accounts active each month by gender, with 95% CIs

do "$dofile/set_globals.do"

use "$volume_analysis/tweet_volume_analysis_sample.dta", clear

preserve
	* Step 1: One obs per (author × month × gender) — get their average monthly tweets
	collapse (mean) total_month_tweets, by(months_from_birth author_id female)
	sort author_id months_from_birth

	* Step 2: Binary indicator — did this account tweet at all this month?
	gen active_this_month = (total_month_tweets > 0)

	* Step 3: Collapse to (month × gender) cell means + counts for CI denominator
	collapse (mean) active_this_month ///
			 (count) N = active_this_month, ///
			 by(months_from_birth female)

	* Step 4: 95% CI using normal approximation for a proportion: ±1.96*sqrt(p(1-p)/N)
	gen se       = sqrt(active_this_month * (1 - active_this_month) / N)
	gen ci_upper = active_this_month + 1.96 * se
	gen ci_lower = active_this_month - 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth if female==1, lcolor($col_ci_female) lwidth($lw_ci)) ///
		(rcap ci_upper ci_lower months_from_birth if female==0, lcolor($col_ci_male)   lwidth($lw_ci)) ///
		(line active_this_month months_from_birth if female==1, lcolor($col_female)    lwidth($lw_main)) ///
		(line active_this_month months_from_birth if female==0, lcolor($col_male)      lwidth($lw_main)) ///
		, $xline_birth ///
		$xlab_months ///
		$xtitle_months ///
		ytitle("Share Active", size($ytitle_size)) ///
		$ylab ///
		$leg_gender ///
		$region

	graph export "$ext_out/extensive_margin_gender.$fig_format", replace
restore
