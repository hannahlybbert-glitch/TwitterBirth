* Author: Hannah Lybbert
* Created: 05/07/2026
* Purpose: Only adding in rt/reply volume flag, post BA flag, and analysis sample restriction based on the cleaning done in the VOLUME and TEXT scripts. 

use "$intermediate/user_info_full_sample_preclean.dta", clear

*=============================================================================
* SECTION 1: Volume flags
*=============================================================================

*--- Rt/Reply Volume data --- (Which accounts have rt/reply volume data)
tempfile useralmostclean
save `useralmostclean'
* RUN VOLUME SECTION (below) FIRST to get clean dataset with needed variables!!
use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	collapse (mean) no_rt_reply full_3years, by(unique_id)
	merge 1:1 unique_id using `useralmostclean', force	
	drop _merge
	
tempfile useronemoremerge
save `useronemoremerge'

*--- Acct tweeted post BA ---
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
	collapse (max) acct_tweeted_postBA, by(unique_id)
	merge 1:1 unique_id using `useronemoremerge'
	drop _merge
	
	
*=============================================================================
* SECTION 2: Keep only ANALYSIS SAMPLE
*=============================================================================

*--- Add back in unique ID time stamp ---
tempfile current_data
save `current_data'

use "$intermediate/user_info_full_sample.dta", clear
	keep unique_id
	gen uid_trunc = regexs(1) if regexm(unique_id, "^(.*)T")
	rename unique_id unique_id_ts
	duplicates drop uid_trunc, force
	tempfile orig_ids
	save `orig_ids'

use `current_data', clear
rename unique_id uid_trunc
merge 1:1 uid_trunc using `orig_ids', keepusing(unique_id_ts) keep(master match) nogen
replace uid_trunc = unique_id_ts if !missing(unique_id_ts)
rename uid_trunc unique_id
drop unique_id_ts


*=============================================================================
* SECTION 3: Keep only ANALYSIS SAMPLE
*=============================================================================

*--- Keep only Analysis Sample Authors (6969) ---


*=============================================================================
* SECTION 4: Label Variables 
*=============================================================================

label variable unique_id "Unique identifier for each author and birth"
label variable author_id "Unique identifer for each Twitter user"
label variable username "Twitter username"
label variable name "Name attached to Twitter account"
label variable description "Twitter account bio"
label variable profile_image_url "url to account profile picture"
label variable user_created_at "Date of account creation"
label variable female "1- female, 0- male"
label variable race "1- black, 2- white, 3- asian, 4- hispanic, 5- other, -99- null"
label variable occupation "1-educ, 2-health, 3-tech, 4-business, 5-govt, 6-arts, 7-service, 8-student, 9-other" // ChatGPT classified occupation"
label variable child_number "Child number _ being born"
label variable date_birth_tweet "Date of the tweet announcing the birth"
label variable days_from "Days separating birth tweet and actual birth of child (- pre, + post)"
label variable date_birth "Child birth date"
label variable following_count "How many accounts does this person follow?"
label variable followers_count "How many accounts are following this person?"
label variable lifetime_posts "Total number of tweets from this account since the user was created" 
label variable verified "Is this Twitter account verified?"
label variable verified_type "Type of Twitter verification"
label variable tweet_id "Unique identifer for each tweet"
label variable text "Content of the tweet"
label variable tweet_url "Twitter URL of tweet"
label variable has_picture "1- Tweet contains a picture, 0- no picture"
label variable media_url "Link to picture on tweet (if applicable)"
label variable like_count "# of likes on tweet"
label variable retweet_count "# of retweets on tweet"
label variable reply_count "# of replies on tweet"
label variable quote_count "# of quote tweets on tweet"
label variable begin_date "First day of data scraped from this account (18mo pre-birth)"
label variable end_date "Last day of data scraped from this account (18mo post-birth)"
label variable orig_qt_count "Total original + quote tweets (18mo pre/post birth)"
label variable rt_reply_count "Total retweet + replies (18mo pre/post birth)"
label variable no_rt_reply "If we have no retweet/reply volume for this account"
label variable full_3years "If account was created at least 18 months pre birth"
// label variable birth_tweet "Birth announcement tweet id"
// label variable acct_tweeted_postBA "Did this account tweet at all post birth announcement?"
	
	
*=============================================================================
* SECTION 5: Order Variables 
*=============================================================================

order unique_id author_id username name description profile_image_url user_created_at female race occupation child_number date_birth_tweet days_from date_birth following_count followers_count lifetime_posts verified verified_type tweet_id text tweet_url has_picture media_url like_count retweet_count reply_count quote_count begin_date end_date orig_qt_count rt_reply_count full_3years no_rt_reply

*=============================================================================
* SECTION 6: Save Files
*=============================================================================
save "$cleaned/user_info_full_sample_CLEAN.dta", replace
save "$final/user_info_full_sample_CLEAN.dta", replace

