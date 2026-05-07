* Author: Hannah Lybbert
* Created: 05/07/2026
* Purpose: Organzie the USER final cleaning steps from "final_cleaning_3_datasets.do"
		* Should be run first out of the final 3 cleaning scripts 

use "$intermediate/user_info_full_sample.dta", clear

*=============================================================================
* SECTION 1: Variable Types
*=============================================================================

*--- Integers ---
	foreach var in child_number days_from following_count followers_count lifetime_posts has_picture like_count retweet_count reply_count quote_count orig_qt_count rt_reply_count {
		destring `var', replace
	}
	
*--- Verified --- (change from True/False to 1/0)
	gen byte verified_num = (verified == "True")
	drop verified
	rename verified_num verified
	
*--- Demographic ---
replace race = "-99.0" if missing(race)
* Convert to numeric
	foreach var in female race occupation {
		destring `var', replace
	}
	
*--- Dates ---
	foreach var in user_created_at date_birth_tweet date_birth begin_date end_date {
		gen `var'_stata = date(substr(`var',1,10), "YMD") // remove time stamp
		format `var'_stata %td 
		count if missing(`var')
		drop `var'
		count if missing(`var'_stata)
		rename `var'_stata `var'
	}
	
*--- Time stamp --- (truncate from unique_id)
	replace unique_id = regexs(1) if regexm(unique_id, "^(.*)T")
	
*--- Child Number ---
	replace child_number = -99 if child_number == 99
	// What else do I need to do here? (more cleaning if Devin wants)
	

*=============================================================================
* SECTION 2: Duplicates
*=============================================================================

* Duplicate accounts & null fields (numbers)
	duplicates report unique_id tweet_id
	duplicates tag author_id, gen(dup_tag)
	drop if dup_tag==1 & abs(days_from) > 8 // taking care of duplicate announces
	drop dup_tag
	drop if missing(begin_date)	

*=============================================================================
* SECTION 5: Birth Announcement Cleaning
*=============================================================================

*--- Drop second birth --- (one birth birth author)
	duplicates tag author_id, gen(dup_tag)
	sort author_id date_birth
		bysort author_id: gen dup_order = _n
		drop if dup_order == 2
		drop dup*

*--- Drop BA more than two weeks away from birth --- 
gen late_announcement = abs(date_birth - date_birth_tweet) > 14
drop if late_announcement ==1
drop late_announcement

*--- CHANGE DIRECTION OF DAYS_FROM ---
	* will now be negative values are pre birth and positive values are post birth
gen days_from2 = date_birth_tweet - date_birth
drop days_from
rename days_from2 days_from


*=============================================================================
* SECTION 6: Label Variables 
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
// label variable birth_tweet "Birth announcement tweet id"
// label variable acct_tweeted_postBA "Did this account tweet at all post birth announcement?"
//	
	
*=============================================================================
* SECTION 7: Order Variables 
*=============================================================================

order unique_id author_id username name description profile_image_url user_created_at female race occupation child_number date_birth_tweet days_from date_birth following_count followers_count lifetime_posts verified verified_type tweet_id text tweet_url has_picture media_url like_count retweet_count reply_count quote_count begin_date end_date orig_qt_count rt_reply_count

*=============================================================================
* SECTION 8: Save Files
*=============================================================================
save "$intermediate/user_info_full_sample_preclean.dta", replace

