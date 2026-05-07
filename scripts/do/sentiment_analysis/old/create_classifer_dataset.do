******** CREATING DATASETS ********

** TWO COLUMN DATASET (pre/post)

use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
merge m:1 unique_id using "$final/user_analysis_sample.dta", keepusing(date_birth)
drop _merge

* Binary indicator pre/post birth
	gen post = date_birth < created_at

* Build two column dataset (pre/post indicator and text)
keep text post

save "$sentiment/tweet_text_prepost.dta", replace
export delimited using "$sentiment/tweet_text_prepost.csv", replace quote delimiter(",") nolabel


***********************************************************

* BALANCED for FINAL CLASSIFICATION

use "$sentiment/tweet_text_prepost.dta", clear
	tab post
	
	preserve 
		keep if post == 1 & !missing(text)
		tempfile balanced_post
		save `balanced_post'
	restore
	
	preserve
		keep if post == 0 & !missing(text)
		gen rand = runiform()
		sort rand
		keep in 1/705359
		drop rand
		
		append using `balanced_post'
		
		save "$sentiment/tweet_text_prepost_balanced_FULL.dta", replace
		export delimited using "$sentiment/tweet_text_prepost_balanced_FULL.csv", replace quote delimiter(",") nolabel

	restore


***********************************************************
** BALANCED SAMPLE (10,000 tweets) for sample analysis
use "$sentiment/tweet_text_prepost.dta", clear

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

* Create 1000 tweet sample for starter analysis (NOT balanced)
	gen rand = runiform()

	sort rand

	keep in 1/1000

	drop rand

save "$sentiment/tweet_text_prepost_SAMPLE.dta", replace
export delimited using "$sentiment/tweet_text_prepost_SAMPLE.csv", replace quote delimiter(",") nolabel



	
***********************************************************
***** TWEET TEXT ONLY *****
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
	
	order unique_id author_id tweet_id created_at text

	* keep only tweet_id and tweet text
// 	keep tweet_id text

save "$sentiment/tweet_text.dta", replace
export delimited using "$sentiment/tweet_text_MFT.csv", replace quote delimiter(",") nolabel


***** 10,000 SAMPLE *****
use "$sentiment/tweet_text.dta", clear

	gen rand = runiform()
	sort rand
	keep in 1/10000
	drop rand

save "$sentiment/tweet_text_10kSAMPLE.dta", replace
export delimited using "$sentiment/tweet_text_10kSAMPLE.csv", replace quote delimiter(",") nolabel






