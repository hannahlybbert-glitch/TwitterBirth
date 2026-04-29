* Author:  Hannah Lybbert
* Created: 2026-01-09
* Updated: 2026-04-13
* Purpose: Distribution of average sentiment score pre vs post birth

do "$dofile/set_globals.do"

global sent_desc_out "$output/descriptives/sentiment"
capture mkdir "$output/descriptives"
capture mkdir "$sent_desc_out"

use "$sentiment/output/sentiment_analysis_sample.dta", clear

* ----------------------------------------------------------------
* FIGURE: Distribution of average sentiment score pre vs post birth
* ----------------------------------------------------------------
preserve
	* Average sentiment score per account pre and post birth
	bysort author_id (post): egen score_pre  = mean(cond(post==0, sentiment_score, .))
	bysort author_id (post): egen score_post = mean(cond(post==1, sentiment_score, .))
	bysort author_id: keep if _n == 1

	keep author_id score_pre score_post
	reshape long score_, i(author_id) j(period) string
	rename score_ avg_score
	replace period = "Pre-Birth"  if period == "pre"
	replace period = "Post-Birth" if period == "post"

	twoway ///
		(histogram avg_score if period=="Pre-Birth",  bin(50) color(gs4%50)    freq) ///
		(histogram avg_score if period=="Post-Birth", bin(50) color(purple%50) freq), ///
		xtitle("Average Sentiment Score <---(-)--------(+)--->", size($xtitle_size)) ///
		ytitle("Number of Accounts", size($ytitle_size)) ///
		legend(order(1 "Pre-Birth" 2 "Post-Birth") $leg_pos_ur) ///
		$region
	graph export "$sent_desc_out/sentiment_prepost.$fig_format", replace
restore
