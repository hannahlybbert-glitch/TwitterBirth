******** SENTIMENT ANALYSIS ********
* Author: Hannah Lybbert
* Created: 
* Purpose: Preliminary Figures for sentiment analysis

*----------------- CONFIDENCE INTERVAL (no BA) -----------------*
use "$sentiment/output/sentiment_scoresFULL_clean.dta", clear

preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) sentiment_score (sd) sd_compound = sentiment_score (count) n = sentiment_score, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_compound / sqrt(n)
	gen ci_lower = sentiment_score - 1.96 * se
	gen ci_upper = sentiment_score + 1.96 * se

twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
    (line sentiment_score months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Sentiment") ///
		  label(1 "95% CI") ///
		  position(2) ring(0)) ///
      ytitle("Mean Sentiment") ///
      xtitle("Months from Birth") ///
      title("Tweet Sentiment Around Birth") ///
	  note("Note: Birth announcement tweet excluded." ///
	  "Dropped months where total month tweets for the account were > 95th percentile." ///
	  "Sentiment score = positive score - negative score." ///
	  "Sample size = 4,145 accounts") ///
	  graphregion(color(white)) ///
	  ylabel(0.30(0.02)0.40) ///
      xlabel(-18(2)18)
graph export "$tweetNLP_figs/simple_sentiment/sentiment_score95CI.jpg", replace
restore
	
** Positive 
preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) pos (sd) sd_compound = pos (count) n = pos, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_compound / sqrt(n)
	gen ci_lower = pos - 1.96 * se
	gen ci_upper = pos + 1.96 * se
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
    (line pos months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Positivity") ///
		  label(1 "95% CI") ///
		  position(4) ring(0)) ///
      ytitle("Mean Positivity") ///
      xtitle("Months from Birth") ///
      title("Tweet Positivity Around Birth") ///
	  note("Note: Birth announcement tweet excluded." ///
	  "Dropped months where total month tweets for the account were > 95th percentile." ///
	  "Sample size = 4,145 accounts") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18) 
graph export "$tweetNLP_figs/simple_sentiment/pos_score95CI.jpg", replace
restore

** NEGATIVE
preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) neg (sd) sd_compound = neg (count) n = neg, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_compound / sqrt(n)
	gen ci_lower = neg - 1.96 * se
	gen ci_upper = neg + 1.96 * se
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
    (line neg months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Negativity") ///
		  label(1 "95% CI") ///
		  position(2) ring(0)) ///
      ytitle("Mean Negativity") ///
      xtitle("Months from Birth") ///
      title("Tweet Negativity Around Birth") ///
	  note("Note: Birth announcement tweet excluded." ///
	  "Dropped months where total month tweets for the account were > 95th percentile." ///
	  "Sample size = 4,145 accounts") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18) 
graph export "$tweetNLP_figs/simple_sentiment/neg_score95CI.jpg", replace
restore



* ---------------------------------------------------------------------------------------------- *



*----------------- BY GENDER -----------------*
use "$sentiment/output/sentiment_scoresFULL_clean.dta", clear

* 1. Sentiment score
preserve
* Collapse to mean/sd/count by month AND gender
collapse (mean) sentiment_score (sd) sd_compound = sentiment_score (count) n = sentiment_score, by(female months_from_birth)

* Standard errors + 95% CI
gen se = sd_compound / sqrt(n)
gen ci_lower = sentiment_score - 1.96 * se
gen ci_upper = sentiment_score + 1.96 * se

* Plot female vs male on same figure
twoway /// 
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red)) ///
    (line sentiment_score months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue)) ///
    (line sentiment_score months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    , ///
      legend(order(2 "Female Avg" ///
                   4 "Male Avg") ///
             position(4) ring(0)) ///
      ytitle("Avg Sentiment") ///
      xtitle("Months from Birth") ///
      title("Tweet Sentiment Pre/Post Birth by Gender") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18) ///
	  note("Note: Birth announcement tweet excluded. Sentiment = Positive - Negative scores" ///
	  "Dropped months where total month tweets for the account were > 95th percentile." ///
	  "Sample size = 4,017 accounts, 42% female, 58% male")
graph export "$tweetNLP_figs/gender/sentiment_gender.jpg", replace
restore


*2. Positivity pre/post male/female ***
preserve
* Collapse to month × gender
collapse (mean) pos (sd) sd_compound = pos (count) n = pos, ///
    by(months_from_birth female)

