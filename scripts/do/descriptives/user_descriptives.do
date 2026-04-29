* Author:  Hannah Lybbert
* Created: 2026-04-10
* Updated: 2026-04-14
* Purpose: User-level descriptive figures and summary stats for full sample

do "$dofile/set_globals.do"

global desc_out "$output/descriptives"
capture mkdir "$desc_out"

* ----------------------------------------------------------------
* LOAD & FILTER
* ----------------------------------------------------------------
use "$final/user_info_full_sample_CLEAN.dta", clear
keep if full_3years == 1

* ----------------------------------------------------------------
* FIGURE 1: Gender split (Male / Female / Unknown)
* ----------------------------------------------------------------
tempvar gender_cat
gen `gender_cat' = .
replace `gender_cat' = 1 if female == 0
replace `gender_cat' = 2 if female == 1
replace `gender_cat' = 3 if female == -99
label define gender_lbl 1 "Male" 2 "Female" 3 "Unknown", replace
label values `gender_cat' gender_lbl

graph bar (percent), over(`gender_cat') ///
	ytitle("Share of Accounts", size($ytitle_size)) ///
	blabel(total, format(%9.1f) size(medlarge)) ///
	asyvars ///
	bar(1, color($col_male%60)) bar(2, color($col_female%60)) bar(3, color(gs10%60)) ///
	legend(label(1 "Male") label(2 "Female") label(3 "Unknown") $leg_pos_ur) ///
	$region ///
	name(gender_fig, replace)
graph export "$desc_out/gender_shares.$fig_format", replace

* ----------------------------------------------------------------
* FIGURE 2: Race split
* ----------------------------------------------------------------
graph pie, over(race) ///
	plabel(1 percent, format(%9.1f) size(medlarge) gap(-10)) ///
	plabel(2 percent, format(%9.1f) size(medlarge)) ///
	plabel(3 percent, format(%9.1f) size(medlarge)) ///
	plabel(4 percent, format(%9.1f) size(medlarge) gap(10)) ///
	plabel(5 percent, format(%9.1f) size(medlarge) gap(0)) ///
	plabel(6 percent, format(%9.1f) size(medlarge) gap(10)) ///
	pie(1, color(teal%60)) pie(2, color(maroon%60)) pie(3, color(forest_green%60)) ///
	pie(4, color(dkorange%60)) pie(5, color(navy%60)) pie(6, color(cranberry%60)) ///
	legend(label(1 "Unknown") label(2 "Black") label(3 "White") ///
	       label(4 "Asian") label(5 "Hispanic") label(6 "Other") $leg_pos_ur) ///
	$region ///
	name(race_fig, replace)
graph export "$desc_out/race_shares.$fig_format", replace

* ----------------------------------------------------------------
* FIGURE 2b: Combined gender + race panel (1x2)
* ----------------------------------------------------------------
graph combine gender_fig race_fig, ///
	cols(2) ///
	$region
graph export "$desc_out/gender_race_shares.$fig_format", replace

* ----------------------------------------------------------------
* FIGURE 3: Date of birth distribution
// 		title("Distribution of Birth Dates in Sample") ///
* ----------------------------------------------------------------
hist date_birth, freq ///
	xtitle("Date of Birth", size($xtitle_size)) ///
	ytitle("Number of Accounts", size($ytitle_size)) ///
	color($col_main%70) ///
	xlabel(, format(%tdMonCCYY)) ///
	$region
graph export "$desc_out/DOB_dist.$fig_format", replace

* ----------------------------------------------------------------
* FIGURE 4: Days from birth distribution
* (days_from: - = announcement before birth, + = announcement after birth)
// 			title("Difference in days from Birth Tweet and DOB") ///
* ----------------------------------------------------------------
hist days_from, freq gap(0) ///
	xtitle("Days Between Birth Tweet and Date of Birth", size($xtitle_size)) ///
	ytitle("Number of Accounts", size($ytitle_size)) ///
	color($col_main%70) ///
	$region
graph export "$desc_out/days_from_dist.$fig_format", replace

* ----------------------------------------------------------------
* FIGURE 4a: Days from birth distribution (capped at -7/7)
* ----------------------------------------------------------------
gen days_from_capped = max(min(days_from, 7), -7)
hist days_from_capped, freq width(2) gap(0) ///
	xtitle("Days Between Birth Tweet and Date of Birth", size($xtitle_size)) ///
	ytitle("Number of Accounts", size($ytitle_size)) ///
	color($col_main%70) ///
	xlabel(-7(1)7) ///
	$region
graph export "$desc_out/days_from_dist_capped.$fig_format", replace

* ----------------------------------------------------------------
* FIGURE 4b: Absolute value of days from birth distribution
* ----------------------------------------------------------------
gen abs_days_from = abs(days_from)
hist abs_days_from, freq width(2) gap(0) ///
	xtitle("Absolute Days Between Birth Tweet and Date of Birth", size($xtitle_size)) ///
	ytitle("Number of Accounts", size($ytitle_size)) ///
	color($col_main%70) ///
	$region
graph export "$desc_out/abs_days_from_dist.$fig_format", replace

* ----------------------------------------------------------------
* FIGURE 4c: Absolute value of days from birth, capped at 7
* ----------------------------------------------------------------
gen abs_days_from_capped = min(abs_days_from, 7)
hist abs_days_from_capped, freq width(1) gap(0) ///
	xtitle("Absolute Days Between Birth Tweet and Date of Birth", size($xtitle_size)) ///
	ytitle("Number of Accounts", size($ytitle_size)) ///
	color($col_main%70) ///
	xlabel(0(1)7) ///
	note("Values beyond 7 days grouped into the 7 bin.") ///
	$region
graph export "$desc_out/abs_days_from_dist_capped.$fig_format", replace

* ----------------------------------------------------------------
* FIGURE 5: Account creation date distribution
	// 	title("Distribution of Twitter Account Creation Dates") ///
* ----------------------------------------------------------------
hist user_created_at, freq ///
	xtitle("Account Creation Date", size($xtitle_size)) ///
	ytitle("Number of Accounts", size($ytitle_size)) ///
	color($col_main%70) ///
	xlabel(, format(%tdMonCCYY)) ///
	$region
graph export "$desc_out/account_creation_dist.$fig_format", replace

* ----------------------------------------------------------------
* SUMMARY STATS TABLE
* Vars: followers_count, following_count, lifetime_posts,
*       orig_qt_count (3yr orig+quote), rt_reply_count (3yr rt+reply)
* Stats: N, mean, median, SD, min, max
* Requires: ssc install estout
* ----------------------------------------------------------------
estpost summarize followers_count following_count lifetime_posts ///
                  orig_qt_count rt_reply_count, detail

esttab using "$desc_out/user_sum_stats.tex", replace ///
    cells("count(fmt(%9.0f) label(N)) mean(fmt(%9.2f) label(Mean)) p50(fmt(%9.2f) label(Median)) sd(fmt(%9.2f) label(SD)) min(fmt(%9.0f) label(Min)) max(fmt(%9.0f) label(Max))") ///
    noobs nonumber nomtitle ///
    title("Summary Statistics") ///
    booktabs

di "Saved summary stats to $desc_out/user_sum_stats.tex"
