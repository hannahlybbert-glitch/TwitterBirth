* Author:  Hannah Lybbert
* Created: 02/20/2026
* Updated: 02/23/2026
* Purpose: Diverging dot plot of post-pre change in absolute tweet volume by topic across all 19 topics
			* How did raw number of tweets per topic change after birth?

do "$dofile/set_globals.do"

use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear


* ----------------------------------------------------------------
* Block 1: Account-level SE calculation
* ----------------------------------------------------------------
preserve
	gen count_var = 1
	collapse (sum) n=count_var, by(author_id post_birth topic)

	keep author_id post_birth topic n
	reshape wide n, i(author_id topic) j(post_birth)

	replace n0 = 0 if n0 == .
	replace n1 = 0 if n1 == .

	gen change_account_level = n1 - n0

	collapse (mean) mean_change_level=change_account_level ///
		(sd) sd_change_level=change_account_level ///
		(count) n_accounts=change_account_level, by(topic)

	gen se_change_level = sd_change_level / sqrt(n_accounts)

	tempfile account_se
	save `account_se'
restore


* ----------------------------------------------------------------
* Block 2: Aggregate level change + plot
* ----------------------------------------------------------------
preserve
	gen count_var = 1
	collapse (sum) n=count_var, by(author_id post_birth topic)

	bysort post_birth topic: egen topic_tweets = sum(n)
	bysort post_birth topic: egen n_distinct_accounts = count(author_id)
	gen tweets_per_account = topic_tweets / n_distinct_accounts

	bysort post_birth topic: keep if _n == 1
	keep post_birth topic tweets_per_account n_distinct_accounts

	reshape wide tweets_per_account n_distinct_accounts, i(topic) j(post_birth)
	gen change_level = tweets_per_account1 - tweets_per_account0

	merge 1:1 topic using `account_se', nogen

	gen change_ci_lower = change_level - 1.96 * se_change_level
	gen change_ci_upper = change_level + 1.96 * se_change_level

	* Clean up topic names
	gen topic_clean = topic
	replace topic_clean = subinstr(topic_clean, "_&_", " & ", .)
	replace topic_clean = subinstr(topic_clean, "_", " ", .)
	replace topic_clean = proper(topic_clean)

	* Sort and assign plot order
	gsort -change_level
	gen order = _n
	labmask order, values(topic_clean)

	twoway ///
		(rcap change_ci_upper change_ci_lower order, horizontal lcolor($col_ci_main) lwidth($lw_dot_ci)) ///
		(scatter order change_level, mcolor($col_main) msize($msize_dot) msymbol($msym)), ///
		$xline_zero ///
		ylabel(1(1)19, valuelabel angle(0) labsize($ytopics_size)) ///
		xlabel(, labsize($xtick_size) format(%3.1f)) ///
		ytitle("") ///
		xtitle("Change in Tweets", size($xtitle_size)) ///
		$leg_off ///
		$region

	graph export "$topics_out/topic_level_diff.$fig_format", replace

	list topic_clean change_level se_change_level change_ci_lower change_ci_upper ///
		tweets_per_account0 tweets_per_account1 n_distinct_accounts0 n_distinct_accounts1, ///
		clean noobs

restore


* ----------------------------------------------------------------
* Block 3: Unconditional mean — same denominator as SE (for comparison)
* Point estimate = mean(n1 - n0) across all accounts in either period
* ----------------------------------------------------------------
preserve
	use `account_se', clear

	gen ci_lower = mean_change_level - 1.96 * se_change_level
	gen ci_upper = mean_change_level + 1.96 * se_change_level

	gen topic_clean = topic
	replace topic_clean = subinstr(topic_clean, "_&_", " & ", .)
	replace topic_clean = subinstr(topic_clean, "_", " ", .)
	replace topic_clean = proper(topic_clean)

	gsort -mean_change_level
	gen order = _n
	labmask order, values(topic_clean)

	twoway ///
		(rcap ci_upper ci_lower order, horizontal lcolor($col_ci_main) lwidth($lw_dot_ci)) ///
		(scatter order mean_change_level, mcolor($col_main) msize($msize_dot) msymbol($msym)), ///
		$xline_zero ///
		ylabel(1(1)19, valuelabel angle(0) labsize($ytopics_size)) ///
		xlabel(, labsize($xtick_size) format(%3.1f)) ///
		ytitle("") ///
		xtitle("Change in Tweets", size($xtitle_size)) ///
		$leg_off ///
		$region

	graph export "$topics_out/topic_level_diff_acct.$fig_format", replace

	list topic_clean mean_change_level se_change_level ci_lower ci_upper n_accounts, ///
		clean noobs

restore
