* Author: Hannah Lybbert
* Created: 12/01/2025
* Purpose: Individual Fixed effects on Family Orientedness



* ----------- NO BIRTH ANNOUNCEMENT -------------- *
use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

areg family post_birth, absorb(author_id)

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

* --------------- Plot BETAS --------------- *
* ----- FAMILY SCORE ----- *
preserve
areg family _*, absorb(author_id)

parmest, norestore // extract coefficient
keep if substr(parm,1,1) == "_"   // keeps only the dummies
drop if parm == "_cons"
* Add months variable back in
	gen month = .
	replace month = -real(substr(parm,2,strpos(parm,"pre")-2)) if strpos(parm,"pre")>0
	replace month =  real(substr(parm,2,strpos(parm,"post")-2)) if strpos(parm,"post")>0

* Rename vars
	rename estimate beta
	rename stderr se
summ beta min95 max95

* PLOT
twoway ///
    (rcap min95 max95 month, lcolor(gs10)) ///
    (scatter beta month, mcolor(blue)) ///
    (line beta month, lcolor(blue)) ///
    , yline(0, lcolor(red)) ///
	xline(0, lcolor(black)) xline(-1, lcolor(gs8) lpattern(dash)) ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth") ///
      ytitle("Estimated Effect on Family Orientation of Tweets") ///
      title("FE Estimates of Family-Related Tweet Probability") ///
      legend(label(1 "95% CI") label(2 "Coefficient") position(4) ring(0)) ///
	  note("Note: Birth announcement tweet excluded. Base Month = -1.")
graph export "$family_figs/fixed_effects/family_coeffs.jpg", replace
restore



*----- BY GENDER -----*
* FEMALES first
preserve
	keep if female==1

	areg family _female*, absorb(author_id)
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

* MALES second
preserve
	keep if female==0

	areg family _male*, absorb(author_id)
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
    , yline(0, lcolor(gs8)) ///
    xline(0, lcolor(black)) xline(-1, lcolor(gs8) lpattern(dash)) ///
    xlabel(-18(2)18) ///
    xtitle("Months from Birth") ///
      ytitle("Estimated Effect on Family Orientation of Tweets") ///
      title("FE Estimates of Family-Related Tweet Probability by Gender") ///
      legend(label(1 "95% CI") label(2 "Coefficient") position(4) ring(0)) ///
	  note("Note: Birth announcement tweet excluded. Base Month = -1.") ///
    legend(order(3 "Female" 4 "Male") position(2) ring(0))
	
graph export "$family_figs/fixed_effects/family_coeffs_bygender.jpg", replace
restore




* ------------------------ NO BIRTH MONTH -------------------------- *
use "$sentiment/output/tweetNLP/NLP_topics_Karthik_noBM.dta", clear

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

* --------------- Plot BETAS --------------- *
preserve
areg family _*, absorb(author_id)

parmest, norestore // extract coefficient
keep if substr(parm,1,1) == "_"   // keeps only the dummies
drop if parm == "_cons"
* Add months variable back in
	gen month = .
	replace month = -real(substr(parm,2,strpos(parm,"pre")-2)) if strpos(parm,"pre")>0
	replace month =  real(substr(parm,2,strpos(parm,"post")-2)) if strpos(parm,"post")>0

* Rename vars
	rename estimate beta
	rename stderr se
summ beta min95 max95

* PLOT
twoway ///
    (rcap min95 max95 month, lcolor(gs10)) ///
    (scatter beta month, mcolor(blue)) ///
    (line beta month, lcolor(blue)) ///
    , yline(0, lcolor(red)) ///
	xline(0, lcolor(black)) xline(-1, lcolor(gs8) lpattern(dash)) ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth") ///
      ytitle("Estimated Effect on Family Orientation of Tweets") ///
      title("Fixed-Effects Estimates of Family Oriented Tweets") ///
      legend(label(1 "95% CI") label(2 "Coefficient") position(4) ring(0)) ///
	  note("Note: Tweets +/- 14 days from birth excluded. Base Month = -1.")
graph export "$tweetNLP_figs/topic_class/fixed_effects/noBM/family_coeffs_noBM.jpg", replace
restore


*----- BY GENDER -----*

* FEMALES ONLY
preserve
	keep if female==1

	areg family _female*, absorb(author_id)
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

	areg family _male*, absorb(author_id)
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
    , yline(0, lcolor(gs8)) ///
    xline(0, lcolor(black)) xline(-1, lcolor(gs8) lpattern(dash)) ///
    xlabel(-18(2)18) ///
    xtitle("Months from Birth") ///
      ytitle("Estimated Effect on Family Orientation of Tweets") ///
      title("Fixed-Effects Estimates of Family Oriented Tweets by Gender") ///
      legend(label(1 "95% CI") label(2 "Coefficient") position(4) ring(0)) ///
	  note("Note: Tweets +/- 14 days from birth excluded. Base Month = -1.") ///
    legend(order(3 "Female" 4 "Male") position(2) ring(0))
graph export "$tweetNLP_figs/topic_class/fixed_effects/noBM/family_coeffs_noBM_bygender.jpg", replace
restore