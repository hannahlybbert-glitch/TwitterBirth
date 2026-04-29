
********************************* PRE GPT *********************************

use "$archive/pre_GPT_master_full_sample.dta", clear

* Fix date variables
	gen str10 created_date = substr(created_at, 1, 10)
	* Convert to Stata daily date
	gen double birth_date_estimate = date(created_date, "YMD")
	format birth_date_estimate %tdDDmonCCYY
	
* Check for tweet_id duplicates
	* Tag duplicates of tweet_id (52821 duplicates)
	duplicates tag tweet_id, gen(dup) 
	tab dup
* Check for how mnay contian "i liked a @youtube video"
	count if strpos(lower(text), "i liked a @youtube video")
	
* Histograms
	hist birth_date_estimate, title("All Observations (327,448)")

********************************* POST TEXT CLASSIF. *********************************

use "$archive/classified_text_full_sample.dta", clear

* Fix date variables
	gen str10 created_date = substr(created_at, 1, 10)
	* Convert to Stata daily date
	gen double birth_date_estimate = date(created_date, "YMD")
	format birth_date_estimate %tdDDmonCCYY

* Histograms
	hist birth_date_estimate, title("All Observations (197,768)")
	hist birth_date_estimate if text_classification == "1", title("Birth Announcement based on text (78,018)")
	hist birth_date_estimate if text_classification == "0", title("NOT Birth Announcement based on text (93,799)")
	

********************************* AFTER IMAGE CLASSIF. *********************************

use "$raw/classified_images_full_sample.dta", clear

** Cleaning
	* Fix date variables
	gen str10 created_date = substr(created_at, 1, 10)
	* Convert to Stata daily date
	gen double birth_date_estimate = date(created_date, "YMD")
	format birth_date_estimate %tdDDmonCCYY

* Histograms
	hist birth_date_estimate, title("All Observations (197,768)")
	hist birth_date_estimate if text_classification == "1", title("Birth Announcement based on text (78,018)")
	hist birth_date_estimate if text_classification == "1" & pic_classification == "1.0", title("Birth Announcement based on image & text (3,927)")
	hist birth_date_estimate if !missing(media_url), title("# of births announcements/year with a photo attached")


********************************* PRE HAND CODING *********************************

use "$archive/to_hand_code_full_sample.dta", clear
	
** Cleaning
	* Fix date variables
	gen str10 created_date = substr(created_at, 1, 10)
	* Convert to Stata daily date
	gen double birth_date_estimate = date(created_date, "YMD")
	format birth_date_estimate %tdDDmonCCYY
	
* Histograms
	hist birth_date_estimate, title("All Accounts (75,711)")
	hist birth_date_estimate if text_classification == "1" & pic_classification == "1.0", title("Classified as Birth Announcement by GPT (3,927)")	
	
// ********************************* POST HAND CODING *********************************

use "$archive/hand_coded_master_full_sample.dta", clear

** Cleaning
	* Fix date variables
	gen str10 created_date = substr(created_at, 1, 10)
	* Convert to Stata daily date
	gen double birth_date_estimate = date(created_date, "YMD")
	format birth_date_estimate %tdDDmonCCYY
	
* Histograms
	hist birth_date_estimate, title("All Hand Coded Obs (79,192)")
	hist birth_date_estimate if birth_announcement == 1, title("Birth Announcement after RA classification (8,098)")
		* no 2017 jump anymore but we do see at mid 2015 jump now. Must be an RA problem
	hist birth_date_estimate if birth_announcement == 0, title("NON Birth Announcements after RA classification (71,052)")

**** RA PROBLEM? ***
* Check each csv that was sent to Rory
foreach name in Alex Ben Christian Claire Emily Gavin Jake Jonas Julia Justin Meklet Robert Sarah Sonia Zoe {
		import delimited using "$hand_coding/2013_2017/hand_coded_`name'.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

		** Date variables
			gen str10 created_date = substr(created_at, 1, 10)
			gen double birth_date_estimate = date(created_date, "YMD")
			format birth_date_estimate %tdDDmonCCYY
		** Histogram
			hist birth_date_estimate if birth_announcement == "1"
			graph export "$hand_coding/2013_2017/by_RA_hists/hand_coded_`name'.png", replace

}


		
	
	




	
	
	
	
	

// FILE MERGING 

********************************* PRE GPT *********************************
// ************ 2013-2017 ************
// import delimited using "$raw/query_results_2013_01_01-2017_12_31.csv", stringcols(_all) varnames(1) clear
//
// * Save temp file for merging momentarily
// tempfile query1317
// save `query1317'
//
// ************ 2018 ************
// import delimited using "$raw/query_results_2018_01_01-2018_12_31.csv", stringcols(_all) varnames(1) clear
//
// ** Append on temp file to check birth_date histogram
// append using `query1317'
//
// save "$archive/pre_GPT_master_full_sample.dta", replace


********************************* POST TEXT CLASSIF. *********************************
// import delimited using "$raw/classified_text_2018_01_01-2018_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
// tempfile text2018
// save `text2018' 
//
// import delimited using "$raw/classified_text_2013_01_01-2017_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
//
// append using `text2018'
// save "$archive/classified_text_full_sample.dta", replace


********************************* AFTER IMAGE CLASSIF. *********************************
// import delimited using "$raw/classified_images_2018_01_01-2018_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
// tempfile images2018
// save `images2018' 
//
// import delimited using "$raw/classified_images_2013_01_01-2017_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
//
// append using `images2018'
// save "$raw/classified_images_full_sample.dta", replace


********************************* PRE HAND CODING *********************************
// import delimited using "$hand_coding/2013_2017/to_hand_code_2013_01_01-2017_12_31.csv", stringcols(_all) bindquotes(strict) maxquotedrows(unlimited) clear
//
// tempfile tohc2013_17
// save `tohc2013_17'
//
// import delimited using "$hand_coding/2018/to_hand_code_2018_01_01-2018_12_31.csv", stringcols(_all) bindquotes(strict) maxquotedrows(unlimited) clear
//
// append using `tohc2013_17'
//	
// save "$archive/to_hand_code_full_sample.dta", replace


********************************* POST HAND CODING *********************************
// ************ 2013-2017 ************
// import delimited using "$hand_coding/2013_2017/hand_coded_master_2013_2017.csv", clear
//
// keep if birth_announcement == "0" | birth_announcement == "1"
// destring birth_announcement, replace
//
// * Save temp file for merging momentarily
// tempfile hcmaster1317
// save `hcmaster1317'
//
// ************ 2018 ************
// import delimited using "$hand_coding/2018/hand_coded_master_2018.csv", clear
//
// keep if birth_announcement == "0" | birth_announcement == "1"
// destring birth_announcement, replace
//
// ** Append on temp file to check birth_date histogram
// append using `hcmaster1317'
//
// save "$archive/hand_coded_master_full_sample.dta", replace
//
//
// use "$archive/hand_coded_master_full_sample.dta", clear


// * Checking if it was a specific RA problem: --> NOPE (at least not once data was merged)
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Alex"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Auto"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Ben"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Christian"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Claire"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Emily"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Gavin"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Jake"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Jonas"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Julia"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Justin"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Meklet"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Robert" 
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Sarah"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Sonia"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Zoe"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Rory"
// 	* 2018
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Bolun"
// 	hist birth_date_estimate if birth_announcement == 1 & assigned_to == "Min"