* Compute SE and 95% CI
gen se       = sd_compound / sqrt(n)
gen ci_lower = pos - 1.96 * se
gen ci_upper = pos + 1.96 * se

twoway ///
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red)) ///
    (line pos months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue)) ///
    (line pos months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    , ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth") ///
      ytitle("Average Positivity") ///
      title("Tweet Positivity Around Birth by Gender") ///
	  note("Note: Birth announcement tweet excluded." ///
	  "Dropped months where total month tweets for the account were > 95th percentile." ///
	  "Sample size = 4,017 accounts, 42% female, 58% male") ///
      graphregion(color(white)) ///
      legend(order(2 "Female Avg" 4 "Male Avg") ///
             position(2) ring(0))
graph export "$tweetNLP_figs/gender/pos_gender.jpg", replace
restore



*3. Negativity pre/post male/female ***
preserve
* Collapse to month × gender
collapse (mean) neg (sd) sd_compound = neg (count) n = neg, ///
    by(months_from_birth female)

* Compute SE and 95% CI
gen se       = sd_compound / sqrt(n)
gen ci_lower = neg - 1.96 * se
gen ci_upper = neg + 1.96 * se

twoway ///
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red)) ///
    (line neg months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue)) ///
    (line neg months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    , ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth") ///
      ytitle("Average Negativity") ///
      title("Tweet Negativity Around Birth by Gender") ///
	  note("Note: Birth announcement tweet excluded." ///
	  "Dropped months where total month tweets for the account were > 95th percentile." ///
	  "Sample size = 4,017 accounts, 42% female, 58% male") ///
      graphregion(color(white)) ///
      legend(order(2 "Female Avg" 4 "Male Avg") ///
             position(2) ring(0))
graph export "$tweetNLP_figs/gender/neg_gender.jpg", replace
restore




* ONE DEVIN WANTED ME TO TRY 1/9/2026 (averaged by month and account)
use "$sentiment/output/sentiment_scoresFULL_clean.dta", clear

preserve
	
	* CHANGE 1: First collapse to mean by author_id and months_from_birth
	collapse (mean) sentiment_score, by(author_id months_from_birth)
	
	* CHANGE 2: Then collapse to mean and standard deviation by months_from_birth
	collapse (mean) sentiment_score (sd) sd_compound = sentiment_score (count) n = sentiment_score, by(months_from_birth)
	
	* Standard error and 95% confidence intervals
	gen se = sd_compound / sqrt(n)
	gen ci_lower = sentiment_score - 1.96 * se
	gen ci_upper = sentiment_score + 1.96 * se

twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
    (line sentiment_score months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Sentiment") ///
		  label(1 "95% CI") ///
		  position(2) ring(0)) ///
      ytitle("Mean Sentiment") ///
      xtitle("Months from Birth") ///
      title("Tweet Sentiment Around Birth (Averaged by Month & Account)") ///
	  note("Note: Birth announcement tweet excluded. Averaged by account and month" ///
	  "Dropped months where total month tweets for the account were > 95th percentile." ///
	  "Sentiment score = positive score - negative score." ///
	  "Sample size = 4,145 accounts") ///
	  graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$tweetNLP_figs/simple_sentiment/sent_score_avgMO_ACCT.jpg", replace
restore



* -------------------------------- END ----------------------------------- *





* -------------- Same graphs as above but with pre/post averages -------------- *
// *** Averages pre/post male/female ***
// preserve
// * Collapse to month × gender
// collapse (mean) sentiment_score (sd) sd_compound = sentiment_score (count) n = sentiment_score, ///
//     by(months_from_birth female)
//
// * Compute SE and 95% CI
// gen se       = sd_compound / sqrt(n)
// gen ci_lower = sentiment_score - 1.96 * se
// gen ci_upper = sentiment_score + 1.96 * se
//
// * Female averages
// sum sentiment_score if female==1 & months_from_birth < 0
// local fem_pre_avg = r(mean)
// sum sentiment_score if female==1 & months_from_birth >= 0
// local fem_post_avg = r(mean)
//
// * Male averages
// sum sentiment_score if female==0 & months_from_birth < 0
// local male_pre_avg = r(mean)
// sum sentiment_score if female==0 & months_from_birth >= 0
// local male_post_avg = r(mean)
//
// twoway ///
//     (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red)) ///
//     (line sentiment_score months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
//     (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue)) ///
//     (line sentiment_score months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
//     , ///
// 		yline(`fem_pre_avg',  lcolor(red%30)  lpattern(dash)) ///
// 		yline(`fem_post_avg', lcolor(red%60)  lpattern(dash)) ///
// 		yline(`male_pre_avg', lcolor(blue%30) lpattern(dash)) ///
// 		yline(`male_post_avg', lcolor(blue%60) lpattern(dash)) ///
//       xlabel(-18(2)18) ///
//       xtitle("Months from Birth") ///
//       ytitle("Average Sentiment") ///
//       title("Tweet Sentiment Around Birth by Gender") ///
// 	  note("Note: 95% CI. Light lines = pre average. Dark lines = post average. Sentiment score = positive-negative") ///
//       graphregion(color(white)) ///
//       legend(order(2 "Female Avg"  ///
//                    4 "Male Avg") ///
//              position(2) ring(0))
// graph export "$tweetNLP_figs/gender/sent_score_gender.jpg", replace
// // graph export "$tweetNLP_figs/gender/sent_score_gender_noBM.jpg", replace
// restore
//
//
// *** Positivity pre/post male/female ***
// preserve
// * Collapse to month × gender
// collapse (mean) pos (sd) sd_compound = pos (count) n = pos, ///
//     by(months_from_birth female)
//
// * Compute SE and 95% CI
// gen se       = sd_compound / sqrt(n)
// gen ci_lower = pos - 1.96 * se
// gen ci_upper = pos + 1.96 * se
//
// * Female averages
// sum pos if female==1 & months_from_birth < 0
// local fem_pre_avg = r(mean)
// sum pos if female==1 & months_from_birth >= 0
// local fem_post_avg = r(mean)
//
// * Male averages
// sum pos if female==0 & months_from_birth < 0
// local male_pre_avg = r(mean)
// sum pos if female==0 & months_from_birth >= 0
// local male_post_avg = r(mean)
//
// twoway ///
//     (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red)) ///
//     (line pos months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
//     (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue)) ///
//     (line pos months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
//     , ///
// 		yline(`fem_pre_avg',  lcolor(red%30)  lpattern(dash)) ///
// 		yline(`fem_post_avg', lcolor(red%60)  lpattern(dash)) ///
// 		yline(`male_pre_avg', lcolor(blue%30) lpattern(dash)) ///
// 		yline(`male_post_avg', lcolor(blue%60) lpattern(dash)) ///
//       xlabel(-18(2)18) ///
//       xtitle("Months from Birth") ///
//       ytitle("Average Positivity") ///
//       title("Tweet Positivity Around Birth by Gender") ///
// 	  note("Note: 95% CI. Light lines = pre-birth average. Dark lines = post-birth average.") ///
//       graphregion(color(white)) ///
//       legend(order(2 "Female Avg"  ///
//                    4 "Male Avg") ///
//              position(2) ring(0))
// graph export "$tweetNLP_figs/gender/pos_gender.jpg", replace
// // graph export "$tweetNLP_figs/gender/pos_gender_noBM.jpg", replace
// restore
//
//
//
// *** Negativity pre/post male/female ***
// preserve
// * Collapse to month × gender
// collapse (mean) neg (sd) sd_compound = neg (count) n = neg, ///
//     by(months_from_birth female)
//
// * Compute SE and 95% CI
// gen se       = sd_compound / sqrt(n)
// gen ci_lower = neg - 1.96 * se
// gen ci_upper = neg + 1.96 * se
//
// * Female averages
// sum neg if female==1 & months_from_birth < 0
// local fem_pre_avg = r(mean)
// sum neg if female==1 & months_from_birth >= 0
// local fem_post_avg = r(mean)
//
// * Male averages
// sum neg if female==0 & months_from_birth < 0
// local male_pre_avg = r(mean)
// sum neg if female==0 & months_from_birth >= 0
// local male_post_avg = r(mean)
//
// twoway ///
//     (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red)) ///
//     (line neg months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
//     (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue)) ///
//     (line neg months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
//     , ///
// 		yline(`fem_pre_avg',  lcolor(red%30)  lpattern(dash)) ///
// 		yline(`fem_post_avg', lcolor(red%60)  lpattern(dash)) ///
// 		yline(`male_pre_avg', lcolor(blue%30) lpattern(dash)) ///
// 		yline(`male_post_avg', lcolor(blue%60) lpattern(dash)) ///
//       xlabel(-18(2)18) ///
//       xtitle("Months from Birth") ///
//       ytitle("Average Negativity") ///
//       title("Tweet Negativity Around Birth by Gender") ///
// 	  note("Note: 95% CI. Light lines = pre-birth average. Dark lines = post-birth average.") ///
//       graphregion(color(white)) ///
//       legend(order(2 "Female Avg"  ///
//                    4 "Male Avg") ///
//              position(2) ring(0))
// graph export "$tweetNLP_figs/gender/neg_gender.jpg", replace
// // graph export "$tweetNLP_figs/gender/neg_gender_noBM.jpg", replace
// restore


// *** Neutrality pre/post male/female ***
// preserve
// 	* Collapse to month × gender
// 	collapse (mean) neu (sd) sd_compound = neu (count) n = neu, ///
// 		by(months_from_birth female)
//
// 	* Compute SE and 95% CI
// 	gen se       = sd_compound / sqrt(n)
// 	gen ci_lower = neu - 1.96 * se
// 	gen ci_upper = neu + 1.96 * se
//
// 	* Female averages
// 	sum neu if female==1 & months_from_birth < 0
// 	local fem_pre_avg = r(mean)
// 	sum neu if female==1 & months_from_birth >= 0
// 	local fem_post_avg = r(mean)
//
// 	* Male averages
// 	sum neu if female==0 & months_from_birth < 0
// 	local male_pre_avg = r(mean)
// 	sum neu if female==0 & months_from_birth >= 0
// 	local male_post_avg = r(mean)
//
// twoway ///
//     (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red)) ///
//     (line neu months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
//     (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue)) ///
//     (line neu months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
//     , ///
// 		yline(`fem_pre_avg',  lcolor(red%30)  lpattern(dash)) ///
// 		yline(`fem_post_avg', lcolor(red%60)  lpattern(dash)) ///
// 		yline(`male_pre_avg', lcolor(blue%30) lpattern(dash)) ///
// 		yline(`male_post_avg', lcolor(blue%60) lpattern(dash)) ///
//       xlabel(-18(2)18) ///
//       xtitle("Months from Birth") ///
//       ytitle("Average Neutrality") ///
//       title("Tweet Neutrality Around Birth by Gender") ///
// 	  note("Note: 95% CI. Light lines = pre-birth average. Dark lines = post-birth average.") ///
//       graphregion(color(white)) ///
//       legend(order(2 "Female Avg"  ///
//                    4 "Male Avg") ///
//              position(2) ring(0))
// graph export "$tweetNLP_figs/gender/neu_gender.jpg", replace
// // graph export "$tweetNLP_figs/gender/neu_gender_noBM.jpg", replace
// restore



* ---------------------- OLD ----------------------------- *

// *----------------- CONFIDENCE INTERVAL (no BIRTH MONTH)) -----------------*
// use "$sentiment/output/sentiment_scores_1modrop.dta", clear
//
// preserve
// 	* Collapse to mean and standard deviation by month
// 	collapse (mean) sentiment_score (sd) sd_compound = sentiment_score (count) n = sentiment_score, by(months_from_birth)
// 	* Standard error and 95% confidence intervals
// 	gen se = sd_compound / sqrt(n)
// 	gen ci_lower = sentiment_score - 1.96 * se
// 	gen ci_upper = sentiment_score + 1.96 * se
// 	* Compute pre/post averages for dashed lines
// 	sum sentiment_score if months_from_birth < 0
// 	local pre_birth_avg = r(mean)
// 	sum sentiment_score if months_from_birth >= 0
// 	local post_birth_avg = r(mean)
// twoway ///
//     (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
//     (line sentiment_score months_from_birth, lwidth(medthick) lcolor(blue)) ///
//     , xline(0, lpattern(dash) lcolor(edkblue)) ///
//       yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
//       yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
// 	  legend(order(2 1 3 4) ///
// 		  label(2 "Avg Sentiment") ///
// 		  label(1 "95% CI") ///
// 		  position(4) ring(0)) ///
//       ytitle("Avg Sentiment") ///
//       xtitle("Months from Birth") ///
//       title("Average Tweet Sentiment Around Birth") ///
// 	  note("Note: Tweets +/- 14 days from birth excluded. Sentiment score = pos - neg. Red = pre birth avg; Green = post birth avg") ///
// 	  graphregion(color(white)) ///
//       xlabel(-18(2)18) 
// graph export "$tweetNLP_figs/simple_sentiment/noBM/sentiment_score95CI_noBM.jpg", replace
// restore
//	
// ** Positive 
// preserve
// 	* Collapse to mean and standard deviation by month
// 	collapse (mean) pos (sd) sd_compound = pos (count) n = pos, by(months_from_birth)
// 	* Standard error and 95% confidence intervals
// 	gen se = sd_compound / sqrt(n)
// 	gen ci_lower = pos - 1.96 * se
// 	gen ci_upper = pos + 1.96 * se
// 	* Compute pre/post averages for dashed lines
// 	sum pos if months_from_birth < 0
// 	local pre_birth_avg = r(mean)
// 	sum pos if months_from_birth >= 0
// 	local post_birth_avg = r(mean)
// twoway ///
//     (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
//     (line pos months_from_birth, lwidth(medthick) lcolor(blue)) ///
//     , xline(0, lpattern(dash) lcolor(edkblue)) ///
//       yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
//       yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
// 	  legend(order(2 1 3 4) ///
// 		  label(2 "Avg Positivity") ///
// 		  label(1 "95% CI") ///
// 		  position(4) ring(0)) ///
//       ytitle("Average Positivity") ///
//       xtitle("Months from Birth") ///
//       title("Average Tweet Positivity Around Birth") ///
//   	  note("Note: Tweets +/- 14 days from birth excluded. Red = pre birth avg; Green = post birth avg") ///
//       graphregion(color(white)) ///
//       xlabel(-18(2)18) 
// graph export "$tweetNLP_figs/simple_sentiment/noBM/pos_score95CI_noBM.jpg", replace
// restore
//
// ** NEGATIVE
// preserve
// 	* Collapse to mean and standard deviation by month
// 	collapse (mean) neg (sd) sd_compound = neg (count) n = neg, by(months_from_birth)
// 	* Standard error and 95% confidence intervals
// 	gen se = sd_compound / sqrt(n)
// 	gen ci_lower = neg - 1.96 * se
// 	gen ci_upper = neg + 1.96 * se
// 	* Compute pre/post averages for dashed lines
// 	sum neg if months_from_birth < 0
// 	local pre_birth_avg = r(mean)
// 	sum neg if months_from_birth >= 0
// 	local post_birth_avg = r(mean)
// twoway ///
//     (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
//     (line neg months_from_birth, lwidth(medthick) lcolor(blue)) ///
//     , xline(0, lpattern(dash) lcolor(edkblue)) ///
//       yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
//       yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
// 	  legend(order(2 1 3 4) ///
// 		  label(2 "Avg Negativity") ///
// 		  label(1 "95% CI") ///
// 		  position(2) ring(0)) ///
//       ytitle("Average Negativity") ///
//       xtitle("Months from Birth") ///
//       title("Average Tweet Negativity Around Birth") ///
// 	  note("Note: Tweets +/- 14 days from birth excluded. Red = pre birth avg; Green = post birth avg") ///
//       graphregion(color(white)) ///
//       xlabel(-18(2)18) 
// graph export "$tweetNLP_figs/simple_sentiment/noBM/neg_score95CI_noBM.jpg", replace
// restore
//
// ** NEUTRAL
// preserve
// 	* Collapse to mean and standard deviation by month
// 	collapse (mean) neu (sd) sd_compound = neu (count) n = neu, by(months_from_birth)
// 	* Standard error and 95% confidence intervals
// 	gen se = sd_compound / sqrt(n)
// 	gen ci_lower = neu - 1.96 * se
// 	gen ci_upper = neu + 1.96 * se
// 	* Compute pre/post averages for dashed lines
// 	sum neu if months_from_birth < 0
// 	local pre_birth_avg = r(mean)
// 	sum neu if months_from_birth >= 0
// 	local post_birth_avg = r(mean)
// twoway ///
//     (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
//     (line neu months_from_birth, lwidth(medthick) lcolor(blue)) ///
//     , xline(0, lpattern(dash) lcolor(edkblue)) ///
//       yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
//       yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
// 	  legend(order(2 1 3 4) ///
// 		  label(2 "Avg Neutrality") ///
// 		  label(1 "95% CI") ///
// 		  position(2) ring(0)) ///
//       ytitle("Average Neutrality") ///
//       xtitle("Months from Birth") ///
//       title("Average Tweet Neutrality Around Birth") ///
// 	  note("Note: Tweets +/- 14 days from birth excluded. Red = pre birth avg; Green = post birth avg") ///
//       graphregion(color(white)) ///
//       xlabel(-18(2)18) 
// graph export "$tweetNLP_figs/simple_sentiment/noBM/neu_score95CI_noBM.jpg", replace
// restore




// * --------------- Line Chart --------------- *
// use "$sentiment/output/sentiment_analysis_sample.dta", clear
//
// ** Simple Sentiment pre/post (MONTH)
// preserve
// collapse (mean) sentiment_score, by(months_from_birth)
//
// 	* Average family rating pre/post birth
// 	sum sentiment_score if months_from_birth < 0
// 	local pre_birth_avg = r(mean)
// 	sum sentiment_score if months_from_birth >= 0
// 	local post_birth_avg = r(mean)
//
// ** PLOT (total tweets)
// twoway (line sentiment_score months_from_birth, lwidth(medthick) lcolor(blue)) ///
//        , xline(0, lpattern(dash) lcolor(edkblue)) ///
// 	     yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
// 		 yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
//          ytitle("Mean Sentiment (Positive - Negative)") ///
//          xtitle("Months from Birth") ///
//          title("Tweet Sentiment Around Birth") ///
//          graphregion(color(white)) ///
// 		 note("Note: Birth announcement tweet excluded. Red line = pre-birth average. Green line = post-birth average.") ///
//          xlabel(-18(2)18)
// * Save graph
// graph export "$tweetNLP_figs/simple_sentiment/sentiment_score.jpg", replace
// restore


// ** Simple Sentiment pre/post LINE GRAPH  - by WEEK
// preserve
// collapse (mean) sentiment_score, by(week_from_birth)
//
// 	* Average family rating pre/post birth
// 	sum sentiment_score if week_from_birth < 0
// 	local pre_birth_avg = r(mean)
// 	sum sentiment_score if week_from_birth >= 0
// 	local post_birth_avg = r(mean)
//
// ** PLOT (total tweets)
// twoway (line sentiment_score week_from_birth, lwidth(medthick) lcolor(blue)) ///
//        , xline(0, lpattern(dash) lcolor(edkblue)) ///
// 	     yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
// 		 yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
//          ytitle("Mean Tweet Sentiment (Pos-Neg)") ///
//          xtitle("Weeks from Birth") ///
//          title("Tweet Sentiment Around Birth") ///
//          graphregion(color(white)) ///
//          xlabel(-78(13)78)
// * Save graph
// graph export "$tweetNLP_figs/simple_sentiment/sentiment_score.jpg", replace
// restore


// *----------------- FILLED BAR (test) -----------------*
// // use "$sentiment/output/sentiment_scoresFULL.dta", clear
// use "$sentiment/output/sentiment_scores_1modrop.dta", clear
//
// // preserve
// gen pos_count = (sentiment== "positive")
// gen neg_count = (sentiment== "negative")
// gen neu_count = (sentiment== "neutral")
// collapse (sum) pos_count neg_count neu_count, by(months_from_birth)
// gen total = pos_count+neg_count+neu_count
// gen posi_share = pos_count/total
// gen nega_share = neg_count/total
// gen neut_share = neu_count/total
//
// * Generate cumulative shares for stacked plotting
// gen posi_cum = posi_share
// gen neut_cum = posi_share + neut_share
// gen nega_cum = posi_share + neut_share + nega_share   // should = 1
// gen zero = 0
//
// * Stacked filled area graph
// twoway ///
//     (rarea nega_cum neut_cum months_from_birth, color(eltblue)) ///      // negative area (top)
//     (rarea neut_cum posi_cum months_from_birth, color(dknavy))  ///      // neutral area (middle)
//     (rarea posi_cum zero months_from_birth, color(cranberry))         ///      // positive area (bottom)
//     , ///
//       legend(order(3 "Positive" 2 "Neutral" 1 "Negative") pos(6)) ///
//       xtitle("Months from Birth") ///
//       ytitle("Share of Tweets") ///
//       ylabel(0(0.2)1) ///
//       xlabel(-18(2)18) ///
//       title("Tweet Sentiment Composition Around Birth (no Birth Month)") ///
//       yscale(range(0 1))
// graph export "$tweetNLP_figs/stacked_line_sentiment_noBM.jpg", replace



// * --------------- HAND CODED SAMPLE ---------------*

// import delimited using "$sentiment/output/LLM_topic_classifier100.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
// tempfile LLM_classif
// save `LLM_classif', replace
//
// import delimited using "$sentiment/output/tweetNLP/NLP_topic_classifier100.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
// merge 1:1 tweet_id using `LLM_classif'
// drop _merge
//
// ** CLEANING / DATA PREP 
// 	* STRING --> INTEGERS
// 	gen tweet_id_clean = subinstr(tweet_id, "'", "", .)
// 	drop tweet_id
// 	rename tweet_id_clean tweet_id
// 	gen author_id_clean = subinstr(author_id, "'", "", .)
// 	drop author_id
// 	rename author_id_clean author_id
//
// 	* DATE VARIABLES
// 	destring created_at date_birth date_birth_tweet, replace
// 	format created_at date_birth date_birth_tweet %td
//
// 	* DESTRING 
// 	foreach var in like_count retweet_count reply_count quote_count post_birth days_from_birth week_from_birth months_from_birth full_3years no_rt_reply tweet_postba acct_tweeted_postba female family_prob family_flag  {
// 		destring `var', replace
// 	}
// 	order unique_id author_id tweet_id created_at date_birth date_birth_tweet text like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls
//
//
// gen LLM_family_flag = (classification=="family")
// gen hand_family_flag = (hand_topic=="1")
//
// label variable family_prob "P(family tweet) tweetNLP"
// label variable family_flag "If P(family tweet) > 0.5 tweetNLP"
// label variable classification "LLM tweet classification (1-family, 2-politics, 3-other)"
// label variable LLM_family_flag "Family related tweet LLM"
// label variable hand_family_flag "Hand coded family related tweet"
// label variable hand_topic "Hand coded topic (1-family, 2-politics, 3-sports, 0-other)"
//
// rename family_flag NLP_family_flag
// rename family_prob NLP_family_prob
// rename classification LLM_classification
// rename reasoning LLM_reasoning
//
//
// save "$sentiment/output/handcode100_t1.dta", replace	

// ****************************** OTHER NOTES ******************************

// ** VADER TAKE 2
// preserve
// collapse (mean) vader_score, by(months_from_birth)
//
// 	* Average family rating pre/post birth
// 	sum vader_score if months_from_birth < 0
// 	local pre_birth_avg = r(mean)
// 	sum vader_score if months_from_birth >= 0
// 	local post_birth_avg = r(mean)
//
// ** PLOT (total tweets)
// twoway (line vader_score months_from_birth, lwidth(medthick) lcolor(blue)) ///
//        , xline(0, lpattern(dash) lcolor(edkblue)) ///
// 	     yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
// 		 yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
//          ytitle("Avg Sentiment by User by Month") ///
//          xtitle("Months from Birth") ///
//          title("Tweeting Sentiment Pre/Post Birth (no BA)") ///
//          graphregion(color(white)) ///
//          xlabel(-18(2)18)
// * Save graph
// graph export "$sentiment_figs/vader_posneg_Kcode.jpg", replace
// restore	
//
// ** CREATE MERGABLE TWEET TEXT DATASET
//
// use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
//
// merge m:1 unique_id using "$final/user_info_full_sample_CLEAN.dta", keepusing(date_birth user_created_at)
// drop _merge
//
// 	** Generate needed variables
// 	gen days_from_birth = created_at - date_birth
// 	gen months_from_birth = floor(days_from_birth / 30)
// 	gen week_from_birth = floor(days_from_birth / 7)
//
// 	** Restrict sample to accounts created 18 months pre birth
// 	gen days_alive = user_created_at - date_birth 
// 	drop if days_alive > -546
//	
// 	* TEXT var right type for merge
// 	gen str100 text_str = substr(text, 1, 100)
// 	drop text
// 	rename text_str text
//	
// 	* Take care of duplicates so it can merge:
// 	duplicates report unique_id tweet_id
// 	bysort unique_id tweet_id: gen dup_order = _n
// 	drop if dup_order == 2
//	
// save "$sentiment/tweets_by_user_restricted_CLEAN.dta", replace



// 	* Don't think this is right here for the var type it ended up being in excel
// 	gen stata_date = date(created_at, "DMY")
// 	* Format it as a readable date
// 	format stata_date %td
		
	
// // // Sample taken analysis
// import delimited using "$sentiment/tweet_text_sample.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
//
// import delimited using "$sentiment/tweet_text_sample.csv", stringcols(_all) varnames(1) clear