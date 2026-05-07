** Hannah's notes on Numbers (Rory's below)

**# These need to be updated as of 10/24
* User info
	use "$final/user_analysis_sample.dta", clear
	count // 8,474
	distinct unique_id author_id // 8,474 announcements from 8,440 accounts
	distinct author_id if full_3years == 1 // 7,510 accounts active for full 3
	distinct author_id if full_3years == 1 & acct_tweeted_postBA == 1 // 4,145
	
* Volume data
	use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	count // 9,014,492 days scraped
	distinct author_id // 8,440 accounts
	distinct author_id if full_3years==1 // 7,510 accounts active for full 3years
	distinct author_id if full_3years == 1 & acct_tweeted_postBA == 1 // 4,145
	count if full_3years == 1 & acct_tweeted_postBA == 1 // 4,537,256 days from final sample

* Tweet text data
	use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
	count // 1,790,618 tweets for all acounts over three years
	distinct author_id // 8,440 accounts total
	count if tweet_postbirth ==1 // 704,103 tweets from accounts w/ tweets post birth
	distinct author_id if tweet_postbirth ==1 // 5,428 accounts w/ tweets post birth

	

*------------------------------ RORY COUNTS ------------------------------*

* getting figures for appendix section

***************** 2018 *****************
* Initial pull
import delimited using "$raw/query_results_2018_01_01-2018_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

unique author_id if regexm(lower(text), "i liked a @youtube video")

count
unique tweet_id
unique author_id
* 41,046 posts pulled. 36,017 unique posts from API for 2018. 31,665 unique accounts. 

* classified by text
import delimited using "$raw/classified_text_GPT4_2018_01_01-2018_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

tab text_classification
unique tweet_id if text_classification == "1"
* 36.28% (12,232) made it through text classification from chatgpt
count if text_classification == "1" & has_picture == "1"
* 3,648 classified as 1 and have a picture

* classified by images
import delimited using "$raw/classified_images_2018_01_01-2018_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
tab pic_classification

* file that gets hand-coded
import delimited using "$raw/hand_coding/to_hand_code_2018_01_01-2018_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
tab pic_classification 

* hand-coding results
import delimited using "$raw/hand_coding/2018/hand_coded_2018_master.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

tab birth_announcement, m
tab days_from
* 6,477 hand-coded. 4,554 left over from total of 11,031. Of the hand-coded ones, 2,040 (32%) were birth announcements.

// * check date of account creation
// gen date_user_created = date(substr(user_created_at,1,10),"YMD")
// gen year_user_created = year(date_user_created)
//	
// tw (hist year_user_created, col(blue%50) width(1) frequency discrete) ///
// (hist year_user_created if missing(birth_announcement), col(red%50) width(1) frequency discrete), ///
// legend(order(1 "All" 2 "Hand-Coded So Far") ring(0) pos(2)) xlabel(2006(1)2018, nogrid) ///
// ytitle("Number of Accounts") ylabel(,nogrid format(%12.0fc))


* distribution of volume of tweets (got number of original tweets + quote tweets)
use "$cleaned/user_info.dta", clear
unique author_id
destring days_from, replace
unique author_id if abs(days_from) <= 7 | missing(days_from)

* how many accounts and tweets we have in sample once we drop any birth outside 7 days from tweet
use "$cleaned/tweets_by_user.dta", clear
unique author_id // 1318 accounts
unique tweet_id // 790,126 tweets
destring days_from, replace
keep if abs(days_from) <= 7 | missing(days_from)
unique author_id // 1161 accounts
unique tweet_id // 672,431 tweets


***************** 2013-2017 *****************

* Initial pull
import delimited using "$raw/query_results_2013_01_01-2017_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

count
unique tweet_id
unique author_id
* 212,848 posts pulled. 164,049 unique posts from API for 2018. 140,314 unique accounts. 

* classified by text
import delimited using "$raw/classified_text_GPT4_2013_01_01-2017_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

unique tweet_id if text_classification == "1"
* 75,361 made it through text classification
unique tweet_id if has_picture == "1"
* 5,844 had a picture
count if text_classification == "1" & has_picture == "1"
* 2,986 were classified as birth announcement and have a picture

* classified by images
import delimited using "$raw/classified_images_2013_01_01-2017_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
tab pic_classification
* 1,583 classified as a birth announcement based on picture 
* 28 failures

* file that gets hand-coded
import delimited using "$raw/hand_coding/2013_2017/to_hand_code_2013_01_01-2017_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
unique tweet_id
* 73,986 tweets to hand-code

* Hand-coded results
 * Load in hand_coded file
import delimited using "$raw/hand_coding/2013_2017/partially_hand_coded_master_2013_2017.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
* save as tempfile
tab birth_announcement if assigned_to == "Auto"
* 7,656 are auto-coded as not a birth announcement

* fully hand-coded file
import delimited using "$raw/hand_coding/2013_2017/hand_coded_2013_2017_master.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

tab birth,m 
* 6,542 birth announcements (8.84%)


***************** Full Sample *****************
use "$intermediate/tweet_volume_by_user_full_sample.dta", clear
merge m:1 unique_id using "$intermediate/user_info_full_sample.dta", keepusing(days_from)
destring days_from, replace
unique unique_id if !missing(orig_qt_count) & abs(days_from) <= 7
unique unique_id if !missing(rt_reply_count) & abs(days_from) <= 7


use "$intermediate/user_info_full_sample.dta", clear
destring days_from, replace
unique unique_id if !missing(orig_qt_count) & abs(days_from) <= 7
unique unique_id if !missing(rt_reply_count) & abs(days_from) <= 7



