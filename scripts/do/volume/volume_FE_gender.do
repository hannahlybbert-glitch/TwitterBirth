* Author: Hannah Lybbert
* Created: 11/25/2025
* Purpose: Individual Fixed effects on Volume Behavior by GENDER

use "$volume_analysis/tweet_volume_analysis_sample.dta", clear
// 	keep if full_3years==1 & acct_tweeted_postBA ==1

** by Month
	* Pre: 18 → 0
	forvalues i = 18(-1)2 {
		gen _`i'pre = (months_from_birth == -`i')
	}

	* Post: 0 → 18
	forvalues i = 0/18 {
		gen _`i'post = (months_from_birth == `i')
	}

* Interact all time dummies with gender
	foreach var of varlist _* {
		gen _female`var' = `var' * female
		gen _male`var' = `var' * (1 - female)
	}

*----- TOTAL TWEETS BY GENDER -----*

* FEMALES ONLY
preserve
	keep if female==1

	areg total_tweets _female*, absorb(author_id)
	parmest, norestore

	keep if substr(parm,1,1) == "_"
	drop if parm == "_cons"

	gen month = .
	replace month = -real(regexs(1)) if regexm(parm, "_([0-9]+)pre")
	replace month = real(regexs(1)) if regexm(parm, "_([0-9]+)post")

	rename estimate beta_female
	rename stderr se_female
	rename min95 min95_female
	rename max95 max95_female

	* Keep only what we need
	keep month beta_female se_female min95_female max95_female

	tempfile female_results
	save `female_results'
restore

* MALES ONLY
preserve
	keep if female==0

	areg total_tweets _male*, absorb(author_id)
	parmest, norestore

	keep if substr(parm,1,1) == "_"
	drop if parm == "_cons"

	gen month = .
	replace month = -real(regexs(1)) if regexm(parm, "_([0-9]+)pre")
	replace month = real(regexs(1)) if regexm(parm, "_([0-9]+)post")

	rename estimate beta_male
	rename stderr se_male
	rename min95 min95_male
	rename max95 max95_male

	* Keep only what we need
	keep month beta_male se_male min95_male max95_male

* MERGE AND PLOT
merge 1:1 month using `female_results', nogen

* PLOT
twoway ///
    (rcap min95_female max95_female month, lcolor(pink%50)) ///
    (rcap min95_male max95_male month, lcolor(blue%50)) ///
    (connected beta_female month, mcolor(red) lcolor(red) msymbol(circle)) ///
    (connected beta_male month, mcolor(blue) lcolor(blue) msymbol(square)) ///
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(gs8)) ///
    xline(0, lcolor(black)) ///
    xlabel(-18(2)18) ///
    xtitle("Months from Birth") ///
    ytitle("Estimated Change in Tweeting Habits per Month") ///
    title("Gender Differences in Tweeting Behavior Around Birth (FE Estimates)") ///
	note("Note: Baseline = 1 month pre birth." ///
		"Tweeting Behavior includes all original, quote, retweets, and replies." ///
		"Sample size = 5,671. ~44% female accounts, 56% male accounts") ///
	legend(order(3 "Female" 4 "Male" 5 "baseline") position(2) ring(0))
	
graph export "$volume_figs/fixed_effects/gender/tot_tweets_FE_bygender.jpg", replace
restore


*----- RETWEET + REPLIES BY GENDER -----*
* FEMALES ONLY
preserve
	keep if female==1

	areg rt_reply_count _female*, absorb(author_id)
	parmest, norestore

	keep if substr(parm,1,1) == "_"
	drop if parm == "_cons"

	gen month = .
	replace month = -real(regexs(1)) if regexm(parm, "_([0-9]+)pre")
	replace month = real(regexs(1)) if regexm(parm, "_([0-9]+)post")

	rename estimate beta_female
	rename stderr se_female
	rename min95 min95_female
	rename max95 max95_female

	* Keep only what we need
	keep month beta_female se_female min95_female max95_female

	tempfile female_results
	save `female_results'
restore

* MALES ONLY
preserve
	keep if female==0

	areg rt_reply_count _male*, absorb(author_id)
	parmest, norestore

	keep if substr(parm,1,1) == "_"
	drop if parm == "_cons"

	gen month = .
	replace month = -real(regexs(1)) if regexm(parm, "_([0-9]+)pre")
	replace month = real(regexs(1)) if regexm(parm, "_([0-9]+)post")

	rename estimate beta_male
	rename stderr se_male
	rename min95 min95_male
	rename max95 max95_male

	* Keep only what we need
	keep month beta_male se_male min95_male max95_male

* MERGE AND PLOT
merge 1:1 month using `female_results', nogen

* PLOT
twoway ///
    (rcap min95_female max95_female month, lcolor(pink%50)) ///
    (rcap min95_male max95_male month, lcolor(blue%50)) ///
    (connected beta_female month, mcolor(red) lcolor(red) msymbol(circle)) ///
    (connected beta_male month, mcolor(blue) lcolor(blue) msymbol(square)) ///
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(gs8)) ///
    xline(0, lcolor(black)) ///
    xlabel(-18(2)18) ///
	  xtitle("Months from Birth") ///
	  ytitle("Estimated Change in Retweets + Replies per Month", size(small)) ///
	  title("Change in Retweets + Replies Around Birth (Fixed Effects Estimates)") ///
	note("Note: Baseline = 1 month pre birth." ///
		"Sample size = 5,671. ~44% female accounts, 56% male accounts") ///
	legend(order(3 "Female" 4 "Male" 5 "baseline") position(2) ring(0))
	
graph export "$volume_figs/fixed_effects/gender/rt_rply_FE_bygender.jpg", replace
restore


