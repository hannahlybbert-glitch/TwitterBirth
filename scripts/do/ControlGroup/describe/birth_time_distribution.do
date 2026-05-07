* Author: Hannah Lybbert
* Created: 04/28/2026
* Updated: 04/28/2026
* Purpose: Distribution of birth tweet times across a 24-hour period for final sample authors

do "$dofile/set_globals.do"

// local outdir "$output/placebo/describe"

* ----------------------------------------------------------------
* Step 1: Get final sample authors from volume analysis
* ----------------------------------------------------------------
use "$volume_analysis/ogqt_volume_analysis_sample.dta", clear
keep author_id
duplicates drop
tempfile volume_authors
save `volume_authors'

* ----------------------------------------------------------------
* Step 2: Extract birth tweet time from user_info_full_sample
* unique_id format: 100011302_2016-07-26T22:06:15.000Z
* Keep only the portion after the "T"
* ----------------------------------------------------------------
use "$cleaned/user_info_full_sample.dta", clear

gen time_birth_tweet = substr(unique_id, strpos(unique_id, "T") + 1, .)

keep author_id time_birth_tweet

* ----------------------------------------------------------------
* Step 3: Restrict to final sample authors
* ----------------------------------------------------------------
merge m:1 author_id using `volume_authors', keep(match) nogen

* ----------------------------------------------------------------
* Step 4: Extract hour and plot distribution across 24-hour period
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
