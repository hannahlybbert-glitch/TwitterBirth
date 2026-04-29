* Author: Hannah Lybbert
* Created: 
* Purpose: Clean python sentiment output

** Data from python TweetNLP sentiment analysis (sample)
// import delimited using "$sentiment/output/tweetNLP/sentiment_scores10k_mypipe.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
import delimited using "$sentiment/output/tweetNLP/sentiment_scoresFULL.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear


** CLEANING / DATA PREP 
	* STRING --> INTEGERS
	gen tweet_id_clean = subinstr(tweet_id, "'", "", .)
	drop tweet_id
	rename tweet_id_clean tweet_id
	gen author_id_clean = subinstr(author_id, "'", "", .)
	drop author_id
	rename author_id_clean author_id

	* DATE VARIABLES
	destring created_at date_birth date_birth_tweet, replace
	format created_at date_birth date_birth_tweet %td

	* DESTRING 
	foreach var in like_count retweet_count reply_count quote_count neg	neu pos sentiment_score post_birth days_from_birth week_from_birth months_from_birth full_3years no_rt_reply tweet_postba acct_tweeted_postba female {
		destring `var', replace
	}

	* RESTRICT 18 pre/18 post (cannot be more than 18mo pre/post)	
	* Drop outside of 18 months of data 
	drop if abs(days_from_birth) > 547 // Keep only 18 months of data for each acct
	drop if months_from_birth == -19 | months_from_birth == 18 // drop if month is larger than the panel size
	drop if full_3years == 0

	
order unique_id author_id tweet_id created_at date_birth date_birth_tweet text like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls


* Total month tweets variable
gen counter = 1
egen total_og_month_tweets = sum(counter), by(months_from_birth unique_id)

// save "$sentiment/output/sentiment_scores10k.dta", replace
save "$sentiment/output/sentiment_scoresFULL_clean.dta", replace

	drop if abs(days_from_birth) <= 14 // 
	save "$sentiment/output/sentiment_scores_1modrop.dta", replace

	
	
	
	
	
	
// ***** TRIM top 5% of tweeters *****
// sum total_og_month_tweets, d
// local p95 = r(p95)
// drop if total_og_month_tweets > `p95'
// drop counter
// drop total_og_month_tweets
//
// save "$sentiment/output/sentiment_analysis_sample.dta", replace


