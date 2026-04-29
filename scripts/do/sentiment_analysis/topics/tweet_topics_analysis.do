* Author: Hannah Lybbert
* Created: 11/17/2025
* Purpose: Probability tweets for family, politics, and sports related around birth (simple and by gender) --> Inital Event Study

** Tweet NLP analysis **


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
	

	
*------------------------------------ FIGURES ----------------------------------- *
// use "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN.dta", clear
use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

* 					============= FAMILY ================ *
*---- Simple Family pre/post ----*
preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) family (sd) sd_compound = family (count) n = family, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_compound / sqrt(n)
	gen ci_lower = family - 1.96 * se
	gen ci_upper = family + 1.96 * se


** PLOT (total tweets)
twoway (rcap ci_upper ci_lower months_from_birth, lcolor(navy%50)) ///
    (line family months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg P(family)") ///
		  label(1 "95% CI") ///
		  position(2) ring(0)) ///
         ytitle("Average P(Family-Related Tweet)") ///
         xtitle("Months from Birth") ///
         title("Family-Related Tweeting Aroung Birth") ///
		 note("Note: Birth announcement tweet excluded. 'Family' probability.") ///
         graphregion(color(white)) ///
         xlabel(-18(2)18)
* Save graph
graph export "$family_figs/family_oriented.jpg", replace
restore


*---- Simple Family by gender ----*
preserve
	* Collapse to month × gender
	collapse (mean) family (sd) sd_compound = family (count) n = family, ///
		by(months_from_birth female)
	* Compute SE and 95% CI
	gen se       = sd_compound / sqrt(n)
	gen ci_lower = family - 1.96 * se
	gen ci_upper = family + 1.96 * se

twoway ///
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(pink%50)) ///
    (line family months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%50)) ///
    (line family months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
		, xline(0, lpattern(dash) lcolor(edkblue%30)) ///
      xlabel(-18(2)18) ///
         ytitle("Average P(Family-Related Tweet)") ///
         xtitle("Months from Birth") ///
         title("Family-Related Tweeting Aroung Birth by Gender") ///
		 note("Note: Birth announcement tweet excluded. 'Family' probability.") ///
      graphregion(color(white)) ///
      legend(order(2 "Female Avg"  ///
                   4 "Male Avg") ///
             position(2) ring(0))
// graph export "$family_figs/family_prob_gender_noBM.jpg", replace
graph export "$family_figs/family_prob_gender.jpg", replace
restore


* 							============= POLITICS ================ *
*---- Simple Politics pre/post ----*
preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) news__social_concern (sd) sd_compound = news__social_concern (count) n = news__social_concern, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_compound / sqrt(n)
	gen ci_lower = news__social_concern - 1.96 * se
	gen ci_upper = news__social_concern + 1.96 * se

** PLOT (total tweets)
twoway (rcap ci_upper ci_lower months_from_birth, lcolor(navy%50)) ///
    (line news__social_concern months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg P(political)") ///
		  label(1 "95% CI") ///
		  position(4) ring(0)) ///
         ytitle("Average P(News & Social Concern)") ///
         xtitle("Months from Birth") ///
         title("Political Tweeting Aroung Birth") ///
		 note("Note: Birth announcement tweet excluded. 'news & social concern' probability.") ///
         graphregion(color(white)) ///
         xlabel(-18(2)18)
* Save graph
graph export "$politics_figs/political_tweets_cnts.jpg", replace
restore


*---- Simple Politics by gender ----*
preserve
	* Collapse to month × gender
	collapse (mean) news__social_concern (sd) sd_compound = news__social_concern (count) n = news__social_concern, ///
		by(months_from_birth female)
	* Compute SE and 95% CI
	gen se       = sd_compound / sqrt(n)
	gen ci_lower = news__social_concern - 1.96 * se
	gen ci_upper = news__social_concern + 1.96 * se

twoway ///
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(pink%50)) ///
    (line news__social_concern months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%50)) ///
    (line news__social_concern months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    , ///
		xline(0, lpattern(dash) lcolor(edkblue%30)) ///
      xlabel(-18(2)18) ///
         ytitle("Average P(News & Social Concern)") ///
         xtitle("Months from Birth") ///
         title("Political Tweeting Aroung Birth by Gender") ///
		 note("Note: Birth announcement tweet excluded. 'news & social concern' probability.") ///
      graphregion(color(white)) ///
      legend(order(2 "Female Avg"  ///
                   4 "Male Avg") ///
             position(4) ring(0))
// graph export "$politics_figs/politics_prob_gender_noBM.jpg", replace
graph export "$politics_figs/politics_prob_gender.jpg", replace
restore


* 							============= SPORTS ================ *
*---- Simple Sports pre/post ----*
preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) sports (sd) sd_compound = sports (count) n = sports, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_compound / sqrt(n)
	gen ci_lower = sports - 1.96 * se
	gen ci_upper = sports + 1.96 * se

** PLOT (total tweets)
twoway (rcap ci_upper ci_lower months_from_birth, lcolor(navy%50)) ///
    (line sports months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Sentiment") ///
		  label(1 "95% CI") ///
		  position(4) ring(0)) ///
         ytitle("Average P(Sports) Tweet") ///
         xtitle("Months from Birth") ///
         title("Sports Tweeting Aroung Birth") ///
		 note("Note: Birth announcement tweet excluded. 'Sports' probability.") ///
         graphregion(color(white)) ///
         xlabel(-18(2)18)
* Save graph
graph export "$sports_figs/sports_tweets_cnts.jpg", replace
restore


*---- Simple Sports by gender ----*
preserve
	* Collapse to month × gender
	collapse (mean) sports (sd) sd_compound = sports (count) n = sports, ///
		by(months_from_birth female)
	* Compute SE and 95% CI
	gen se       = sd_compound / sqrt(n)
	gen ci_lower = sports - 1.96 * se
	gen ci_upper = sports + 1.96 * se

twoway ///
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(pink%50)) ///
    (line sports months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%50)) ///
    (line sports months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    , ///
		xline(0, lpattern(dash) lcolor(edkblue%30)) ///
      xlabel(-18(2)18) ///
         ytitle("Average P(Sports) Tweet") ///
         xtitle("Months from Birth") ///
         title("Sports Tweeting Aroung Birth by Gender") ///
		 note("Note: Birth announcement tweet excluded. 'Sports' probability.") ///
      graphregion(color(white)) ///
      legend(order(2 "Female Avg"  ///
                   4 "Male Avg") ///
             position(3) ring(0))
// graph export "$sports_figs/sports_prob_gender_noBM.jpg", replace
graph export "$sports_figs/sports_prob_gender.jpg", replace
restore

