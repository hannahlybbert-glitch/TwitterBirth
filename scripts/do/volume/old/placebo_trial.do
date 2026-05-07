
****************** TAKE TWO (ds) *************************************************************

**# RESTRICT THE SAMPLE to accounts active for 18 months pre birth


use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear

* 1. Generate real birth timeline variables
gen days_from_birth = date - date_birth
gen week_from_birth = floor(days_from_birth / 7)
gen total_tweets = orig_qt_count + rt_reply_count

* 1A. Collapse to weekly means (real birth)
preserve
collapse (mean) real_tweets = total_tweets, by(week_from_birth)
tempfile real_data
save `real_data'
restore


* 2. Generate random placebo dates (restricted to pre-birth period)
set seed 1234 // fix a starting value so figure is reproducible
bysort unique_id: gen rand_days = runiformint(-540, -270)  // Random day between 18mo and 9mo pre-birth
gen date_placebo = date_birth + rand_days

* 2A. Generate placebo timeline variables
gen days_from_placebo = date - date_placebo
gen week_from_placebo = floor(days_from_placebo / 7)

* 2B. Collapse to weekly means (placebo)
gen placebo_tweets = total_tweets
collapse (mean) placebo_tweets, by(week_from_placebo)
rename week_from_placebo week_from_birth
tempfile placebo_data
save `placebo_data'


* 3. Merge real and placebo data
use `real_data', clear
merge 1:1 week_from_birth using `placebo_data', nogen
drop if week_from_birth > 78
// drop if week_from_birth > 78 | week_from_birth < -78 // should we restrict the sample here aswell?

* 3A. Plot both lines
twoway (line real_tweets week_from_birth, lcolor(orange) lwidth(medthick)) ///
       (line placebo_tweets week_from_birth, lcolor(gs8) lpattern(dash)), ///
       xline(0, lcolor(black) lpattern(dash)) ///
       ytitle("Average Tweets per User per Week") ///
       xtitle("Weeks from (Real/Placebo) Birth") ///
       title("Tweeting Behavior Real vs. Placebo Birth") ///
       legend(order(1 "Real Birth" 2 "Placebo Birth") position(6) ring(0)) ///
       graphregion(color(white)) ///
       xlabel(-78(13)78)
graph export "$figures/twt_behavior/placebo/all_placebo.jpg", replace

	   
// legend(label(1 "Female") label(2 "Male") position(6) ring(0))






****************** BY GENDER *************************************************************

use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear

merge m:1 unique_id using "$final/user_analysis_sample.dta", keepusing(female) //30 not matched, check out
drop _merge

* 1. Generate real birth timeline variables
gen days_from_birth = date - date_birth
gen week_from_birth = floor(days_from_birth / 7)
gen total_tweets = orig_qt_count + rt_reply_count

* 1A. Collapse to weekly means (real birth)
preserve
collapse (mean) real_tweets = total_tweets, by(week_from_birth female)
tempfile real_data
save `real_data'
restore


* 2. Generate random placebo dates (restricted to pre-birth period)
set seed 1234 // fix a starting value so figure is reproducible
bysort unique_id: gen rand_days = runiformint(-540, -270)  // Random day between 18mo and 9mo pre-birth
gen date_placebo = date_birth + rand_days

* 2A. Generate placebo timeline variables
gen days_from_placebo = date - date_placebo
gen week_from_placebo = floor(days_from_placebo / 7)

* 2B. Collapse to weekly means (placebo)
gen placebo_tweets = total_tweets
collapse (mean) placebo_tweets, by(week_from_placebo female)
rename week_from_placebo week_from_birth
tempfile placebo_data
save `placebo_data'


* 3. Merge real and placebo data
use `real_data', clear
merge 1:1 week_from_birth female using `placebo_data', nogen
drop if week_from_birth > 78
// drop if week_from_birth > 78 | week_from_birth < -78 // should we restrict the sample here aswell?


