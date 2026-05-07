**# to be moved into prep_data .do file once I know this runs well
** Prepare the 2018 text data for analysis 


** First I need to modify the 2018 user info data to make sure I can merge it into the tweet text file with the needed information. What I will do
	* 1. Drop all observations where births (days_from) are more than 7 days before or after the actual birth date
	* 2. For observations with multiple children (one author_id but multiple tweet_id birth announcments) I will only keep the first tweet announcing a birth. This is just so I can get access to a unique_id which will be used 

	
************** MODIFYING 2018 user info dataset **************
use "$intermediate/user_info_full_sample.dta", clear

// Checking if the same account announces multiple births within the dataset time frame
duplicates tag author_id, generate(dup_tag)  

// Drop the second observation so we can have a unique_id (one per account)
	sort author_id

	* Within each author_id group, assign order
	by author_id: gen obs_order = _n

	* Drop the second observation in each group
	drop if obs_order == 2
	drop dup_tag obs_order

save "$cleaned/user_info_first_child_NOTfull.dta", replace // only kept first child and births to uniquely identify the parent



// Merge 2018 user info with 2018 tweet text 
import delimited using "$raw/tweets_by_user_2018.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

// save "$raw/tweets_by_user_2018_cleaning.dta", replace // creating a temporary file to be filled later 

merge m:1 author_id using "$cleaned/user_info_first_child_NOTfull.dta" 
	* from this merge, they all found matches but 7,149 of them which don't have a value for "created_at", meaning that we wont know when those tweets were posted. But I think for these, the "created_at" value is the same as teh "date_birth_tweet" because they are missing fo the birth announcements 

** THIS MIGHT BE WRONG!!! But I manually checked 10 and they matched up either exactly or wtihin one day
replace created_at = date_birth_tweet if _merge == 2
	
drop _merge


** Keep only the variables we need for the tweet text data
keep unique_id author_id tweet_id created_at text like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls

* Order the variables for easy appending to the 2013-2017 data
order unique_id author_id tweet_id created_at text like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls


// save raw 2018 file .dta (to be used later for creating the )
save "$raw/tweets_by_user_2018_matching.dta", replace


// Get it back into .csv format for Python analysis
use "$raw/tweets_by_user_2018_matching.dta", clear
export delimited using "$raw/tweets_by_user_2018_matching.csv", replace







************** PREVIOUS NOTES **********************

// use "$intermediate/user_info_full_sample.dta", clear
//
// // drop if the birth occurred more than 7 days before or after the birth announcement tweet
// destring days_from, replace
// drop if days_from > 7 | days_from < -7 
// // would drop 270 obs


// ************** MODIFYING 2018 user info dataset **************
// use "$intermediate/user_info_full_sample.dta", clear
//
// // Checking if the same account announces multiple births within the dataset time frame
// duplicates tag author_id, generate(dup_tag)  
//
// // Drop the second observation so we can have a unique_id (one per account)
// 	sort author_id
//
// 	* Within each author_id group, assign order
// 	by author_id: gen obs_order = _n
//
// 	* Drop the second observation in each group
// 	drop if obs_order == 2
// 	drop dup_tag obs_order
//
// save "$cleaned/user_info_first_child_NOTfull.dta", replace // only kept first child and births to uniquely identify the parent
//
//
//
// // Merge 2018 user info with 2018 tweet text 
// import delimited using "$raw/tweets_by_user_2018.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
//
// // save "$raw/tweets_by_user_2018_cleaning.dta", replace // creating a temporary file to be filled later 
//
// merge m:1 author_id using "$cleaned/user_info_first_child_NOTfull.dta" 
// 	* from this merge, they all found matches but 7,149 of them which don't have a value for "created_at", meaning that we wont know when those tweets were posted. But I think for these, the "created_at" value is the same as teh "date_birth_tweet" because they are missing fo the birth announcements 
//	
// // Drop all tweets that weren't within 7 days of the birth
// destring days_from, replace
// drop if days_from > 7 | days_from < -7
// tostring days_from, replace


** THIS MIGHT BE WRONG!!! But I manually checked 10 and they matched up either exactly or wtihin one day
replace created_at = date_birth_tweet if _merge == 2
	
drop _merge
