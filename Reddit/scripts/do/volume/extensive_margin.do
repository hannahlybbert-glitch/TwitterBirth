* Author:  Hannah Lybbert
* Created: 2026-04-09
* Updated: 2026-04-09
* Purpose: Extensive margin — share of accounts active each month by gender, with 95% CIs
* Output:  extensive_margin_gender.jpg

do "$dofile/set_globals_reddit.do"

* ----------------------------------------------------------------
* LOAD & FILTER
* Sample: full_18_pre == 1 (no posted_after_birth restriction)
* ----------------------------------------------------------------
import delimited "$Reddit_final/births_and_posts_FULL.csv", bindquote(strict) maxquotedrows(unlimited) clear
keep if full_18_pre == 1
keep author female months_from_birth id

* ----------------------------------------------------------------
* BUILD FULL PANEL: all authors x months [-18, 18] with zero-fill
* An author with no posts in a month gets active=0 for that month
* Mirrors Python: panel cross-join then fill zeros
* ----------------------------------------------------------------

* Save author-gender mapping before collapsing
preserve
	keep author female
	duplicates drop
	tempfile author_gender
	save `author_gender'
restore

* Count posts per author-month from raw post-level data
gen byte counter = 1
collapse (count) posts = counter, by(author months_from_birth)
tempfile post_counts
save `post_counts'

* Expand author list to full panel (37 months: -18 to 18)
use `author_gender', clear
expand 37
bysort author: gen months_from_birth = -18 + (_n - 1)

* Merge in actual post counts; missing months = 0 posts
merge 1:1 author months_from_birth using `post_counts', keep(master match) nogen
replace posts = 0 if posts == .

* Binary indicator: did this account post at all this month?
gen active = (posts > 0)

* ----------------------------------------------------------------
* FIGURE: Extensive Margin by Gender
* ----------------------------------------------------------------
preserve
	* Collapse to (month x gender): mean active + count for CI denominator
	collapse (mean) active ///
	         (count) N = active, ///
	         by(months_from_birth female)

	* 95% CI using normal approximation for a proportion: ±1.96*sqrt(p(1-p)/N)
	gen se       = sqrt(active * (1 - active) / N)
	gen ci_upper = active + 1.96 * se
	gen ci_lower = active - 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth if female==1, lcolor($col_ci_female) lwidth($lw_ci)) ///
		(rcap ci_upper ci_lower months_from_birth if female==0, lcolor($col_ci_male)   lwidth($lw_ci)) ///
		(line active months_from_birth if female==1, lcolor($col_female) lwidth($lw_main)) ///
		(line active months_from_birth if female==0, lcolor($col_male)   lwidth($lw_main)) ///
		, $xline_birth ///
		  $xlab_months ///
		  $xtitle_months ///
		  ytitle("Share Active", size($ytitle_size)) ///
		  $ylab ///
		  $leg_gender ///
		  $region

	graph export "$ext_out/extensive_margin_gender.$fig_format", replace
restore
