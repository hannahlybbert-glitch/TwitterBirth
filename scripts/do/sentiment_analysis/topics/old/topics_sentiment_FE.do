* Author: Hannah Lybbert
* Created: 12/03/2025
* Purpose: Sentiment of tweets with individual fixed effects


* ----------- NO BIRTH ANNOUNCEMENT -------------- *
use "$sentiment/output/topic_sentiment_merge_Karthik.dta", clear

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
	keep if family_flag == 1

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
	  note("Note: Birth announcement tweet excluded. Base Month = -1. Family tweet >= P(0.2). 277,746 tweets from 4,094 accts.", size(small))
graph export "$tweetNLP_figs/topic_class/sentiment_by_topic/fixed_effects/family_sentiment_FE.jpg", replace
restore


* --- positive - family --- *
preserve
	keep if family_flag == 1

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
	  note("Note: Birth announcement tweet excluded. Base Month = -1. Family tweet >= P(0.2). 277,746 tweets from 4,094 accts.", size(small))
graph export "$tweetNLP_figs/topic_class/sentiment_by_topic/fixed_effects/family_pos_FE.jpg", replace
restore


* --- negative - family --- *
preserve
	keep if family_flag == 1

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
	  note("Note: Birth announcement tweet excluded. Base Month = -1. Family tweet >= P(0.2). 277,746 tweets from 4,094 accts.", size(small))
graph export "$tweetNLP_figs/topic_class/sentiment_by_topic/fixed_effects/family_neg_FE.jpg", replace
restore


* ------------------------ sentiment of NEWS TWEETS pre/post ------------------------ *

* --- SENTIMENT - news --- *
preserve
	keep if topic == "news_&_social_concern"

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
      ytitle("Estimated Effect on Sentiment of News Tweets") ///
      title("FE Estimates of Tweet Sentiment of News Tweets") ///
	  legend(order(1) label(1 "95% CI") position(2) ring(0)) ///
	  note("Note: Birth announcement tweet excluded. Base Month = -1. 122,902 tweets classified as 'news & social concern' from 4,030 accts.", size(vsmall))
graph export "$tweetNLP_figs/topic_class/sentiment_by_topic/fixed_effects/news_sentiment_FE.jpg", replace
restore


* --- positive - news --- *
preserve
	keep if topic == "news_&_social_concern"

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
      ytitle("Estimated Effect on Positivity of News Tweets") ///
      title("FE Estimates of Tweet Positivity of News Tweets") ///
	  legend(order(1) label(1 "95% CI") position(2) ring(0)) ///
	  note("Note: Birth announcement tweet excluded. Base Month = -1. 122,902 tweets classified as 'news & social concern' from 4,030 accts.", size(vsmall))
graph export "$tweetNLP_figs/topic_class/sentiment_by_topic/fixed_effects/news_pos_FE.jpg", replace
restore


* --- negative - news --- *
preserve
	keep if topic == "news_&_social_concern"

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
      ytitle("Estimated Effect on Negativity of News Tweets") ///
      title("FE Estimates of Tweet Negativity of News Tweets") ///
	  legend(order(1) label(1 "95% CI") position(2) ring(0)) ///
	  note("Note: Birth announcement tweet excluded. Base Month = -1. 122,902 tweets classified as 'news & social concern' from 4,030 accts.", size(vsmall))
graph export "$tweetNLP_figs/topic_class/sentiment_by_topic/fixed_effects/news_neg_FE.jpg", replace
restore


* ------------------------ sentiment of SPORTS TWEETS pre/post ------------------------ *

* --- SENTIMENT - news --- *
preserve
	keep if topic == "sports"

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
      ytitle("Estimated Effect on Sentiment of Sports Tweets") ///
      title("FE Estimates of Tweet Sentiment of Sports Tweets") ///
	  legend(order(1) label(1 "95% CI") position(2) ring(0)) ///
	  note("Note: Birth announcement tweet excluded. Base Month = -1. 248,512 tweets classified as 'sports' from 4,074 accts.", size(vsmall))
graph export "$tweetNLP_figs/topic_class/sentiment_by_topic/fixed_effects/sports_sentiment_FE.jpg", replace
restore


* --- positive - news --- *
preserve
	keep if topic == "sports"

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
      ytitle("Estimated Effect on Positivity of Sports Tweets") ///
      title("FE Estimates of Tweet Positivity of Sports Tweets") ///
	  legend(order(1) label(1 "95% CI") position(2) ring(0)) ///
	  note("Note: Birth announcement tweet excluded. Base Month = -1. 248,512 tweets classified as 'sports' from 4,074 accts.", size(vsmall))
graph export "$tweetNLP_figs/topic_class/sentiment_by_topic/fixed_effects/sports_pos_FE.jpg", replace
restore


* --- negative - news --- *
preserve
	keep if topic == "sports"

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
      ytitle("Estimated Effect on Negativity of Sports Tweets") ///
      title("FE Estimates of Tweet Negativity of Sports Tweets") ///
	  legend(order(1) label(1 "95% CI") position(2) ring(0)) ///
	  note("Note: Birth announcement tweet excluded. Base Month = -1. 248,512 tweets classified as 'sports' from 4,074 accts.", size(vsmall))
graph export "$tweetNLP_figs/topic_class/sentiment_by_topic/fixed_effects/sports_neg_FE.jpg", replace
restore