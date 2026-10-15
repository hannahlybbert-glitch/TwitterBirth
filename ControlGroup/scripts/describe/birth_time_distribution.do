* Author: Hannah Lybbert
* Created: 04/28/2026
* Updated: 05/07/2026
* Purpose: Distribution of birth tweet times across a 24-hour period for final sample authors

do "$dofile/set_globals.do"

// local outdir "$output/placebo/describe"

* ----------------------------------------------------------------
* Step 1: Load final sample (unique_id format: authorid_YYYY-MM-DDTHH:MM:SS.000Z)
* ----------------------------------------------------------------
use "$final/user_analysis_sample.dta", clear

gen time_birth_tweet = substr(unique_id, strpos(unique_id, "T") + 1, .)

* ----------------------------------------------------------------
* Step 2: Extract hour and plot distribution across 24-hour period
* ----------------------------------------------------------------
gen hour_birth = real(substr(time_birth_tweet, 1, 2))
label var hour_birth "Hour of Day (UTC)"

histogram hour_birth, ///
    discrete freq ///
    color("$col_main") ///
    xlabel(0(2)23, labsize($xtick_size)) ///
    ylabel(, labsize($ytick_size)) ///
    xtitle("Hour of Day (UTC)", size($xtitle_size)) ///
    ytitle("Number of Authors", size($ytitle_size)) ///
    $region

// graph export "`outdir'/birth_time_dist.jpg", width($fig_width) height($fig_height) replace
