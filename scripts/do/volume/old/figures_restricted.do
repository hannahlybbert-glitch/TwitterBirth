*********************** FIGURES (RESTRICTED) ******************************


****************************************************
******* RESTRICTED SAMPLE *********

use "$final/tweet_volume_by_user_full_sample_CLEAN.dta", clear

** Generate "months from birth" var
gen days_from_birth = date - date_birth
gen months_from_birth = floor(days_from_birth / 30)
gen week_from_birth = floor(days_from_birth / 7)
	
** Sum tweet habits per day
gen total_tweets = orig_qt_count + rt_reply_count
** Average tweets/week

/// Restricting the sample
* find minimum days_from_birth per unique_id
egen min_days = min(days_from_birth), by(unique_id)
*create not_546 flag
gen not_546 = min_days > -546

* find maximum days_from_birth per unique_id
egen max_days = max(days_from_birth), by(unique_id)
*create not_546 flag to restrict to accounts present for full 3 year sample
replace not_546 = 1 if max_days < 546 // No obs that didn't make it to 546 days post birth

drop if not_546 == 1


**1. TOTAL TWEETS (og+qt+rt+rply)
preserve
collapse (mean) total_tweets, by(week_from_birth)

** PLOT (total tweets)
twoway (line total_tweets week_from_birth, lwidth(medthick) lcolor(orange)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Tweets per User per Week") ///
         xtitle("Weeks from Birth") ///
         title("Tweeting Behavior Before and After Birth (restr.)") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78)
* Save graph
graph export "$figures/twt_behavior/restricted/tweets_over_time_restricted.jpg", replace
restore

**2. ORIGINAL & QUOTE TWEETS
preserve
collapse (mean) orig_qt_count, by(week_from_birth)

** PLOT (original/quote tweets)
twoway (line orig_qt_count week_from_birth, lwidth(medthick) lcolor(orange)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Original Tweets per User per Week") ///
         xtitle("Weeks from Birth") ///
         title("Original Tweeting Behavior Before and After Birth (restr.)") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78)
* Save graph
graph export "$figures/twt_behavior/restricted/original_tweets_over_time_restricted.jpg", replace
restore

**3. RETWEET & REPLIES
preserve
collapse (mean) rt_reply_count, by(week_from_birth)

** PLOT (retweet/reply)
twoway (line rt_reply_count week_from_birth, lwidth(medthick) lcolor(orange)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Retweets/Replies per User per Week") ///
         xtitle("Weeks from Birth") ///
         title("Retweet/Reply Behavior Before and After Birth (restr.)") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78)
* Save graph
graph export "$figures/twt_behavior/restricted/rt_rply_tweets_over_time_restricted.jpg", replace
restore



****************************************************
******* RESTRICTED SAMPLE (by gender) *********

use "$final/tweet_volume_by_user_full_sample_CLEAN.dta", clear

merge m:1 unique_id using "$final/user_analysis_sample.dta", keepusing(female) //30 not matched, check out
drop _merge

** Generate needed variables
gen days_from_birth = date - date_birth
gen months_from_birth = floor(days_from_birth / 30)
gen week_from_birth = floor(days_from_birth / 7)
gen total_tweets = orig_qt_count + rt_reply_count

** Restrict sample
egen min_days = min(days_from_birth), by(unique_id)
gen not_546 = min_days > -546
egen max_days = max(days_from_birth), by(unique_id)
replace not_546 = 1 if max_days < 546 

drop if not_546 == 1


**1. TOTAL TWEETS by GENDER (og+qt+rt+rply)
preserve
collapse (mean) total_tweets, by(week_from_birth female) 

