* Author: Hannah Lybbert
* Created: 12/01/2025
* Purpose: Individual Fixed effects on Tweet Sentiment by GENDER

use"$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

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
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(gs8)) ///
    xline(0, lcolor(black)) ///
    xlabel(-18(2)18) ///
    xtitle("Months from Birth") ///
    ytitle("Estimated Effect on Sentiment") ///
    title("Fixed-Effects Estimates of Tweet Sentiment Around Birth by Gender") ///
	  note("Note: Birth announcement tweet excluded. Sentiment = Positive - Negative scores. Base month = -1" ///
	  "Dropped months where total month tweets for the account were > 95th percentile." ///
	  "Sample size = 1,559,404 tweets from 4,017 accounts (42% female, 58% male)")  ///
	  legend(order(3 "Female" 4 "Male" 5 "Baseline") position(2) ring(0))
	
graph export "$tweetNLP_figs/fixed_effects/gender/sentiment_coeffs_gender.jpg", replace
restore




*----- POSITIVITY Score BY GENDER -----*

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
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(gs8)) ///
    xline(0, lcolor(black)) ///
    xlabel(-18(2)18) ///
    xtitle("Months from Birth") ///
    ytitle("Estimated Effect on Positivity") ///
    title("Fixed-Effects Estimates of Tweet Positivity Around Birth by Gender") ///
	  note("Note: Birth announcement tweet excluded. Base month = -1" ///
	  "Dropped months where total month tweets for the account were > 95th percentile." ///
	  "Sample size = 1,559,404 tweets from 4,017 accounts (42% female, 58% male)")  ///
	  legend(order(3 "Female" 4 "Male" 5 "Baseline") position(2) ring(0))
graph export "$tweetNLP_figs/fixed_effects/gender/pos_coeffs_gender.jpg", replace
restore



*----- NEGATIVITY Score BY GENDER -----*

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
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(gs8)) ///
    xline(0, lcolor(black)) ///
    xlabel(-18(2)18) ///
    xtitle("Months from Birth") ///
    ytitle("Estimated Effect on Negativity") ///
    title("Fixed-Effects Estimates of Tweet Negativity Around Birth by Gender") ///
	  note("Note: Birth announcement tweet excluded. Base month = -1" ///
	  "Dropped months where total month tweets for the account were > 95th percentile." ///
	  "Sample size = 1,559,404 tweets from 4,017 accounts (42% female, 58% male)")  ///
	  legend(order(3 "Female" 4 "Male" 5 "Baseline") position(4) ring(0))
	
graph export "$tweetNLP_figs/fixed_effects/gender/neg_coeffs_gender.jpg", replace
restore





* ------------------ REMOVE FAMILY-RELATED TWEETS ------------------ *
use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear
	drop if family >= 0.2

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

*----- SENTIMENT BY GENDER - no family -----*

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
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(gs8)) ///
    xline(0, lcolor(black)) ///
    xlabel(-18(2)18) ///
    xtitle("Months from Birth") ///
    ytitle("Estimated Effect on Sentiment") ///
    title("FE Estimates of Tweet Sentiment Around Birth by Gender (no family tweets)", size(mlarge)) ///
	  legend(order(3 "Female" 4 "Male" 5 "Baseline") position(2) ring(0)) ///
	  note("Note: Exclude birth announcement tweet & all tweets where P(family tweet) >= 0.2. (lose ~17% of all tweets)" ///
	  "Sample size: 1,300,191 tweets from 4,017 accounts (42% female, 58% male)" ///
	  "Base Month = -1.")
graph export "$tweetNLP_figs/fixed_effects/nofamily/sentiment_coeffs_gender_nofam.jpg", replace
restore




*----- POSITIVITY Score BY GENDER -----*

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
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(gs8)) ///
    xline(0, lcolor(black)) ///
    xlabel(-18(2)18) ///
    xtitle("Months from Birth") ///
    ytitle("Estimated Effect on Positivity") ///
    title("FE Estimates of Tweet Positivity Around Birth by Gender (no family tweets)", size(mlarge)) ///
	  legend(order(3 "Female" 4 "Male" 5 "Baseline") position(2) ring(0)) ///
	  note("Note: Exclude birth announcement tweet & all tweets where P(family tweet) >= 0.2. (lose ~17% of all tweets)" ///
	  "Sample size: 1,300,191 tweets from 4,017 accounts (42% female, 58% male)" ///
	  "Base Month = -1.")
	
graph export "$tweetNLP_figs/fixed_effects/nofamily/pos_coeffs_gender_nofam.jpg", replace
restore



*----- NEGATIVITY Score BY GENDER -----*

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
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(gs8)) ///
    xline(0, lcolor(black)) ///
    xlabel(-18(2)18) ///
    xtitle("Months from Birth") ///
    ytitle("Estimated Effect on Negativity") ///
    title("FE Estimates of Tweet Negativity Around Birth by Gender (no family tweets)", size(mlarge)) ///
	  legend(order(3 "Female" 4 "Male" 5 "Baseline") position(4) ring(0)) ///
	  note("Note: Exclude birth announcement tweet & all tweets where P(family tweet) >= 0.2. (lose ~17% of all tweets)" ///
	  "Sample size: 1,300,191 tweets from 4,017 accounts (42% female, 58% male)" ///
	  "Base Month = -1.")
	
graph export "$tweetNLP_figs/fixed_effects/nofamily/neg_coeffs_gender_nofam.jpg", replace
restore



* ----------------------------- WITHOUT DDL or FAMILY ---------------------------
use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear
distinct author_id if female == 0 | female ==1
	drop if topic == "diaries_&_daily_life" | topic == "family"
	distinct author_id if female == 0 | female ==1
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
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(gs8)) ///
    xline(0, lcolor(black)) ///
    xlabel(-18(2)18) ///
    xtitle("Months from Birth") ///
    ytitle("Estimated Effect on Sentiment") ///
    title("FE Estimates of Tweet Sentiment (no DDL or Family tweets) ") ///
	  note("Note: Birth announcement tweet excluded. Sentiment = Positive - Negative scores. Base month = -1. Dropped months" ///
	  "where total month tweets for the account were > 95th percentile. Sample size = 820,152 tweets from 4,017 accounts" ///
	  "(42% female, 58% male). Dropped if topic = 'Diaries/Daily Life' or 'Family' and lost ~47% of tweets")  ///
	  legend(order(3 "Female" 4 "Male" 5 "Baseline") position(2) ring(0))
	
graph export "$tweetNLP_figs/fixed_effects/gender/sent_coeffs_gender_noDDL_fam.jpg", replace
restore
