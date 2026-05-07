* Author: Hannah Lybbert
* Created: 05/07/2026
* Purpose: Organzie the TWEET TEXT final cleaning steps from "final_cleaning_3_datasets.do"


use "$intermediate/tweets_by_user_full_sample.dta", clear

*=============================================================================
* SECTION 1: Variable Types
*=============================================================================

*--- Integers ---
	foreach var in like_count retweet_count reply_count quote_count {
		destring `var', replace
	}

*--- Dates ---
	foreach var in created_at {
		gen `var'_stata = date(substr(`var',1,10), "YMD")
		format `var'_stata %td
		count if missing(`var')
		drop `var'
		count if missing(`var'_stata)
		rename `var'_stata `var'
	}
	
*--- Time stamp --- (truncate from unique_id)
	replace unique_id = regexs(1) if regexm(unique_id, "^(.*)T")


*=============================================================================
* SECTION 2: Duplicates
*=============================================================================

	duplicates report unique_id tweet_id
	bysort unique_id tweet_id: gen dup_order = _n
	drop if dup_order == 2
	drop dup_order
	
	* A couple more duplicates
	duplicates tag tweet_id, gen(dup_tag)
	bysort tweet_id (tweet_id): gen dup_order = _n
	drop if dup_tag == 1 & dup_order == 2
	drop dup_tag dup_order
	

*=============================================================================
* SECTION 3: Double Check Numbers
*=============================================================================

*--- BA tweets in tweet text data ---
	merge m:1 unique_id using "$intermediate/user_info_full_sample_preclean.dta", force
*--- Remove tweets with no account information ---
	drop if _merge == 1
*--- All BA have full info---
	replace created_at = date_birth_tweet if _merge == 2
	replace tweet_type = "original" if _merge == 2
*--- Replace birth_tweet = "0" if birth_tweet_id != tweet_id ---
	drop _merge


*=============================================================================
* SECTION 4: Variable Generation
*=============================================================================

*--- Post_birth (binary, pre/post birth) ---
	gen post_birth = (date_birth < created_at)
	replace post_birth = 1 if date_birth == created_at
**# Might need to change something here (below) to accomodate for some people posting more than once on the date of the BA...
	gen tweet_postBA = (date_birth_tweet < created_at)
	replace tweet_postBA = 1 if date_birth_tweet == created_at //THIS ONE
	egen acct_tweeted_postBA = max(tweet_postBA), by(unique_id)

	
*--- Days/Weeks/Months from birth ---
	gen days_from_birth = created_at - date_birth
	gen week_from_birth = floor(days_from_birth / 7)
	gen months_from_birth = floor(days_from_birth / 30)


*=============================================================================
* SECTION 5: Drop unneeded obs
*=============================================================================

*--- Outside of 18 months pre/post ---
	drop if abs(days_from_birth) > 547 // Keep only 18 months of data for each acct
	drop if months_from_birth == -19 | months_from_birth == 18 // drop if month is larger than the panel size

*--- Check duplicates one more time ---
	duplicates tag tweet_id, gen(dup_tag)
	bysort tweet_id (tweet_id): drop if dup_tag == 1 & _n == 2
	drop dup_tag
	
// 	* Check duplicates one more time
// 	duplicates tag text, gen(dup_tag)
// 	bysort text (text): drop if dup_tag == 1 & _n == 2
// 	drop dup_tag

*--- Drop BA more than two weeks away from birth --- 
gen late_announcement = abs(date_birth - date_birth_tweet) > 14
drop if late_announcement == 1
drop late_announcement

*--- Drop second birth --- (one birth birth author)
	bysort author_id: egen earliest_birth = min(date_birth)
	gen has_multiple_births = (date_birth != earliest_birth)
	drop if has_multiple_births == 1
	drop has_multiple_births
	drop earliest_birth


*=============================================================================
* SECTION 5b: Merge VOLUME flags
*=============================================================================

*--- Pull full_3years and no_rt_reply from VOLUME_CLEAN ---
	tempfile vol_flags
	preserve
		use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
		collapse (mean) full_3years no_rt_reply, by(unique_id)
		save `vol_flags'
	restore
	merge m:1 unique_id using `vol_flags', keepusing(full_3years no_rt_reply) nogen


*=============================================================================
* SECTION 6: Organize Variables
*=============================================================================

*--- Keep only necessary vars ---
keep unique_id author_id user_created_at date_birth female date_birth_tweet days_from tweet_id text created_at days_from_birth week_from_birth months_from_birth like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls full_3years no_rt_reply post_birth  tweet_postBA acct_tweeted_postBA lifetime_posts

*--- Order ---
order unique_id author_id user_created_at date_birth female date_birth_tweet days_from tweet_id text created_at days_from_birth week_from_birth months_from_birth like_count retweet_count reply_count quote_count lifetime_posts tweet_type tweet_url embedded_urls media_urls full_3years no_rt_reply post_birth tweet_postBA acct_tweeted_postBA


*=============================================================================
* SECTION 8: Label Variables 
*=============================================================================

label variable unique_id "Unique identifier for each Twitter user and their first birth"
label variable author_id "Unique identifer for each Twitter user"
label variable tweet_id "Unique identifer for each tweet"
label variable created_at "Date of tweet post"
label variable text "Text of the tweet"
label variable like_count "# of likes on tweet"
label variable retweet_count "# of retweets on tweet"
label variable reply_count "# of replies on tweet"
label variable quote_count "# of quote tweets on tweet"
label variable tweet_url "Twitter URL of tweet"
label variable media_url "URL link to picture or video on tweet (if applicable)"
label variable tweet_type "Type of tweet (original vs quote)"
label variable embedded_urls "URL linked in tweet (if applicable) or self-link for tweets including photo/video"
label variable post_birth "If tweet was post birth date (birth date = 1)"
label variable days_from_birth "Days since birth"
label variable week_from_birth "Weeks since birth"
label variable months_from_birth "Months since birth"
label variable acct_tweeted_postBA "Did this account tweet after the birth announcement?"
label variable tweet_postBA "If tweet was post birth announcement (birth tweet = 1)"
// label variable birth_tweet "Is this the birth announcement tweet itself? (0/1)"


*=============================================================================
* SECTION 9: Save Data
*=============================================================================
save "$cleaned/tweets_by_user_full_sample_CLEAN.dta", replace
save "$final/tweets_by_user_full_sample_CLEAN.dta", replace