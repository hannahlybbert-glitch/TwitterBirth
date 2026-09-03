* Author:  Hannah Lybbert
* Created: 2026-08-31
* Purpose: Individual fixed effects on Reddit posting volume around birth
* Output:  volume_FE_reddit_18post.jpg,        volume_FE_reddit_24post.jpg
*          volume_FE_reddit_18post_gender.jpg, volume_FE_reddit_24post_gender.jpg

do "$dofile/set_globals_reddit.do"

* ----------------------------------------------------------------
* LOAD
* ----------------------------------------------------------------
import delimited "$Reddit_final/births_and_posts_FULL.csv", bindquote(strict) maxquotedrows(unlimited) clear
keep if full_18_pre == 1
keep author female months_from_birth id full_18_post full_24_post

tempfile raw author_gender post_counts
save `raw'

* ----------------------------------------------------------------
* Run once per post-birth horizon: 18 and 24 months
* Sample each time: balanced panel (full_18_pre == 1 & full_`h'_post == 1)
* ----------------------------------------------------------------
foreach h in 18 24 {

	use `raw', clear
	keep if full_`h'_post == 1

	* ----- BUILD FULL PANEL: authors x months [-18, `h'] with zero-fill -----
	* Reddit data is post-level, so months with no posts are missing rows
	preserve
		keep author female
		duplicates drop
		save `author_gender', replace
	restore

	gen byte counter = 1
	collapse (count) posts = counter, by(author months_from_birth)
	save `post_counts', replace

	use `author_gender', clear
	expand `=`h'+19'
	bysort author: gen months_from_birth = -18 + (_n - 1)

	merge 1:1 author months_from_birth using `post_counts', keep(master match) nogen
	replace posts = 0 if posts == .

	* numeric id for areg absorb()
	egen author_id = group(author)
	summ author_id, meanonly
	local n_authors = r(max)

	* ----- EVENT-TIME DUMMIES (baseline = 1 month pre birth) -----
	forvalues i = 18(-1)2 {
		gen _`i'pre = (months_from_birth == -`i')
	}
	forvalues i = 0/`h' {
		gen _`i'post = (months_from_birth == `i')
	}

	* ----- SINGLE EVENT REGRESSION -----
	gen post_birth = 1 if months_from_birth >= 0
	replace post_birth = 0 if months_from_birth < 0

	areg posts post_birth, absorb(author_id)

	* Single var regression by gender
	areg posts i.post_birth##i.female if inlist(female, 0, 1), absorb(author_id)

	cap mkdir "$output/volume"

	* ----- FIXED EFFECTS REGRESSION + EVENT-STUDY PLOT (POOLED) -----
	preserve
	areg posts _*, absorb(author_id)

		parmest, norestore // extract coefficients
		keep if substr(parm,1,1) == "_"   // keeps only the dummies
		drop if parm == "_cons"
		* Add months variable back in
			gen month = .
			replace month = -real(substr(parm,2,strpos(parm,"pre")-2))  if strpos(parm,"pre")>0
			replace month =  real(substr(parm,2,strpos(parm,"post")-2)) if strpos(parm,"post")>0

		* Rename vars
			rename estimate beta
			rename stderr se

	* Add baseline point back in so the line connects through it
	local N = _N
	set obs `=`N'+1'
	replace month = -1 in `=`N'+1'
	replace beta = 0 in `=`N'+1'
	sort month

	* PLOT
	twoway ///
		(rcap min95 max95 month, lcolor(gs10)) ///
		(scatter beta month, mcolor(blue)) ///
		(line beta month, lcolor(blue)) ///
		(scatteri 0 -1, msymbol(square) mcolor(black) msize(small)) ///
		, yline(0, lcolor(red)) ///
		xline(0, lcolor(black)) ///
		  xlabel(-18(2)`h') ///
		  xtitle("Months from Birth") ///
		  ytitle("Estimated Change in Posts per Month") ///
		  title("Change in Reddit Posting Around Birth (Fixed Effects Estimates)") ///
		  legend(order(1 4) label(1 "95% CI") label(4 "Baseline") position(2) ring(0))
	graph export "$output/volume/volume_FE_reddit_`h'post.jpg", replace
	restore

	* ----- FIXED EFFECTS EVENT-STUDY PLOT — BY GENDER -----
	* Same specification, run separately on female and male authors.

	* FEMALES
	preserve
		keep if female == 1
		areg posts _*, absorb(author_id)
		parmest, norestore
		keep if substr(parm,1,1) == "_"
		drop if parm == "_cons"

		gen month = .
		replace month = -real(substr(parm,2,strpos(parm,"pre")-2))  if strpos(parm,"pre")>0
		replace month =  real(substr(parm,2,strpos(parm,"post")-2)) if strpos(parm,"post")>0

		rename estimate beta_female
		rename stderr   se_female
		rename min95    min95_female
		rename max95    max95_female
		keep month beta_female se_female min95_female max95_female

		tempfile female_results
		save `female_results'
	restore

	* MALES — merge female results and plot
	preserve
		keep if female == 0
		areg posts _*, absorb(author_id)
		parmest, norestore
		keep if substr(parm,1,1) == "_"
		drop if parm == "_cons"

		gen month = .
		replace month = -real(substr(parm,2,strpos(parm,"pre")-2))  if strpos(parm,"pre")>0
		replace month =  real(substr(parm,2,strpos(parm,"post")-2)) if strpos(parm,"post")>0

		rename estimate beta_male
		rename stderr   se_male
		rename min95    min95_male
		rename max95    max95_male
		keep month beta_male se_male min95_male max95_male

		merge 1:1 month using `female_results', nogen

		* Add baseline point back in so each line connects through (-1, 0)
		local N = _N + 1
		set obs `N'
		replace month       = -1 in `N'
		replace beta_female = 0  in `N'
		replace beta_male   = 0  in `N'
		sort month

		twoway ///
			(rcap min95_female max95_female month, lcolor($col_ci_female) lwidth($lw_ci)) ///
			(rcap min95_male   max95_male   month, lcolor($col_ci_male)   lwidth($lw_ci)) ///
			(connected beta_female month, mcolor($col_female) lcolor($col_female) msymbol($msym_gender) lwidth($lw_main)) ///
			(connected beta_male   month, mcolor($col_male)   lcolor($col_male)   msymbol($msym_gender) lwidth($lw_main)) ///
			($baseline_point) ///
			, $yline_zero ///
			$xline_birth ///
			xlabel(-18(2)`h', labsize($xtick_size)) ///
			$xtitle_months ///
			ytitle("Estimated Change in Posts per Month", size($ytitle_size)) ///
			$ylab ///
			$leg_gender ///
			$region
		graph export "$output/volume/volume_FE_reddit_`h'post_gender.jpg", replace
	restore
}
