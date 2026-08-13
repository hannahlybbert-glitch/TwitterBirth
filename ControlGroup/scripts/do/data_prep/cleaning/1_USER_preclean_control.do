* Author: Hannah Lybbert
* Created: 08/11/2026
* Purpose: Clean the data from the Control group API pull

use "$control_user/test/user_info.dta", clear


*=============================================================================
* SECTION 1: Variable Types
*=============================================================================

*--- Integers ---
	foreach var in following_count followers_count tweet_count like_count account_age_weeks avg_weekly_tweets days_from {
		destring `var', replace
	}

*--- Strings ---
	foreach var in author_id {
		tostring `var', replace
	}

*--- Dates ---
	foreach var in seed_tweet_date account_created_at date_birth_placebo {
		gen `var'_stata = date(substr(`var',1,10), "YMD") // remove time stamp
		format `var'_stata %td 
		count if missing(`var')
		drop `var'
		count if missing(`var'_stata)
		rename `var'_stata `var'
	}
	
*=============================================================================
* SECTION 2: Duplicates
*=============================================================================
		* Note: we deal with duplicates after the user pull, but just a double check here.
* Duplicate accounts & null fields (numbers)
	duplicates report author_id tweet_id
	duplicates tag author_id, gen(dup_tag)
	drop if dup_tag == 1
	drop dup_tag
	

*=============================================================================
* SECTION 3: Variable Generation
*=============================================================================

* --- Generate treatment flag (treated == 0 for all these authors)
gen treated = 0


*=============================================================================
* SECTION 4: Rename, remove, and Label Variables 
*=============================================================================

*--- Remove variables
drop not_found filter_a_pass filter_b_pass week_start


*--- Rename vars
rename tweet_count lifetime_posts
rename account_created_at user_created_at
rename seed_tweet_date date_seed_tweet

*--- Label Vars
label variable author_id "Unique identifer for each Twitter user"
label variable username "Twitter username"
// label variable name "Name attached to Twitter account" //not in test group but will be in full
label variable description "Twitter account bio"
label variable user_created_at "Date of account creation"
label variable date_seed_tweet "Date of the anniversary tweet"
label variable days_from "Days separating seed tweet and placebo birth tweet (- pre, + post)"
label variable date_birth_placebo "Placebo birth date based on treatment distribution of days_from"
label variable following_count "How many accounts does this person follow?"
label variable followers_count "How many accounts are following this person?"
label variable lifetime_posts "Total number of tweets from this account since the user was created" 
label variable verified "Is this Twitter account verified?"
label variable tweet_id "Unique identifer for each tweet"
label variable text "Content of the tweet"
label variable like_count "# of likes on tweet"
label variable treated "Is this author part of the treated group?"

*=============================================================================
* SECTION 7: Order Variables 
*=============================================================================

// order author_id username name description user_created_at date_seed_tweet days_from date_birth_placebo following_count followers_count lifetime_posts verified tweet_id text like_count 

order author_id username description user_created_at date_seed_tweet date_birth_placebo days_from date_birth_placebo following_count followers_count lifetime_posts verified tweet_id text like_count 

*=============================================================================
* SECTION 8: Save Files
*=============================================================================
save "$control_cleaned/test/user_info_control_preclean.dta", replace


* TO do
	* create variables we need
	* do volume clean and dtermine the final set of authors
	* create a new user clean do file and reduce down to only the authors we keep and add in the sample tweet metric and anything else we need.