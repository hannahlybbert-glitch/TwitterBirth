* ======================================================================================== *
* Author: Hannah Lybbert
* Created: 12/05/2025
* Purpose: All on same plot?


use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

gen pol_fam_flag = 0
replace pol_fam_flag = 1 if family >= 0.2
replace pol_fam_flag = 2 if news__social_concern >= 0.2

*---- Simple Politics by gender ----*
preserve
	* Collapse to month × gender
	collapse (mean) sentiment_score (sd) sd_compound = sentiment_score (count) n = sentiment_score, ///
		by(months_from_birth pol_fam_flag)
	* Compute SE and 95% CI
	gen se       = sd_compound / sqrt(n)
	gen ci_lower = sentiment_score - 1.96 * se
	gen ci_upper = sentiment_score + 1.96 * se
// 	* Female averages
// 	sum sentiment if female==1 & months_from_birth < 0
// 	local fem_pre_avg = r(mean)
// 	sum sentiment if female==1 & months_from_birth >= 0
// 	local fem_post_avg = r(mean)
// 	* Male averages
// 	sum sentiment if female==0 & months_from_birth < 0
// 	local male_pre_avg = r(mean)
// 	sum sentiment if female==0 & months_from_birth >= 0
// 	local male_post_avg = r(mean)

twoway ///
    (rcap ci_upper ci_lower months_from_birth if pol_fam_flag==1, lcolor(orange%50)) ///
    (line sentiment_score months_from_birth if pol_fam_flag==1, lcolor(orange) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if pol_fam_flag==2, lcolor(purple%50)) ///
    (line sentiment_score months_from_birth if pol_fam_flag==2, lcolor(purple) lwidth(medthick)) ///
    , ///
		xline(0, lpattern(dash) lcolor(edkblue%30)) ///
      xlabel(-18(2)18) ///
         ytitle("Average P(News & Social Concern)") ///
         xtitle("Months from Birth") ///
         title("Political Tweeting Aroung Birth by Gender") ///
		 note("Note: Birth announcement tweet excluded. Light line = pre-birth average. Darker line = post-birth average. 'News & Social Concern probability.", size(vsmall)) ///
      graphregion(color(white)) ///
      legend(order(2 "Family Sentiment"  ///
                   4 "Political Sentiment") ///
             position(4) ring(0))
// graph export "$politics_figs/politics_prob_gender_noBM.jpg", replace
// graph export "$politics_figs/politics_prob_gender.jpg", replace
restore