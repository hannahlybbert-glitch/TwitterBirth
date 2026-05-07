* Make sure that in the 2018 data, you make sure not to do any analysis on births that occur more than 7 days before or after the birth announcement tweet.

********************************************************************************************************
* Something isn't really adding up numbers-wise I did my best. Maybe you can find what I did wrong here
********************************************************************************************************

*********************** VOLUME DATA ***********************
// 2018
	* Load in tweet volume data for 2018
	import delimited using "$raw/tweet_volume_by_user_2018.csv", stringcols(_all) varnames(1) clear
	*rename variable for clarity
	rename tweet_count orig_qt_count

	* Save as a tempfile that will get merged with the retweet and reply volume
	tempfile vol_2018 
	sa `vol_2018'

	* Load in retweet and reply tweet volume from 2018
	import delimited using "$raw/retweet_reply_volume_by_user_2018.csv", stringcols(_all) varnames(1) clear
	* We merge on author_id and date, and then rt_reply count is the variable we want to add to our tweet volume dataset
	keep author_id date rt_reply_count
	* Keep regardless of merge status
	merge 1:1 author_id date using `vol_2018'
	drop if date == "No Data"
	
	drop _merge

	* this is an ID that will mimic the IDs created for the 2018 data. It is a combination of the author_id variable and the timestamp for the date of birth of the child. The timestamps are kind of long which make our code run slower. Once everything is all cleaned up, you could truncate the IDs if you want by removing the seconds, minutes, and hours from the timestamp.
	gen unique_id = author_id + "_" + date_birth

	* Set variable order
	order unique_id author_id date orig_qt_count rt_reply_count user_created_at date_birth begin_date end_date

	* Save as a cleaned file (ID, date, tweet ct/date, acct creation, chld birth date, begin/end_date)
	sa "$cleaned/tweet_volume_by_user_2018.dta", replace 

	* Now, we want to get the sum 
	destring orig_qt_count rt_reply_count, replace

	* Get the number of days of data in our dataset
	egen tag = tag(author_id date)
	egen days_data = total(tag), by(author_id)
	drop tag

	* Summary stats for the day of data in the file
	su days_data

	* Calculate how many days of data we should have
	gen begin_stata = date(substr(begin_date,1,10),"YMD") 
	gen end_stata = date(substr(end_date,1,10),"YMD")
	format *stata %td
	gen days_test = end_stata - begin_stata + 1

	* See which accounts are missing volume data
	tab unique_id if days_test != days_data

	* This will break the script if there still are incomplete series of data
	assert days_test == days_data

	* Collapse dataset into sums by
	collapse (sum) orig_qt_count rt_reply_count, by(unique_id begin_date end_date)

	* Save tempfile with volume from 2018
	tempfile vol_counts_2018
	sa `vol_counts_2018'

// 2013-2017
* Now do the same with 2013-2017 data (only difference is we merge on unique_id)
	* Load in tweet volume data for 2013-2017
	import delimited using "$raw/tweet_volume_by_user_2013_2017.csv", stringcols(_all) varnames(1) clear
	*rename variable for clarity
	rename tweet_count orig_qt_count

	* Save as a tempfile that will get merged with the retweet and reply volume
	tempfile vol_2013_2017 
	sa `vol_2013_2017'

	* Load in retweet and reply tweet volume from 2013-2017
	import delimited using "$raw/retweet_reply_volume_by_user_2013_2017.csv", stringcols(_all) varnames(1) clear
	* We merge on author_id and date, and then rt_reply count is the variable we want to add to our tweet volume dataset
	keep unique_id date rt_reply_count

	merge 1:1 unique_id date using `vol_2013_2017'
	* When _merge == 1, we got rt and reply volume but not original + quote
	* when _merge == 2, we got original + quote volume, but not rt and reply
	drop _merge
	* these are observations we do not have data for
	drop if date == "No Data"
	
	* Set variable order
	order unique_id author_id date orig_qt_count rt_reply_count user_created_at date_birth begin_date end_date

	* Save as a cleaned file
	sa "$cleaned/tweet_volume_by_user_2013_2017.dta", replace
	
// ALL years together
	* Now, we want to get the sum of tweet volume across sample period for each birth
	* First we use destring to make into a numeric variable
	destring orig_qt_count rt_reply_count, replace

	* Get the number of days of data in our dataset
	egen tag = tag(author_id date)
	egen days_data = total(tag), by(author_id)
	drop tag

	* Summary stats for the day of data in the file
	su days_data

	* Calculate how many days of data we should have
	gen begin_stata = date(substr(begin_date,1,10),"YMD") 
	gen end_stata = date(substr(end_date,1,10),"YMD")
	format *stata %td
	gen days_test = end_stata - begin_stata + 1

	* See which accounts are missing volume data
	tab unique_id if days_test != days_data

	* Drop accounts with incomplete series of data
	drop if date == "No Data"

// 	assert days_test == days_data

	* Collapse dataset into sums, grouping by unique_id (just bringing begin_date and end_date along)
	collapse (sum) orig_qt_count rt_reply_count, by(unique_id begin_date end_date)

	* Save tempfile with volume from 2018
	tempfile vol_counts_2013_2017
	sa `vol_counts_2013_2017'
	
	* append the volume counts from 2018
	append using `vol_counts_2018'
	
	* save tempfile for volume counts across entire sample
	tempfile vol_counts
	sa `vol_counts'
	
