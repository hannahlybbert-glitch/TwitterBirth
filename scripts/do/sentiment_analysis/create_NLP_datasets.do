****** Getting Samples ready for sentiment/classification analysis ******

* ----------------------------------------------------------------------------------------
* --------------------------- TEXT CLEANING FOR NLP ANALYSIS --------------------------------
* ----------------------------------------------------------------------------------------

** Full tweet text data prep **
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
	
	keep if full_3years == 1 & acct_tweeted_postBA == 1
	keep if abs(months_from_birth) <= 18

	* Handle links in tweets (to avoid polluting textual analysis)
	gen link_intext = ustrregexs(0) if ustrregexm(text, "https?://[^ ]+")
// 		preserve
// 			keep author_id tweet_id text link_intext tweet_url media_urls embedded_urls
// 			save "$sentiment/link_intext.dta", replace
// 		restore
	gen text_nolink = ustrregexra(text, "https?://[^ ]+", "")
	drop if missing(text_nolink)
	rename text text_with_link
	rename text_nolink text
	
	* Check duplicates one more time
	duplicates tag text, gen(dup_tag)
	bysort text (text): drop if dup_tag == 1 & _n == 2
	drop dup_tag
	
	* solution?
	gen contains_follow = regexm(lower(text), "follower|followed|unfollowed")
	browse author_id created_at text dup_tag if dup_tag >0 & contains_follow == 1
	count if  dup_tag >0 & contains_follow == 1
	
	* Preserve tweet_id as a string
	gen tweet_id_quotes = "'" + tweet_id + "'"
	drop tweet_id
	rename tweet_id_quotes tweet_id
	
	* Preserve author_id as a string
	gen author_id_quotes = "'" + author_id + "'"
	drop author_id
	rename author_id_quotes author_id	
	
	* Preserve dates
	format created_at date_birth date_birth_tweet %12.0g
	
	* Remove Birthtweet
	drop if created_at == date_birth_tweet
		
	order unique_id author_id date_birth female date_birth_tweet tweet_id text created_at days_from_birth week_from_birth months_from_birth like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls full_3years no_rt_reply post acct_tweeted_postBA
	
save "$sentiment/tweet_text_FULL.dta", replace
export delimited using "$sentiment/tweet_text_FULL.csv", replace quote delimiter(",") nolabel

	* remove +/- 2 weeks around birth
	drop if abs(days_from_birth) <= 14 // 
	
save "$sentiment/tweet_text_FULL_1mo_drop.dta", replace
export delimited using "$sentiment/tweet_text_FULL_1mo_drop.csv", replace quote delimiter(",") nolabel
	
***** 10,000 SAMPLE *****
use "$sentiment/tweet_text_FULL.dta", clear

	gen rand = runiform()
	sort rand
	keep in 1/10000
	drop rand

// save "$sentiment/tweet_text_10kSAMPLE.dta", replace
export delimited using "$sentiment/tweet_text_10kSAMPLE.csv", replace quote delimiter(",") nolabel

***** No Birth Month - 10,000 SAMPLE *****
use "$sentiment/tweet_text_FULL_1mo_drop.dta", clear

	gen rand = runiform()
	sort rand
	keep in 1/10000
	drop rand

// save "$sentiment/tweet_text_10kSAMPLE_1mo_drop.dta", replace
export delimited using "$sentiment/tweet_text_10kSAMPLE_1mo_drop.csv", replace quote delimiter(",") nolabel


* -----------------------------------------------------------------
* ---------------- TWO COLUMN DATASET (pre/post) ------------------
* -----------------------------------------------------------------

use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear

	* drop birth announcement itself
	drop if created_at == date_birth_tweet
	keep if abs(months_from_birth) <= 18

* Build two column dataset (pre/post indicator and text)
preserve
	keep text post_birth
	order post_birth text

save "$sentiment/tweet_text_prepost_FULL.dta", replace
// export delimited using "$sentiment/tweet_text_prepost_FULL.csv", replace quote delimiter(",") nolabel
restore

	* remove +/- 2 weeks around birth
	drop if abs(days_from_birth) <= 14
	keep text post_birth
	order post_birth text

save "$sentiment/tweet_text_prepost_1mo_drop.dta", replace


****** BALANCED for CLASSIFICATION ******

