****************************** DATA CLEANING ******************************

** GOAL: produce three final datasets for analysis (labeled, clean, right var type, etc.)


********************************************************
***************** USER INFO DATA *****************

use "$cleaned/user_info_full_sample.dta", clear

*** Variable types ***
**Integers
	foreach var in child_number days_from following_count followers_count lifetime_posts has_picture like_count retweet_count reply_count quote_count orig_qt_count rt_reply_count {
		destring `var', replace
	}
	
** change "verified" variable from True/False to 1/0
	gen byte verified_num = (verified == "True")
	drop verified
	rename verified_num verified
	
** Demographic
replace race = "-99.0" if missing(race)
* Convert to numeric
	foreach var in female race occupation {
		destring `var', replace
	}
	
*** Dates ***
	foreach var in user_created_at date_birth_tweet date_birth begin_date end_date {
		gen `var'_stata = date(substr(`var',1,10), "YMD") // remove time stamp
		format `var'_stata %td 
		count if missing(`var')
		drop `var'
		count if missing(`var'_stata)
		rename `var'_stata `var'
	}
	

* Truncate time stamp from unique_id
	replace unique_id = regexs(1) if regexm(unique_id, "^(.*)T")
	
* Child num cleaning
	replace child_number = -99 if child_number == 99
	// What else do I need to do here? (more cleaning if Devin wants)
	
	
* Duplicate accounts & null fields (numbers)
	duplicates report unique_id tweet_id
	duplicates tag author_id, gen(dup_tag)
	drop if dup_tag==1 & abs(days_from) > 8 // taking care of duplicate announces
	drop dup_tag
	drop if missing(begin_date)	

	
** Which accounts have actual data? --> Trying to understand which we don't have retweet/reply volume for
tempfile useralmostclean
save `useralmostclean'
* RUN VOLUME SECTION (below) FIRST to get clean dataset with needed variables!!
use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	collapse (mean) no_rt_reply full_3years, by(unique_id)
	merge 1:1 unique_id using `useralmostclean', force	
	drop _merge
	
tempfile useronemoremerge
save `useronemoremerge'

use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
	collapse (max) acct_tweeted_postBA, by(unique_id)
	merge 1:1 unique_id using `useronemoremerge'
	drop _merge
	
	
* Drop the second birth (so we only have one birth per author per period)	
	duplicates tag author_id, gen(dup_tag)
	sort author_id date_birth
		bysort author_id: gen dup_order = _n
		drop if dup_order == 2
		drop dup*

* Drop if birth was announced more than two weeks away from birth
gen late_announcement = abs(date_birth - date_birth_tweet) > 14
drop if late_announcement ==1
drop late_announcement

** CHANGE DIRECTION OF DAYS_FROM**
	* will now be negative values are pre birth and positive values are post birth
gen days_from2 = date_birth_tweet - date_birth
drop days_from
rename days_from2 days_from


*** Label all variables ***
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
	
	
* Re order
order unique_id author_id username name description profile_image_url user_created_at female race occupation child_number date_birth_tweet days_from date_birth following_count followers_count lifetime_posts verified verified_type tweet_id text tweet_url has_picture media_url like_count retweet_count reply_count quote_count begin_date end_date orig_qt_count rt_reply_count full_3years no_rt_reply

** SAVE
save "$cleaned/user_info_full_sample_CLEAN.dta", replace
save "$final/user_info_full_sample_CLEAN.dta", replace


********************************************************
***************** VOLUME DATA *****************

use "$cleaned/tweet_volume_by_user_full_sample.dta", clear

** Manual cleaning - 1 var with no orig_qt_count
replace author_id = "312469045" if unique_id == "312469045_2017-09-20T21:33:40.000Z"
replace user_created_at = "2011-06-07T05:16:53.000Z" if unique_id == "312469045_2017-09-20T21:33:40.000Z"
replace date_birth = "2017-09-20T21:33:40.000Z" if unique_id == "312469045_2017-09-20T21:33:40.000Z"

*** Variable types ***
	* Integers
	foreach var in orig_qt_count rt_reply_count {
		destring `var', replace
	}

*** Dates ***
	foreach var in date user_created_at date_birth begin_date end_date {
		gen `var'_stata = date(substr(`var',1,10), "YMD")
		format `var'_stata %td
		count if missing(`var')
		drop `var'
		count if missing(`var'_stata)
		rename `var'_stata `var'
	} // 1093 missing values generated here are from the same observation above
	
*** Other cleaning ***
* Truncate time stamp from unique_id
	replace unique_id = regexs(1) if regexm(unique_id, "^(.*)T")
	
* Take care of observations with null fields
	drop if missing(begin_date)
	drop if unique_id == "1038449551_2017-10-01"
	
