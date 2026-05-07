* Author: Hannah Lybbert
* Created: 05/07/2026
* Purpose: Organzie the VOLUME final cleaning steps from "final_cleaning_3_datasets.do"


use "$intermediate/tweet_volume_by_user_full_sample.dta", clear

*=============================================================================
* Pre Manual Cleaning - 1 var with no orig_qt_count
*=============================================================================
replace author_id = "312469045" if unique_id == "312469045_2017-09-20T21:33:40.000Z"
replace user_created_at = "2011-06-07T05:16:53.000Z" if unique_id == "312469045_2017-09-20T21:33:40.000Z"
replace date_birth = "2017-09-20T21:33:40.000Z" if unique_id == "312469045_2017-09-20T21:33:40.000Z"

*=============================================================================
* SECTION 1: Variable Types
*=============================================================================

*--- Integers ---
	foreach var in orig_qt_count rt_reply_count {
		destring `var', replace
	}

*--- Dates ---
	foreach var in date user_created_at date_birth begin_date end_date {
		gen `var'_stata = date(substr(`var',1,10), "YMD")
		format `var'_stata %td
		count if missing(`var')
		drop `var'
		count if missing(`var'_stata)
		rename `var'_stata `var'
	} // 1093 missing values generated here are from the same observation above
	
*--- Time stamp --- (truncate from unique_id)
	replace unique_id = regexs(1) if regexm(unique_id, "^(.*)T")
	
*--- Drop obs with null fields ---
	drop if missing(begin_date)
	drop if unique_id == "1038449551_2017-10-01"
	
*=============================================================================
* SECTION 2: Generate Variables
*=============================================================================

*--- Tweet habits per day ---
	gen total_tweets = orig_qt_count + rt_reply_count
	gen no_rt_reply = missing(rt_reply_count)	
	
*--- Days/Weeks/Months from birth ---
	gen days_from_birth = date - date_birth
	gen week_from_birth = floor(days_from_birth / 7)
	gen months_from_birth = floor(days_from_birth / 30)
	
*--- Account age ---
	gen account_24_mo_old =  (abs(date_birth - user_created_at) >= 720)
	gen account_30_mo_old =  (abs(date_birth - user_created_at) >= 900)

*--- Post (if day is pre/post birth) ---
	gen post_birth = (date_birth < date)
	replace post_birth = 1 if date_birth == date
	
*--- Merge in female identifier ---
	merge m:1 unique_id using "$intermediate/user_info_full_sample_preclean.dta", keepusing(female date_birth_tweet) //30 not matched, check out
	drop _merge


*=============================================================================
* SECTION 3: Full Window available 
*=============================================================================

*--- Full 3 years indicator ---
	egen min_days = min(days_from_birth), by(unique_id)
	gen full_3years = (abs(min_days) >= 540) // account at least 540 days pre birth (~18 months)
	egen max_days = max(days_from_birth), by(unique_id)
	
*--- Keep only 18 months of data [-18, 17]
	drop if abs(days_from_birth) > 547 // Keep only 18 months of data for each acct
	drop if months_from_birth == -19 | months_from_birth == 18 // drop if month is larger than the panel size

	
*=============================================================================
* SECTION 4: Birth Announcement Cleaning
*=============================================================================

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
* SECTION 5: Monthly and Weekly Total Sample Vars 
*=============================================================================

*--- Total sample tweets --- 
		*(how much a user tweets in each category across the full sample)	
	egen total_month_tweets = sum(total_tweets), by(unique_id months_from_birth)
	replace total_month_tweets = . if missing(total_tweets)	
	egen total_sample_tweets = sum(total_tweets), by(unique_id)
	replace total_sample_tweets = . if missing(total_tweets)
	
*--- Monthly Orig_QT ---  
	egen og_qt_month_tweets = sum(orig_qt_count), by(unique_id months_from_birth)
	replace og_qt_month_tweets = . if missing(orig_qt_count)	
	egen og_qt_sample_tweets = sum(orig_qt_count), by(unique_id)
	replace og_qt_sample_tweets = . if missing(orig_qt_count)

*--- Monthly RT/RP ---
	egen rt_rp_month_tweets = sum(rt_reply_count), by(unique_id months_from_birth)
	replace rt_rp_month_tweets = . if missing(rt_reply_count)
	egen rt_rp_sample_tweets = sum(rt_reply_count), by(unique_id)
	replace rt_rp_sample_tweets = . if missing(rt_reply_count)
	

*=============================================================================
* SECTION 6: Organize Variables
*=============================================================================

*--- Drop unneeded vars ---*
drop min_days max_days	

*--- Order ---
order unique_id author_id female user_created_at date_birth date_birth_tweet date orig_qt_count rt_reply_count total_tweets total_month_tweets total_sample_tweets begin_date end_date 

*--- Sort ---
sort author_id date

*=============================================================================
* SECTION 7: Label Variables 
*=============================================================================\

label variable unique_id "Unique identifier for each author and birth"
label variable author_id "Unique identifer for each Twitter user"
label variable date "Running date variable, 18 months pre-birth until 18-months post-birth"
label variable orig_qt_count "# of original and quote tweets by the user that day"
label variable rt_reply_count "# of retweets and replies by the user that day"
label variable user_created_at "Date of account creation"
label variable date_birth "Child birth date"
label variable begin_date "Date 18 months pre-birth"
label variable end_date "Date 18 months post-birth"
label variable days_from_birth "Days since birth: (-) pre-birth, (+) post-birth"
label variable months_from_birth "Months since birth: (-) pre-birth, (+) post-birth (floor(days/30))"
label variable week_from_birth "Weeks since birth: (-) pre-birth, (+) post-birth"
label variable total_tweets "Original + Quote + Retweet + Reply on that day"
label variable no_rt_reply "If we have no retweet/reply volume for this account"
label variable full_3years "If account was created at least 18 months pre birth"
// label variable acct_tweeted_postBA "Did this account tweet at all post birth announcement?"
// label variable birth_tweet "Is this the birth announcement tweet? (0/1)"
label variable post_birth "Is this date after birth date? (birth date = 1)"
label variable total_month_tweets "Total tweets from that month from that author"
label variable total_sample_tweets "Total tweets from that account during the sample"
label variable account_24_mo_old "Account created at least 24 months pre-birth"
label variable account_30_mo_old "Account created at least 30 months pre-birth"
label variable og_qt_month_tweets "Total original/quote tweets from that month and author"
label variable rt_rp_month_tweets "Total retweets/replies from that month and author"
label variable og_qt_sample_tweets "Total sample original/quote tweets from the author"
label variable rt_rp_sample_tweets "Total sample retweets/replies from the author"


*=============================================================================
* SECTION 8: Save Data
*=============================================================================

save "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", replace
save "$final/tweet_volume_by_user_full_sample_CLEAN.dta", replace


