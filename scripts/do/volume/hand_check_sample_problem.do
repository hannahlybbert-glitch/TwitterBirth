

use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years==1
	
	drop if missing(rt_reply_count)

// Trim 95th percentile of tweeters
summarize total_sample_tweets, detail
	local p50 = r(p50)
	
	drop if total_sample_tweets > `p50' & !missing(total_sample_tweets)
	distinct author_id
	distinct author_id if !missing(rt_reply_count)
		
	
** 1A. TOTAL TWEETS - 95% conf intvl (og+qt+rt+rply)
preserve
// 	keep if account_30_mo_old ==1
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
		  note("Note: Total tweets = original + quote + retweet + reply. Red line = pre-birth average. Green line = post birth average." ///
		  "Trimmed observations where total month tweets > 95th percentile (> 419 tweets/month)" ///
		  "Sample Size = 6,327 accounts") ///
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
// graph export "$volume_figs/twt_behavior/tweets_over_time.jpg", replace
restore




* ====================== HAND CHECKING BEHAVIOR ========================== *
use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years==1
	
	drop if missing(rt_reply_count)
	
collapse (max) total_month_tweets , by(author_id months_from_birth )
sum total_month_tweets, d
browse author_id  months_from_birth total_month_tweets if total_month_tweets > = 1103

* hand checking

	browse months_from_birth total_month_tweets if author_id == "101180245"
		* first half of data is crazy high, second half is actually all under the 95th percentile (50% > 95th, 50% < 95th)
		
	browse months_from_birth total_month_tweets if author_id == "21109095"
		* again, 50% is crazy, the other 50% is totally normal
		
	browse months_from_birth total_month_tweets if author_id == "273733157"
		* 16 months < 95th. Clustered heavy in pre birth period.
	
	browse months_from_birth total_month_tweets if author_id == "21612784"
		* big tweeter all through sample
	
	browse months_from_birth total_month_tweets if author_id == "297279897"
		* big tweeter
		
	browse months_from_birth total_month_tweets if author_id == "312926404"
		* big tweeter
	
	browse months_from_birth total_month_tweets if author_id == "21109095"
	browse months_from_birth total_month_tweets if author_id == "21109095"

preserve
keep if total_month_tweets > 1103
	twoway ///
		(line total_month_tweets months_from_birth, lwidth(medthick) lcolor(blue)) ///
		, xline(0, lpattern(dash) lcolor(edkblue)) ///
		  ytitle("Avgerage Total Tweets per User") ///
		  xtitle("Months from Birth") ///
		  title("Total Tweeting Frequency Around Birth") ///
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
restore	
	
	
	
	
	
use "$final/tweet_volume_analysis_sample.dta", clear
// 	keep if full_3years==1


** 1A. TOTAL TWEETS - 95% conf intvl (og+qt+rt+rply)
preserve
	* First: Average by account
	collapse (mean) avg_tweets_per_account = total_month_tweets, by(author_id months_from_birth)
	
	* Then: Average across accounts
	collapse (mean) total_month_tweets = avg_tweets_per_account ///
		(sd) sd_total = avg_tweets_per_account ///
		(count) n = avg_tweets_per_account, ///
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
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
// graph export "$volume_figs/twt_behavior/tweets_over_time.jpg", replace
restore	
	




// summarize total_month_tweets, detail
// 	local p95 = r(p95)
//	
// 	drop if total_month_tweets > `p95' & !missing(total_month_tweets)
// 	distinct author_id
// 	distinct author_id if !missing(rt_reply_count)