** Trying to figure out date skew problem

// ******************************* HAND CODING MASTER *******************************
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


**************/// Graphing non birth announcements ///************
** Hand coding test...
// gen date_tweet = date(substr(created_at,1,10), "YMD")
// format date_tweet %td
// gen year_tweet = year(date_tweet)
// tab year_tweet
// tab year_tweet if !missing(birth_announcement)
//
// * Graph
// tw (hist year_tweet if birth_announcement == 1, col(blue%30) width(1) frequency discrete) ///
//  (hist year_tweet if birth_announcement == 0, width(1) col(red%30) frequency discrete), ///
//  legend(order(1 "BA" 2 "Not BA") ring(0) pos(2)) xlabel(2006(1)2017, nogrid) ytitle("Number of Accounts") ylabel(,nogrid format(%12.0fc))
******************///******************///******************///******************///
use "$archive/hand_coded_master_full_sample.dta", clear

	* Fix date variables
	gen str10 created_date = substr(created_at, 1, 10)
	* Convert to Stata daily date
	gen double birth_date = date(created_date, "YMD")
	format birth_date %tdDDmonCCYY
	
** Figure out data skew
hist birth_date

preserve
keep if birth_announcement == 1
hist birth_date
restore

preserve
keep if birth_announcement == 0
hist birth_date
restore


******************************* GPT CLASSIFICATIONS *******************************
*** IMAGE classification as a potential error spot. --> ALL classifications
// import delimited using "$raw/classified_images_2018_01_01-2018_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
//
// // ** Cleaning
// // 	* Fix date variables
// // 	gen str10 created_date = substr(created_at, 1, 10)
// // 	* Convert to Stata daily date
// // 	gen double birth_date = date(created_date, "YMD")
// // 	format birth_date %tdDDmonCCYY
//	
// ** Figure out data skew
// hist birth_date if missing(pic_classification)
//
// preserve
// keep if pic_classification == "1.0"
// keep if pic_classification == "0.0"
// keep if text_classification == "1"
// keep if text_classification == "0"
// hist birth_date
// restore
//
// tempfile images2018
// save `images2018' 
//
// import delimited using "$raw/classified_images_2013_01_01-2017_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
//
// append using `images2018'
//
// save "$raw/classified_images_full_sample.dta", replace

use "$raw/classified_images_full_sample.dta", clear

	** NOTES
		* 197,768 obs
		* Distinct accounts:
			* 167,912 author_id
			* 3,927 where image classification AND text classifiation are true 
			* 3,927 where image classification is true
			* 78,018 where text classification is true

* Fix date variables
gen str10 created_date = substr(created_at, 1, 10)
* Convert to Stata daily date
gen double birth_date = date(created_date, "YMD")
format birth_date %tdDDmonCCYY
	
** Figure out data skew
hist birth_date

preserve
keep if text_classification == "1"
hist birth_date
restore

preserve
keep if text_classification == "0"
hist birth_date
restore

preserve
keep if pic_classification == "0.0"  
hist birth_date
restore

preserve
keep if pic_classification == "1.0"
hist birth_date
restore



// Figuring out media_url and pic_classification problem
* Create indicators for missingness
gen byte miss_media = missing(media_url)
gen byte miss_pic   = missing(pic_classification)

* Tabulate combinations of missingness
tab miss_media miss_pic

hist birth_date if miss_media == 1 & miss_pic == 1
hist birth_date if miss_media == 0 & miss_pic == 1 // also CULPRIT
	hist birth_date if miss_media == 0 & pic_classification == "1.0" 
	hist birth_date if miss_media == 0 & pic_classification == "0.0"
hist birth_date if miss_media == 0 & miss_pic == 0 // CULPRIT

hist birth_date if miss_media == 1 & miss_pic == 1 & text_classification =="1"
hist birth_date if miss_media == 0 & miss_pic == 0 & text_classification =="1" // CULPRIT

hist birth_date if miss_media == 0 & miss_pic == 1 & text_classification =="0"
hist birth_date if miss_media == 1 & miss_pic == 1 & text_classification =="0"

hist birth_date if missing(pic_classification)
hist birth_date if missing(media_url)
**# BIG problem is when media URLS are classified 
hist birth_date if !missing(pic_classification)
hist birth_date if !missing(media_url)


**# Right Skew distribution here..
preserve
keep if !missing(pic_classification)
hist birth_date
restore

preserve
keep if text_classification == "1" & !missing(pic_classification)
hist birth_date
restore

**# Multimodal distribution here (three peaks)
preserve
keep if missing(pic_classification)
hist birth_date
restore

* mostly normal, tad left skewed
preserve
keep if text_classification == "1" & missing(pic_classification)
hist birth_date
restore

*** TEXT classification as a potential error spot. (update: its more likely pics)
import delimited using "$raw/classified_text_2018_01_01-2018_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

tempfile text2018
save `text2018' 

import delimited using "$raw/classified_text_2013_01_01-2017_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

append using `text2018'

	** NOTES
		* 197,768 obs
		* Distinct accounts:
			* 167,912 distinct author accounts
			* 78,018 where text classification is true

			
** Still figuring it out
use "$raw/classified_images_full_sample.dta", clear
count if text_classification == "1" & pic_classification == "0.0"
* Fix date variables
gen str10 created_date = substr(created_at, 1, 10)
* Convert to Stata daily date
gen double birth_date = date(created_date, "YMD")
format birth_date %tdDDmonCCYY

**# CULPRIT!!!!
* but not sure why it is happening here still... or what to do about it...
preserve
keep if text_classification == "1" & pic_classification == "0.0"
hist birth_date
restore
			
**# ALSO PROBLEM !!!! -> very right skewed
preserve
keep if text_classification == "1" & pic_classification == "1.0"
hist birth_date
restore		

**# This one is totally uniform though. SOmething is up with the classifiation
hist birth_date
		
			
			
**** How many does restricting sample to 7 days pre post birth get?
use "$archive/hand_coded_master_full_sample.dta", clear
			
** Cleaning
	* Fix date variables
	gen str10 created_date = substr(created_at, 1, 10)
	* Convert to Stata daily date
	destring days_from, replace
	gen double birth_date = date(created_date, "YMD") + (days_from)
	format birth_date %tdDDmonCCYY	
	
			
			
******* try to get full 8,441 sample
use "$raw/classified_images_full_sample.dta", clear

gen birth_announcement = 1 if text_classification == "1" & pic_classification == "1.0"

replace birth_announcement = 0 if text_classification == "0" | pic_classification == "0.0"

tab birth_announcement // 4,020 obs / 3,927 unique accounts

merge m:1 author_id using "$archive/hand_coded_master_full_sample.dta" keepusing()


use "$archive/hand_coded_master_full_sample.dta", clear

merge 