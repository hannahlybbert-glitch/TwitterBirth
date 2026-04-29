* Author: Hannah Lybbert
* Created: Jan 8, 2026
* Purpose: Build dataset for volume analysis (Deal with outliers and generate a couple of vars)


* Load data
use "$final/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years==1
	
	drop if missing(rt_reply_count) // I think we need to drop all observations we don't have rt reply volume for because the original/quote tweet coutns are crazy skewed for those observations.

	summarize total_month_tweets, detail
	local p95 = r(p95)
	
	drop if total_month_tweets > `p95' & !missing(total_month_tweets)
	distinct author_id
	distinct author_id if !missing(rt_reply_count)
	
	
	egen og_qt_month_tweets = sum(orig_qt_count), by(unique_id months_from_birth)
	replace og_qt_month_tweets = . if missing(orig_qt_count)	

	egen rt_rp_month_tweets = sum(rt_reply_count), by(unique_id months_from_birth)
	replace rt_rp_month_tweets = . if missing(rt_reply_count)		


save "$final/tweet_volume_analysis_sample.dta", replace




