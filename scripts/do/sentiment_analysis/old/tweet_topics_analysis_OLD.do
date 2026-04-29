* Author: Hannah Lybbert
* Created: 11/18/2025
* Purpose: TweetNLP topics summary stats and basic figures

use "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN.dta", clear
// use "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN_noBM.dta", clear


* ---------- SUM STATS ----------- *
use "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN.dta", clear
	asdoc tab topic post_birth, replace ///
	save($tweetNLP_figs/topic_class/counts.doc)

* to csv
	preserve
		gen one = 1
		collapse (count) count = one, by(topic post_birth)
		reshape wide count, i(topic) j(post_birth)
	export delimited using "$tweetNLP_figs/topic_class/counts"
	restore

use "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN_noBM.dta", clear
	asdoc tab topic post_birth, replace ///
	save($tweetNLP_figs/topic_class/counts_noBM.doc)
		
	
*--------- FIGURES ----------*
use "$sentiment/output/tweetNLP/NLP_topics_Karthik.dta", clear

*---- Simple Family pre/post ----*
preserve
collapse (mean) family, by(week_from_birth)

	* Average family rating pre/post birth
	sum family if week_from_birth < 0
	local pre_birth_avg = r(mean)
	sum family if week_from_birth >= 0
	local post_birth_avg = r(mean)

** PLOT (total tweets)
twoway (line family week_from_birth, lwidth(medthick) lcolor(blue)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
	     yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
		 yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
         ytitle("Average Family-Orientation Score") ///
         xtitle("Weeks from Birth") ///
         title("Family-Orientation of Tweets Pre/Post Birth") ///
		 note("Birth announcement tweet excluded. Red = pre-birth avg; Green = post-birth avg") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78)
* Save graph
graph export "$tweetNLP_figs/topic_class/family_oriented.jpg", replace
restore



*---- Simple by gender ----*
use "$sentiment/output/tweetNLP/NLP_topics_Karthik.dta", clear
preserve
* Collapse to month × gender
collapse (mean) family (sd) sd_compound = family (count) n = family, ///
    by(months_from_birth female)

* Compute SE and 95% CI
gen se       = sd_compound / sqrt(n)
gen ci_lower = family - 1.96 * se
gen ci_upper = family + 1.96 * se

* Female averages
sum family if female==1 & months_from_birth < 0
local fem_pre_avg = r(mean)
sum family if female==1 & months_from_birth >= 0
local fem_post_avg = r(mean)

* Male averages
sum family if female==0 & months_from_birth < 0
local male_pre_avg = r(mean)
sum family if female==0 & months_from_birth >= 0
local male_post_avg = r(mean)

twoway ///
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(pink%50)) ///
    (line family months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%50)) ///
    (line family months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    , ///
    yline(`fem_pre_avg',  lcolor(red%30)  lpattern(dash)) ///
    yline(`fem_post_avg', lcolor(red%60)  lpattern(dash)) ///
    yline(`male_pre_avg', lcolor(blue%30) lpattern(dash)) ///
    yline(`male_post_avg', lcolor(blue%60) lpattern(dash)) ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth") ///
      ytitle("Average Family-Orientation Score") ///
      title("Family-Orientation of Tweets Pre/Post Birth by Gender") ///
	  note("Birth announcement tweet excluded. Light line = pre-birth avg; darker line = post-birth avg.") ///
      graphregion(color(white)) ///
      legend(order(2 "Female Avg"  ///
                   4 "Male Avg") ///
             position(2) ring(0))
graph export "$tweetNLP_figs/topic_class/family_prob_gender.jpg", replace
restore




* ------------ FIGURES no BIRTH MONTH ------------ *
// use "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN_noBM.dta", clear
use "$sentiment/output/tweetNLP/NLP_topics_Karthik_noBM.dta", clear

*---- Simple Family pre/post ----*
preserve
collapse (mean) family, by(week_from_birth)

	* Average family rating pre/post birth
	sum family if week_from_birth < 0
	local pre_birth_avg = r(mean)
	sum family if week_from_birth >= 0
	local post_birth_avg = r(mean)

** PLOT (total tweets)
twoway (line family week_from_birth, lwidth(medthick) lcolor(blue)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
	     yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
		 yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
         ytitle("Average Family-Orientation Score") ///
         xtitle("Weeks from Birth") ///
         title("Family-Orientation of Tweets Pre/Post Birth") ///
		 note("Tweets +/- 14 days from birth excluded. Red = pre-birth avg; Green = post-birth avg") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78)
* Save graph
graph export "$tweetNLP_figs/topic_class/family_oriented_noBM.jpg", replace
restore


*---- Simple by gender ----*
use "$sentiment/output/tweetNLP/NLP_topics_Karthik_noBM.dta", clear
preserve
* Collapse to month × gender
collapse (mean) family (sd) sd_compound = family (count) n = family, ///
    by(months_from_birth female)

* Compute SE and 95% CI
gen se       = sd_compound / sqrt(n)
gen ci_lower = family - 1.96 * se
gen ci_upper = family + 1.96 * se

* Female averages
sum family if female==1 & months_from_birth < 0
local fem_pre_avg = r(mean)
sum family if female==1 & months_from_birth >= 0
local fem_post_avg = r(mean)

* Male averages
sum family if female==0 & months_from_birth < 0
local male_pre_avg = r(mean)
sum family if female==0 & months_from_birth >= 0
local male_post_avg = r(mean)

twoway ///
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red)) ///
    (line family months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue)) ///
    (line family months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    , ///
    yline(`fem_pre_avg',  lcolor(red%30)  lpattern(dash)) ///
    yline(`fem_post_avg', lcolor(red%60)  lpattern(dash)) ///
    yline(`male_pre_avg', lcolor(blue%30) lpattern(dash)) ///
    yline(`male_post_avg', lcolor(blue%60) lpattern(dash)) ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth") ///
      ytitle("Average Family-Orientation Score") ///
      title("Family-Orientation of Tweets Pre/Post Birth by Gender") ///
	  note("Tweets +/- 14 days from birth excluded. Light line = pre-birth avg; darker line = post-birth avg.") ///
      graphregion(color(white)) ///
      legend(order(2 "Female Avg"  ///
                   4 "Male Avg") ///
             position(2) ring(0))
graph export "$tweetNLP_figs/topic_class/family_prob_gender_noBM.jpg", replace
restore




