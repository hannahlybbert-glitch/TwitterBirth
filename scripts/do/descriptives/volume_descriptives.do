* Author:  Hannah Lybbert
* Created: 2026-04-13
* Updated: 2026-04-14
* Purpose: Volume descriptive figures and statistics

do "$dofile/set_globals.do"

global vol_desc_out "$output/descriptives/volume"
capture mkdir "$output/descriptives"
capture mkdir "$vol_desc_out"

use "$final/tweet_volume_analysis_sample.dta", clear

* ----------------------------------------------------------------
* CREATE VARIABLES
* ----------------------------------------------------------------
* Total orig+quote tweets per author across full 3-year sample
bysort author_id: egen total_orig_quote_tweets = sum(orig_qt_count)

* Total orig+quote tweets per author by pre/post period
bysort author_id post_birth: egen total_orig_qt_period = sum(orig_qt_count)

* ----------------------------------------------------------------
* FIGURE 2: Distribution of total orig+quote tweets per author
* ----------------------------------------------------------------
preserve
	bysort author_id: keep if _n == 1
	gen total_oq_capped = min(total_orig_quote_tweets, 5000)
	hist total_oq_capped, bin(50) freq ///
		xtitle("Total Original & Quote Tweets (3-Year Period)", size($xtitle_size)) ///
		ytitle("Number of Accounts", size($ytitle_size)) ///
		color($col_main%70) ///
		xlabel(0(500)5000) ///
		$region
	graph export "$vol_desc_out/hist_orig_qt_totals.$fig_format", replace
restore

* ----------------------------------------------------------------
* FIGURE 3: Distribution of total orig+quote tweets pre vs post birth
* ----------------------------------------------------------------
preserve
	bysort author_id post_birth: keep if _n == 1
	gen period_oq_capped = min(total_orig_qt_period, 2000)
	twoway ///
		(histogram period_oq_capped if post_birth == 0, bin(50) freq color(gs4%50) lcolor(gs2) lwidth(thin)) ///
		(histogram period_oq_capped if post_birth == 1, bin(50) freq color(purple%50) lcolor(gs2) lwidth(thin)), ///
		xtitle("Total Original & Quote Tweets", size($xtitle_size)) ///
		ytitle("Number of Accounts", size($ytitle_size)) ///
		legend(order(1 "Pre-Birth" 2 "Post-Birth") $leg_pos_ur) ///
		xlabel(0(500)2000) ///
		$region
	graph export "$vol_desc_out/hist_orig_qt_totals_prepost.$fig_format", replace
restore
