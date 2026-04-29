* Author: Hannah Lybbert
* Created: 11/25/2025
* Purpose: Individual Fixed effects on Volume Behavior

use "$final/tweet_volume_by_user_full_sample_CLEAN.dta", clear

areg total_tweets post_birth, absorb(author_id)

** by Month
	* Pre: 18 → 0
	forvalues i = 18(-1)2 {
		gen _`i'pre = (months_from_birth == -`i')
	}

	* Post: 0 → 18
	forvalues i = 0/18 {
		gen _`i'post = (months_from_birth == `i')
	}
	

*----- TOTAL TWEETS -----*
preserve
keep if full_3years==1
// keep if full_3years==1 & acct_tweeted_postBA==1
areg total_tweets _*, absorb(author_id)

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
local ymin = r(min)
local ymax = r(max)	

* PLOT
twoway ///
    (rcap min95 max95 month, lcolor(gs10)) ///
    (scatter beta month, mcolor(blue)) ///
    (line beta month, lcolor(blue)) ///
    , yline(0, lcolor(red)) ///
	xline(0, lcolor(black)) xline(-1, lcolor(gs8) lpattern(dash)) ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth (base = 1mo pre)") ///
      ytitle("Effect on Posting") ///
      title("Tweeting Behavior - Individual Fixed Effect Coeffs") ///
      legend(label(1 "95% CI") label(2 "Coefficient") position(3) ring(0))
graph export "$volume_figs/fixed_effects/tot_tweets_FE.jpg", replace
// graph export "$volume_figs/fixed_effects/tot_tweets_FE_beyondBA.jpg", replace
restore


*----- ORIGINAL TWEETS -----*
preserve
// keep if full_3years==1
keep if full_3years==1 & acct_tweeted_postBA==1
areg orig_qt_count _*, absorb(author_id)

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
local ymin = r(min)
local ymax = r(max)	

* PLOT
twoway ///
    (rcap min95 max95 month, lcolor(gs10)) ///
    (scatter beta month, mcolor(blue)) ///
    (line beta month, lcolor(blue)) ///
    , yline(0, lcolor(red)) ///
	xline(0, lcolor(black)) xline(-1, lcolor(gs8) lpattern(dash)) ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth (base = 1mo pre)") ///
      ytitle("Effect on Posting") ///
      title("Original Tweeting Behavior - Individual Fixed Effect Coeffs (beyondBA)") ///
      legend(label(1 "95% CI") label(2 "Coefficient") position(3) ring(0))
// graph export "$volume_figs/fixed_effects/orig_tweets_FE.jpg", replace
graph export "$volume_figs/fixed_effects/orig_tweets_FE_beyondBA.jpg", replace
restore
