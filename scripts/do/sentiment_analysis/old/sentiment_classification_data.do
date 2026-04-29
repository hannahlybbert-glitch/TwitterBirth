****** Getting Samples ready for sentiment/classification analysis testing ******

use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
		
	* Handle duplicates vite-fait
	duplicates tag tweet_id, gen(dup_tag)
	bysort tweet_id (tweet_id): drop if dup_tag == 1 & _n == 2
	drop dup_tag
	
	* Handle links in tweets (to avoid polluting textual analysis)
	gen text_nolink = ustrregexra(text, "https?://[^ ]+", "")
	drop if missing(text_nolink)
	drop text
	rename text_nolink text
	order unique_id author_id tweet_id created_at text
	
	* Preserve tweet_id as a string
	gen tweet_id_quotes = "'" + tweet_id + "'"
	drop tweet_id
	rename tweet_id_quotes tweet_id
		
	order unique_id author_id tweet_id created_at text like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls
	
save "$sentiment/tweet_text_only_FULL.dta", replace
export delimited using "$sentiment/tweet_text_only_FULL.csv", replace quote delimiter(",") nolabel
	
***** 10,000 SAMPLE *****
use "$sentiment/tweet_text_only_FULL.dta", clear

	gen rand = runiform()
	sort rand
	keep in 1/10000
	drop rand

save "$sentiment/tweet_text_only_10kSAMPLE.dta", replace
export delimited using "$sentiment/tweet_text_only_10kSAMPLE.csv", replace quote delimiter(",") nolabel







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