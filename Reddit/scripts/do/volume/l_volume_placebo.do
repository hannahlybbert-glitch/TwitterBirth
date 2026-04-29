* Author:  Hannah Lybbert
* Created: 2026-04-10
* Updated: 2026-04-10
* Purpose: Log avg post volume around birth — treatment vs control overall and by gender
* Output:  l_avg_posts_month_placebo.jpg, l_avg_posts_month_placebo_gender.jpg

do "$dofile/set_globals_reddit.do"

global ytitle_vol  "Log Posts per Month"
global col_control "steel"        // control group line color

* ----------------------------------------------------------------
* LOAD & FILTER
* Sample: full_18_pre == 1
* ----------------------------------------------------------------
import delimited "$Reddit_final/treatment_control_births_posts.csv", bindquote(strict) maxquotedrows(unlimited) clear
keep if full_18_pre == 1
keep if months_from_birth >= -18 & months_from_birth <= 18
keep author treated female months_from_birth id

* ----------------------------------------------------------------
* BUILD FULL PANEL: all authors x months [-18, 18] with zero-fill
* Mirrors Python: compute_l_stats() fills zeros for missing months
* ----------------------------------------------------------------

* Save author-level metadata before collapsing
preserve
	keep author treated female
	duplicates drop
	tempfile author_meta
	save `author_meta'
restore

* Count posts per author-month from raw post-level data
gen byte counter = 1
collapse (count) posts = counter, by(author months_from_birth)
tempfile post_counts
save `post_counts'

* Expand author list to full panel (37 months: -18 to 18)
use `author_meta', clear
expand 37
bysort author: gen months_from_birth = -18 + (_n - 1)

* Merge in actual post counts; missing = 0 posts
merge 1:1 author months_from_birth using `post_counts', keep(master match) nogen
replace posts = 0 if posts == .
gen l_posts = log(posts + 1)

* ----------------------------------------------------------------
* FIGURE 1: Log Posts — Treatment vs Control (overall)
* ----------------------------------------------------------------
preserve
	collapse (mean) l_posts          ///
	         (sd)   sd_var = l_posts ///
	         (count) n     = l_posts, ///
	         by(treated months_from_birth)

	gen se       = sd_var / sqrt(n)
	gen ci_lower = l_posts - 1.96 * se
	gen ci_upper = l_posts + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth if treated==1, lcolor($col_main%50)    lwidth($lw_ci)) ///
		(rcap ci_upper ci_lower months_from_birth if treated==0, lcolor($col_control%50) lwidth($lw_ci)) ///
		(line l_posts months_from_birth if treated==1, lcolor($col_main)    lwidth($lw_main)) ///
		(line l_posts months_from_birth if treated==0, lcolor($col_control) lwidth($lw_main)) ///
		, $xline_birth ///
		  ytitle("$ytitle_vol", size($ytitle_size)) ///
		  $ylab ///
		  $xtitle_months ///
		  $xlab_months ///
		  xscale(range(-18 18)) ///
		  legend(order(3 "Treatment" 4 "Control") $leg_pos_ur) ///
		  $region
	graph export "$vol_out/l_avg_posts_month_placebo.$fig_format", replace
restore

* ----------------------------------------------------------------
* FIGURE 2: Log Posts — Treatment Female, Treatment Male, Control
* Three lines: treated==1 & female==1, treated==1 & female==0, treated==0
* Control has no gender split (female missing for placebo authors)
* ----------------------------------------------------------------
preserve
	* group: 1 = treatment female, 2 = treatment male, 3 = control
	gen group = .
	replace group = 1 if treated==1 & female==1
	replace group = 2 if treated==1 & female==0
	replace group = 3 if treated==0
	drop if group == .

	collapse (mean) l_posts          ///
	         (sd)   sd_var = l_posts ///
	         (count) n     = l_posts, ///
	         by(group months_from_birth)

	gen se       = sd_var / sqrt(n)
	gen ci_lower = l_posts - 1.96 * se
	gen ci_upper = l_posts + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth if group==1, lcolor($col_ci_female)  lwidth($lw_ci)) ///
		(rcap ci_upper ci_lower months_from_birth if group==2, lcolor($col_ci_male)    lwidth($lw_ci)) ///
		(rcap ci_upper ci_lower months_from_birth if group==3, lcolor($col_control%50) lwidth($lw_ci)) ///
		(line l_posts months_from_birth if group==1, lcolor($col_female)  lwidth($lw_main)) ///
		(line l_posts months_from_birth if group==2, lcolor($col_male)    lwidth($lw_main)) ///
		(line l_posts months_from_birth if group==3, lcolor($col_control) lwidth($lw_main)) ///
		, $xline_birth ///
		  ytitle("$ytitle_vol", size($ytitle_size)) ///
		  $ylab ///
		  $xtitle_months ///
		  $xlab_months ///
		  xscale(range(-18 18)) ///
		  legend(order(4 "Treatment — Female" 5 "Treatment — Male" 6 "Control") $leg_pos_ur) ///
		  $region
	graph export "$vol_out/l_avg_posts_month_placebo_gender.$fig_format", replace
restore