*********************** USER DATA merge & clean ***********************
	* Create empty tempfile and load in the user info files
	clear
	tempfile user
	sa `user', emptyok

	* Append together the user info files with demographics
	foreach year in "2018" "2013_2017" {
		import delimited using "$raw/user_info_with_demographics_`year'.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
		
		append using `user'
		sa `user', replace
	}

	* Local of variables that we want to keep (and the order that they should be in)
	local user_vars unique_id author_id username name description profile_image_url user_created_at female race occupation num_children created_at days_fro date_birth following_count followers_count tweet_count verified verified_type tweet_id text tweet_url has_picture media_url like_count retweet_count reply_count quote_count
	keep `user_vars'
	order `user_vars'

	* Rename some variables for clarity
	rename created_at date_birth_tweet
	rename tweet_count lifetime_posts
	rename num_children child_number

	* Merge in the volume counts
	merge 1:1 unique_id using `vol_counts'
	drop _merge
	
	
**# Should we do the same thing for user_created_at date_birth_tweet date_birth begin_date end_date? If yes...
// 	replace user_created_at = regexs(1) if regexm(user_created_at, "^(.*)T")
// 	replace date_birth_tweet = regexs(1) if regexm(date_birth_tweet, "^(.*)T")
// 	replace date_birth = regexs(1) if regexm(date_birth, "^(.*)T")
// 	replace begin_date = regexs(1) if regexm(begin_date, "^(.*)T")
// 	replace end_date = regexs(1) if regexm(end_date, "^(.*)T")


	* Save the cleaned file
	sa "$intermediate/user_info_full_sample.dta", replace

* merge with updated gender variable (manually edited gender values)
	use "$intermediate/user_info_full_sample.dta", clear
	
	merge 1:1 unique_id using "$raw\user_info_genderx2check.dta", keepusing(female)

	drop _merge
	
	save "$intermediate/user_info_full_sample.dta", replace
	
** OTHER CLEANING USER DATA
	use "$intermediate/user_info_full_sample.dta", clear
	
	* truncate the unique_ID to eliminate time stamp (h)
	replace unique_id = regexs(1) if regexm(unique_id, "^(.*)T")
	
	
	
	
	
	
*********************** VOLUME data merge ***********************
	* Now just append the tweet_volume_by_user files together to get full sample one
	use "$cleaned/tweet_volume_by_user_2018.dta", clear
	append using "$cleaned/tweet_volume_by_user_2013_2017.dta"
	
	sa "$intermediate/tweet_volume_by_user_full_sample.dta", replace

	
*********************** SENTIMENT ANALYSIS ***********************
import delimited using "$raw/tweets_by_user_2013_2017.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

append using "$raw/tweets_by_user_2018_matching.dta"

sort unique_id created_at
drop if tweet_id == "No Data" // 5 observations had no data, drop.

save "$raw/tweets_by_user_full_sample.dta", replace
save "$intermediate/tweets_by_user_full_sample.dta", replace

// convert back to .csv for Python sentiment analysis
use "$raw/tweets_by_user_full_sample.dta", clear
export delimited using "$raw/tweets_by_user_full_sample.csv", replace



////////////////////////////// STOPPED HERE /////////////////////////////////


	* Next Steps:
	* you should do the sentiment analysis using the tweets_by_user_{year}.csv files in the $raw folder. Then you can append them together to create a cleaned .dta file with tweet histories and sentiment scores (or whatever metric you use a machine-learning type model to analyze tweets) for the whole sample.

	* start with loading the file in
import delimited using "$raw/tweets_by_user_2013_2017.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear


* and then figure out how to combine with 2018 file
import delimited using "$raw/tweets_by_user_2018.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
// author_id, tweet_id, created_at, text, like_count, retweet_count, reply_count, quote_count, tweet_type, tweet_url, embedded_urls, media_urls

* make sure to drop if the birth occurred more than 7 days before or after the birth announcement tweet (only need to check this for 2018 data). You might need to merge in the user_info file to get "days_from" variable

* create unique_id variable for this file:

* figure out how to append them together

* when you finish sentiment analysis stuff (basically any ML stuff that needs python), make sure to incorporate in cleaned files

*To do this, fill in the blanks and run
gen unique_id = 
merge : unique_id using ""

* and then run
drop if abs(days_from) > 7



*******************************************************



*** BELOW HERE IS OLD CODE THAT MIGHT BE USEFUL AS YOU KEEP WORKING ***
*** Feel free to delete at some point ***

* Userful trick for turning timestamp into stata date
use "$intermediate/tweet_volume_by_user_full_sample.dta", clear

* combines two commands: the inner command (substr) evaluates first. It takes a string and keeps characters i-j where you have substr(var,i,j). So in our case it's substr(date_birth,1,10) keeps first 10 characters of "date_birth", which is just the YYYY-MM-DD part of the timestamp
* the outer command (date) converts YYYY-MM-DD formatted string into a stata date
gen stata_date_birth = date(substr(date_birth, 1,10),"YMD")
* then you can format stata date to show up in nicer format
format stata_date_birth %td


* start of old work
import delimited using "$raw/user_info_with_demographics_2018.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

local user_vars unique_id author_id username name description profile_image_url user_created_at date_birth following_count followers_count tweet_count verified verified_type tweet_id created_at text tweet_url has_picture media_url like_count retweet_count reply_count quote_count days_from

keep `user_vars'
order `user_vars'







* make sure to drop them if the birth was more than a week ago
//
// keep author_id-tweet_id created_at days_from profile_image_url user_created_at-verified

// bysort author_id (created_at): drop if _n > 1



tempfile user_2018 
sa `user_2018'

