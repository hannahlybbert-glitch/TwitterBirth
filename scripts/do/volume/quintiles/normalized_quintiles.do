// Author: Hannah Lybbert
// Created: 01/22/2026
// Purpose: Volume fig using quintiles

use "$final/tweet_volume_analysis_sample.dta", clear


*------------------------------------------------------------------------------
* NORMALIZED: all 5 quintiles together
*------------------------------------------------------------------------------

preserve
    * First, calculate total tweets per user across all months
    bysort author_id: egen user_total_tweets = total(total_month_tweets)
    
    * Create quintiles based on user's total tweet volume
    xtile volume_quintile = user_total_tweets, nquantiles(5)
    
    * Label the quintiles for clarity
    label define quint_lab 1 "Q1 (Lowest)" 2 "Q2" 3 "Q3" 4 "Q4" 5 "Q5 (Highest)"
    label values volume_quintile quint_lab
    
    * Collapse by quintile AND months_from_birth
    collapse (mean) total_month_tweets, by(author_id volume_quintile months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(volume_quintile months_from_birth)
    
    * Calculate pre-birth average for each quintile (months < 0)
    bysort volume_quintile: egen prebirth_avg = mean(total_month_tweets) if months_from_birth < 0
    bysort volume_quintile: egen prebirth_baseline = max(prebirth_avg)
    drop prebirth_avg
    
    * Normalize to pre-birth baseline (as percentage of pre-birth average)
    gen normalized_tweets = (total_month_tweets / prebirth_baseline) * 100
    
    * Generate confidence intervals for normalized values
    gen se = sd_total / sqrt(n)
    gen ci_lower_raw = total_month_tweets - 1.96 * se
    gen ci_upper_raw = total_month_tweets + 1.96 * se
    gen ci_lower = (ci_lower_raw / prebirth_baseline) * 100
    gen ci_upper = (ci_upper_raw / prebirth_baseline) * 100
    
    * Create the graph with separate lines for each quintile
    twoway ///
        (line normalized_tweets months_from_birth if volume_quintile==1, lwidth(medthick) lcolor(blue)) ///
        (line normalized_tweets months_from_birth if volume_quintile==2, lwidth(medthick) lcolor(green)) ///
        (line normalized_tweets months_from_birth if volume_quintile==3, lwidth(medthick) lcolor(orange)) ///
        (line normalized_tweets months_from_birth if volume_quintile==4, lwidth(medthick) lcolor(red)) ///
        (line normalized_tweets months_from_birth if volume_quintile==5, lwidth(medthick) lcolor(purple)) ///
        , xline(0, lpattern(dash) lcolor(edkblue)) ///
          yline(100, lpattern(dash) lcolor(gs10)) ///
          ytitle("Tweet Volume (% of Pre-Birth Average)") ///
          xtitle("Months from Birth") ///
          title("Total Tweeting Frequency Around Birth by Volume Quintile") ///
          subtitle("(Normalized to Pre-Birth Baseline = 100%)") ///
          legend(label(1 "Q1 (Lowest)") label(2 "Q2") label(3 "Q3") ///
                 label(4 "Q4") label(5 "Q5 (Highest)") ///
                 position(2) ring(0)) ///
          note("Note: Each quintile normalized to its own pre-birth average (months < 0)." ///
               "Sample Size per quintile = 1,172 accounts (20% of 5,862 accounts") ///
          graphregion(color(white)) ///
          xlabel(-18(2)18)
    graph export "$volume_figs/twt_behavior/quintiles/quintiles_normalized.jpg", replace
restore



*------------------------------------------------------------------------------
* FEMALE: all 5 quintiles together
*------------------------------------------------------------------------------
preserve
	keep if female == 1
    * First, calculate total tweets per user across all months
    bysort author_id: egen user_total_tweets = total(total_month_tweets)
    
    * Create quintiles based on user's total tweet volume
    xtile volume_quintile = user_total_tweets, nquantiles(5)
    
    * Label the quintiles for clarity
    label define quint_lab 1 "Q1 (Lowest)" 2 "Q2" 3 "Q3" 4 "Q4" 5 "Q5 (Highest)"
    label values volume_quintile quint_lab
    
    * Collapse by quintile AND months_from_birth
    collapse (mean) total_month_tweets, by(author_id volume_quintile months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(volume_quintile months_from_birth)
    
    * Calculate pre-birth average for each quintile (months < 0)
    bysort volume_quintile: egen prebirth_avg = mean(total_month_tweets) if months_from_birth < 0
    bysort volume_quintile: egen prebirth_baseline = max(prebirth_avg)
    drop prebirth_avg
    
    * Normalize to pre-birth baseline (as percentage of pre-birth average)
    gen normalized_tweets = (total_month_tweets / prebirth_baseline) * 100
    
    * Generate confidence intervals for normalized values
    gen se = sd_total / sqrt(n)
    gen ci_lower_raw = total_month_tweets - 1.96 * se
    gen ci_upper_raw = total_month_tweets + 1.96 * se
    gen ci_lower = (ci_lower_raw / prebirth_baseline) * 100
    gen ci_upper = (ci_upper_raw / prebirth_baseline) * 100
    
    * Create the graph with separate lines for each quintile
    twoway ///
        (line normalized_tweets months_from_birth if volume_quintile==1, lwidth(medthick) lcolor(blue)) ///
        (line normalized_tweets months_from_birth if volume_quintile==2, lwidth(medthick) lcolor(green)) ///
        (line normalized_tweets months_from_birth if volume_quintile==3, lwidth(medthick) lcolor(orange)) ///
        (line normalized_tweets months_from_birth if volume_quintile==4, lwidth(medthick) lcolor(red)) ///
        (line normalized_tweets months_from_birth if volume_quintile==5, lwidth(medthick) lcolor(purple)) ///
        , xline(0, lpattern(dash) lcolor(edkblue)) ///
          yline(100, lpattern(dash) lcolor(gs10)) ///
          ytitle("Tweet Volume (% of Pre-Birth Average)") ///
          xtitle("Months from Birth") ///
          title("Total Female Tweeting Frequency by Volume Quintile") ///
          subtitle("(Normalized to Pre-Birth Baseline = 100%)") ///
          legend(label(1 "Q1 (Lowest)") label(2 "Q2") label(3 "Q3") ///
                 label(4 "Q4") label(5 "Q5 (Highest)") ///
                 position(2) ring(0)) ///
          note("Note: Each quintile normalized to its own pre-birth average (months < 0)." ///
			  "Sample size per quintile: ~496 female accounts (20% of 2,481)") ///
          graphregion(color(white)) ///
          xlabel(-18(2)18)
    graph export "$volume_figs/twt_behavior/quintiles/female_Q_norm.jpg", replace
restore



*------------------------------------------------------------------------------
* MALE: all 5 quintiles together - NORMALIZED
*------------------------------------------------------------------------------
preserve
	keep if female == 0
    * First, calculate total tweets per user across all months
    bysort author_id: egen user_total_tweets = total(total_month_tweets)
    
    * Create quintiles based on user's total tweet volume
    xtile volume_quintile = user_total_tweets, nquantiles(5)
    
    * Label the quintiles for clarity
    label define quint_lab 1 "Q1 (Lowest)" 2 "Q2" 3 "Q3" 4 "Q4" 5 "Q5 (Highest)"
    label values volume_quintile quint_lab
    
    * Collapse by quintile AND months_from_birth
    collapse (mean) total_month_tweets, by(author_id volume_quintile months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(volume_quintile months_from_birth)
    
    * Calculate pre-birth average for each quintile (months < 0)
    bysort volume_quintile: egen prebirth_avg = mean(total_month_tweets) if months_from_birth < 0
    bysort volume_quintile: egen prebirth_baseline = max(prebirth_avg)
    drop prebirth_avg
    
    * Normalize to pre-birth baseline (as percentage of pre-birth average)
    gen normalized_tweets = (total_month_tweets / prebirth_baseline) * 100
    
    * Generate confidence intervals for normalized values
    gen se = sd_total / sqrt(n)
    gen ci_lower_raw = total_month_tweets - 1.96 * se
    gen ci_upper_raw = total_month_tweets + 1.96 * se
    gen ci_lower = (ci_lower_raw / prebirth_baseline) * 100
    gen ci_upper = (ci_upper_raw / prebirth_baseline) * 100
    
    * Create the graph with separate lines for each quintile
    twoway ///
        (line normalized_tweets months_from_birth if volume_quintile==1, lwidth(medthick) lcolor(blue)) ///
        (line normalized_tweets months_from_birth if volume_quintile==2, lwidth(medthick) lcolor(green)) ///
        (line normalized_tweets months_from_birth if volume_quintile==3, lwidth(medthick) lcolor(orange)) ///
        (line normalized_tweets months_from_birth if volume_quintile==4, lwidth(medthick) lcolor(red)) ///
        (line normalized_tweets months_from_birth if volume_quintile==5, lwidth(medthick) lcolor(purple)) ///
        , xline(0, lpattern(dash) lcolor(edkblue)) ///
          yline(100, lpattern(dash) lcolor(gs10)) ///
          ytitle("Tweet Volume (% of Pre-Birth Average)") ///
          xtitle("Months from Birth") ///
          title("Total Male Tweeting Frequency by Volume Quintile") ///
          subtitle("(Normalized to Pre-Birth Baseline = 100%)") ///
          legend(label(1 "Q1 (Lowest)") label(2 "Q2") label(3 "Q3") ///
                 label(4 "Q4") label(5 "Q5 (Highest)") ///
                 position(2) ring(0)) ///
          note("Note: Each quintile normalized to its own pre-birth average (months < 0)." ///
               "Sample Size per quintile = ~638 male accounts (20% of 3,190)") ///
          graphregion(color(white)) ///
          xlabel(-18(2)18)
    graph export "$volume_figs/twt_behavior/quintiles/male_Q_norm.jpg", replace
restore


*------------------------------------------------------------------------------
* OLD CODE (quintiles separeted out)
*------------------------------------------------------------------------------

preserve
    * First, calculate total tweets per user across all months
    bysort author_id: egen user_total_tweets = total(total_month_tweets)
    
    * Create quintiles based on user's total tweet volume
    xtile volume_quintile = user_total_tweets, nquantiles(5)
    
    * Label the quintiles for clarity
    label define quint_lab 1 "Q1 (Lowest)" 2 "Q2" 3 "Q3" 4 "Q4" 5 "Q5 (Highest)"
    label values volume_quintile quint_lab
    
    * Collapse by quintile AND months_from_birth
    collapse (mean) total_month_tweets, by(author_id volume_quintile months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(volume_quintile months_from_birth)
    
    * Generate confidence intervals
    gen se = sd_total / sqrt(n)
    gen ci_lower = total_month_tweets - 1.96 * se
    gen ci_upper = total_month_tweets + 1.96 * se
    
    * Create the graph with separate lines for each quintile
    twoway ///
        (line total_month_tweets months_from_birth if volume_quintile==1, lwidth(medthick) lcolor(blue)) ///
        (line total_month_tweets months_from_birth if volume_quintile==2, lwidth(medthick) lcolor(green)) ///
        (line total_month_tweets months_from_birth if volume_quintile==3, lwidth(medthick) lcolor(orange)) ///
        (line total_month_tweets months_from_birth if volume_quintile==4, lwidth(medthick) lcolor(red)) ///
        (line total_month_tweets months_from_birth if volume_quintile==5, lwidth(medthick) lcolor(purple)) ///
        , xline(0, lpattern(dash) lcolor(edkblue)) ///
          ytitle("Average Total Tweets per User") ///
          xtitle("Months from Birth") ///
          title("Total Tweeting Frequency Around Birth by Volume Quintile") ///
          legend(label(1 "Q1 (Lowest)") label(2 "Q2") label(3 "Q3") ///
                 label(4 "Q4") label(5 "Q5 (Highest)") ///
                 position(2) ring(0)) ///
          note("Note: Quintiles based on user's total tweet volume across all months." ///
               "Sample Size = 5,862 accounts") ///
          graphregion(color(white)) ///
          xlabel(-18(2)18)
    graph export "$volume_figs/twt_behavior/tweets_quintiles.jpg", replace
restore





preserve
    * First, calculate total tweets per user across all months
    bysort author_id: egen user_total_tweets = total(total_month_tweets)
    
    * Create quintiles based on user's total tweet volume
    xtile volume_quintile = user_total_tweets, nquantiles(5)
    
    * Drop Q5 (highest volume users)
    drop if volume_quintile == 5
    
    * Label the quintiles for clarity
    label define quint_lab 1 "Q1 (Lowest)" 2 "Q2" 3 "Q3" 4 "Q4"
    label values volume_quintile quint_lab
    
    * Collapse by quintile AND months_from_birth
    collapse (mean) total_month_tweets, by(author_id volume_quintile months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(volume_quintile months_from_birth)
    
    * Generate confidence intervals
    gen se = sd_total / sqrt(n)
    gen ci_lower = total_month_tweets - 1.96 * se
    gen ci_upper = total_month_tweets + 1.96 * se
    
    * Create the graph with separate lines for Q1-Q4 only
    twoway ///
        (line total_month_tweets months_from_birth if volume_quintile==1, lwidth(medthick) lcolor(blue)) ///
        (line total_month_tweets months_from_birth if volume_quintile==2, lwidth(medthick) lcolor(green)) ///
        (line total_month_tweets months_from_birth if volume_quintile==3, lwidth(medthick) lcolor(orange)) ///
        (line total_month_tweets months_from_birth if volume_quintile==4, lwidth(medthick) lcolor(red)) ///
        , xline(0, lpattern(dash) lcolor(edkblue)) ///
          ytitle("Average Total Tweets per User") ///
          xtitle("Months from Birth") ///
          title("Total Tweeting Frequency Around Birth by Volume Quintile") ///
          legend(label(1 "Q1 (Lowest)") label(2 "Q2") label(3 "Q3") ///
                 label(4 "Q4") ///
                 position(2) ring(0)) ///
          note("Note: Quintiles based on user's total tweet volume across all months." ///
               "Q5 (highest volume users) excluded." ///
               "Sample Size = 4,690 accounts (80% of original sample)") ///
          graphregion(color(white)) ///
          xlabel(-18(2)18)
    graph export "$volume_figs/twt_behavior/tweets_quintiles_noQ5.jpg", replace
restore




preserve
    * First, calculate total tweets per user across all months
    bysort author_id: egen user_total_tweets = total(total_month_tweets)
    
    * Create quintiles based on user's total tweet volume
    xtile volume_quintile = user_total_tweets, nquantiles(5)
    
    * Keep only Q1-Q3 (lowest to middle volume users)
    keep if inlist(volume_quintile, 1, 2, 3)
    
    * Label the quintiles for clarity
    label define quint_lab 1 "Q1 (Lowest)" 2 "Q2" 3 "Q3"
    label values volume_quintile quint_lab
    
    * Collapse by quintile AND months_from_birth
    collapse (mean) total_month_tweets, by(author_id volume_quintile months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(volume_quintile months_from_birth)
    
    * Generate confidence intervals
    gen se = sd_total / sqrt(n)
    gen ci_lower = total_month_tweets - 1.96 * se
    gen ci_upper = total_month_tweets + 1.96 * se
    
    * Create the graph with separate lines for Q1-Q3 only
    twoway ///
        (line total_month_tweets months_from_birth if volume_quintile==1, lwidth(medthick) lcolor(blue)) ///
        (line total_month_tweets months_from_birth if volume_quintile==2, lwidth(medthick) lcolor(green)) ///
        (line total_month_tweets months_from_birth if volume_quintile==3, lwidth(medthick) lcolor(orange)) ///
        , xline(0, lpattern(dash) lcolor(edkblue)) ///
          ytitle("Average Total Tweets per User") ///
          xtitle("Months from Birth") ///
          title("Total Tweeting Frequency Around Birth by Volume Quintile") ///
          legend(label(1 "Q1 (Lowest)") label(2 "Q2") label(3 "Q3") ///
                 position(2) ring(0)) ///
          note("Note: Quintiles based on user's total tweet volume across all months." ///
               "Q4-Q5 (highest volume users) excluded." ///
               "Sample Size = 3,517 accounts (60% of original sample)") ///
          graphregion(color(white)) ///
          xlabel(-18(2)18)
    graph export "$volume_figs/twt_behavior/tweets_quintiles_Q1Q2Q3.jpg", replace
restore





preserve
    bysort author_id: egen user_total_tweets = total(total_month_tweets)

    xtile volume_quintile = user_total_tweets, nquantiles(5)

    keep if inlist(volume_quintile, 1, 2, 3)

    label define quint_lab 1 "Q1 (Lowest)" 2 "Q2" 3 "Q3"
    label values volume_quintile quint_lab
    
    * Collapse by quintile AND months_from_birth
    collapse (mean) total_month_tweets, by(author_id volume_quintile months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(volume_quintile months_from_birth)
    
    * Generate confidence intervals
    gen se = sd_total / sqrt(n)
    gen ci_lower = total_month_tweets - 1.96 * se
    gen ci_upper = total_month_tweets + 1.96 * se
    
    * Create the graph with separate lines for Q1-Q3 only
    twoway ///
        (line total_month_tweets months_from_birth if volume_quintile==1, lwidth(medthick) lcolor(blue)) ///
        , xline(0, lpattern(dash) lcolor(edkblue)) ///
          ytitle("Average Total Tweets per User") ///
          xtitle("Months from Birth") ///
          title("Total Tweeting Frequency Around Birth by Volume Quintile") ///
          legend(label(1 "Q1 (Lowest)") label(2 "Q2") label(3 "Q3") ///
                 position(2) ring(0)) ///
          note("Note: Quintiles based on user's total tweet volume across all months." ///
               "Q4-Q5 (highest volume users) excluded." ///
               "Sample Size = 3,517 accounts (60% of original sample)") ///
          graphregion(color(white)) ///
          xlabel(-18(2)18)
    graph export "$volume_figs/twt_behavior/tweets_quintiles_Q1.jpg", replace
restore