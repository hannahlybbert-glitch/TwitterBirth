* Author: Hannah Lybbert
* Created: Aug 7, 2026
* Purpose: Get average weekly lifetime tweets trim metric for treatment data to use for control data API pull


use "$cleaned/user_info_full_sample_CLEAN.dta", clear

di "Initial clean user sample"
	distinct author_id
	
* --- User level trim (average lifetime tweets) ---
	keep if full_3years == 1

di "Sample of authors with 3 years of pre-birth data (before any trimming)"
	distinct author_id
	
* Generate the reference date (day the twitter treatment group was pulled) to compute weeks alive
	gen REF_date = mdy(4,15,2025) if year(date_birth_tweet) == 2018
	replace REF_date = mdy(7,17,2025) if inrange(year(date_birth_tweet), 2013, 2017)
	format REF_date %td

	gen weeks_alive = (REF_date - user_created_at) / 7
	gen avg_weekly_tweets = lifetime_posts / weeks_alive

* Compute the 95th percentile of average weekly lifetime tweets and trim off the top 5%
	summarize avg_weekly_tweets, detail
		local p95_m2 = r(p95)
	drop if avg_weekly_tweets > `p95_m2' & !missing(avg_weekly_tweets)

di "After trimming avg weekly lifetime tweets"
distinct author_id
di "95th percentile cut off (use for control phase 2 filtering):"
di "p95 = " %6.2f `p95_m2' ""

keep author_id tweet_id avg_weekly_tweets
save "$cleaned/lifetime_trim_authors.dta", replace