** PLOT (total tweets)
twoway ///
    (line total_tweets week_from_birth if female == 1, lcolor(pink) lwidth(medthick)) ///
    (line total_tweets week_from_birth if female == 0, lcolor(eltblue) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avg Tweets per User per Week") ///
    xtitle("Weeks from Birth") ///
    title("Tweeting Behavior pre/post Birth (by gender, restr.)") ///
    graphregion(color(white)) ///
    xlabel(-78(13)78) ///
    legend(label(1 "Female") label(2 "Male") position(6) ring(0))
* Save graph
graph export "$figures/twt_behavior/restricted/twt_bygender_restricted.jpg", replace
restore


**2. ORIGINAL & QUOTE TWEETS by GENDER (og+qt)
preserve
collapse (mean) orig_qt_count, by(week_from_birth female) 

** PLOT (original & quote)
twoway ///
    (line orig_qt_count week_from_birth if female == 1, lcolor(pink) lwidth(medthick)) ///
    (line orig_qt_count week_from_birth if female == 0, lcolor(eltblue) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avg Original Tweets per User per Week") ///
    xtitle("Weeks from Birth") ///
    title("Original Tweeting Behavior pre/post Birth (by gender, restr.)") ///
    graphregion(color(white)) ///
    xlabel(-78(13)78) ///
    legend(label(1 "Female") label(2 "Male") position(6) ring(0))
* Save graph
graph export "$figures/twt_behavior/restricted/orig_twt_bygender_restricted.jpg", replace
restore
	
	
**3. RETWEET & REPLY by GENDER (rt+rply)
preserve
collapse (mean) rt_reply_count, by(week_from_birth female) 

** PLOT (retweet & reply)
twoway ///
    (line rt_reply_count week_from_birth if female == 1, lcolor(pink) lwidth(medthick)) ///
    (line rt_reply_count week_from_birth if female == 0, lcolor(eltblue) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avg Retweets/Replies per User per Week") ///
    xtitle("Weeks from Birth") ///
    title("Retweet/Reply Tweeting Behavior pre/post Birth (by gender, restr.)") ///
    graphregion(color(white)) ///
    xlabel(-78(13)78) ///
    legend(label(1 "Female") label(2 "Male") position(6) ring(0))
* Save graph
graph export "$figures/twt_behavior/restricted/rt_rp_twt_bygender_restricted.jpg", replace
restore



****************************************************
******* FULL SAMPLE (by RACE) *********
use "$final/tweet_volume_by_user_full_sample_CLEAN.dta", clear

merge m:1 unique_id using "$final/user_analysis_sample.dta", keepusing(race) //30 not matched, check out
drop _merge

* Generate variables for figs (same as above)
gen days_from_birth = date - date_birth
gen months_from_birth = floor(days_from_birth / 30)
gen week_from_birth = floor(days_from_birth / 7)
gen total_tweets = orig_qt_count + rt_reply_count

** Restrict sample
egen min_days = min(days_from_birth), by(unique_id)
gen not_546 = min_days > -546
egen max_days = max(days_from_birth), by(unique_id)
replace not_546 = 1 if max_days < 546 

drop if not_546 == 1


**1. TOTAL TWEETS by RACE (og+qt+rt+rply)
preserve
collapse (mean) total_tweets, by(week_from_birth race) 

** PLOT (total tweets)
twoway ///
    (line total_tweets week_from_birth if race == 1, lcolor(red) lwidth(medthick)) ///
	(line total_tweets week_from_birth if race == 2, lcolor(green) lwidth(medthick)) ///
	(line total_tweets week_from_birth if race == 3, lcolor(blue) lwidth(medthick)) ///
	(line total_tweets week_from_birth if race == 4, lcolor(gold) lwidth(medthick)) ///
    (line total_tweets week_from_birth if race == 5, lcolor(purple) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avg Tweets per User") ///
    xtitle("Weeks from Birth") ///
    title("Tweeting Behavior Before and After Birth (by race, restr.)") ///
    graphregion(color(white)) ///
    xlabel(-78(13)78) ///
    legend(label(1 "Black") label(2 "White") label(3 "Asian") label(4 "Hispanic") label(5 "Other") position(2) ring(0))
* Save graph
graph export "$figures/twt_behavior/restricted/twt_byrace_restricted.jpg", replace
restore


**2. ORIGINAL & QUOTE TWEETS by RACE (og+qt)
preserve
collapse (mean) orig_qt_count, by(week_from_birth race) 

** PLOT (original + quote)
twoway ///
    (line orig_qt_count week_from_birth if race == 1, lcolor(red) lwidth(medthick)) ///
	(line orig_qt_count week_from_birth if race == 2, lcolor(green) lwidth(medthick)) ///
	(line orig_qt_count week_from_birth if race == 3, lcolor(blue) lwidth(medthick)) ///
	(line orig_qt_count week_from_birth if race == 4, lcolor(gold) lwidth(medthick)) ///
    (line orig_qt_count week_from_birth if race == 5, lcolor(purple) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avg Original Tweets per User") ///
    xtitle("Weeks from Birth") ///
    title("Original Tweeting Behavior Before and After Birth (by race, restr.)") ///
    graphregion(color(white)) ///
    xlabel(-78(13)78) ///
    legend(label(1 "Black") label(2 "White") label(3 "Asian") label(4 "Hispanic") label(5 "Other") position(2) ring(0))
* Save graph
graph export "$figures/twt_behavior/restricted/orig_twt_byrace_restricted.jpg", replace
restore


**3. RETWEET & REPLY by RACE (rt+rply)
preserve
collapse (mean) rt_reply_count, by(week_from_birth race) 

** PLOT (retweet/reply)
twoway ///
    (line rt_reply_count week_from_birth if race == 1, lcolor(red) lwidth(medthick)) ///
	(line rt_reply_count week_from_birth if race == 2, lcolor(green) lwidth(medthick)) ///
	(line rt_reply_count week_from_birth if race == 3, lcolor(blue) lwidth(medthick)) ///
	(line rt_reply_count week_from_birth if race == 4, lcolor(gold) lwidth(medthick)) ///
    (line rt_reply_count week_from_birth if race == 5, lcolor(purple) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avg Original Tweets per User") ///
    xtitle("Weeks from Birth") ///
    title("Retweet/Reply Tweeting Behavior Before and After Birth (by race, restr.)") ///
    graphregion(color(white)) ///
    xlabel(-78(13)78) ///
    legend(label(1 "Black") label(2 "White") label(3 "Asian") label(4 "Hispanic") label(5 "Other") position(2) ring(0))
* Save graph
graph export "$figures/twt_behavior/restricted/rt_rply_twt_byrace_restricted.jpg", replace
restore


***************** BY DAY ********************
**1. TOTAL TWEETS (og+qt+rt+rply)
preserve
keep if abs(days_from_birth) <= 60
collapse (mean) total_tweets, by(days_from_birth)

** PLOT (total tweets)
twoway (line total_tweets days_from_birth, lwidth(medthick) lcolor(orange)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Tweets per User per Week") ///
         xtitle("Weeks from Birth") ///
         title("Tweeting Behavior Before and After Birth (restr.)") ///
         graphregion(color(white)) ///
         xlabel(-60(10)60)
* Save graph
graph export "$figures/twt_behavior/restricted/tweets_by_day_rest.jpg", replace
restore

**2. OG & QT
preserve
keep if abs(days_from_birth) <= 60
collapse (mean) orig_qt_count, by(days_from_birth)

** PLOT (total tweets)
twoway (line orig_qt_count days_from_birth, lwidth(medthick) lcolor(orange)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Tweets per User per Day") ///
         xtitle("Days from Birth") ///
         title("Original Tweeting Behavior Before and After Birth (restr.)") ///
         graphregion(color(white)) ///
         xlabel(-60(10)60)
* Save graph
graph export "$figures/twt_behavior/restricted/og_tweets_by_day_restr.jpg", replace
restore

**3. RETWEET & REPLY
preserve
keep if abs(days_from_birth) <= 60
collapse (mean) rt_reply_count, by(days_from_birth)

** PLOT (total tweets)
twoway (line rt_reply_count days_from_birth, lwidth(medthick) lcolor(orange)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Tweets per User per Day") ///
         xtitle("Days from Birth") ///
         title("RT/RPLY Tweeting Behavior Before and After Birth (restr.)") ///
         graphregion(color(white)) ///
         xlabel(-60(10)60)
* Save graph
graph export "$figures/twt_behavior/restricted/rt_rply_tweets_by_day_rest.jpg", replace
restore




*********************** T TEST *************************
use "$final/tweet_volume_by_user_full_sample_CLEAN.dta", clear
merge m:1 unique_id using "$final/user_analysis_sample.dta", keepusing(female) //30 not matched, check out
drop _merge
** Generate needed variables
gen days_from_birth = date - date_birth
gen months_from_birth = floor(days_from_birth / 30)
gen week_from_birth = floor(days_from_birth / 7)
gen total_tweets = orig_qt_count + rt_reply_count
** Restrict sample
egen min_days = min(days_from_birth), by(unique_id)
gen not_546 = min_days > -546
egen max_days = max(days_from_birth), by(unique_id)
replace not_546 = 1 if max_days < 546 
drop if not_546 == 1


*** Diagnostic test ***
gen postbirth = week_from_birth >= 0
collapse (mean) orig_qt_count, by(author_id postbirth)
reshape wide orig_qt_count, i(author_id) j(postbirth) // one author per line (orig_qt_count1 = post birth)
gen change_in_posting = orig_qt_count1 - orig_qt_count0
sum change_in_posting, d

ttest orig_qt_count1 == orig_qt_count0

	
