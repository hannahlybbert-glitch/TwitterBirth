* Author: Hannah Lybbert
* Created: 12/04/2025
* Purpose: Individual Fixed effects on Tweet Sentiment of Family Tweets


* ======================================= FIXED EFFECTS ======================================= *

* ----------- NO BIRTH ANNOUNCEMENT -------------- *
use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear
	keep if family >= 0.5

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


* ------------------------ SENTIMENT of FAMILY TWEETS pre/post ------------------------ *

* --- SENTIMENT - family --- *
preserve
	areg sentiment_score _*, absorb(author_id)

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
      ytitle("Estimated Effect on Sentiment of Family Tweets") ///
      title("FE Estimates of Tweet Sentiment of Family-Related Tweets") ///
	  legend(order(1) label(1 "95% CI") position(2) ring(0)) ///
	  note("Note: Birth announcement tweet excluded. Base Month = -1. 'Family-related' if P(family) >= 0.5. 135,402 tweets from 3,983 accts.", size(vsmall))
graph export "$family_figs/sentiment/fixed_effects/family_sentiment_FE.jpg", replace
restore


* --- positive - family --- *
preserve
	areg pos _*, absorb(author_id)

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
      ytitle("Estimated Effect on Positivity of Family Tweets") ///
      title("FE Estimates of Tweet Positivity of Family-Related Tweets") ///
	  legend(order(1) label(1 "95% CI") position(2) ring(0)) ///
	  note("Note: Birth announcement tweet excluded. Base Month = -1. 'Family-related' if P(family) >= 0.5. 135,402 tweets from 3,983 accts.", size(vsmall))
graph export "$family_figs/sentiment/fixed_effects/family_pos_FE.jpg", replace
restore


* --- negative - family --- *
preserve
	areg neg _*, absorb(author_id)

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
      ytitle("Estimated Effect on Negativity of Family Tweets") ///
      title("FE Estimates of Tweet Negativity of Family-Related Tweets") ///
	  legend(order(1) label(1 "95% CI") position(2) ring(0)) ///
	  note("Note: Birth announcement tweet excluded. Base Month = -1. 'Family-related' if P(family) >= 0.5. 135,402 tweets from 3,983 accts.", size(vsmall))
graph export "$family_figs/sentiment/fixed_effects/family_neg_FE.jpg", replace
restore


* ======================================= by gender ======================================= *


*----- Sentiment Score BY GENDER -----*

* FEMALES ONLY
preserve
	keep if female==1

	areg sentiment_score _female*, absorb(author_id)
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

	areg sentiment_score _male*, absorb(author_id)
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
    ytitle("Estimated Effect on Sentiment") ///
    title("FE Estimates of Tweet Sentiment of Family-Related Tweets Around Birth by Gender", size(mlarge)) ///
	note("Note: Birth announcement tweet excluded. Base Month = -1. 'Family-related' if P(family) >= 0.5. 135,402 tweets from 3,983 accts.", size(vsmall)) ///
    legend(order(3 "Female" 4 "Male") position(2) ring(0))
	
graph export "$family_figs/sentiment/fixed_effects/fam_sent_FE_gender.jpg", replace
restore



*----- Positivity BY GENDER -----*

* FEMALES ONLY
preserve
	keep if female==1

	areg pos _female*, absorb(author_id)
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

	areg pos _male*, absorb(author_id)
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
    ytitle("Estimated Effect on Positivity") ///
    title("FE Estimates of Tweet Positivity of Family-Related Tweets Around Birth by Gender", size(mlarge)) ///
	note("Note: Birth announcement tweet excluded. Base Month = -1. 'Family-related' if P(family) >= 0.5. 135,402 tweets from 3,983 accts.", size(vsmall)) ///
    legend(order(3 "Female" 4 "Male") position(2) ring(0))
	
graph export "$family_figs/sentiment/fixed_effects/fam_pos_FE_gender.jpg", replace
restore


*----- Negativity BY GENDER -----*

* FEMALES ONLY
preserve
	keep if female==1

	areg neg _female*, absorb(author_id)
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

	areg neg _male*, absorb(author_id)
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
    ytitle("Estimated Effect on Negativity") ///
    title("FE Estimates of Tweet Negativity of Family-Related Tweets Around Birth by Gender", size(mlarge)) ///
	note("Note: Birth announcement tweet excluded. Base Month = -1. 'Family-related' if P(family) >= 0.5. 135,402 tweets from 3,983 accts.", size(vsmall)) ///
    legend(order(3 "Female" 4 "Male") position(2) ring(0))
	
graph export "$family_figs/sentiment/fixed_effects/fam_neg_FE_gender.jpg", replace
restore