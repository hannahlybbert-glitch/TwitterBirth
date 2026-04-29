* Author:  Hannah Lybbert
* Created: 2026-04-13
* Updated: 2026-04-14
* Purpose: Avg unique subreddits per author per month relative to birth (zero-filled)

do "$dofile/set_globals_reddit.do"

global sub_div_out "$output/analysis/topics"
capture mkdir "$output/analysis"
capture mkdir "$sub_div_out"

* ----------------------------------------------------------------
* LOAD & FILTER
* Sample: full_18_pre == 1, window ±18 months
* ----------------------------------------------------------------
import delimited "$Reddit_final/births_and_posts_FULL.csv", ///
    bindquote(strict) maxquotedrows(unlimited) clear

keep if full_18_pre == 1
keep if months_from_birth >= -18 & months_from_birth <= 18
keep author female months_from_birth subreddit

* ----------------------------------------------------------------
* BUILD AUTHOR-MONTH PANEL: unique subreddits per author-month
* Zero-filled: all sample authors × all months in ±18 window
* ----------------------------------------------------------------

* Save author roster with gender before collapsing
preserve
    bysort author: keep if _n == 1
    keep author female
    tempfile authors
    save `authors'
restore

* Deduplicate to author × month × subreddit (count each subreddit once)
bysort author months_from_birth subreddit: keep if _n == 1

* Count unique subreddits per author-month (active months only)
bysort author months_from_birth: gen n_sub = _N

* Collapse to one row per author-month
bysort author months_from_birth: keep if _n == 1
keep author months_from_birth n_sub

* Expand to full author × month panel; zero-fill inactive months
fillin author months_from_birth
replace n_sub = 0 if _fillin == 1
drop _fillin

* Restore gender from author roster
merge m:1 author using `authors', nogen keep(master match)

winsor2 n_sub, cuts(0 99) replace
keep author months_from_birth n_sub female

* ----------------------------------------------------------------
* SAMPLE COUNTS
* ----------------------------------------------------------------
bysort author: gen byte auth_tag = (_n == 1)
qui count if auth_tag == 1
local n_authors = r(N)
qui count if auth_tag == 1 & female == 1
local n_female = r(N)
qui count if auth_tag == 1 & female == 0
local n_male = r(N)
drop auth_tag

di ""
di "===================================================="
di "AUTHORS IN SAMPLE (full_18_pre == 1):  `n_authors'"
di "  Female: `n_female'   Male: `n_male'"
di "===================================================="
di ""

* ----------------------------------------------------------------
* FIGURE 1: Overall — avg unique subreddits
* ----------------------------------------------------------------
preserve
	collapse (mean) mean_sub  = n_sub ///
	         (sd)   sd_sub    = n_sub ///
	         (count) active_n = n_sub, ///
	         by(months_from_birth)

	gen se       = sd_sub / sqrt(active_n)
	gen ci_lower = mean_sub - 1.96 * se
	gen ci_upper = mean_sub + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth, lcolor($col_ci_main) lwidth($lw_ci)) ///
		(line mean_sub months_from_birth, lcolor($col_main) lwidth($lw_main)) ///
		, $xline_birth ///
		  ytitle("Unique Subreddits per Month", size($ytitle_size)) ///
		  $ylab ///
		  $xtitle_months ///
		  $xlab_months ///
		  $leg_off ///
		  $region
	graph export "$sub_div_out/unique_subreddits.$fig_format", replace
restore

* ----------------------------------------------------------------
* FIGURE 2: By gender
* ----------------------------------------------------------------
preserve
	collapse (mean) mean_sub  = n_sub ///
	         (sd)   sd_sub    = n_sub ///
	         (count) active_n = n_sub, ///
	         by(months_from_birth female)

	gen se       = sd_sub / sqrt(active_n)
	gen ci_lower = mean_sub - 1.96 * se
	gen ci_upper = mean_sub + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth if female==1, lcolor($col_ci_female) lwidth($lw_ci)) ///
		(rcap ci_upper ci_lower months_from_birth if female==0, lcolor($col_ci_male)   lwidth($lw_ci)) ///
		(line mean_sub months_from_birth if female==1, lcolor($col_female) lwidth($lw_main)) ///
		(line mean_sub months_from_birth if female==0, lcolor($col_male)   lwidth($lw_main)) ///
		, $xline_birth ///
		  ytitle("Unique Subreddits per Month", size($ytitle_size)) ///
		  $ylab ///
		  $xtitle_months ///
		  $xlab_months ///
		  $leg_gender_line ///
		  $region
	graph export "$sub_div_out/unique_subreddits_gender.$fig_format", replace
restore