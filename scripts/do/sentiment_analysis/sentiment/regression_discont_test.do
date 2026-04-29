* Author: Hannah Lybbert
* Created: 12/03/2025
* Purpose: Can I make an RDD work?

use "$sentiment/output/sentiment_scoresFULL_clean.dta", clear


* --------------- LINEAR ------------------- *

** Sentiment with RD-style separate curves
preserve
    * Collapse to mean and standard deviation by month
    collapse (mean) sentiment_score (sd) sd_compound = sentiment_score (count) n = sentiment_score, by(months_from_birth)
    * Standard error and 95% confidence intervals
    gen se = sd_compound / sqrt(n)
    gen ci_lower = sentiment_score - 1.96 * se
    gen ci_upper = sentiment_score + 1.96 * se
    
    * Create separate variables for pre/post birth periods
    gen pos_pre = sentiment_score if months_from_birth < 0
    gen pos_post = sentiment_score if months_from_birth >= 0
    gen months_pre = months_from_birth if months_from_birth < 0
    gen months_post = months_from_birth if months_from_birth >= 0
    
    * Fit separate regression lines for pre/post periods
    reg sentiment_score months_from_birth if months_from_birth < 0
    predict fitted_pre if months_from_birth < 0
    reg sentiment_score months_from_birth if months_from_birth >= 0
    predict fitted_post if months_from_birth >= 0
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy%30)) ///
    (scatter sentiment_score months_from_birth, mcolor(blue%50) msize(medium)) ///
    (line fitted_pre months_from_birth, lcolor(gray) lpattern(solid)) ///
    (line fitted_post months_from_birth, lcolor(gray) lpattern(solid)) ///
    , xline(0, lpattern(dash) lwidth(medthick) lcolor(edkblue)) ///
      legend(order(2 1) ///
          label(2 "Mean Positivity by Month") ///
          label(1 "95% CI") ///
          position(2) ring(0)) ///
      ytitle("Mean Positivity") ///
      xtitle("Months from Birth") ///
      title("Tweet Positivity Around Birth") ///
  	  note("Note: Separate linear fits pre/post birth") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18) 
graph export "$tweetNLP_figs/simple_sentiment/RD/sent_score_RD.jpg", replace
restore

** Positive with RD-style separate curves
preserve
    * Collapse to mean and standard deviation by month
    collapse (mean) pos (sd) sd_compound = pos (count) n = pos, by(months_from_birth)
    * Standard error and 95% confidence intervals
    gen se = sd_compound / sqrt(n)
    gen ci_lower = pos - 1.96 * se
    gen ci_upper = pos + 1.96 * se
    
    * Create separate variables for pre/post birth periods
    gen pos_pre = pos if months_from_birth < 0
    gen pos_post = pos if months_from_birth >= 0
    gen months_pre = months_from_birth if months_from_birth < 0
    gen months_post = months_from_birth if months_from_birth >= 0
    
    * Fit separate regression lines for pre/post periods
    reg pos months_from_birth if months_from_birth < 0
    predict fitted_pre if months_from_birth < 0
    reg pos months_from_birth if months_from_birth >= 0
    predict fitted_post if months_from_birth >= 0
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy%30)) ///
    (scatter pos months_from_birth, mcolor(blue%50) msize(medium)) ///
    (line fitted_pre months_from_birth, lcolor(gray) lpattern(solid)) ///
    (line fitted_post months_from_birth, lcolor(gray) lpattern(solid)) ///
    , xline(0, lpattern(dash) lwidth(medthick) lcolor(edkblue)) ///
      legend(order(2 1) ///
          label(2 "Mean Positivity by Month") ///
          label(1 "95% CI") ///
          position(2) ring(0)) ///
      ytitle("Mean Positivity") ///
      xtitle("Months from Birth") ///
      title("Tweet Positivity Around Birth") ///
  	  note("Note: Separate linear fits pre/post birth") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18) 
graph export "$tweetNLP_figs/simple_sentiment/RD/pos_score_RD.jpg", replace
restore


