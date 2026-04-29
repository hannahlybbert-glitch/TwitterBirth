* Author: Hannah Lybbert
* Created: 8/21/2025
* Purpose: Determine how many accounts dropped out of our sample entirely post birth

******** QUITTING ATTEMPTS *********

********************** QUITTING ATTEMPT # 3 ***************************

use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	keep if acct_tweeted_postBA ==1 & full_3years==1

	gen active_idx = 1 if total_tweets >= 1
	replace active_idx = 0 if total_tweets == 0

// preserve
// ** Account active that week?
// 	collapse (sum) active_idx, by(author_id week_from_birth)
// 	gen active = 1 if active_idx > 0
// 	replace active = 0 if active_idx == 0
//
// * Sort data to find week of last activity during 18 month post period
// 	sort author_id week_from_birth
// 	bysort author_id (week_from_birth): egen last_active = max(cond(active==1, week_from_birth, .))
//
// * Quitting variable
// 	gen quit = (active==0 & week_from_birth > last_active)
// 	gen still_active = (week_from_birth <= last_active)
//	
// collapse (sum) still_active, by(week_from_birth)

// * PLOT
// twoway (line still_active week_from_birth, lwidth(medthick) lcolor(red)) ///
//        , xline(0, lpattern(dash) lcolor(edkblue)) ///
//          ytitle("Active Accounts") ///
//          xtitle("Weeks from Birth") ///
//          title("Account Drop Off Across 3-year Period") ///
//          graphregion(color(white)) ///
//          xlabel(-78(13)78) ///
// 		 note("Note: Accounts 'drop off' once they do not tweet again for the rest of the sample period")
// * Save graph
// graph export "$quitting_figs/account_drop_off.jpg", replace
// restore

preserve
** Account active that week?
	collapse (sum) active_idx, by(author_id months_from_birth)
	gen active = 1 if active_idx > 0
	replace active = 0 if active_idx == 0
* Sort data to find week of last activity during 18 month post period
	sort author_id months_from_birth
	bysort author_id (months_from_birth): egen last_active = max(cond(active==1, months_from_birth, .))
* Quitting variable
	gen quit = (active==0 & months_from_birth > last_active)
	gen still_active = (months_from_birth <= last_active)
collapse (sum) still_active, by(months_from_birth)


