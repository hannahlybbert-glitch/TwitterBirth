* Author: Hannah Lybbert
* Created: 01/09/2025
* Purpose: Log Volume Behavior Graphs



use "$volume_analysis/tweet_volume_analysis_sample.dta", clear
// 	keep if full_3years ==1

gen tmt_1 = total_month_tweets +1 
gen ltotal_month_tweets = log(tmt_1)

gen rtrpmt_1 = rt_rp_month_tweets +1
gen lrt_rp_month_tweets = log(rtrpmt_1)


* TOTAL TWEETS
preserve
	collapse (mean) ltotal_month_tweets ///
			 (sd)   sd_total = ltotal_month_tweets ///
			 (count) n = ltotal_month_tweets, ///
			 by(months_from_birth)
	
	* Generate confidence intervals using standard error
	gen se = sd_total / sqrt(n)
	gen ci_lower = ltotal_month_tweets - 1.96 * se
	gen ci_upper = ltotal_month_tweets + 1.96 * se


	twoway ///
		(rcap ci_upper ci_lower months_from_birth, lcolor(gs8)) ///
		(line ltotal_month_tweets months_from_birth, lwidth(medthick) lcolor(blue)) ///
		, xline(0, lpattern(dash) lcolor(edkblue)) ///
		  ytitle("Avgerage Log Tweets per User Per Month") ///
		  xtitle("Months from Birth") ///
		  title("Total Log Tweeting Frequency Around Birth") ///
		  legend(label(1 "95% CI") label(2 "Avg Tweets") position(2) ring(0)) ///
		  note("Note: Total tweets = original + quote + retweet + reply. Sample size =  5,862 accounts" ///
		  "Note: Generated log total month tweets by adding 1 to all total month tweets to avoid undefined values") ///
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
graph export "$volume_figs/twt_behavior/logtweets_over_time.jpg", replace
restore


* RETWEET / REPLIES
preserve
	collapse (mean) lrt_rp_month_tweets ///
			 (sd)   sd_total = lrt_rp_month_tweets ///
			 (count) n = lrt_rp_month_tweets, ///
			 by(months_from_birth)
	
	* Generate confidence intervals using standard error
	gen se = sd_total / sqrt(n)
	gen ci_lower = lrt_rp_month_tweets - 1.96 * se
	gen ci_upper = lrt_rp_month_tweets + 1.96 * se


	twoway ///
		(rcap ci_upper ci_lower months_from_birth, lcolor(gs8)) ///
		(line lrt_rp_month_tweets months_from_birth, lwidth(medthick) lcolor(blue)) ///
		, xline(0, lpattern(dash) lcolor(edkblue)) ///
		  ytitle("Avgerage Log Rt/Replies per User Per Month") ///
		  xtitle("Months from Birth") ///
		  title("Log Retweet & Reply Frequency") ///
		  legend(label(1 "95% CI") label(2 "Avg Tweets") position(2) ring(0)) ///
		  note("Note: Generated log total month tweets by adding 1 to all total month tweets to avoid undefined values" ///
		  "Sample size =  5,862 accounts") ///
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
graph export "$volume_figs/twt_behavior/log_rt_rp_over_time.jpg", replace
restore



* ------ BY GENDER -------- *
**1. TOTAL TWEETS by GENDER (og+qt+rt+rply)
preserve
collapse (mean) ltotal_month_tweets (sd) sd_tweets = ltotal_month_tweets (count) n = ltotal_month_tweets, ///
	by(months_from_birth female) 
	
	* Standard errors and 95% confidence intervals
	gen se = sd_tweets / sqrt(n)
	gen ci_lower = ltotal_month_tweets - 1.96 * se
	gen ci_upper = ltotal_month_tweets + 1.96 * se

** PLOT (total tweets)
twoway ///
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red%40)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%40)) ///
    (line ltotal_month_tweets months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (line ltotal_month_tweets months_from_birth if female==0, lcolor(blue) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avgerage Log Tweets per User by Month") ///
    xtitle("Months from Birth") ///
    title("Total Log Tweeting Frequency Around Birth by Gender") ///
    legend(order(3 4) label(3 "Female") label(4 "Male") position(2) ring(0)) ///
	note("Note: 95% CI. Total tweets = original+quote+retweet+reply." ///
		"Sample size = 5,671. ~44% female accounts, 56% male accounts") ///
    graphregion(color(white)) ///
    xlabel(-18(2)18)
* Save graph
graph export "$volume_figs/twt_behavior/gender/log_tweets_by_gender.jpg", replace
restore


** 3. RETWEET / REPLY TWEETS by GENDER
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
    ytitle("Avgerage Log Tweets per User by Month") ///
    xtitle("Months from Birth") ///
    title("Log Retweet & Reply Frequency by Gender") ///
    legend(order(3 4) label(3 "Female") label(4 "Male") position(2) ring(0)) ///
	note("Note: 95% CI. Sample size = 5,671. ~44% female accounts, 56% male accounts") ///
    graphregion(color(white)) ///
    xlabel(-18(2)18)
* Save graph
graph export "$volume_figs/twt_behavior/gender/log_rt_rp_by_gender.jpg", replace
restore



use "$volume_analysis/ogqt_volume_analysis_sample.dta", clear
* ORIGINAL & QUOTE TWEETS

gen oqtmt_1 = og_qt_month_tweets +1
gen log_qt_month_tweets = log(oqtmt_1)

preserve
	collapse (mean) log_qt_month_tweets ///
			 (sd)   sd_total = log_qt_month_tweets ///
			 (count) n = log_qt_month_tweets, ///
			 by(months_from_birth)
	
	* Generate confidence intervals using standard error
	gen se = sd_total / sqrt(n)
	gen ci_lower = log_qt_month_tweets - 1.96 * se
	gen ci_upper = log_qt_month_tweets + 1.96 * se

	twoway ///
		(rcap ci_upper ci_lower months_from_birth, lcolor(gs8)) ///
		(line log_qt_month_tweets months_from_birth, lwidth(medthick) lcolor(blue)) ///
		, xline(0, lpattern(dash) lcolor(edkblue)) ///
		  ytitle("Average Log Tweets per Month") ///
		  xtitle("Months from Birth") ///
		  title("") ///
		  legend(label(1 "95% CI") label(2 "Avg Tweets") position(2) ring(0)) ///
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
graph export "$volume_figs/twt_behavior/log_og_qt_over_time.jpg", replace
restore


**2. ORIGINAL and QUOTE TWEETS by GENDER
preserve
collapse (mean) log_qt_month_tweets (sd) sd_tweets = log_qt_month_tweets (count) n = log_qt_month_tweets, ///
	by(months_from_birth female) 
	
	* Standard errors and 95% confidence intervals
	gen se = sd_tweets / sqrt(n)
	gen ci_lower = log_qt_month_tweets - 1.96 * se
	gen ci_upper = log_qt_month_tweets + 1.96 * se


** PLOT (total tweets)
twoway ///
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red%40)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%40)) ///
    (line log_qt_month_tweets months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (line log_qt_month_tweets months_from_birth if female==0, lcolor(blue) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avgerage Log Tweets per Month") ///
    xtitle("Months from Birth") ///
    title("") ///
    legend(order(3 4) label(3 "Female") label(4 "Male") position(2) ring(0)) ///
    graphregion(color(white)) ///
    xlabel(-18(2)18)
* Save graph
graph export "$volume_figs/twt_behavior/gender/log_og_qt_by_gender.jpg", replace
restore

