* Author: Hannah Lybbert
* Created: a while ago
* Purpose: Total, original/qt, rt/rply volume figures for all accounts & by gender

****************************************************
******* FULL SAMPLE *********
use "$final/tweet_volume_analysis_sample.dta", clear

** 1A. TOTAL TWEETS - 95% conf intvl (og+qt+rt+rply)
preserve
// 	keep if account_30_mo_old ==1
	collapse (mean) total_month_tweets, by(author_id months_from_birth)
	collapse (mean) total_month_tweets ///
			 (sd)   sd_total = total_month_tweets ///
			 (count) n = total_month_tweets, ///
			 by(months_from_birth)
	
	* Generate confidence intervals using standard error
	gen se = sd_total / sqrt(n)
	gen ci_lower = total_month_tweets - 1.96 * se
	gen ci_upper = total_month_tweets + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth, lcolor(gs8)) ///
		(line total_month_tweets months_from_birth, lwidth(medthick) lcolor(blue)) ///
		, xline(0, lpattern(dash) lcolor(edkblue)) ///
		  ytitle("Avgerage Total Tweets per User") ///
		  xtitle("Months from Birth") ///
		  title("Total Tweeting Frequency Around Birth") ///
		  legend(label(1 "95% CI") label(2 "Avg Tweets") position(2) ring(0)) ///
		  note("Note: Total tweets = original + quote + retweet + reply." ///
		  "Trimmed accounts where total sample tweets > 95th percentile" ///
		  "Sample Size = 5,862 accounts") ///
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
// graph export "$volume_figs/twt_behavior/tweets_over_time.jpg", replace
restore


**3. RETWEET & REPLIES
preserve
	collapse (mean) rt_rp_month_tweets ///
			 (sd)   sd_total = rt_rp_month_tweets ///
			 (count) n = rt_rp_month_tweets, ///
			 by(months_from_birth)
	
	* Generate confidence intervals using standard error
	gen se = sd_total / sqrt(n)
	gen ci_lower = rt_rp_month_tweets - 1.96 * se
	gen ci_upper = rt_rp_month_tweets + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth, lcolor(gs8)) ///
		(line rt_rp_month_tweets months_from_birth, lwidth(medthick) lcolor(blue)) ///
		, xline(0, lpattern(dash) lcolor(edkblue)) ///
		  ytitle("Avgerage Retweets/Replies per User by Month") ///
		  xtitle("Months from Birth") ///
		  title("Retweet + Reply Frequency Around Birth") ///
		  legend(label(1 "95% CI") label(2 "Avg Tweets") position(2) ring(0)) ///
		  note("Note: Trimmed accounts where total sample tweets > 95th percentile" ///
		  "Sample Size = 5,862 accounts") ///
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
* Save graph
graph export "$volume_figs/twt_behavior/rt_rply_tweets_over_time.jpg", replace
restore



**2. ORIGINAL & QUOTE TWEETS
preserve
use "$final/ogqt_volume_analysis_sample.dta", clear
	collapse (mean) og_qt_month_tweets ///
			 (sd)   sd_total = og_qt_month_tweets ///
			 (count) n = og_qt_month_tweets, ///
			 by(months_from_birth)
	
	* Generate confidence intervals using standard error
	gen se = sd_total / sqrt(n)
	gen ci_lower = og_qt_month_tweets - 1.96 * se
	gen ci_upper = og_qt_month_tweets + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth, lcolor(gs8)) ///
		(line og_qt_month_tweets months_from_birth, lwidth(medthick) lcolor(blue)) ///
		, xline(0, lpattern(dash) lcolor(edkblue)) ///
		  ytitle("Avgerage Original Tweets per User") ///
		  xtitle("Months from Birth") ///
		  title("Original + Quote Tweeting Frequency Around Birth") ///
		  legend(label(1 "95% CI") label(2 "Avg Tweets") position(2) ring(0)) ///
		  note("Note: Trimmed accounts where total sample original/quote tweets > 95th percentile" ///
		  "Sample Size = 6,969 accounts") ///
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
* Save graph
graph export "$volume_figs/twt_behavior/original_tweets_over_time.jpg", replace
restore


****************************************************
******* FULL SAMPLE (by GENDER) *********
use "$final/tweet_volume_analysis_sample.dta", clear