*** GENERATE VARIABLES ***
	** Sum tweet habits per day
	gen total_tweets = orig_qt_count + rt_reply_count
	gen no_rt_reply = missing(rt_reply_count)	
	
	* Days/Weeks/Months from birth Variables
	gen days_from_birth = date - date_birth
	gen week_from_birth = floor(days_from_birth / 7)
	gen months_from_birth = floor(days_from_birth / 30)
	

** Keep only accounts that we have data for 3 full years
	* Indicator for if the account was live at least 18 months pre birth
	egen min_days = min(days_from_birth), by(unique_id)
	gen full_3years = (abs(min_days) >= 540) // account at least 540 days pre birth (~18 months)
	egen max_days = max(days_from_birth), by(unique_id)
	
	* Indicators for age of the account
	gen account_24_mo_old =  (abs(date_birth - user_created_at) >= 720)
	gen account_30_mo_old =  (abs(date_birth - user_created_at) >= 900)
	
* Drop outside of 18 months of data (-18 to 17)
drop if abs(days_from_birth) > 547 // Keep only 18 months of data for each acct
drop if months_from_birth == -19 | months_from_birth == 18 // drop if month is larger than the panel size


* Total sample tweets for total tweets, orig/qt, and rt/reply	
	egen total_month_tweets = sum(total_tweets), by(unique_id months_from_birth)
	replace total_month_tweets = . if missing(total_tweets)	
	egen total_sample_tweets = sum(total_tweets), by(unique_id)
	replace total_sample_tweets = . if missing(total_tweets)
	
	* month original/qt 
	egen og_qt_month_tweets = sum(orig_qt_count), by(unique_id months_from_birth)
	replace og_qt_month_tweets = . if missing(orig_qt_count)	
	egen og_qt_sample_tweets = sum(orig_qt_count), by(unique_id)
	replace og_qt_sample_tweets = . if missing(orig_qt_count)
	
	egen rt_rp_month_tweets = sum(rt_reply_count), by(unique_id months_from_birth)
	replace rt_rp_month_tweets = . if missing(rt_reply_count)
	egen rt_rp_sample_tweets = sum(rt_reply_count), by(unique_id)
	replace rt_rp_sample_tweets = . if missing(rt_reply_count)
	
	* Create post variable for if day is pre/post birth
	gen post_birth = (date_birth < date)
	replace post_birth = 1 if date_birth == date
	

** Merge in female identifier:
merge m:1 unique_id using "$final/user_info_full_sample_CLEAN.dta", keepusing(female date_birth_tweet) //30 not matched, check out
drop _merge

	
* Drop if birth was announced more than two weeks away from birth
gen late_announcement = abs(date_birth - date_birth_tweet) > 14
drop if late_announcement == 1
drop late_announcement

* Drop the second birth (so we only have one birth per author per period)	
	bysort author_id: egen earliest_birth = min(date_birth)
	gen has_multiple_births = (date_birth != earliest_birth)
	drop if has_multiple_births == 1
	drop has_multiple_births
	drop earliest_birth
	
	
** DROP UNNEEDED VARS **
drop min_days max_days	

* Order all vars
order unique_id author_id female user_created_at date_birth date_birth_tweet date orig_qt_count rt_reply_count total_tweets total_month_tweets total_sample_tweets begin_date end_date 

* sort
sort author_id date

*** Label vars ***
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



save "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", replace
save "$final/tweet_volume_by_user_full_sample_CLEAN.dta", replace
// save "$cleaned/tweet_volume_by_user_full_sample_CLEAN_full.dta", replace // "full" means that it includes days beyond 18 months pre birth if they're available



********************************************************
***************** TWEET TEXT DATA *****************

use "$cleaned/tweets_by_user_full_sample.dta", clear

*** Variable types ***
	* Integers
	foreach var in like_count retweet_count reply_count quote_count {
		destring `var', replace
	}

*** Dates ***
	foreach var in created_at {
		gen `var'_stata = date(substr(`var',1,10), "YMD")
		format `var'_stata %td
		count if missing(`var')
		drop `var'
		count if missing(`var'_stata)
		rename `var'_stata `var'
	}
	
*** Other cleaning ***
	* truncate the unique_ID to eliminate time stamp (h)
	replace unique_id = regexs(1) if regexm(unique_id, "^(.*)T")

*** Duplicates ***
	duplicates report unique_id tweet_id
	bysort unique_id tweet_id: gen dup_order = _n
	drop if dup_order == 2
	drop dup_order
	
	* A couple more duplicates
	duplicates tag tweet_id, gen(dup_tag)
	bysort tweet_id (tweet_id): gen dup_order = _n
	drop if dup_tag == 1 & dup_order == 2
	drop dup_tag dup_order
	
* Double check numbers	
		// make sure we include all birth announcement tweets in tweet text data
	merge m:1 unique_id using "$cleaned/user_info_full_sample_CLEAN.dta", force
		// get rid of tweets for which we don't have account information (user info)
	drop if _merge == 1
		// make sure all BA have the full info
	replace created_at = date_birth_tweet if _merge == 2
	replace tweet_type = "original" if _merge == 2
// 	replace birth_tweet = "0" if birth_tweet_id != tweet_id
	drop _merge

* Generate needed Variables
	* Binary indicator pre/post birth
	gen post_birth = (date_birth < created_at)
	replace post_birth = 1 if date_birth == created_at
**# Might need to change something here (below) to accomodate for some people posting more than once on the date of the BA...
	gen tweet_postBA = (date_birth_tweet < created_at)
	replace tweet_postBA = 1 if date_birth_tweet == created_at //THIS ONE
// 	egen acct_tweeted_postBA = max(tweet_postBA), by(unique_id)

	
	* Days/Weeks/Months from birth Variables
	gen days_from_birth = created_at - date_birth
	gen week_from_birth = floor(days_from_birth / 7)
	gen months_from_birth = floor(days_from_birth / 30)

	
	* Drop outside of 18 months of data 
	drop if abs(days_from_birth) > 547 // Keep only 18 months of data for each acct
	drop if months_from_birth == -19 | months_from_birth == 18 // drop if month is larger than the panel size

	* Check duplicates one more time
	duplicates tag tweet_id, gen(dup_tag)
	bysort tweet_id (tweet_id): drop if dup_tag == 1 & _n == 2
	drop dup_tag
	
// 	* Check duplicates one more time
// 	duplicates tag text, gen(dup_tag)
// 	bysort text (text): drop if dup_tag == 1 & _n == 2
// 	drop dup_tag



* Drop if birth was announced more than two weeks away from birth
gen late_announcement = abs(date_birth - date_birth_tweet) > 14
drop if late_announcement == 1
drop late_announcement

* Drop the second birth (so we only have one birth per author per period)	
	bysort author_id: egen earliest_birth = min(date_birth)
	gen has_multiple_births = (date_birth != earliest_birth)
	drop if has_multiple_births == 1
	drop has_multiple_births
	drop earliest_birth


* Keep only necessary variables ...
keep unique_id author_id user_created_at date_birth female date_birth_tweet days_from tweet_id text created_at days_from_birth week_from_birth months_from_birth like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls full_3years no_rt_reply post_birth  tweet_postBA acct_tweeted_postBA lifetime_posts

* Correct order
order unique_id author_id user_created_at date_birth female date_birth_tweet days_from tweet_id text created_at days_from_birth week_from_birth months_from_birth like_count retweet_count reply_count quote_count lifetime_posts tweet_type tweet_url embedded_urls media_urls full_3years no_rt_reply post_birth tweet_postBA acct_tweeted_postBA

*** Label all variables ***
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


save "$cleaned/tweets_by_user_full_sample_CLEAN.dta", replace
save "$final/tweets_by_user_full_sample_CLEAN.dta", replace


// keep if tweet_postbirth == 1 & full_3years == 1
// save "$cleaned/tweets_by_user_for_TEXT_ANALYSIS.dta", replace





********** Restricting 
// use "$cleaned/user_info_full_sample_CLEAN.dta", clear
// merge 1:m unique_id using "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", keepusing(full_3years no_rt_reply) force



*********************** OLD TWEET TEXT DATA CLEANING ************************

