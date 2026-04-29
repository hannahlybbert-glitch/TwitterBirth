* Author: Hannah Lybbert
* Created: 12/01/2025
* Purpose: Clean topics python output

// import delimited using "$sentiment/output/tweetNLP/topic_classifier_10k.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

import delimited using "$sentiment/output/tweetNLP/NLP_topic_classifier_FULL.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear



*--------- CLEANING / DATA PREP ----------*
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
	foreach var in female days_from_birth week_from_birth months_from_birth like_count retweet_count reply_count quote_count full_3years no_rt_reply post_birth acct_tweeted_postba tweet_postba family_prob family_flag {
		destring `var', replace
	}

	* RESTRICT 18 pre/18 post (cannot be more than 18mo pre/post)
	drop if abs(days_from_birth) > 547 // Keep only 18 months of data for each acct
	drop if months_from_birth == -19 | months_from_birth == 18 // drop if month is larger than the panel size
	drop if full_3years == 0
	
order unique_id author_id tweet_id text created_at date_birth date_birth_tweet like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls
*** cleaning done ***


* --------- DATA SPECIFIC CLEANING ---------- *
	* change family threshold
	replace family_flag = 1 if family_prob >= 0.2

save "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN.dta", replace

	* drop birth month
	drop if abs(days_from_birth) <= 14
save "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN_noBM.dta", replace



* ========================================================================================== *

* Karthik's topics run (full probabilities for all categories)
import delimited using "C:/Users/hlybbert/Downloads/tweetnlp_topics.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear


*--------- CLEANING / DATA PREP ----------*
	* DATE VARIABLES
	foreach var in created_at date_birth date_birth_tweet{
		replace `var' = subinstr(`var', "-", "", .)
		gen `var'_num = daily(`var', "YMD")
		format `var'_num %td
		drop `var'
		rename `var'_num `var'
	}


	* DESTRING 
	foreach var in female days_from_birth week_from_birth months_from_birth like_count retweet_count reply_count quote_count full_3years no_rt_reply post_birth tweet_postba acct_tweeted_postba arts__culture business__entrepreneurs celebrity__pop_culture diaries__daily_life family fashion__style film_tv__video fitness__health food__dining gaming learning__educational music news__social_concern other_hobbies relationships science__technology sports travel__adventure youth__student_life {
		destring `var', replace
	}

	* RESTRICT 18 pre/18 post (cannot be more than 18mo pre/post)
	drop if abs(days_from_birth) > 547 // Keep only 18 months of data for each acct
	drop if months_from_birth == -19 | months_from_birth == 18 // drop if month is larger than the panel size
	
	* Keep if active post BA and we have >= 18 months pre birth data
	keep if acct_tweeted_postba == 1 & full_3years == 1

	* Generate family flag
	gen family_flag = (family >= 0.2)
	
order unique_id author_id tweet_id text created_at date_birth date_birth_tweet like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls

	drop if created_at == date_birth_tweet // drop birth tweet itself
save "$sentiment/output/tweetNLP/NLP_topics_Karthik.dta", replace

	* drop birth month
	drop if abs(days_from_birth) <= 14
save "$sentiment/output/tweetNLP/NLP_topics_Karthik_noBM.dta", replace



* -------------- MERGING (karthik's and mine to get single topic and probabilities) ------------ *
* my topics code, not karthiks
use "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN.dta", clear
	merge 1:1 tweet_id using "$sentiment/output/sentiment_scoresFULL_clean.dta"
	keep if _merge == 3
	drop _merge
save "$sentiment/output/topic_sentiment_merge.dta", replace

* with karthik's data
use "$sentiment/output/tweetNLP/NLP_topics_Karthik.dta", clear
	merge 1:1 tweet_id using "$sentiment/output/sentiment_scoresFULL_clean.dta"
	keep if _merge == 3
	drop _merge
	
	merge 1:1 tweet_id using "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN.dta", keepusing(topic) 
	drop _merge
	
save "$sentiment/output/topic_sentiment_FULL_Karthik.dta", replace // Main one without dropping >95th percentile


* -------------- TRIM >95th percentile ------------ *
gen counter = 1
egen total_og_sample_tweets = sum(counter), by(unique_id)	

sum total_og_sample_tweets, d
local p95 = r(p95)
drop if total_og_sample_tweets > `p95'
drop counter

save "$sentiment/output/topic_sentiment_analysis.dta", replace // main one we use for sentiment and topics analysis
