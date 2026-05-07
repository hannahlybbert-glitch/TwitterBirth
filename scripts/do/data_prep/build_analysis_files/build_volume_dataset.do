* Author: Hannah Lybbert
* Created: Jan 8, 2026
* Purpose: Build dataset for volume analysis (Deal with outliers and generate a couple of vars)


* ------ BUILD ORIGINAL + QUOTE TWEET VOLUME DATASET ------ *
use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years==1
	distinct author_id
summarize og_qt_sample_tweets, detail
	local p95 = r(p95)
	
	drop if og_qt_sample_tweets > `p95' & !missing(og_qt_sample_tweets)
	distinct author_id
save "$final/ogqt_volume_analysis_sample.dta", replace
	
	
* ----- BUILD TOTAL TWEET / RETWEET REPLIES VOLUME DATASET ------ *
use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
distinct author_id
	keep if full_3years==1
	distinct author_id
	drop if missing(rt_reply_count)
	distinct author_id

// Trim 95th percentile of tweeters
summarize total_sample_tweets, detail
	local p95 = r(p95)
	
	drop if total_sample_tweets > `p95' & !missing(total_sample_tweets)
	distinct author_id
	distinct author_id if !missing(rt_reply_count)

save "$final/tweet_volume_analysis_sample.dta", replace




// summarize total_month_tweets, detail
// 	local p95 = r(p95)
//	
// 	drop if total_month_tweets > `p95' & !missing(total_month_tweets)
// 	distinct author_id
// 	distinct author_id if !missing(rt_reply_count)		
	
	
	
	
