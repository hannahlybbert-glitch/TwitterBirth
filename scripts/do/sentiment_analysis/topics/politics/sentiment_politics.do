* Author: Hannah Lybbert
* Created: 12/03/2025
* Purpose: Sentiment of Political tweets

* -------------------- sentiment of NEWS TWEETS pre/post ------------------------ *

use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear
// 	keep if topic == "news_&_social_concern"
	keep if news__social_concern >= 0.2
	
* --- SENTIMENT --- *
preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) sentiment_score (sd) sd_compound = sentiment_score (count) n = sentiment_score, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_compound / sqrt(n)
	gen ci_lower = sentiment_score - 1.96 * se
	gen ci_upper = sentiment_score + 1.96 * se
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy%60)) ///
    (line sentiment_score months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Sentiment") ///
		  label(1 "95% CI") ///
		  position(2) ring(0)) ///
      ytitle("Mean Sentiment of News Tweets") ///
      xtitle("Months from Birth") ///
      title("Sentiment of Political Tweets Around Birth") ///
      title("Sentiment of Family Related Tweets Around Birth") ///
	  note("Note: Birth tweet excluded. Analyzed on tweets where P(news & social concern) > 0.2, ~17% of all tweets from 4,093 accounts") ///
	  graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$politics_figs/sentiment/news_sentiment.jpg", replace
restore

preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) pos (sd) sd_compound = pos (count) n = pos, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_compound / sqrt(n)
	gen ci_lower = pos - 1.96 * se
	gen ci_upper = pos + 1.96 * se
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy%60)) ///
    (line pos months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Sentiment") ///
		  label(1 "95% CI") ///
		  position(2) ring(0)) ///
      ytitle("Mean Positivity of News Tweets") ///
      xtitle("Months from Birth") ///
      title("Positivity of Political Tweets Around Birth") ///
	  note("Note: Birth tweet excluded. Analyzed on tweets where P(news & social concern) > 0.2, ~17% of all tweets from 4,093 accounts") ///
	  graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$politics_figs/sentiment/news_positive.jpg", replace
restore

* --- negative - news --- *
preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) neg (sd) sd_compound = neg (count) n = neg, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_compound / sqrt(n)
	gen ci_lower = neg - 1.96 * se
	gen ci_upper = neg + 1.96 * se
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy%60)) ///
    (line neg months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Sentiment") ///
		  label(1 "95% CI") ///
		  position(2) ring(0)) ///
      ytitle("Mean Negativity of News Tweets") ///
      xtitle("Months from Birth") ///
      title("Negativity of Political Tweets Around Birth") ///
	  note("Note: Birth tweet excluded. Analyzed on tweets where P(news & social concern) > 0.2, ~17% of all tweets from 4,093 accounts") ///
	  graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$politics_figs/sentiment/news_negative.jpg", replace
restore


* ======================================= BY GENDER ======================================= *
use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear
	keep if news__social_concern >= 0.2

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
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(pink%30)) ///
    (line sentiment_score months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%30)) ///
    (line sentiment_score months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    , ///
      legend(order(2 "Female Avg" ///
                   4 "Male Avg") ///
             position(2) ring(0)) ///
      ytitle("Mean Sentiment of News Tweets") ///
      xtitle("Months from Birth") ///
      title("Sentiment of Political Tweets Around Birth by Gender") ///
	  note("Note: Birth tweet excluded. Base month = -1" ///
	  "Analyzed on tweets where P(news & social concern) > 0.2, ~17% of all tweets from 4,011 accounts. 42% female, 58% male") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$politics_figs/sentiment/news_sent_bygender.jpg", replace

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
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(pink%30)) ///
    (line pos months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%30)) ///
    (line pos months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    , ///
      legend(order(2 "Female Avg" ///
                   4 "Male Avg") ///
             position(1) ring(0)) ///
      ytitle("Mean Positivity of News Tweets") ///
      xtitle("Months from Birth") ///
      title("Positivity of Political Tweets Around Birth by Gender") ///
	  note("Note: Birth tweet excluded. Base month = -1" ///
	  "Analyzed on tweets where P(news & social concern) > 0.2, ~17% of all tweets from 4,011 accounts. 42% female, 58% male") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$politics_figs/sentiment/news_pos_bygender.jpg", replace

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
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(pink%30)) ///
    (line neg months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%30)) ///
    (line neg months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    , ///
      legend(order(2 "Female Avg" ///
                   4 "Male Avg") ///
             position(3) ring(0)) ///
      ytitle("Mean Negativity of News Tweets") ///
      xtitle("Months from Birth") ///
      title("Negativity of Political Tweets Around Birth by Gender") ///
	  note("Note: Birth tweet excluded. Base month = -1" ///
	  "Analyzed on tweets where P(news & social concern) > 0.2, ~17% of all tweets from 4,011 accounts. 42% female, 58% male") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$politics_figs/sentiment/news_neg_bygender.jpg", replace

restore