* 4. Plot both lines by gender
twoway ///
    (line real_tweets week_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (line placebo_tweets week_from_birth if female==1, lcolor(red) lpattern(dash)) ///
    (line real_tweets week_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    (line placebo_tweets week_from_birth if female==0, lcolor(blue) lpattern(dash)), ///
    xline(0, lcolor(black) lpattern(dash)) ///
    ytitle("Average Tweets per User per Week") ///
    xtitle("Weeks from (Real/Placebo) Birth") ///
    title("Tweeting Behavior: Real vs Placebo Birth, by Gender") ///
    legend(order(1 "Real - Women" 2 "Placebo - Women" 3 "Real - Men" 4 "Placebo - Men") ///
           position(2) ring(0)) ///
    graphregion(color(white)) ///
    xlabel(-78(13)78)

graph export "$figures/twt_behavior/placebo/all_placebo_gender.jpg", replace







****************** Previous attempts *************************************************************

use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear

** 1. Generate "months from birth" var
gen days_from_birth = date - date_birth
gen months_from_birth = floor(days_from_birth / 30)
gen total_tweets = orig_qt_count + rt_reply_count
gen week_from_birth = floor(days_from_birth / 7)


***** 2. Placebo coding...

** (A) Generate min and max dates where placebo can occur
gen placebo_min = date_birth - (78*7)
gen placebo_max = date_birth - (39*7)

** (B) Generate random placebo date for each account
preserve
	keep unique_id date_birth placebo_min placebo_max
	duplicates drop
	 
	gen double rand = runiform() // random # [0,1]
	gen double placebo_days = floor(rand * (placebo_max - placebo_min)) // random # of days in range
	gen double placebo_birth_date = placebo_min + placebo_days // random placebo birth date
	
	drop rand placebo_days 
	tempfile placebo_dates
	save `placebo_dates'
restore

** (C) Merge placebo birth dates back into main dataset
merge m:1 unique_id using `placebo_dates' // might say it doesn't uniquely identify, in that case I need to keep unique_id above on line 47 and then merge back on unique_id
drop _merge

** (D) Calculate days, weeks, months from placebo date
gen days_from_placebo = date - placebo_birth_date
gen months_from_placebo = floor(days_from_placebo / 30)
gen week_from_placebo = floor(days_from_placebo / 7)

** (E) Restrict sample
**# Do I want to be dropping obs here?? Try and see how it goes...
keep if abs(days_from_birth) >= 546 | (abs(days_from_placebo) >= 540  & abs(days_from_placebo) >= 550)

** (F1) Collapse to weekly average behavior (treatment)
preserve
	gen period = "treatment"
	collapse (mean) total_tweets, by(week_from_birth period)
	rename week_from_birth week
// 	rename total_tweets avg_tweets
	tempfile treatment 
	save `treatment'
restore

** (F2) Collapse to weekly average behavior (placebo)
gen period = "placebo"
collapse (mean) total_tweets, by(week_from_placebo period)
rename week_from_placebo week
// rename total_tweets avg_tweets
tempfile placebo
save `placebo'

** (H) Append datasets
use `treatment', clear
append using `placebo'

** Plot
twoway (line total_tweets week if period=="treatment", lpattern(solid) lwidth(medium) ///
       lcolor(blue)) ///
       (line total_tweets week if period=="placebo", lpattern(dash) lwidth(medium) ///
       lcolor(ebg)), ///
       ytitle("Average Tweets per Week") ///
       xtitle("Weeks from Event") ///
       legend(order(1 "Treatment (birth)" 2 "Placebo (random pre-birth)") pos(6)) ///
       title("Twitter Activity Before and After Birth vs. Placebo Date") ///
       graphregion(color(white))



*******************************************************************************




/// Restricting the sample
egen min_days = min(days_from_birth), by(unique_id)
gen not_546 = min_days > -546
egen max_days = max(days_from_birth), by(unique_id)
replace not_546 = 1 if max_days < 546 // No obs that didn't make it to 546 days post birth

drop if not_546 == 1


**1. TOTAL TWEETS (og+qt+rt+rply)
preserve
collapse (mean) total_tweets, by(week_from_birth)

** PLOT (total tweets)
twoway (line total_tweets week_from_birth, lwidth(medthick) lcolor(orange)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Tweets per User") ///
         xtitle("Weeks from Birth") ///
         title("Tweeting Behavior Before and After Birth (restr.)") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78)









**************** EXPERIMENTING PLACEBO ******************

use "$final/user_analysis_sample.dta", clear

hist date_birth

hist date_birth, width(91.25) ///
    discrete ///
    xlabel(, format(%td)) ///
    xtitle("Date of Birth") ///
    title("Distribution of Birthdates") ///
    ytitle("Number of Observations") ///
    graphregion(color(white))

*******************************************************************************
	
use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear

hist date

hist date, width(182.75) ///
    discrete ///
    xlabel(, format(%td)) ///
    xtitle("Date of Birth") ///
    title("Distribution of Birthdates") ///
    ytitle("Number of Observations") ///
    graphregion(color(white))
	
	