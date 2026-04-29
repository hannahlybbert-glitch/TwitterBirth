* Author: Hannah Lybbert
* Created: 11/12/2025
* Purpose: Individual Fixed effects on Tweet Sentiment

* --------------- REGRESSIONS ------------------ *
use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

// use "$sentiment/output/topic_sentiment_analysis.dta", clear

areg sentiment_score post_birth, absorb(author_id)

** by Month
	* Pre: 18 → 0
	forvalues i = 18(-1)2 {
		gen _`i'pre = (months_from_birth == -`i')
	}

	* Post: 0 → 18
	forvalues i = 0/18 {
		gen _`i'post = (months_from_birth == `i')
	}


* --------------- Plot BETAS --------------- *

*----- SENTIMENT SCORE -----*
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
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(red)) ///
	xline(0, lcolor(black)) ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth") ///
      ytitle("Estimated Effect on Sentiment") ///
      title("Fixed-Effects Estimates of Tweet Sentiment Around Birth") ///
      legend(order(1 4) label(1 "95% CI") label(4 "Baseline") position(2) ring(0)) ///
	  note("Note: Birth announcement tweet excluded. Base Month = -1." ///
	  "Trimmed observations where total month original tweets > 95th percentile" ///
	  "Sample size: 1,613,691 tweets from 4,145 accounts")
graph export "$tweetNLP_figs/fixed_effects/sentiment_coeffs.jpg", replace
restore



*----- POSITIVITY -----*
preserve
areg pos _*, absorb(author_id)

parmest, norestore // extract coefficient
keep if substr(parm,1,1) == "_"   // keeps only the dummies
drop if parm == "_cons"

	gen month = .
	replace month = -real(substr(parm,2,strpos(parm,"pre")-2)) if strpos(parm,"pre")>0
	replace month =  real(substr(parm,2,strpos(parm,"post")-2)) if strpos(parm,"post")>0

	rename estimate beta
	rename stderr se
summ beta min95 max95

* PLOT
twoway ///
    (rcap min95 max95 month, lcolor(gs10)) ///
    (scatter beta month, mcolor(blue)) ///
    (line beta month, lcolor(blue)) ///
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(red)) ///
	xline(0, lcolor(black)) ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth") ///
      ytitle("Estimated Effect on Positivity") ///
      title("Fixed-Effects Estimates of Tweet Positivity Around Birth") ///
      legend(order(1 4) label(1 "95% CI") label(4 "Baseline") position(2) ring(0)) ///
	  note("Note: Birth announcement tweet excluded. Base Month = -1." ///
	  "Trimmed observations where total month original tweets > 95th percentile" ///
	  "Sample size: 1,613,691 tweets from 4,145 accounts")
graph export "$tweetNLP_figs/fixed_effects/pos_coeffs.jpg", replace
restore
	
	
	
	
* ----- Negativity ----- *
preserve
areg neg _*, absorb(author_id)

parmest, norestore // extract coefficient
keep if substr(parm,1,1) == "_"   // keeps only the dummies
drop if parm == "_cons"
	gen month = .
	replace month = -real(substr(parm,2,strpos(parm,"pre")-2)) if strpos(parm,"pre")>0
	replace month =  real(substr(parm,2,strpos(parm,"post")-2)) if strpos(parm,"post")>0

	rename estimate beta
	rename stderr se
summ beta min95 max95

* PLOT
twoway ///
    (rcap min95 max95 month, lcolor(gs10)) ///
    (scatter beta month, mcolor(blue)) ///
    (line beta month, lcolor(blue)) ///
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(red)) ///
	xline(0, lcolor(black)) ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth") ///
      ytitle("Estimated Effect on Negativity") ///
      title("Fixed-Effects Estimates of Tweet Negativity Around Birth") ///
      legend(order(1 4) label(1 "95% CI") label(4 "Baseline") position(4) ring(0)) ///
	  note("Note: Birth announcement tweet excluded. Base Month = -1." ///
	  "Trimmed observations where total month original tweets > 95th percentile" ///
	  "Sample size: 1,613,691 tweets from 4,145 accounts")
graph export "$tweetNLP_figs/fixed_effects/neg_coeffs.jpg", replace
restore