* PLOT -- by month
twoway (line still_active months_from_birth, lwidth(medthick) lcolor(red)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Active Accounts") ///
         xtitle("Months from Birth") ///
         title("Account Drop Off Across 3-year Period") ///
         graphregion(color(white)) ///
         xlabel(-18(2)18) ///
		 note("Note: Accounts 'drop off' once they do not tweet again for the rest of the sample period. 2,775 accounts still active at month 18", size(vsmall))
* Save graph
graph export "$quitting_figs/account_drop_off_MO.jpg", replace

restore






********************** QUITTING ATTEMPT #2 ***************************

use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear

gen days_from_birth = date - date_birth
gen week_from_birth = floor(days_from_birth / 7)
gen total_tweets = orig_qt_count + rt_reply_count
gen active_idx = 1 if total_tweets >= 1
replace active_idx = 0 if total_tweets == 0

** Account active that week?
	collapse (sum) active_idx, by(unique_id week_from_birth)
	gen active = 1 if active_idx > 0
	replace active = 0 if active_idx == 0

* Sort data to find week of last activity during 18 month post period
	sort unique_id week_from_birth
	bysort unique_id (week_from_birth): egen last_active = max(cond(active==1, week_from_birth, .))

* Quitting variable
	gen quit = (active==0 & week_from_birth > last_active)
	gen still_active = (week_from_birth <= last_active)


* Save temp file for figure
	tempfile quitting_data
	save `quitting_data'

** Merge
	use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	gen days_from_birth = date - date_birth
	gen week_from_birth = floor((days_from_birth) / 7)
	merge m:1 unique_id week_from_birth using `quitting_data', nogen

	gen total_tweets = orig_qt_count + rt_reply_count

* PLOTTING
** Prep to plot
	collapse (sum) still_active, by(author_id week_from_birth)
	gen activity_idx = 1 if still_active > 0
	**# Confused here because at time of birth it only shows 8429 active accounts instead of 8441 (12 less than there should be)
	replace activity_idx = 0 if still_active == 0 

**# What to do here? Why are we missing twelve accounts at the point of birth?
	** Number discrepancy...
	distinct author_id
	sum activity_idx if week_from_birth == 0
	count if week_from_birth == 0


* PLOT
collapse (sum) activity_idx, by(week_from_birth)
drop if week_from_birth <= -79 | week_from_birth >= 78	 
twoway (line activity_idx week_from_birth, lwidth(medthick) lcolor(red)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Active Accounts") ///
         xtitle("Weeks from Birth") ///
         title("All Active Accounts across 3 year period") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78) ///
// 		 ylabel (0(1000)8500)

* Save graph
graph export "$figures/twt_behavior/quitting/all_quitting.jpg", replace
restore



********************** QUITTING (restricted sample) ***************************
use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear

gen days_from_birth = date - date_birth
gen week_from_birth = floor(days_from_birth / 7)
gen total_tweets = orig_qt_count + rt_reply_count
gen active_idx = 1 if total_tweets >= 1 // was this acct active this day?
replace active_idx = 0 if total_tweets == 0

** Account active that week?
	collapse (sum) active_idx, by(unique_id week_from_birth)
	gen active = 1 if active_idx > 0
	replace active = 0 if active_idx == 0

** Find week of last activity during 18 month post period
	sort unique_id week_from_birth
	bysort unique_id (week_from_birth): egen last_active = max(cond(active==1, week_from_birth, .)) // week of last activity for rest of 18mo period

* Quitting variable(s)
	gen quit = (active==0 & week_from_birth > last_active)
	gen still_active = (week_from_birth <= last_active) // Inverse of quit for counting purposes

* Save quitting varialbes as a temp file
	tempfile quitting_data
	save `quitting_data'

** Merge
	use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	gen days_from_birth = date - date_birth
	gen week_from_birth = floor((days_from_birth) / 7)
	merge m:1 unique_id week_from_birth using `quitting_data', nogen
	gen total_tweets = orig_qt_count + rt_reply_count

** Restrict sample to only live accounts for full period
	egen min_days = min(days_from_birth), by(unique_id)
	gen not_546 = min_days > -546
	egen max_days = max(days_from_birth), by(unique_id)
	replace not_546 = 1 if max_days < 546 
	drop if not_546 == 1

** PLOTTING 
** Prep to plot
	collapse (sum) still_active, by(author_id week_from_birth)
	gen activity_idx = 1 if still_active > 0
	replace activity_idx = 0 if still_active == 0 

** PLOT
collapse (sum) activity_idx, by(week_from_birth)
drop if week_from_birth <= -79 | week_from_birth >= 78	 
twoway (line activity_idx week_from_birth, lwidth(medthick) lcolor(blue)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Active Accounts") ///
         xtitle("Weeks from Birth") ///
         title("Active Accounts across 3 year period (restricted)") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78) ///
// 		 ylabel (0(1000)8500)

* Save graph
graph export "$figures/twt_behavior/quitting/quitting_restr.jpg", replace
restore





********************** QUITTING ATTEMPT #1 ***************************

use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear

gen days_from_birth = date - date_birth
gen week_from_birth = floor(days_from_birth / 7)
gen total_tweets = orig_qt_count + rt_reply_count
gen quitting_idx = 1 if total_tweets == 1
replace quitting_idx = 0 if total_tweets == 0

// preserve
drop if days_from_birth < 0
collapse (sum) quitting_idx, by(unique_id)
tempfile quitting_data
save `quitting_data'

count if quitting_idx > 0
count if quitting_idx == 0

** Merge
use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
merge m:1 unique_id using `quitting_data', nogen

gen days_from_birth = date - date_birth
gen week_from_birth = floor(days_from_birth / 7)
gen total_tweets = orig_qt_count + rt_reply_count
gen quit = 1 if quitting_idx == 0
replace quit = 0 if quitting_idx > 0


** PLOT
collapse (mean) total_tweets, by(week_from_birth quit)

twoway (line total_tweets week_from_birth if quit == 0, lwidth(medthick) lcolor(orange)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Tweets per User per Week") ///
         xtitle("Weeks from Birth") ///
         title("Tweeting Behavior for accounts active for full 3 year period") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78)
* Save graph
graph export "$figures/twt_behavior/quitting/noquit_behavior.jpg", replace
restore



** PLOT

// preserve
// collapse (mean) total_tweets, by(week_from_birth quit) 
//
// ** PLOT (total tweets)
// twoway ///
//     (line total_tweets week_from_birth if quit == 1, lcolor(red) lwidth(medthick)) ///
//     (line total_tweets week_from_birth if quit == 0, lcolor(eltblue) lwidth(medthick)), ///
//     xline(0, lpattern(dash) lcolor(edkblue)) ///
//     ytitle("Avg Tweets per User per Week") ///
//     xtitle("Weeks from Birth") ///
//     title("Tweeting Behavior pre/post Birth (quitting)") ///
//     graphregion(color(white)) ///
//     xlabel(-78(13)78) ///
//     legend(label(1 "No Quit") label(2 "Quit") position(6) ring(0))
// * Save graph
// graph export "$figures/twt_behavior/quitting/all_quitting.jpg", replace
// restore