use "$sentiment/tweet_text_prepost_FULL.dta", clear
	drop if missing(text)
	tab post
	count if post == 1
	local freq_post1 = r(N)
	
	preserve 
		keep if post == 1
		tempfile balanced_post
		save `balanced_post'
	restore
	
	preserve
		keep if post == 0
		gen rand = runiform()
		sort rand
		keep in 1/`freq_post1'
		drop rand
		
		append using `balanced_post'
		
		save "$sentiment/tweet_text_prepost_balanced_FULL.dta", replace
		export delimited using "$sentiment/tweet_text_prepost_balanced_FULL.csv", replace quote delimiter(",") nolabel

	restore
	
***********************************************************
** BALANCED SAMPLE (10,000 tweets) for sample analysis
use "$sentiment/tweet_text_prepost_FULL.dta", clear

preserve
	keep if post == 0
	gen rand = runiform()
	sort rand
	keep in 1/5000
	drop rand
	
	tempfile pre_text
	save `pre_text'
restore

preserve
	keep if post == 1
	gen rand = runiform()
	sort rand
	keep in 1/5000
	drop rand
	
	append using `pre_text'
	
	save "$sentiment/tweet_text_prepost_balanced_SAMPLE.dta", replace
	export delimited using "$sentiment/tweet_text_prepost_balanced_SAMPLE.csv", replace quote delimiter(",") nolabel
	
restore
	
***********************************************************
****** NO BIRTH MONTH BALANCED ******

use "$sentiment/tweet_text_prepost_1mo_drop.dta", clear
	
	drop if missing(text)
	tab post
	count if post == 1
	local freq_post1 = r(N)
	
	preserve 
		keep if post == 1
		tempfile balanced_post
		save `balanced_post'
	restore
	
	preserve
		keep if post == 0
		gen rand = runiform()
		sort rand
		keep in 1/`freq_post1'
		drop rand
		
		append using `balanced_post'
		
		save "$sentiment/tweet_text_prepost_balanced_1mo_drop.dta", replace
		export delimited using "$sentiment/tweet_text_prepost_balanced_1mo_drop.csv", replace quote delimiter(",") nolabel

	restore

** SAMPLE (10,000 tweets) NO BIRTH MONTH
use "$sentiment/tweet_text_prepost_balanced_1mo_drop.dta", clear

preserve
	keep if post == 0
	gen rand = runiform()
	sort rand
	keep in 1/5000
	drop rand
	tempfile pre_text
	save `pre_text'
restore
preserve
	keep if post == 1
	gen rand = runiform()
	sort rand
	keep in 1/5000
	drop rand
	append using `pre_text'
// 	save "$sentiment/tweet_text_prepost_balanced_SAMPLE_1mo_drop.dta", replace
	export delimited using "$sentiment/tweet_text_prepost_balanced_SAMPLE_1mo_drop.csv", replace quote delimiter(",") nolabel
restore


* -----------------------------------------------------------------------------------
* ---------------- PREP ONE-DOC CLASSIFICATION DATASET (pre/post) -------------------
* ------------------------------------------------------------------------------------
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear

	* Cleaning
	keep if acct_tweeted_postBA == 1 & full_3years == 1 // acct must tweet >1 time post BA
	drop if created_at == date_birth_tweet // drop BA itself
	
	sort author_id post_birth
// 	keep author_id post_birth text
// 	rename post_birth post

export delimited using "$sentiment/text_aid_prepost.csv", replace quote delimiter(",") nolabel


* -------------------------------------------------------------------
* ---------------- Build mini dataset for testing -------------------
* -------------------------------------------------------------------
use "$sentiment/tweet_text_FULL.dta", clear
	gen rand = runiform()
	sort rand
	keep in 1/10
	drop rand

save "$sentiment/tweet_text_mini_testing.dta", replace
export delimited using "$sentiment/tweet_text_mini_testing.csv", replace quote delimiter(",") nolabel

* -----------------------------------------------------------
* ---------------- Build Handcode dataset -------------------
* -----------------------------------------------------------
use "$sentiment/tweet_text_FULL.dta", clear
	gen rand = runiform()
	sort rand
	keep in 1/100
	drop rand
	
gen hand_topic = .
order unique_id author_id date_birth female date_birth_tweet tweet_id text hand_topic

// save "$sentiment/tweet_text_handcode.dta", replace
// export delimited using "$sentiment/tweet_text_handcode.csv", replace quote delimiter(",") nolabel



* ----------------------------------------------------------------------------
* ---------------------------- OLD NOTES -------------------------------------
* -----------------------------------------------------------------------------

// ******* REMOVE LINK FROM TEXT COLUMN *********
// use "$sentiment/tweet_text_prepost_FULL.dta", clear
//
// 	* Handle links in tweets (to avoid polluting textual analysis)
// 	gen text_nolink = ustrregexra(text, "https?://[^ ]+", "")
// 	drop if missing(text_nolink)
// 	drop text
// 	rename text_nolink text
//
// 	* Balanced dataset 
// 	tab post
// 	count if post == 1
// 	local freq_post1_nolink = r(N)
//	
// 	preserve 
// 		keep if post == 1 & !missing(text)
// 		tempfile balanced_post
// 		save `balanced_post'
// 	restore
//	
// 	preserve
// 		keep if post == 0 & !missing(text)
// 		gen rand = runiform()
// 		sort rand
// 		keep in 1/`freq_post1_nolink'
// 		drop rand
//		
// 		append using `balanced_post'
//		
// 		save "$sentiment/tweet_text_prepost_balanced_nolink_FULL.dta", replace
// 		export delimited using "$sentiment/tweet_text_prepost_balanced_nolink_FULL.csv", replace quote delimiter(",") nolabel
//
// 	restore
//
// *** BALANCED SAMPLE 10k ***	
// use "$sentiment/tweet_text_prepost_balanced_nolink_FULL.dta", clear
// 	preserve
// 		keep if post == 1
// 		gen rand = runiform()
// 		sort rand
// 		keep in 1/5000
// 		drop rand
// 		tempfile post_sample
// 		save `post_sample'
// 	restore
// 	preserve
// 		keep if post == 0
// 		gen rand = runiform()
// 		sort rand
// 		keep in 1/5000
// 		drop rand
// 		append using `post_sample'
// save "$sentiment/tweet_text_prepost_balanced_nolink_10k.dta", replace
// export delimited using "$sentiment/tweet_text_prepost_balanced_nolink_10k.csv", replace quote delimiter(",") nolabel
//	
// 	restore
// ***********************************************************
// ****** NO BIRTH MONTH, NO LINK, BALANCED  ******
//
// use "$sentiment/tweet_text_prepost_1mo_drop.dta", clear
//
// 	* Handle links in tweets (to avoid polluting textual analysis)
// 	gen text_nolink = ustrregexra(text, "https?://[^ ]+", "")
// 	drop if missing(text_nolink)
// 	drop text
// 	rename text_nolink text
//	
// 	drop if missing(text)
// 	tab post
// 	count if post == 1
// 	local freq_post1 = r(N)
//	
// 	preserve 
// 		keep if post == 1
// 		tempfile balanced_post
// 		save `balanced_post'
// 	restore
//	
// 	preserve
// 		keep if post == 0
// 		gen rand = runiform()
// 		sort rand
// 		keep in 1/`freq_post1'
// 		drop rand
// 		append using `balanced_post'
//		
// 		save "$sentiment/tweet_text_prepost_balanced_1mo_drop_nolink.dta", replace
// 		export delimited using "$sentiment/tweet_text_prepost_balanced_1mo_drop_nolink.csv", replace quote delimiter(",") nolabel
// 	restore
//
// ** SAMPLE (10,000 tweets) NO BIRTH MONTH
// use "$sentiment/tweet_text_prepost_balanced_1mo_drop_nolink.dta", clear
//
// preserve
// 	keep if post == 0
// 	gen rand = runiform()
// 	sort rand
// 	keep in 1/5000
// 	drop rand
// 	tempfile pre_text
// 	save `pre_text'
// restore
// preserve
// 	keep if post == 1
// 	gen rand = runiform()
// 	sort rand
// 	keep in 1/5000
// 	drop rand
// 	append using `pre_text'
// // 	save "$sentiment/tweet_text_prepost_balanced_SAMPLE_1mo_drop.dta", replace
// 	export delimited using "$sentiment/tweet_text_prepost_balanced_SAMPLE_1mo_drop_nolink.csv", replace quote delimiter(",") nolabel
// restore


****** OTHER NOTES ******
// * Create 1000 tweet sample for starter analysis (NOT balanced)
// 	gen rand = runiform()
//
// 	sort rand
//
// 	keep in 1/1000
//
// 	drop rand
//
// save "$sentiment/tweet_text_prepost_SAMPLE.dta", replace
// export delimited using "$sentiment/tweet_text_prepost_SAMPLE.csv", replace quote delimiter(",") nolabel
//
//
//
// gen has_word = ustrregexm(text, "rt")
// tab has_word
// browse if has_word ==1
// drop has_word


// gen has_word = ustrregexm(text, "https?://[^ ]+")
// tab has_word
// browse if has_word ==1
// drop has_word

// * other code for use soon:
// keep if tweet_postbirth == 1 & full_3years == 1
// save "$cleaned/tweets_by_user_for_TEXT_ANALYSIS.dta", replace


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