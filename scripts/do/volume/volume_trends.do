// Author: Hannah Lybbert
// Created: 01/26/2026
// Purpose: Volume regression -18 to -9, 1-17

use "$final/tweet_volume_analysis_sample.dta", clear


*--------------------------------------------------------------------------
* FEMALES: plot volume with trend lines
*--------------------------------------------------------------------------
preserve
    * Keep only female accounts
    keep if female == 1
    
    * Collapse to get average tweets per user per month
    collapse (mean) total_month_tweets, by(author_id months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(months_from_birth)
    
    * Generate confidence intervals
    gen se = sd_total / sqrt(n)
    gen ci_lower = total_month_tweets - 1.96 * se
    gen ci_upper = total_month_tweets + 1.96 * se
    
    *--------------------------------------------------------------------------
    * Regression 1: Pre-birth period (-18 to -9 months)
    *--------------------------------------------------------------------------
    reg total_month_tweets months_from_birth if months_from_birth >= -18 & months_from_birth <= -9
    
    * Store coefficients for plotting
    local pre_intercept = _b[_cons]
    local pre_slope = _b[months_from_birth]
    
    * Generate predicted values for pre-birth period
    gen pred_prebirth = `pre_intercept' + `pre_slope' * months_from_birth ///
        if months_from_birth >= -18 & months_from_birth <= -9
    
    *--------------------------------------------------------------------------
    * Regression 2: Post-birth period (1 to 17 months)
    *--------------------------------------------------------------------------
    reg total_month_tweets months_from_birth if months_from_birth >= 1 & months_from_birth <= 17
    
    * Store coefficients for plotting
    local post_intercept = _b[_cons]
    local post_slope = _b[months_from_birth]
    
    * Generate predicted values for post-birth period
    gen pred_postbirth = `post_intercept' + `post_slope' * months_from_birth ///
        if months_from_birth >= 1 & months_from_birth <= 17
    
    *--------------------------------------------------------------------------
    * Create the graph with actual data, CIs, and regression lines
    *--------------------------------------------------------------------------
    twoway ///
        (rcap ci_upper ci_lower months_from_birth, lcolor(gs8)) ///
        (line total_month_tweets months_from_birth, lwidth(medthick) lcolor(red)) ///
        (line pred_prebirth months_from_birth, lwidth(thick) lcolor(navy) lpattern(dash)) ///
        (line pred_postbirth months_from_birth, lwidth(thick) lcolor(navy) lpattern(dash)) ///
        , xline(0, lpattern(dash) lcolor(edkblue)) ///
          ytitle("Average Total Tweets per User") ///
          xtitle("Months from Birth") ///
          title("Female Tweeting Frequency Around Birth with Trend Lines") ///
          legend(label(1 "95% CI") label(2 "Avg Tweets") ///
                 label(3 "Pre-birth trend (-18 to -9)") ///
                 label(4 "Post-birth trend (1 to 17)") ///
                 position(2) ring(0)) ///
          note("Note: Pre-birth regression: months -18 to -9. Post-birth regression: months 1 to 17." ///
               "Sample: 2,481 female accounts") ///
          graphregion(color(white)) ///
          xlabel(-18(2)18)
    graph export "$volume_figs/twt_behavior/female_trend.jpg", replace
restore


*--------------------------------------
* FEMALES: compare pre/post trends
*--------------------------------------

preserve
    * Keep only female accounts
    keep if female == 1
    
    * Collapse to get average tweets per user per month
    collapse (mean) total_month_tweets, by(author_id months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(months_from_birth)
    
    * Keep only the periods of interest
    keep if (months_from_birth >= -18 & months_from_birth <= -9) | ///
            (months_from_birth >= 1 & months_from_birth <= 17)
    
    * Create indicator for post-birth period
    gen post_birth = (months_from_birth >= 1)
    
    * Create interaction term
    gen post_X_months = post_birth * months_from_birth
    
    * Run regression with interaction
    reg total_month_tweets months_from_birth post_birth post_X_months
    
    * Test if slopes are different
    test post_X_months = 0
    
restore



*--------------------------------------------------------------------------
* MALES
*--------------------------------------------------------------------------
preserve
    * Keep only female accounts
    keep if female == 0
    
    * Collapse to get average tweets per user per month
    collapse (mean) total_month_tweets, by(author_id months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(months_from_birth)
    
    * Generate confidence intervals
    gen se = sd_total / sqrt(n)
    gen ci_lower = total_month_tweets - 1.96 * se
    gen ci_upper = total_month_tweets + 1.96 * se
    
    *--------------------------------------------------------------------------
    * Regression 1: Pre-birth period (-18 to -9 months)
    *--------------------------------------------------------------------------
    reg total_month_tweets months_from_birth if months_from_birth >= -18 & months_from_birth <= -9
    
    * Store coefficients for plotting
    local pre_intercept = _b[_cons]
    local pre_slope = _b[months_from_birth]
    
    * Generate predicted values for pre-birth period
    gen pred_prebirth = `pre_intercept' + `pre_slope' * months_from_birth ///
        if months_from_birth >= -18 & months_from_birth <= -9
    
    *--------------------------------------------------------------------------
    * Regression 2: Post-birth period (1 to 17 months)
    *--------------------------------------------------------------------------
    reg total_month_tweets months_from_birth if months_from_birth >= 1 & months_from_birth <= 17
    
    * Store coefficients for plotting
    local post_intercept = _b[_cons]
    local post_slope = _b[months_from_birth]
    
    * Generate predicted values for post-birth period
    gen pred_postbirth = `post_intercept' + `post_slope' * months_from_birth ///
        if months_from_birth >= 1 & months_from_birth <= 17
    
    *--------------------------------------------------------------------------
    * Create the graph with actual data, CIs, and regression lines
    *--------------------------------------------------------------------------
    twoway ///
        (rcap ci_upper ci_lower months_from_birth, lcolor(gs8)) ///
        (line total_month_tweets months_from_birth, lwidth(medthick) lcolor(red)) ///
        (line pred_prebirth months_from_birth, lwidth(thick) lcolor(navy) lpattern(dash)) ///
        (line pred_postbirth months_from_birth, lwidth(thick) lcolor(navy) lpattern(dash)) ///
        , xline(0, lpattern(dash) lcolor(edkblue)) ///
          ytitle("Average Total Tweets per User") ///
          xtitle("Months from Birth") ///
          title("Male Tweeting Frequency Around Birth with Trend Lines") ///
          legend(label(1 "95% CI") label(2 "Avg Tweets") ///
                 label(3 "Pre-birth trend (-18 to -9)") ///
                 label(4 "Post-birth trend (1 to 17)") ///
                 position(2) ring(0)) ///
          note("Note: Pre-birth regression: months -18 to -9. Post-birth regression: months 1 to 17." ///
               "Sample: 3,190 male accounts") ///
          graphregion(color(white)) ///
          xlabel(-18(2)18)
    graph export "$volume_figs/twt_behavior/male_trend.jpg", replace
restore

*--------------------------------------
* MALES: compare pre/post trends
*--------------------------------------

preserve
    * Keep only female accounts
    keep if female == 0
    
    * Collapse to get average tweets per user per month
    collapse (mean) total_month_tweets, by(author_id months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(months_from_birth)
    
    * Keep only the periods of interest
    keep if (months_from_birth >= -18 & months_from_birth <= -9) | ///
            (months_from_birth >= 1 & months_from_birth <= 17)
    
    * Create indicator for post-birth period
    gen post_birth = (months_from_birth >= 1)
    
    * Create interaction term
    gen post_X_months = post_birth * months_from_birth
    
    * Run regression with interaction
    reg total_month_tweets months_from_birth post_birth post_X_months
    
    * Test if slopes are different
    test post_X_months = 0
    
restore