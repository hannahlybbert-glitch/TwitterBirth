* Author: Hannah Lybbert
* Created: 11/25/2025
* Purpose: Individual Fixed effects on Volume Behavior

use "$volume_analysis/tweet_volume_analysis_sample.dta", clear
// 	keep if full_3years==1 & acct_tweeted_postBA==1

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
	(scatteri 0 -1, msymbol(square) mcolor(black) msize(small)) ///
	, yline(0, lcolor(red)) ///
	xline(0, lcolor(black)) ///
	  xlabel(-18(2)18) ///
	  xtitle("Months from Birth") ///
	  ytitle("Estimated Change in Tweeting Habits per Month") ///
	  title("Change in Tweeting Behavior Around Birth (Fixed Effects Estimates)") ///
	  note("Note: Baseline = 1 month pre birth" ///
		  "Trimmed accounts where total sample tweets > 95th percentile" ///
		  "Sample size =  5,862 accounts") ///
	  legend(order(1 4) label(1 "95% CI") label(4 "Baseline") position(2) ring(0))
graph export "$volume_figs/fixed_effects/tot_tweets_FE.jpg", replace
restore



*----- RETWEET + REPLIES -----*
preserve
areg rt_reply_count _*, absorb(author_id)

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
	(scatteri 0 -1, msymbol(square) mcolor(black) msize(small)) ///
	, yline(0, lcolor(red)) ///
	xline(0, lcolor(black)) ///
	  xlabel(-18(2)18) ///
	  xtitle("Months from Birth") ///
	  ytitle("Estimated Change in Retweets + Replies per Month", size(small)) ///
	  title("Change in Retweets + Replies Around Birth (Fixed Effects Estimates)") ///
	  note("Note: Baseline = 1 month pre birth" ///
		  "Trimmed accounts where total sample tweets > 95th percentile" ///
		  "Sample size =  5,862 accounts") ///
	  legend(order(1 4) label(1 "95% CI") label(4 "Baseline") position(2) ring(0))
graph export "$volume_figs/fixed_effects/rt_rply_FE.jpg", replace
restore



*----- ORIGINAL + QUOTE TWEETS -----*
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

preserve	
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
	(scatteri 0 -1, msymbol(square) mcolor(black) msize(small)) ///
	, yline(0, lcolor(red)) ///
	xline(0, lcolor(black)) ///
	  xlabel(-18(2)18) ///
	  xtitle("Months from Birth") ///
	  ytitle("Estimated Change in Tweeting per Month") ///
	  title("Change in Original Tweeting Around Birth (Fixed Effects Estimates)") ///
	  note("Note: Baseline = 1 month pre birth" ///
		  "Trimmed accounts where total sample original/quote tweets > 95th percentile" ///
		  "Sample Size = 6,969 accounts") ///
	  legend(order(1 4) label(1 "95% CI") label(4 "Baseline") position(2) ring(0))
graph export "$volume_figs/fixed_effects/orig_qt_FE.jpg", replace
restore
