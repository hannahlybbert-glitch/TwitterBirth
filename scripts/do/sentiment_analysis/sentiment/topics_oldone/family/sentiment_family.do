* Author: Hannah Lybbert
* Created: 12/03/2025
* Purpose: Sentiment of Family tweets & sentiment with individual fixed effects


* ------------------------ SENTIMENT of FAMILY TWEETS pre/post ------------------------ *
// use "$sentiment/output/topic_sentiment_merge.dta", clear
use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear
// 	keep if family_flag == 1
	keep if family >= 0.5

* --- SENTIMENT --- *
preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) sentiment_score (sd) sd_compound = sentiment_score (count) n = sentiment_score, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_compound / sqrt(n)
	gen ci_lower = sentiment_score - 1.96 * se
	gen ci_upper = sentiment_score + 1.96 * se
	* Compute pre/post averages for dashed lines
	sum sentiment_score if months_from_birth < 0
	local pre_birth_avg = r(mean)
	sum sentiment_score if months_from_birth >= 0
	local post_birth_avg = r(mean)
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy%60)) ///
    (line sentiment_score months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
      yline(`pre_birth_avg', lcolor(red%30) lpattern(dash)) ///
      yline(`post_birth_avg', lcolor(green%30) lpattern(dash)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Sentiment") ///
		  label(1 "95% CI") ///
		  position(8) ring(0)) ///
      ytitle("Mean Sentiment of Family Tweets") ///
      xtitle("Months from Birth") ///
      title("Sentiment of Family Related Tweets Around Birth") ///
	  note("Note: Birth announcement tweet excluded. Family tweet if P(family) >= 0.5. Red = pre-birth avg; Green = post-birth avg. 135,402 tweets from 3,983 accts.", size(vsmall)) ///
	  graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$family_figs/sentiment/family_sentiment.jpg", replace
restore


* --- Positive - Family --- *
preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) pos (sd) sd_compound = pos (count) n = pos, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_compound / sqrt(n)
	gen ci_lower = pos - 1.96 * se
	gen ci_upper = pos + 1.96 * se
	* Compute pre/post averages for dashed lines
	sum pos if months_from_birth < 0
	local pre_birth_avg = r(mean)
	sum pos if months_from_birth >= 0
	local post_birth_avg = r(mean)
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy%60)) ///
    (line pos months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
      yline(`pre_birth_avg', lcolor(red%30) lpattern(dash)) ///
      yline(`post_birth_avg', lcolor(green%30) lpattern(dash)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Sentiment") ///
		  label(1 "95% CI") ///
		  position(7) ring(0)) ///
      ytitle("Mean Positivity of Family Tweets") ///
      xtitle("Months from Birth") ///
      title("Positivity of Family Related Tweets Around Birth") ///
	  note("Note: Birth announcement tweet excluded. 'Family tweet' if P(family) >= 0.5. Red = pre-birth avg; Green = post-birth avg. 135,402 tweets from 3,983 accts.", size(vsmall)) ///
	  graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$family_figs/sentiment/family_positive.jpg", replace
restore



* --- Negative Family --- *
preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) neg (sd) sd_compound = neg (count) n = neg, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_compound / sqrt(n)
	gen ci_lower = neg - 1.96 * se
	gen ci_upper = neg + 1.96 * se
	* Compute pre/post averages for dashed lines
	sum neg if months_from_birth < 0
	local pre_birth_avg = r(mean)
	sum neg if months_from_birth >= 0
	local post_birth_avg = r(mean)
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy%60)) ///
    (line neg months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
      yline(`pre_birth_avg', lcolor(red%30) lpattern(dash)) ///
      yline(`post_birth_avg', lcolor(green%30) lpattern(dash)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Sentiment") ///
		  label(1 "95% CI") ///
		  position(11) ring(0)) ///
      ytitle("Mean Negativity of Family Tweets") ///
      xtitle("Months from Birth") ///
      title("Negativity of Family Related Tweets Around Birth") ///
	  note("Note: Birth announcement tweet excluded. 'Family tweet' if P(family) >= 0.5. Red = pre-birth avg; Green = post-birth avg. 135,402 tweets from 3,983 accts.", size(vsmall)) ///
	  graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$family_figs/sentiment/family_negative.jpg", replace
restore


* ======================================= BY GENDER ======================================= *
use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear
	keep if family >= 0.5

*** SENTIMENT ***
preserve
	* Collapse to mean/sd/count by month AND gender
	collapse (mean) sentiment_score (sd) sd_compound = sentiment_score (count) n = sentiment_score, by(female months_from_birth)

	* Standard errors + 95% CI
	gen se = sd_compound / sqrt(n)
	gen ci_lower = sentiment_score - 1.96 * se
	gen ci_upper = sentiment_score + 1.96 * se

* Plot female vs male on same figure
twoway /// 
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(pink%60)) ///
    (line sentiment_score months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%60)) ///
    (line sentiment_score months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    , ///
      legend(order(2 "Female Avg" ///
                   4 "Male Avg") ///
             position(8) ring(0)) ///
      ytitle("Mean Sentiment of Family Tweets") ///
      xtitle("Months from Birth") ///
      title("Sentiment of Family Related Tweets Around Birth by Gender") ///
	  note("Note: Birth announcement tweet excluded. 95% CI. Family tweet if P(family) >= 0.5. 135,402 tweets from 3,983 accts.") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$family_figs/sentiment/family_sent_bygender.jpg", replace

restore


*** POSITIVITY ***
preserve
	* Collapse to mean/sd/count by month AND gender
	collapse (mean) pos (sd) sd_compound = pos (count) n = pos, by(female months_from_birth)

	* Standard errors + 95% CI
	gen se = sd_compound / sqrt(n)
	gen ci_lower = pos - 1.96 * se
	gen ci_upper = pos + 1.96 * se

* Plot female vs male on same figure
twoway /// 
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(pink%60)) ///
    (line pos months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%60)) ///
    (line pos months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    , ///
      legend(order(2 "Female Avg" ///
                   4 "Male Avg") ///
             position(1) ring(0)) ///
      ytitle("Mean Positivity of Family Tweets") ///
      xtitle("Months from Birth") ///
      title("Positivity of Family Related Tweets Around Birth by Gender") ///
	  note("Note: Birth announcement tweet excluded. 95% CI. Family tweet if P(family) >= 0.5. 135,402 tweets from 3,983 accts.") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$family_figs/sentiment/family_pos_bygender.jpg", replace

restore



*** NEGATIVITY ***
preserve
	* Collapse to mean/sd/count by month AND gender
	collapse (mean) neg (sd) sd_compound = neg (count) n = neg, by(female months_from_birth)

	* Standard errors + 95% CI
	gen se = sd_compound / sqrt(n)
	gen ci_lower = neg - 1.96 * se
	gen ci_upper = neg + 1.96 * se

* Plot female vs male on same figure
twoway /// 
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(pink%60)) ///
    (line neg months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%60)) ///
    (line neg months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    , ///
      legend(order(2 "Female Avg" ///
                   4 "Male Avg") ///
             position(2) ring(0)) ///
      ytitle("Mean Negativity of Family Tweets") ///
      xtitle("Months from Birth") ///
      title("Negativity of Family Related Tweets Around Birth by Gender") ///
	  note("Note: Birth announcement tweet excluded. 95% CI. Family tweet if P(family) >= 0.5. 135,402 tweets from 3,983 accts.") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$family_figs/sentiment/family_neg_bygender.jpg", replace

restore