// *----- NEUTRALITY -----*
// preserve
// areg neu _*, absorb(author_id)
//
// parmest, norestore // extract coefficient
// keep if substr(parm,1,1) == "_"   // keeps only the dummies
// drop if parm == "_cons"
//
// 	gen month = .
// 	replace month = -real(substr(parm,2,strpos(parm,"pre")-2)) if strpos(parm,"pre")>0
// 	replace month =  real(substr(parm,2,strpos(parm,"post")-2)) if strpos(parm,"post")>0
//
// 	rename estimate beta
// 	rename stderr se
//	
// summ beta min95 max95
//
// * PLOT
// twoway ///
//     (rcap min95 max95 month, lcolor(gs10)) ///
//     (scatter beta month, mcolor(blue)) ///
//     (line beta month, lcolor(blue)) ///
//     , yline(0, lcolor(red)) ///
// 	xline(0, lcolor(black)) xline(-1, lcolor(gs8) lpattern(dash)) ///
//       xlabel(-18(2)18) ///
//       xtitle("Months from Birth") ///
//       ytitle("Estimated Effect on Neutrality") ///
//       title("Fixed-Effects Estimates of Tweet Neutrality Around Birth") ///
//       legend(label(1 "95% CI") label(2 "Coefficient") position(2) ring(0)) ///
// 	  note("Note: Birth announcement tweet excluded. Base Month = -1.")
// graph export "$tweetNLP_figs/fixed_effects/neu_coeffs.jpg", replace
// // graph export "$tweetNLP_figs/fixed_effects/noBM/neu_coeffs_noBM.jpg", replace
// restore


* ------------------------- REMOVE FAMILY-CATEGORIZED TWEETS ------------------ *

*----- SENTIMENT SCORE -----*
preserve
	drop if family >= 0.2
	distinct author_id
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
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(red)) ///
	xline(0, lcolor(black)) ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth") ///
      ytitle("Estimated Effect on Sentiment") ///
      title("FE Estimates of Tweet Sentiment Around Birth (no family tweets)") ///
      legend(order(1 4) label(1 "95% CI") label(4 "Baseline") position(2) ring(0)) ///
	  note("Note: Exclude birth announcement tweet & all tweets where P(family tweet) >= 0.2." ///
	  "Sample size: 1,347,864 tweets from 4,145 accounts (lose ~16% of all tweets)" ///
	  "Base Month = -1.")
graph export "$tweetNLP_figs/fixed_effects/nofamily/sentiment_coeffs_nofam.jpg", replace
restore


*----- POSITIVITY -----*
preserve
// 	drop if topic == "family"
	drop if family >= 0.2
	
	areg pos _*, absorb(author_id)

	parmest, norestore // extract coefficient
	keep if substr(parm,1,1) == "_"   // keeps only the dummies
	drop if parm == "_cons"

		gen month = .
		replace month = -real(substr(parm,2,strpos(parm,"pre")-2)) if strpos(parm,"pre")>0
		replace month =  real(substr(parm,2,strpos(parm,"post")-2)) if strpos(parm,"post")>0

		rename estimate beta
		rename stderr se
	summ beta min95 max95

* PLOT
twoway ///
    (rcap min95 max95 month, lcolor(gs10)) ///
    (scatter beta month, mcolor(blue)) ///
    (line beta month, lcolor(blue)) ///
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(red)) ///
	xline(0, lcolor(black)) ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth") ///
      ytitle("Estimated Effect on Positivity") ///
      title("FE Estimates of Tweet Positivity Around Birth (no family tweets)") ///
      legend(order(1 4) label(1 "95% CI") label(4 "Baseline") position(2) ring(0)) ///
	  note("Note: Exclude birth announcement tweet & all tweets where P(family tweet) >= 0.2." ///
	  "Sample size: 1,347,864 tweets from 4,145 accounts (lose ~16% of all tweets)" ///
	  "Base Month = -1.")
graph export "$tweetNLP_figs/fixed_effects/nofamily/pos_coeffs_nofam.jpg", replace
restore


* ----- NEGATIVE ----- *
preserve
	drop if family >= 0.2

	areg neg _*, absorb(author_id)

	parmest, norestore // extract coefficient
	keep if substr(parm,1,1) == "_"   // keeps only the dummies
	drop if parm == "_cons"
		gen month = .
		replace month = -real(substr(parm,2,strpos(parm,"pre")-2)) if strpos(parm,"pre")>0
		replace month =  real(substr(parm,2,strpos(parm,"post")-2)) if strpos(parm,"post")>0

		rename estimate beta
		rename stderr se
	summ beta min95 max95

* PLOT
twoway ///
    (rcap min95 max95 month, lcolor(gs10)) ///
    (scatter beta month, mcolor(blue)) ///
    (line beta month, lcolor(blue)) ///
	(scatteri 0 -1, msymbol(diamond) mcolor(black) msize(small)) ///
    , yline(0, lcolor(red)) ///
	xline(0, lcolor(black)) ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth") ///
      ytitle("Estimated Effect on Negativity") ///
      title("FE Estimates of Tweet Negativity Around Birth (no family tweets)") ///
            legend(order(1 4) label(1 "95% CI") label(4 "Baseline") position(2) ring(0)) ///
	  note("Note: Exclude birth announcement tweet & all tweets where P(family tweet) >= 0.2." ///
	  "Sample size: 1,347,864 tweets from 4,145 accounts (lose ~16% of all tweets)" ///
	  "Base Month = -1.")
graph export "$tweetNLP_figs/fixed_effects/nofamily/neg_coeffs_nofam.jpg", replace
restore