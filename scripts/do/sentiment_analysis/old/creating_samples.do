****** Getting Samples ready for sentiment analysis testing ******

use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear

	gen rand = runiform()

	sort rand

	keep in 1/1000

	drop rand

** Make some vars strings so that excel doesn't round
	tostring created_at, replace
	* tweet_id preservation
	gen tweet_id_quotes = "'" + tweet_id + "'"
	drop tweet_id
	rename tweet_id_quotes tweet_id
	
	order unique_id author_id tweet_id created_at text like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls

save "$sentiment/tweet_text_sample.dta", replace

// export delimited using "$sentiment/tweet_text_sample.csv", replace
export delimited using "$sentiment/tweet_text_sample.csv", replace quote delimiter(",") nolabel



// ** Going to need to convert some variables to strings so Excel doesn't mess it up (done above) and then will have to convert back to integers or date variables post sentiment analysis (below)
//
// * STRING --> INTEGERS
// 	gen tweet_id_clean = subinstr(tweet_id, "'", "", .)
// 	drop tweet_id
// 	rename tweet_id_clean tweet_id
// 	order unique_id author_id tweet_id created_at text like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls
//
// * DATE VARIABLES
// 	destring created_at, replace
// 	format created_at %td
//	
// 	* Don't think this is right here for the var type it ended up being in excel
// 	gen stata_date = date(created_at, "DMY")
// 	* Format it as a readable date
// 	format stata_date %td