* Author: Hannah Lybbert
* Created: 02/10/2026
* Purpose: Create a sample of 200 birth announcements to hand identify gender of baby


use "$final/user_analysis_sample.dta", clear

	keep if full_3years == 1


********************************************************************************
* Sample 200 observations for hand-checking child gender predictions
********************************************************************************


* Set seed for reproducibility
set seed 12345
* Take random sample of 200 observations
sample 200, count

keep tweet_id tweet_url username description text 
order username description tweet_id tweet_url text

gen baby_girl = .


save "$testing/baby_gender_sample200.dta", replace

use "$testing/baby_gender_sample200.dta", clear



// lets use author_id as the main indicator.
// the code should follow the same structure as lines 1-30, 55-76, 82-139 (but this should include the baby gender message we've already typed up instead of account gender like it is in that script), 272-392 in get_demographics.py.
// Note the output from this file should be the input file but with two additional columns 'baby_girl' (gender of baby, 1 if female, 0 if male, -99 if missing or unsure), and confidence score.
//

use "$intermediate/user_info_full_sample.dta", clear

set seed 12345
sample 50, count
save "$testing/baby_gender_minisample.dta", replace

use "$raw/child_gender_prediction.dta", clear
merge 1:1 unique_id using "$testing/baby_gender_minisample.dta"


use "$raw/child_gender_prediction.dta", clear
merge 1:1 unique_id using "$intermediate/user_info_full_sample.dta"