* merge in the original and quote tweet data and make sure the totals match up correctly
import delimited using "$raw/tweet_volume_by_user_2018.csv", stringcols(_all) varnames(1) clear
rename tweet_count orig_qt_count

tempfile vol_2018 
sa `vol_2018'

import delimited using "$raw/retweet_reply_volume_by_user_2018.csv", stringcols(_all) varnames(1) clear
keep author_id date rt_reply_count

merge 1:1 author_id date using `vol_2018'
drop if _merge == 1
drop _merge

* this is an ID that will mimic the IDs created for the 2018 data. It is a combination of the author_id variable and the timestamp for the date of birth of the child. The timestamps are kind of long which make our code run slower. Once everything is all cleaned up, you could truncate the IDs if you want by removing the seconds, minutes, and hours from the timestamp.
gen unique_id = author_id + "_" + date_birth

sa "$cleaned/tweet_volume_by_user_2018.dta", replace
sa `vol_2018', replace

destring orig_qt_count rt_reply_count, replace

egen tag = tag(author_id date)
egen days_data = total(tag), by(author_id)
drop tag

su days_data

gen begin_stata = date(substr(begin_date,1,10),"YMD") 
gen end_stata = date(substr(end_date,1,10),"YMD")

format *stata %td

* make sure we have the correct number of days of data
gen days_test = end_stata - begin_stata + 1
count if days_test != days_data
// assert days_test == days_data

* shows if there are entries that shouldn't be in there
tab author_id if days_test != days_data

drop if days_test != days_data

collapse (sum) orig_qt_count rt_reply_count, by(author_id begin_date end_date)

merge 1:1 author_id using `user_2018', nogen

// gen unique_id = author_id + "_" + date_birth

sa `user_2018', replace

sa "$cleaned/user_info_2018.dta", replace

import delimited using "$raw/tweets_by_user_2018.csv",  stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear


merge m:1 author_id using "$cleaned/user_info_2018.dta"
drop if _merge == 2
drop _merge embedded_urls
keep author_id-date_birth date_birth_tweet days_from

destring days_from, replace
drop if abs(days_from) > 7

drop if tweet_id == "No Data"

tempfile tweets_2018
sa `tweets_2018'

sa "$cleaned/tweets_by_user_2018.dta", replace 


import delimited using "$raw/user_info_with_demographics_2018.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear



* Now do a similar thing for the 2013-2017 data. There will be some different types of variables in this dataset, so be careful.
* first load in the user data
import delimited using "$raw/user_info_2013_2017.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

local user_vars unique_id author_id username name description profile_image_url user_created_at date_birth following_count followers_count tweet_count verified verified_type tweet_id created_at text tweet_url has_picture media_url like_count retweet_count reply_count quote_count

keep `user_vars'
order `user_vars'





* tweet histories
import delimited using "$raw/tweets_by_user_2013_2017.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

drop if tweet_id == "No Data"

gen one = 1
collapse (sum) tweet_count = one, by(unique_id)

keep 



* Things will change a little bit once we get the demographic variables together too
import delimited using "$raw/tweet_volume_by_user_2013_2017.csv", stringcols(_all) varnames(1) clear


import delimited using "$raw/retweet_reply_volume_by_user_2013_2017.csv", stringcols(_all) varnames(1) clear

* How to get dummy for outside links
// gen has_link = 0
// replace has_link = 1 if regexm(text,"https://")
// replace has_link = 0 if !missing(media_urls)
//
// tab has_link, m



import delimited using "$raw/user_info_with_demographics_2013_2017.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear





