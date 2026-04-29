* Author: Hannah Lybbert
* Created: 01/07/2026
* Purpose: Winsorize practice


* Load data
use "$final/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years==1
	

preserve
	summarize total_month_tweets, detail
	local p95 = r(p95)
	drop if total_month_tweets >= `p95' & !missing(total_month_tweets)
	distinct author_id
	distinct author_id if !missing(rt_reply_count)
restore	

*------- MUST RUN THIS SECTION TOGETHER ------
* Store the 95th percentile value as a variable
summarize total_month_tweets, detail
local p95 = r(p95)

* Winsorzie at 95th percentile
replace total_month_tweets = `p95' if total_month_tweets > `p95' & !missing(total_month_tweets)
* --------------------------------------------- *



* TEST SOME GRAPHS

* BASIC VOLUME GRAPH
preserve
	collapse (mean) total_month_tweets ///
			 (sd)   sd_total = total_month_tweets ///
			 (count) n = total_month_tweets, ///
			 by(months_from_birth)
	
	* Generate confidence intervals using standard error
	gen se = sd_total / sqrt(n)
	gen ci_lower = total_month_tweets - 1.96 * se
	gen ci_upper = total_month_tweets + 1.96 * se

	* Pre/post averages
	sum total_month_tweets if months_from_birth < 0
	local pre_birth_avg = r(mean)
	sum total_month_tweets if months_from_birth >= 0
	local post_birth_avg = r(mean)

	twoway ///
		(rcap ci_upper ci_lower months_from_birth, lcolor(gs8)) ///
		(line total_month_tweets months_from_birth, lwidth(medthick) lcolor(blue)) ///
		, xline(0, lpattern(dash) lcolor(edkblue)) ///
		  yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
		  yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
		  ytitle("Avgerage Tweets per User per Month") ///
		  xtitle("Months from Birth") ///
		  title("Total Tweeting Frequency Around Birth - Winsorized 95th pctl") ///
		  legend(label(1 "95% CI") label(2 "Avg Tweets") position(2) ring(0)) ///
		  note("Note: Total tweets = original + quote + retweet + reply. Red line = pre-birth average. Green line = post birth average." ///
		  "Sample Size = 6,353 accounts (85% of valid accounts)") ///
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
graph export "$volume_figs/twt_behavior/tweets_over_time_WINS.jpg", replace
restore


* EXTENSIVE MARGIN
preserve
	collapse (mean) total_month_tweets, by(months_from_birth author_id)
	sort author_id months

	gen active_this_month = (total_month_tweets>0)

collapse (mean) active_this_month, by(months_from_birth)
twoway line active_this_month months_from_birth, sort ///
    ytitle("Share active this month") ///
    xtitle("Months from birth") ///
	title("Extensive Margin - Monthly users (Winsorized 95th pctl)") ///
	xline(0, lpattern(dash) lcolor(edkblue)) ///
	xlabel(-18(2)18) ///
	note("'Active' if posted at least once during that month." ///
	"Sample Size = 6,353 accounts (85% of valid accounts)")

graph export "$volume_figs/twt_behavior/extensive_margin_WINS.jpg", replace
restore


* LOG GRAPH
gen tmt_1 = total_month_tweets +1 
gen ltotal_month_tweets = log(tmt_1)

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
		  title("Total Log Tweeting Frequency - Winsorized 95th pctl") ///
		  legend(label(1 "95% CI") label(2 "Avg Tweets") position(2) ring(0)) ///
		  note("Note: Total tweets = original + quote + retweet + reply." ///
		  "Sample Size = 6,353 accounts (85% of valid accounts)") ///
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
graph export "$volume_figs/twt_behavior/logtweets_over_time_WINS.jpg", replace
restore