**1. TOTAL TWEETS by GENDER (og+qt+rt+rply)
preserve
collapse (mean) total_month_tweets (sd) sd_tweets = total_month_tweets (count) n = total_month_tweets, ///
	by(months_from_birth female) 
	
	* Standard errors and 95% confidence intervals
	gen se = sd_tweets / sqrt(n)
	gen ci_lower = total_month_tweets - 1.96 * se
	gen ci_upper = total_month_tweets + 1.96 * se

** PLOT (total tweets)
twoway ///
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red%40)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%40)) ///
    (line total_month_tweets months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (line total_month_tweets months_from_birth if female==0, lcolor(blue) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avgerage Tweets per User by Month") ///
    xtitle("Months from Birth") ///
    title("Total Tweeting Frequency Around Birth by Gender") ///
    legend(order(3 4) label(3 "Female") label(4 "Male") position(2) ring(0)) ///
	note("Note: 95% CI. Total tweets = original+quote+retweet+reply." ///
		"Sample size = 5,671. ~44% female accounts, 56% male accounts" ///
		  "Trimmed accounts where total sample tweets > 95th percentile") ///
    graphregion(color(white)) ///
    xlabel(-18(2)18)
* Save graph
graph export "$volume_figs/twt_behavior/gender/tweets_over_time_bygender.jpg", replace
restore


**3. RETWEET & REPLY by GENDER (rt+rply)
preserve
collapse (mean) rt_rp_month_tweets (sd) sd_tweets = rt_rp_month_tweets (count) n = rt_rp_month_tweets, ///
	by(months_from_birth female) 
	
	* Standard errors and 95% confidence intervals
	gen se = sd_tweets / sqrt(n)
	gen ci_lower = rt_rp_month_tweets - 1.96 * se
	gen ci_upper = rt_rp_month_tweets + 1.96 * se

** PLOT (total tweets)
twoway ///
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red%40)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%40)) ///
    (line rt_rp_month_tweets months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (line rt_rp_month_tweets months_from_birth if female==0, lcolor(blue) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avgerage Retweets/Replies per User by Month") ///
    xtitle("Months from Birth") ///
    title("Retweet + Reply Frequency Around Birth by Gender") ///
    legend(order(3 4) label(3 "Female") label(4 "Male") position(2) ring(0)) ///
	note("Note: 95% CI. Total tweets = original+quote+retweet+reply." ///
		"Sample size = 5,671. ~44% female accounts, 56% male accounts" ///
		  "Trimmed accounts where total sample tweets > 95th percentile") ///
    graphregion(color(white)) ///
    xlabel(-18(2)18)
* Save graph
graph export "$volume_figs/twt_behavior/gender/rt_rply_tweets_over_time_bygender.jpg", replace
restore


**2. ORIGINAL & QUOTE TWEETS by GENDER (og+qt)
preserve
use "$final/ogqt_volume_analysis_sample.dta", clear
collapse (mean) og_qt_month_tweets (sd) sd_tweets = og_qt_month_tweets (count) n = og_qt_month_tweets, ///
	by(months_from_birth female) 
	
	* Standard errors and 95% confidence intervals
	gen se = sd_tweets / sqrt(n)
	gen ci_lower = og_qt_month_tweets - 1.96 * se
	gen ci_upper = og_qt_month_tweets + 1.96 * se

** PLOT (total tweets)
twoway ///
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red%40)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%40)) ///
    (line og_qt_month_tweets months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (line og_qt_month_tweets months_from_birth if female==0, lcolor(blue) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avgerage Original/Quote Tweets per User by Month") ///
    xtitle("Months from Birth") ///
    title("Original + Quote Tweeting Frequency Around Birth by Gender") ///
    legend(order(3 4) label(3 "Female") label(4 "Male") position(2) ring(0)) ///
		  note("Note: Trimmed accounts where total sample original/quote tweets > 95th percentile" ///
		  "Sample Size = 6,737 accounts, 44% female, 56% male") ///
    graphregion(color(white)) ///
    xlabel(-18(2)18)
* Save graph
graph export "$volume_figs/twt_behavior/gender/original_tweets_over_time_bygender.jpg", replace
restore
	
	

		
	

* ----------------------------------------------------------------------------------------------- *
* ----------------------------------------------------------------------------------------------- *
* ----------------------------------------------------------------------------------------------- *


	
*---------------------- OLD CODE (pre confidence intvls) ------------------- *
// **1. TOTAL TWEETS (og+qt+rt+rply)
// preserve
// collapse (mean) total_tweets, by(months_from_birth)
//
// 	* Average pre/post birth levels
// 	sum total_tweets if months_from_birth < 0
// 	local pre_birth_avg = r(mean)
// 	sum total_tweets if months_from_birth >= 0
// 	local post_birth_avg = r(mean)
//	
// ** PLOT (total tweets)
// twoway (line total_tweets months_from_birth, lwidth(medthick)) ///
//        , xline(0, lpattern(dash) lcolor(edkblue)) ///
// 	     yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
// 		 yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
//          ytitle("Avg Tweets per User") ///
//          xtitle("Weeks from Birth") ///
//          title("Tweeting Behavior Before and After Birth") ///
//          graphregion(color(white)) ///
//          xlabel(-18(2)18)
// * Save graph
// // graph export "$figures/twt_behavior/tweets_over_time.jpg", replace
// restore
//	
// **2. ORIGINAL & QUOTE TWEETS
//
// use "$final/tweet_volume_analysis_sample.dta", clear
// 	keep if full_3years==1 & acct_tweeted_postBA ==1
// 	keep if abs(months_from_birth) <= 18
//	
// preserve
//
// collapse (mean) orig_qt_count, by(months_from_birth)
//
// 	* Average pre/post birth levels
// 	sum orig_qt_count if months_from_birth < 0
// 	local pre_birth_avg = r(mean)
// 	sum orig_qt_count if months_from_birth >= 0
// 	local post_birth_avg = r(mean)
//
// ** PLOT (original/quote tweets)
// twoway (line orig_qt_count months_from_birth, lwidth(medthick)) ///
//        , xline(0, lpattern(dash) lcolor(edkblue)) ///
// 	     yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
// 		 yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
//          ytitle("Avg Original Tweets per User") ///
//          xtitle("Weeks from Birth") ///
//          title("Original Tweeting Behavior Before and After Birth") ///
//          graphregion(color(white)) ///
//          xlabel(-18(2)18)
// * Save graph
// // graph export "$figures/twt_behavior/original_tweets_over_time.jpg", replace
// restore
//
// **3. RETWEET & REPLIES
// preserve
//
// collapse (mean) rt_reply_count, by(week_from_birth)
//
// 	* Average pre/post birth levels
// 	sum rt_reply_count if week_from_birth < 0
// 	local pre_birth_avg = r(mean)
// 	sum rt_reply_count if week_from_birth >= 0
// 	local post_birth_avg = r(mean)
//
// ** PLOT (retweet/reply)
// twoway (line rt_reply_count week_from_birth, lwidth(medthick)) ///
//        , xline(0, lpattern(dash) lcolor(edkblue)) ///
// 	     yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
// 		 yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
//          ytitle("Avg Retweets/Replies per User") ///
//          xtitle("Weeks from Birth") ///
//          title("Retweet/Reply Tweeting Behavior Before and After Birth (Beyond BA)") ///
//          graphregion(color(white)) ///
//          xlabel(-78(13)78)
// * Save graph
// graph export "$figures/twt_behavior/rt_rply_tweets_over_time.jpg", replace
// restore
	

	
**1. TOTAL TWEETS by GENDER (og+qt+rt+rply)
preserve

collapse (mean) total_tweets, by(months_from_birth female) 

	* Female averages
	sum total_tweets if female==1 & months_from_birth < 0
	local fem_pre_avg = r(mean)
	sum total_tweets if female==1 & months_from_birth >= 0
	local fem_post_avg = r(mean)

	* Male averages
	sum total_tweets if female==0 & months_from_birth < 0
	local male_pre_avg = r(mean)
	sum total_tweets if female==0 & months_from_birth >= 0
	local male_post_avg = r(mean)

** PLOT (total tweets)
twoway ///
    (line total_tweets months_from_birth if female == 1, lcolor(red) lwidth(medthick)) ///
    (line total_tweets months_from_birth if female == 0, lcolor(blue) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    yline(`fem_pre_avg',  lcolor(red%30)  lpattern(dash)) ///
    yline(`fem_post_avg', lcolor(red%60)  lpattern(dash)) ///
    yline(`male_pre_avg', lcolor(blue%30) lpattern(dash)) ///
    yline(`male_post_avg', lcolor(blue%60) lpattern(dash)) ///
    ytitle("Avg Tweets per User") ///
    xtitle("Months from Birth") ///
    title("Tweeting Behavior Before and After Birth (by gender)") ///
    graphregion(color(white)) ///
    xlabel(-18(2)18) ///
    legend(label(1 "Female") label(2 "Male") position(2) ring(0))
* Save graph
graph export "$volume_figs/twt_behavior/gender/tweets_over_time_bygender.jpg", replace
restore


**2. ORIGINAL & QUOTE TWEETS by GENDER (og+qt)
preserve

collapse (mean) orig_qt_count, by(months_from_birth female) 

	* Female averages
	sum orig_qt_count if female==1 & months_from_birth < 0
	local fem_pre_avg = r(mean)
	sum orig_qt_count if female==1 & months_from_birth >= 0
	local fem_post_avg = r(mean)

	* Male averages
	sum orig_qt_count if female==0 & months_from_birth < 0
	local male_pre_avg = r(mean)
	sum orig_qt_count if female==0 & months_from_birth >= 0
	local male_post_avg = r(mean)

** PLOT (original & quote)
twoway ///
    (line orig_qt_count months_from_birth if female == 1, lcolor(red) lwidth(medthick)) ///
    (line orig_qt_count months_from_birth if female == 0, lcolor(blue) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    yline(`fem_pre_avg',  lcolor(red%30)  lpattern(dash)) ///
    yline(`fem_post_avg', lcolor(red%60)  lpattern(dash)) ///
    yline(`male_pre_avg', lcolor(blue%30) lpattern(dash)) ///
    yline(`male_post_avg', lcolor(blue%60) lpattern(dash)) ///
    ytitle("Avg Original Tweets per User") ///
    xtitle("Months from Birth") ///
    title("Original Tweeting Behavior Before and After Birth (by gender)") ///
    graphregion(color(white)) ///
    xlabel(-18(2)18) ///
    legend(label(1 "Female") label(2 "Male") position(2) ring(0))
* Save graph
graph export "$volume_figs/twt_behavior/gender/original_tweets_over_time_bygender.jpg", replace
restore
	
	
**3. RETWEET & REPLY by GENDER (rt+rply)
preserve

collapse (mean) rt_reply_count, by(months_from_birth female) 

	* Female averages
	sum rt_reply_count if female==1 & months_from_birth < 0
	local fem_pre_avg = r(mean)
	sum rt_reply_count if female==1 & months_from_birth >= 0
	local fem_post_avg = r(mean)

	* Male averages
	sum rt_reply_count if female==0 & months_from_birth < 0
	local male_pre_avg = r(mean)
	sum rt_reply_count if female==0 & months_from_birth >= 0
	local male_post_avg = r(mean)

** PLOT (retweet & reply)
twoway ///
    (line rt_reply_count months_from_birth if female == 1, lcolor(red) lwidth(medthick)) ///
    (line rt_reply_count months_from_birth if female == 0, lcolor(blue) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    yline(`fem_pre_avg',  lcolor(red%30)  lpattern(dash)) ///
    yline(`fem_post_avg', lcolor(red%60)  lpattern(dash)) ///
    yline(`male_pre_avg', lcolor(blue%30) lpattern(dash)) ///
    yline(`male_post_avg', lcolor(blue%60) lpattern(dash)) ///
    ytitle("Avg Retweets/Replies per User") ///
    xtitle("Months from Birth") ///
    title("Retweet/Reply Tweeting Behavior Before and After Birth (by gender)") ///
    graphregion(color(white)) ///
    xlabel(-18(2)18) ///
    legend(label(1 "Female") label(2 "Male") position(2) ring(0))
* Save graph
graph export "$volume_figs/twt_behavior/gender/rt_rply_tweets_over_time_bygender.jpg", replace
restore
	
	
// ****************************************************
// ******* FULL SAMPLE (by RACE) *********
// use "$final/tweet_volume_analysis_sample.dta", clear
//
// merge m:1 unique_id using "$final/user_analysis_sample.dta", keepusing(race) //30 not matched, check out
// drop _merge
//
// * Generate variables for figs (same as above)
// gen days_from_birth = date - date_birth
// gen months_from_birth = floor(days_from_birth / 30)
// gen week_from_birth = floor(days_from_birth / 7)
// gen total_tweets = orig_qt_count + rt_reply_count
//
//
// **1. TOTAL TWEETS by RACE (og+qt+rt+rply)
// preserve
// collapse (mean) total_tweets, by(week_from_birth race) 
//
// ** PLOT (total tweets)
// twoway ///
//     (line total_tweets week_from_birth if race == 1, lcolor(cranberry) lwidth(medthick)) ///
// 	(line total_tweets week_from_birth if race == 2, lcolor(lime) lwidth(medthick)) ///
// 	(line total_tweets week_from_birth if race == 3, lcolor(midblue) lwidth(medthick)) ///
// 	(line total_tweets week_from_birth if race == 4, lcolor(yellow) lwidth(medthick)) ///
//     (line total_tweets week_from_birth if race == 5, lcolor(lavender) lwidth(medthick)), ///
//     xline(0, lpattern(dash) lcolor(edkblue)) ///
//     ytitle("Avg Tweets per User") ///
//     xtitle("Weeks from Birth") ///
//     title("Tweeting Behavior Before and After Birth (by race)") ///
//     graphregion(color(white)) ///
//     xlabel(-78(13)78) ///
//     legend(label(1 "Black") label(2 "White") label(3 "Asian") label(4 "Hispanic") label(5 "Other") position(2) ring(0))
// * Save graph
// graph export "$figures/twt_behavior/tweets_over_time_byrace.jpg", replace
// restore
//
//
// **2. ORIGINAL & QUOTE TWEETS by RACE (og+qt)
// preserve
// collapse (mean) orig_qt_count, by(week_from_birth race) 
//
// ** PLOT (original + quote)
// twoway ///
//     (line orig_qt_count week_from_birth if race == 1, lcolor(cranberry) lwidth(medthick)) ///
// 	(line orig_qt_count week_from_birth if race == 2, lcolor(lime) lwidth(medthick)) ///
// 	(line orig_qt_count week_from_birth if race == 3, lcolor(midblue) lwidth(medthick)) ///
// 	(line orig_qt_count week_from_birth if race == 4, lcolor(yellow) lwidth(medthick)) ///
//     (line orig_qt_count week_from_birth if race == 5, lcolor(lavender) lwidth(medthick)), ///
//     xline(0, lpattern(dash) lcolor(edkblue)) ///
//     ytitle("Avg Original Tweets per User") ///
//     xtitle("Weeks from Birth") ///
//     title("Original Tweeting Behavior Before and After Birth (by race)") ///
//     graphregion(color(white)) ///
//     xlabel(-78(13)78) ///
//     legend(label(1 "Black") label(2 "White") label(3 "Asian") label(4 "Hispanic") label(5 "Other") position(2) ring(0))
// * Save graph
// graph export "$figures/twt_behavior/original_tweets_over_time_byrace.jpg", replace
// restore
//
//
// **3. RETWEET & REPLY by RACE (rt+rply)
// preserve
// collapse (mean) rt_reply_count, by(week_from_birth race) 
//
// ** PLOT (retweet/reply)
// twoway ///
//     (line rt_reply_count week_from_birth if race == 1, lcolor(cranberry) lwidth(medthick)) ///
// 	(line rt_reply_count week_from_birth if race == 2, lcolor(lime) lwidth(medthick)) ///
// 	(line rt_reply_count week_from_birth if race == 3, lcolor(midblue) lwidth(medthick)) ///
// 	(line rt_reply_count week_from_birth if race == 4, lcolor(yellow) lwidth(medthick)) ///
//     (line rt_reply_count week_from_birth if race == 5, lcolor(lavender) lwidth(medthick)), ///
//     xline(0, lpattern(dash) lcolor(edkblue)) ///
//     ytitle("Avg Original Tweets per User") ///
//     xtitle("Weeks from Birth") ///
//     title("Retweet/Reply Tweeting Behavior Before and After Birth (by race)") ///
//     graphregion(color(white)) ///
//     xlabel(-78(13)78) ///
//     legend(label(1 "Black") label(2 "White") label(3 "Asian") label(4 "Hispanic") label(5 "Other") position(2) ring(0))
// * Save graph
// graph export "$figures/twt_behavior/rt_rply_tweets_over_time_byrace.jpg", replace
// restore
//
//
//
// ****************************************************
// ******* RESTRICTED SAMPLE *********
//
// use "$final/tweet_volume_analysis_sample.dta", clear
//
// ** Generate "months from birth" var
// gen days_from_birth = date - date_birth
// gen months_from_birth = floor(days_from_birth / 30)
//	
// ** Sum tweet habits per day
// gen total_tweets = orig_qt_count + rt_reply_count
// ** Average tweets/week
// gen week_from_birth = floor(days_from_birth / 7)
//
// /// Restricting the sample
// * find minimum days_from_birth per unique_id
// egen min_days = min(days_from_birth), by(unique_id)
// *create not_546 flag
// gen not_546 = min_days > -546
//
// * find maximum days_from_birth per unique_id
// egen max_days = max(days_from_birth), by(unique_id)
// *create not_546 flag
// replace not_546 = 1 if max_days < 546 // No obs that didn't make it to 546 days post birth
//
// drop if not_546 == 1
//
// **1. TOTAL TWEETS (og+qt+rt+rply)
// preserve
// collapse (mean) total_tweets, by(week_from_birth)
//
// ** PLOT (total tweets)
// twoway (line total_tweets week_from_birth, lwidth(medthick) lcolor(orange)) ///
//        , xline(0, lpattern(dash) lcolor(edkblue)) ///
//          ytitle("Avg Tweets per User") ///
//          xtitle("Weeks from Birth") ///
//          title("Tweeting Behavior Before and After Birth (restr.)") ///
//          graphregion(color(white)) ///
//          xlabel(-78(13)78)
// * Save graph
// graph export "$figures/tweets_over_time_restricted.jpg", replace
// restore
//
// **2. ORIGINAL & QUOTE TWEETS
// preserve
// collapse (mean) orig_qt_count, by(week_from_birth)
//
// ** PLOT (original/quote tweets)
// twoway (line orig_qt_count week_from_birth, lwidth(medthick) lcolor(orange)) ///
//        , xline(0, lpattern(dash) lcolor(edkblue)) ///
//          ytitle("Avg Original Tweets per User") ///
//          xtitle("Weeks from Birth") ///
//          title("Original Tweeting Behavior Before and After Birth (restr.)") ///
//          graphregion(color(white)) ///
//          xlabel(-78(13)78)
// * Save graph
// graph export "$figures/original_tweets_over_time_restricted.jpg", replace
// restore
//
// **3. RETWEET & REPLIES
// preserve
// collapse (mean) rt_reply_count, by(week_from_birth)
//
// ** PLOT (retweet/reply)
// twoway (line rt_reply_count week_from_birth, lwidth(medthick) lcolor(orange)) ///
//        , xline(0, lpattern(dash) lcolor(edkblue)) ///
//          ytitle("Avg Retweets/Replies per User") ///
//          xtitle("Weeks from Birth") ///
//          title("Retweet/Reply Tweeting Behavior Before and After Birth (restr.)") ///
//          graphregion(color(white)) ///
//          xlabel(-78(13)78)
// * Save graph
// graph export "$figures/rt_rply_tweets_over_time_restricted.jpg", replace
// restore





// ************************ EXTRA NOTES ************************
//
// ********************** Figure out missing varialbes
// * is the date_birth less than 1.5 years after user_created_at? 
// 	* this may result in being unable to scrape pre history because they weren't on Twitter for at least a year and a half before announcing birth
//	
// // Calcualte # of days between account creation and birth_date
// gen days_acct_b4_birth = date_birth - user_created_at
//
// // Which accounts created less than 1.5 years before child's birth_date
// gen timing_issue = days_acct_b4_birth < 547
// gen timing_issue1yr = days_acct_b4_birth < 365
//	
// // how many unique_id have this timing issue?
// preserve
// collapse (max) timing_issue, by(unique_id)
// count if timing_issue == 1
// restore

