* Author:  Hannah Lybbert
* Created: 2026-04-09
* Updated: 2026-04-09
* Purpose: Log avg post volume around birth — overall and by gender
* Output:  log_total_posts.jpg, log_total_posts_gender.jpg

do "$dofile/set_globals_reddit.do"

global ytitle_vol "Log Posts per Month"

* ----------------------------------------------------------------
* LOAD & FILTER
* Sample: full_18_pre == 1
* ----------------------------------------------------------------
import delimited "$Reddit_final/births_and_posts_FULL.csv", bindquote(strict) maxquotedrows(unlimited) clear
keep if full_18_pre == 1
keep author female months_from_birth id

* ----------------------------------------------------------------
* BUILD FULL PANEL: all authors x months [-18, 18] with zero-fill
* Mirrors Python: compute_l_stats() fills zeros for missing months
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

* Merge in actual post counts; missing = 0 posts
merge 1:1 author months_from_birth using `post_counts', keep(master match) nogen
replace posts = 0 if posts == .
gen l_posts = log(posts + 1)

* ----------------------------------------------------------------
* FIGURE 1: Log Posts Overall
* ----------------------------------------------------------------
preserve
	collapse (mean) l_posts          ///
	         (sd)   sd_var = l_posts ///
	         (count) n     = l_posts, ///
	         by(months_from_birth)

	gen se       = sd_var / sqrt(n)
	gen ci_lower = l_posts - 1.96 * se
	gen ci_upper = l_posts + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth,  lcolor($col_ci_main) lwidth($lw_ci)) ///
		(line l_posts months_from_birth, lcolor($col_main) lwidth($lw_main)) ///
		, $xline_birth ///
		  ytitle("$ytitle_vol", size($ytitle_size)) ///
		  $ylab ///
		  $xtitle_months ///
		  $xlab_months ///
		  $leg_off ///
		  $region
	graph export "$vol_out/log_total_posts.$fig_format", replace
restore

* ----------------------------------------------------------------
* FIGURE 2: Log Posts by Gender
* ----------------------------------------------------------------
preserve
	collapse (mean) l_posts          ///
	         (sd)   sd_var = l_posts ///
	         (count) n     = l_posts, ///
	         by(months_from_birth female)

	gen se       = sd_var / sqrt(n)
	gen ci_lower = l_posts - 1.96 * se
	gen ci_upper = l_posts + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth if female==1, lcolor($col_ci_female) lwidth($lw_ci)) ///
		(rcap ci_upper ci_lower months_from_birth if female==0, lcolor($col_ci_male)   lwidth($lw_ci)) ///
		(line l_posts months_from_birth if female==1, lcolor($col_female) lwidth($lw_main)) ///
		(line l_posts months_from_birth if female==0, lcolor($col_male)   lwidth($lw_main)) ///
		, $xline_birth ///
		  ytitle("$ytitle_vol", size($ytitle_size)) ///
		  $ylab ///
		  $xtitle_months ///
		  $xlab_months ///
		  $leg_gender ///
		  $region
	graph export "$vol_out/log_total_posts_gender.$fig_format", replace
restore