** Negative with RD-style separate curves
preserve
    * Collapse to mean and standard deviation by month
    collapse (mean) neg (sd) sd_compound = neg (count) n = neg, by(months_from_birth)
    * Standard error and 95% confidence intervals
    gen se = sd_compound / sqrt(n)
    gen ci_lower = neg - 1.96 * se
    gen ci_upper = neg + 1.96 * se
    
    * Create separate variables for pre/post birth periods
    gen pos_pre = neg if months_from_birth < 0
    gen pos_post = neg if months_from_birth >= 0
    gen months_pre = months_from_birth if months_from_birth < 0
    gen months_post = months_from_birth if months_from_birth >= 0
    
    * Fit separate regression lines for pre/post periods
    reg neg months_from_birth if months_from_birth < 0
    predict fitted_pre if months_from_birth < 0
    reg neg months_from_birth if months_from_birth >= 0
    predict fitted_post if months_from_birth >= 0
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy%30)) ///
    (scatter neg months_from_birth, mcolor(blue%50) msize(medium)) ///
    (line fitted_pre months_from_birth, lcolor(gray) lpattern(solid)) ///
    (line fitted_post months_from_birth, lcolor(gray) lpattern(solid)) ///
    , xline(0, lpattern(dash) lwidth(medthick) lcolor(edkblue)) ///
      legend(order(2 1) ///
          label(2 "Mean Positivity by Month") ///
          label(1 "95% CI") ///
          position(2) ring(0)) ///
      ytitle("Mean Negativity") ///
      xtitle("Months from Birth") ///
      title("Tweet Negativity Around Birth") ///
  	  note("Note: Separate linear fits pre/post birth") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18) 
graph export "$tweetNLP_figs/simple_sentiment/RD/neg_score_RD.jpg", replace
restore


** Negative with RD-style separate curves
preserve
    * Collapse to mean and standard deviation by month
    collapse (mean) neu (sd) sd_compound = neu (count) n = neu, by(months_from_birth)
    * Standard error and 95% confidence intervals
    gen se = sd_compound / sqrt(n)
    gen ci_lower = neu - 1.96 * se
    gen ci_upper = neu + 1.96 * se
    
    * Create separate variables for pre/post birth periods
    gen pos_pre = neu if months_from_birth < 0
    gen pos_post = neu if months_from_birth >= 0
    gen months_pre = months_from_birth if months_from_birth < 0
    gen months_post = months_from_birth if months_from_birth >= 0
    
    * Fit separate regression lines for pre/post periods
    reg neu months_from_birth if months_from_birth < 0
    predict fitted_pre if months_from_birth < 0
    reg neu months_from_birth if months_from_birth >= 0
    predict fitted_post if months_from_birth >= 0
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy%30)) ///
    (scatter neu months_from_birth, mcolor(blue%50) msize(medium)) ///
    (line fitted_pre months_from_birth, lcolor(gray) lpattern(solid)) ///
    (line fitted_post months_from_birth, lcolor(gray) lpattern(solid)) ///
    , xline(0, lpattern(dash) lwidth(medthick) lcolor(edkblue)) ///
      legend(order(2 1) ///
          label(2 "Mean Positivity by Month") ///
          label(1 "95% CI") ///
          position(2) ring(0)) ///
      ytitle("Mean Neutrality") ///
      xtitle("Months from Birth") ///
      title("Tweet Neutrality Around Birth") ///
  	  note("Note: Separate linear fits pre/post birth") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18) 
graph export "$tweetNLP_figs/simple_sentiment/RD/neu_score_RD.jpg", replace
restore


* --------------- QUADRATIC ------------------- *

** Positive with RD-style separate QUADRATIC curves
preserve
    * Collapse to mean and standard deviation by month
    collapse (mean) pos (sd) sd_compound = pos (count) n = pos, by(months_from_birth)
    * Standard error and 95% confidence intervals
    gen se = sd_compound / sqrt(n)
    gen ci_lower = pos - 1.96 * se
    gen ci_upper = pos + 1.96 * se
    
    * Create separate variables for pre/post birth periods
    gen pos_pre = pos if months_from_birth < 0
    gen pos_post = pos if months_from_birth >= 0
    gen months_pre = months_from_birth if months_from_birth < 0
    gen months_post = months_from_birth if months_from_birth >= 0
    
    * Fit separate QUADRATIC regression lines for pre/post periods
    reg pos c.months_from_birth##c.months_from_birth if months_from_birth < 0
    predict fitted_pre if months_from_birth < 0
    reg pos c.months_from_birth##c.months_from_birth if months_from_birth >= 0
    predict fitted_post if months_from_birth >= 0
    
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy%30)) ///
    (scatter pos months_from_birth, mcolor(blue%50) msize(medium)) ///
    (line fitted_pre months_from_birth, lwidth(thick) lcolor(red) lpattern(solid) sort) ///
    (line fitted_post months_from_birth, lwidth(thick) lcolor(green) lpattern(solid) sort) ///
    , xline(0, lpattern(dash) lwidth(medthick) lcolor(black)) ///
      legend(order(2 1) ///
          label(2 "Mean Positivity by Month") ///
          label(1 "95% CI") ///
          position(2) ring(0)) ///
      ytitle("Average Positivity") ///
      xtitle("Months from Birth") ///
      title("Regression Discontinuity: Tweet Positivity Around Birth") ///
      note("Note: Separate quadratic fits pre/post birth.") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18) 
graph export "$tweetNLP_figs/simple_sentiment/RD/pos_score_RD_quad.jpg", replace
restore