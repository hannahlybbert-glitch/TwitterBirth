* Author:  Hannah Lybbert
* Created: 2026-04-09
* Updated: 2026-04-09
* Purpose: Fixed effects estimates of Reddit post positivity — overall and by gender
* Output:  fe_pos.jpg, fe_pos_gender.jpg

do "$dofile/set_globals_reddit.do"

* Load and filter to event window
import delimited "$Reddit_NLP_sent/vader_sentiment_FULL.csv", ///
    bindquote(strict) maxquotedrows(unlimited) clear

keep if months_from_birth >= -18 & months_from_birth <= 18

* Encode string author to numeric for areg
encode author, gen(author_id)

* Generate event-time dummies (base = month -1)
forvalues i = 18(-1)2 {
	gen _`i'pre = (months_from_birth == -`i')
}
forvalues i = 0/18 {
	gen _`i'post = (months_from_birth == `i')
}


* ----------------------------------------------------------------
* FIGURE 1: Positivity overall
* ----------------------------------------------------------------
preserve
	areg pos _*, absorb(author_id)
	parmest, norestore

	keep if substr(parm,1,1) == "_"
	drop if parm == "_cons"

	gen month = .
	replace month = -real(regexs(1)) if regexm(parm, "_([0-9]+)pre")
	replace month =  real(regexs(1)) if regexm(parm, "_([0-9]+)post")

	rename estimate beta
	rename min95    ci_lower
	rename max95    ci_upper

	* Insert baseline observation at month -1 so connected line passes through (-1, 0)
	local n = _N + 1
	set obs `n'
	replace month    = -1 in `n'
	replace beta     = 0  in `n'
	sort month

	twoway ///
		(rcap ci_lower ci_upper month, lcolor($col_ci_main) lwidth($lw_ci)) ///
		(connected beta month, mcolor($col_main) lcolor($col_main) msymbol($msym) lwidth($lw_main)) ///
		($baseline_point) ///
		, $yline_zero ///
		$xline_birth ///
		$xlab_months ///
		$xtitle_months ///
		$ylab ///
		$leg_off ///
		$region

	graph export "$sent_out/fe_pos.$fig_format", replace
restore


* ----------------------------------------------------------------
* FIGURE 2: Positivity by gender
* ----------------------------------------------------------------

* FEMALES
preserve
	keep if female == 1

	areg pos _*, absorb(author_id)
	parmest, norestore

	keep if substr(parm,1,1) == "_"
	drop if parm == "_cons"

	gen month = .
	replace month = -real(regexs(1)) if regexm(parm, "_([0-9]+)pre")
	replace month =  real(regexs(1)) if regexm(parm, "_([0-9]+)post")

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

	areg pos _*, absorb(author_id)
	parmest, norestore

	keep if substr(parm,1,1) == "_"
	drop if parm == "_cons"

	gen month = .
	replace month = -real(regexs(1)) if regexm(parm, "_([0-9]+)pre")
	replace month =  real(regexs(1)) if regexm(parm, "_([0-9]+)post")

	rename estimate beta_male
	rename stderr   se_male
	rename min95    min95_male
	rename max95    max95_male

	keep month beta_male se_male min95_male max95_male

	merge 1:1 month using `female_results', nogen

	* Insert baseline observation at month -1 so connected line passes through (-1, 0)
	local n = _N + 1
	set obs `n'
	replace month       = -1 in `n'
	replace beta_female = 0  in `n'
	replace beta_male   = 0  in `n'
	sort month

	twoway ///
		(rcap min95_female max95_female month, lcolor($col_ci_female) lwidth($lw_ci)) ///
		(rcap min95_male   max95_male   month, lcolor($col_ci_male)   lwidth($lw_ci)) ///
		(connected beta_female month, mcolor($col_female) lcolor($col_female) msymbol($msym_gender) lwidth($lw_main)) ///
		(connected beta_male   month, mcolor($col_male)   lcolor($col_male)   msymbol($msym_gender) lwidth($lw_main)) ///
		($baseline_point) ///
		, $yline_zero ///
		$xline_birth ///
		$xlab_months ///
		$xtitle_months ///
		$ylab ///
		$leg_gender ///
		$region

	graph export "$sent_out/fe_pos_gender.$fig_format", replace
restore
