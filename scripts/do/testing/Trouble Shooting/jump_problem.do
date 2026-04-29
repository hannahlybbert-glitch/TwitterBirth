
** Handcoded master file 8k accounts with BA
use "$archive/hand_coded_master_full_sample.dta", clear

	* 8,098 distinct author_id if BA = 1

	* Fix date variables
	gen str10 created_date = substr(created_at, 1, 10)
	* Convert to Stata daily date
	gen double birth_date = date(created_date, "YMD")
	format birth_date %tdDDmonCCYY
	gen birth_date_hc = birth_date
	format birth_date_hc %tdDDmonCCYY
	
	* Keep only the birth announcements?
	keep if birth_announcement == 1
	
	* label as hand coded
	gen hand_code = 1

	* Make sure merge variables are the right type
	gen str100 text_str = substr(text, 1, 100)
	drop text
	rename text_str text
	
	gen str20 id_str = substr(author_id, 1, 20)
	drop author_id
	rename id_str author_id

tempfile hand_coded_master
save `hand_coded_master'


** GPT classified, 78k accounts BA
use "$raw/classified_images_full_sample.dta", clear
	* 78,018 distinct author_id if text_class == 1
// use "$archive/to_hand_code_full_sample.dta", clear
// 	* 75,711 distinct author_id if text_class == 1

	* Fix date variables
	gen str10 created_date = substr(created_at, 1, 10)
	* Convert to Stata daily date
	gen double birth_date = date(created_date, "YMD")
	format birth_date %tdDDmonCCYY
	gen birth_date_gpt = birth_date
	format birth_date_gpt %tdDDmonCCYY
	
	* Make sure merge variables are the right type
	gen str100 text_str = substr(text, 1, 100)
	drop text
	rename text_str text
	
	gen str20 id_str = substr(author_id, 1, 20)
	drop author_id
	rename id_str author_id

merge m:1 author_id text using `hand_coded_master', force
	
* double check numbers
	distinct author_id if text_classification == "1" // ~78k
	distinct author_id if hand_code == 1 // ~8k
	distinct author_id if text_classification == "1" & hand_code != 1 // ~70k
	tab hand_code text_classification // 7,611 are the same (not the full 8k)

* Histogram of 78k unique accounts with birth announcement after GPT text classification
hist birth_date if text_classification == "1" 
	* flat (as expected)
	graph export "C:\Users\hlybbert\OneDrive - The University of Chicago\Documents\birth_date_78k.png", replace

* Histogram of 8k unique accounts with birth announcement after hand coding
hist birth_date if birth_announcement == 1 
	* jump (as expected)
	graph export "C:\Users\hlybbert\OneDrive - The University of Chicago\Documents\birth_date_8k.png", replace

* Histogram of ~70k unique accounts text classified by GPT as BA but not hand coded
hist birth_date if hand_code != 1  & text_classification == "1" 
	* flat (NOT as expected, would have anticipated seeing an inverse jump)
	graph export "C:\Users\hlybbert\OneDrive - The University of Chicago\Documents\birth_date_70k.png", replace
	


	
***** INVERSE JUMP? *****
// 2.	So, I'm a bit surprised that there is a jump in birth_date_8k but not a similar drop in the birth_date_70k. Maybe it is just that it is too small to perceive when just looking at the graph? I think mechanically there *has* to be a drop in the birth_date_70k if there is a jump in the birth_date_8k. Can you check and make sure the drop is there and it is just hard to see?

* Take a random sample of the observations that weren't hand coded 
preserve
    keep if hand_code != 1 & text_classification == "1"
    sample 8171, count
	hist birth_date
restore
	
preserve
	keep if hand_code == 1
	count
	hist birth_date
restore
	
***** DATE CHECK *****	
* Check to see if the dates line up between the two files
	gen date_mismatch = (birth_date_gpt != birth_date_hc) if !missing(birth_date_gpt, birth_date_hc)
	tab date_mismatch
		* only 4 that don't line up exactly and its only by a couple of days (2 weeks at most)
		
* Of the 8,000 accounts that merged accurately into the larger 78k accounts, do they have the same date in the final file as they do in the file where they merge in? 
* Date in 8k file = date in 78k file post merge?
preserve
keep if hand_code == 1 & _merge == 3 // 7,610 that merged from hand code file to master file
gen date_mismatch = (birth_date_gpt != birth_date_hc) if !missing(birth_date_gpt, birth_date_hc)
tab date_mismatch
restore
	



***** HAND CODING DOUBLE CHECK *****
use "$archive/hand_coded_master_full_sample.dta", clear
	* Fix date variables
	gen str10 created_date = substr(created_at, 1, 10)
	* Convert to Stata daily date
	gen double birth_date = date(created_date, "YMD")
	format birth_date %tdDDmonCCYY
	
** Take random sample of 100 to x2 check by hand
**** PRE July 2015 ****
		* to see if we need to re hand code 39k observations
	preserve
		keep if birth_date < 20298
		sample 100, count
// 		save "$archive/re_hand_code_sample.dta", replace
	restore

use "$archive/re_hand_code_sample.dta", clear
hist birth_date if birth_announcement == 1

save "$archive/re_hand_code_sample_DONE.dta", replace

**** POST July 2015 ****
	preserve
		keep if birth_date > 20298
		sample 100, count
// 		save "$archive/re_hand_code_sample_postjump.dta", replace
	restore

use "$archive/re_hand_code_sample_postjump.dta", clear
save "$archive/re_hand_code_sample_postjump_DONE.dta", replace


	
	**** NOTES ****
// use "$archive/hand_coded_master_full_sample.dta", clear
// 	gen str10 created_date = substr(created_at, 1, 10)
// 	gen double birth_date = date(created_date, "YMD")
// 	format birth_date %tdDDmonCCYY
//	
// 	preserve
// 	bysort author_id (birth_date): keep if _n == 1
// 	hist birth_date if birth_announcement == 0
// 	restore
//	
// use "$raw/classified_images_full_sample.dta", clear
// 	gen str10 created_date = substr(created_at, 1, 10)
// 	gen double birth_date = date(created_date, "YMD")
// 	format birth_date %tdDDmonCCYY
//	
// 	preserve
// 	bysort author_id (birth_date): keep if _n == 1
// 	hist birth_date if text_classification == "1"
// 	restore


	
	
** Try also merging with the final cleaned user info full sample data file


// * Generate variable with string length
// gen id_len = length(author_id)
//
// * Find the max length
// summarize id_len, meanonly
// list text id_len if id_len == r(max)