// use "$cleaned/tweets_by_user_full_sample.dta", clear
//
// *** Variable types ***
// 	* Integers
// 	foreach var in like_count retweet_count reply_count quote_count {
// 		destring `var', replace
// 	}
//
// *** Dates ***
// 	foreach var in created_at {
// 		gen `var'_stata = date(substr(`var',1,10), "YMD")
// 		format `var'_stata %td
// 		count if missing(`var')
// 		drop `var'
// 		count if missing(`var'_stata)
// 		rename `var'_stata `var'
// 	}
//	
// *** Other cleaning ***
// 	* truncate the unique_ID to eliminate time stamp (h)
// 	replace unique_id = regexs(1) if regexm(unique_id, "^(.*)T")
//	
// 	** Drop if date is outside 18 month pre/post
// 	drop if created_at < 18808
//
// *** Duplicates ***
// 	duplicates report unique_id tweet_id
// 	bysort unique_id tweet_id: gen dup_order = _n
// 	drop if dup_order == 2
// 	drop dup_order
//	
// 	* A couple more duplicates
// 	duplicates tag tweet_id, gen(dup_tag)
// 	bysort tweet_id (tweet_id): gen dup_order = _n
// 	drop if dup_tag == 1 & dup_order == 2
// 	drop dup_tag dup_order
//	
// * Double check numbers	
// 		// make sure we include all birth announcement tweets in tweet text data
// 	merge m:1 unique_id using "$cleaned/user_info_full_sample_CLEAN.dta", force
// 		// get rid of tweets for which we don't have account information (user info)
// 	drop if _merge == 1
// 		// make sure all BA have the full info
// 	replace created_at = date_birth_tweet if _merge == 2
// 	replace tweet_type = "original" if _merge == 2
// 	drop _merge
//
// * Generate needed Variables
// 	* Binary indicator pre/post birth
// 	gen post_birth = (date_birth < created_at)
// 	replace post_birth = 1 if date_birth == created_at
// 	gen tweet_postBA = (date_birth_tweet < created_at)
// 	replace tweet_postBA = 1 if date_birth_tweet == created_at 
// // 	egen acct_tweeted_postBA = max(tweet_postBA), by(unique_id) // merged from user
//
// * Generate birth tweet binary
// // merge 1:1 unique_id tweet_id using "$cleaned/user_info_full_sample_CLEAN.dta", keepusing(tweet_id)
// // 	gen birth_tweet = (date_birth_tweet==created_at)
// // 	replace birth_tweet = 0 if _merge != 3
// // 	drop _merge
//	
// 	* Restrict sample to 18mo pre and 18 mo post
// 	gen days_from_birth = created_at-date_birth
// 	gen months_from_birth = floor(days_from_birth / 30)
// 	gen week_from_birth = floor(days_from_birth / 7)
// 	keep if abs(week_from_birth) <= 78
// 	keep if abs(months_from_birth) <= 18 // keep only 18 months pre and post
//
// 	* Check duplicates one more time
// 	duplicates tag tweet_id, gen(dup_tag)
// 	bysort tweet_id (tweet_id): drop if dup_tag == 1 & _n == 2
// 	drop dup_tag
//	
// * Keep only necessary variables ...
// keep unique_id author_id date_birth female date_birth_tweet tweet_id text created_at days_from_birth week_from_birth months_from_birth like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls full_3years no_rt_reply post tweet_postBA acct_tweeted_postBA 
//
// * Correct order
// order unique_id author_id date_birth female date_birth_tweet tweet_id text created_at days_from_birth week_from_birth months_from_birth like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls full_3years no_rt_reply post tweet_postBA acct_tweeted_postBA 
//
// *** Label all variables ***
// label variable unique_id "Unique identifier for each Twitter user and their first birth"
// label variable author_id "Unique identifer for each Twitter user"
// label variable tweet_id "Unique identifer for each tweet"
// label variable created_at "Date of tweet post"
// label variable text "Text of the tweet"
// label variable like_count "# of likes on tweet"
// label variable retweet_count "# of retweets on tweet"
// label variable reply_count "# of replies on tweet"
// label variable quote_count "# of quote tweets on tweet"
// label variable tweet_url "Twitter URL of tweet"
// label variable media_url "URL link to picture or video on tweet (if applicable)"
// label variable tweet_type "Type of tweet (original vs quote)"
// label variable embedded_urls "URL linked in tweet (if applicable) or self-link for tweets including photo/video"
// label variable post_birth "If tweet was post birth date (birth tweet = 1)"
// label variable days_from_birth "Days since birth"
// label variable week_from_birth "Weeks since birth"
// label variable months_from_birth "Months since birth"
// label variable acct_tweeted_postBA "Did this account tweet after the birth announcement?"
// label variable tweet_postBA "If tweet was post birth announcement (birth tweet = 1)"
// // label variable birth_tweet "Is this the birth announcement tweet? (0/1)"
//
//
// save "$cleaned/tweets_by_user_full_sample_CLEAN.dta", replace
// save "$final/tweets_by_user_full_sample_CLEAN.dta", replace
//







*********************** OTHER NOTES *************************
// Embeded media  = 
		* if they include a link in the text of their post/tweet, that link will be included in the embedded_urls variables
		* if there is no link in the text of their tweet but there is a photo/video/gif attached to their post, the entire tweet link will be included in the embedded_urls variable
		* if they posted on instagram and have their twitter linked, then the instagram link (to the original post) will show up here BUT ONLY SOMETIMES!
	*!! Problem here ... 
		*1. sometimes these are linked urls (i post on Insta and have my account linked to twitter so it automatically posts to Twitter)
		*2. Sometimes they include a instagram/twitter link as a reference but it isn't actually their real post (not linked)
		

// media_urls = 
		* if there is a photo attached to their tweet, the link to that photo will be included in the media_urls variable
		

// Some posts will have no embedded_urls or media_urls but are still a linked post.
	* !! This means we might need to do this manually...



// TRUNCATING
// 	gen un_id_2 = regexs(1) if regexm(unique_id, "^(.*)T")
// 	browse unique_id un_id_2 date_birth