*----- ORIGINAL + QUOTE TWEETS BY GENDER -----*
use "$volume_analysis/ogqt_volume_analysis_sample.dta", clear

** by Month
	* Pre: 18 → 0
	forvalues i = 18(-1)2 {
		gen _`i'pre = (months_from_birth == -`i')
	}

	* Post: 0 → 18
	forvalues i = 0/18 {
		gen _`i'post = (months_from_birth == `i')
	}

* Interact all time dummies with gender
	foreach var of varlist _* {
		gen _female`var' = `var' * female
		gen _male`var' = `var' * (1 - female)
	}
	
* FEMALES ONLY
preserve
	keep if female==1

	areg orig_qt_count _female*, absorb(author_id)
	parmest, norestore

	keep if substr(parm,1,1) == "_"
	drop if parm == "_cons"

	gen month = .
	replace month = -real(regexs(1)) if regexm(parm, "_([0-9]+)pre")
	replace month = real(regexs(1)) if regexm(parm, "_([0-9]+)post")

	rename estimate beta_female
	rename stderr se_female
	rename min95 min95_female
	rename max95 max95_female

	* Keep only what we need
	keep month beta_female se_female min95_female max95_female

	tempfile female_results
	save `female_results'
restore

* MALES ONLY
preserve
	keep if female==0

	areg orig_qt_count _male*, absorb(author_id)
	parmest, norestore

	keep if substr(parm,1,1) == "_"
	drop if parm == "_cons"

	gen month = .
	replace month = -real(regexs(1)) if regexm(parm, "_([0-9]+)pre")
	replace month = real(regexs(1)) if regexm(parm, "_([0-9]+)post")

	rename estimate beta_male
	rename stderr se_male
	rename min95 min95_male
	rename max95 max95_male

	* Keep only what we need
	keep month beta_male se_male min95_male max95_male

* MERGE AND PLOT
merge 1:1 month using `female_results', nogen

* PLOT
twoway ///
    (rcap min95_female max95_female month, lcolor(pink%50)) ///
    (rcap min95_male max95_male month, lcolor(blue%50)) ///
    (connected beta_female month, mcolor(red) lcolor(red) msymbol(circle)) ///
    (connected beta_male month, mcolor(blue) lcolor(blue) msymbol(square)) ///
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(gs8)) ///
    xline(0, lcolor(black)) ///
    xlabel(-18(2)18) ///
	  xtitle("Months from Birth") ///
	  ytitle("Estimated Change in Tweeting per Month") ///
	  title("Change in Original Tweeting Around Birth (Fixed Effects Estimates)") ///
	note("Note: Baseline = 1 month pre birth." ///
		"Sample Size = 6,737 accounts, 44% female, 56% male") ///
	legend(order(3 "Female" 4 "Male" 5 "baseline") position(2) ring(0))
	
graph export "$volume_figs/fixed_effects/gender/orig_qt_FE_bygender.jpg", replace
restore




* ------------------- OLD CODE ----------------------*

// ** by Month
// 	* Pre: 18 → 0
// 	forvalues i = 18(-1)2 {
// 		gen _`i'pre = (months_from_birth == -`i')
// 	}
//
// 	* Post: 0 → 18
// 	forvalues i = 0/18 {
// 		gen _`i'post = (months_from_birth == `i')
// 	}
//
// * Interact all time dummies with gender
// 	foreach var of varlist _* {
// 		gen `var'_female = `var' * female
// 		gen `var'_male = `var' * (1 - female)
// 	}
//
// *----- TOTAL TWEETS BY GENDER -----*
// preserve
// 	keep if full_3years==1
//
// * Run regression with gender interactions
// areg total_tweets _*_female _*_male, absorb(author_id)
// parmest, norestore
//
// * Keep only the dummy coefficients
// keep if regexm(parm, "^_[0-9]+")
//
// * Create gender indicator
// gen gender = ""
// replace gender = "Female" if strpos(parm, "_female") > 0
// replace gender = "Male" if strpos(parm, "_male") > 0
//
// * Clean up parameter names to extract month
// gen parm_clean = regexr(parm, "_female|_male", "")
//
// * Add months variable back in
// gen month = .
// replace month = -real(substr(parm_clean,2,strpos(parm_clean,"pre")-2)) if strpos(parm_clean,"pre")>0
// replace month = real(substr(parm_clean,2,strpos(parm_clean,"post")-2)) if strpos(parm_clean,"post")>0
//
// * Rename vars
// rename estimate beta
// rename stderr se
//
// * Get y-axis limits
// summ beta min95 max95
// local ymin = r(min)
// local ymax = r(max)
//
// * PLOT with separate lines by gender
// twoway ///
//     (rcap min95 max95 month if gender=="Female", lcolor(pink%50)) ///
//     (rcap min95 max95 month if gender=="Male", lcolor(blue%50)) ///
//     (connected beta month if gender=="Female", mcolor(red) lcolor(red) msymbol(circle)) ///
//     (connected beta month if gender=="Male", mcolor(blue) lcolor(blue) msymbol(square)) ///
//     , yline(0, lcolor(red)) ///
//     xline(0, lcolor(black)) xline(-1, lcolor(gs8) lpattern(dash)) ///
//     xlabel(-18(2)18) ///
//     xtitle("Months from Birth (base = 1mo pre)") ///
//     ytitle("Effect on Posting") ///
//     title("Tweeting Behavior by Gender - Individual FE Coeffs") ///
//     legend(order(3 "Female" 4 "Male") position(3) ring(0))
//
// // graph export "$volume_figs/fixed_effects/tot_tweets_FE_bygender.jpg", replace
//
// restore