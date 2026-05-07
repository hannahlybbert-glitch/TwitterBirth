* Author: Hannah Lybbertuse "$final/tweet_volume_by_user_full_sample_CLEAN.dta", clear 
* Created: 12/15/2025
* Purpose: Extensive margin graph


use "$final/tweet_volume_analysis_sample.dta", clear
// 	keep if full_3years ==1

preserve
	collapse (mean) total_month_tweets, by(months_from_birth author_id)
	sort author_id months_from_birth

	gen active_this_month = (total_month_tweets>0)

distinct author_id if active_this_month ==1
distinct author_id if months_from_birth == -18 & active_this_month == 1
distinct author_id if months_from_birth == 0 & active_this_month == 1
distinct author_id if months_from_birth == 17 & active_this_month == 1



collapse (mean) active_this_month, by(months_from_birth)
twoway line active_this_month months_from_birth, sort ///
    ytitle("Share active this month") ///
    xtitle("Months from birth") ///
	title("Extensive Margin - Monthly users") ///
	xline(0, lpattern(dash) lcolor(edkblue)) ///
	xlabel(-18(2)18) ///
	note("Sample size = 5,862 accounts")

graph export "$volume_figs/twt_behavior/extensive_margin.jpg", replace
restore



******* BY GENDER ********
preserve
	collapse (mean) total_month_tweets, by(months_from_birth author_id female)
	sort author_id months_from_birth
	gen active_this_month = (total_month_tweets>0)
	collapse (mean) active_this_month, by(months_from_birth female)
	
	twoway ///
		(line active_this_month months_from_birth if female==1, lcolor(red) sort) ///
		(line active_this_month months_from_birth if female==0, lcolor(blue) sort) ///
		, ytitle("Share active this month") ///
		xtitle("Months from birth") ///
		title("Extensive Margin - Monthly users") ///
		xline(0, lpattern(dash) lcolor(edkblue)) ///
		xlabel(-18(2)18) ///
		note("Sample size = 6,103 accounts, 45% female, 55% male") ///
		legend(order(1 2) label(1 "Female") label(2 "Male") position(2) ring(0))
	
	graph export "$volume_figs/twt_behavior/extensive_margin_GENDER.jpg", replace
restore




