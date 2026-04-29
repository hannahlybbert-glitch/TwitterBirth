* Author: Hannah Lybbert
* Created: 12/03/2025
* Purpose: Sentiment of sports tweets


* ------------------------ SENTIMENT of SPORTS TWEETS pre/post ------------------------ *
use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear
// 	keep if topic == "sports"
	keep if sports >= 0.5
	
* --- SENTIMENT  Sports --- *
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
		  position(2) ring(0)) ///
      ytitle("Mean Sentiment of Family Tweets") ///
      xtitle("Months from Birth") ///
      title("Family Related Tweet Sentiment Around Birth") ///
	  note("Note: Birth announcement tweet excluded. Red = pre-birth avg; Green = post-birth avg") ///
	  graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$sports_figs/sentiment/sports_sentiment.jpg", replace
restore


* --- Positive - Sports --- *
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
		  position(2) ring(0)) ///
      ytitle("Mean Positivity of Sports Tweets") ///
      xtitle("Months from Birth") ///
      title("Sports Tweet Positivity Around Birth") ///
	  note("Note: Birth announcement tweet excluded. Red = pre-birth avg; Green = post-birth avg") ///
	  graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$sports_figs/sentiment/sports_positive.jpg", replace
restore

* --- Negative Sports --- *
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
		  position(2) ring(0)) ///
      ytitle("Mean Negativity of Sports Tweets") ///
      xtitle("Months from Birth") ///
      title("Sports Tweets Negativity Around Birth") ///
	  note("Note: Birth announcement tweet excluded. Red = pre-birth avg; Green = post-birth avg") ///
	  graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$sports_figs/sentiment/sports_negative.jpg", replace
restore
