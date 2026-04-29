// Author: Hannah Lybbert
// Created: 01/26/2026
// Purpose: FEMALES --> Normalized Quintiles + trend lines

use "$volume_analysis/tweet_volume_analysis_sample.dta", clear

*------------------------------------------------------------------------------
* ALL 5 QUINTILES FEMALES with SINGLE OVERALL trend line
* Pre: -18 to -1, Post: 0 to 17
*------------------------------------------------------------------------------
preserve
	* Keep only females
	keep if female == 1
	
	* Save the original data before any collapsing
	tempfile original_data
	save `original_data'
	
	*--------------------------------------------------------------------------
	* STEP 1: Calculate OVERALL trend lines (all quintiles combined)
	*--------------------------------------------------------------------------
	use `original_data', clear
	
	collapse (mean) total_month_tweets, by(author_id months_from_birth)
	collapse (mean) total_month_tweets, by(months_from_birth)
	
	* Pre-birth regression (-18 to -1)
	reg total_month_tweets months_from_birth if months_from_birth >= -18 & months_from_birth <= -1
	local pre_intercept = _b[_cons]
	local pre_slope = _b[months_from_birth]
	
	* Post-birth regression (0 to 17)
	reg total_month_tweets months_from_birth if months_from_birth >= 0 & months_from_birth <= 17
	local post_intercept = _b[_cons]
	local post_slope = _b[months_from_birth]
	
	* Calculate overall pre-birth average for normalization
	sum total_month_tweets if months_from_birth < 0
	local overall_prebirth_avg = r(mean)
	
	*--------------------------------------------------------------------------
	* STEP 2: Create quintiles and time series by quintile
	*--------------------------------------------------------------------------
	use `original_data', clear
	
	* Calculate total tweets per user
	bysort author_id: egen user_total_tweets = total(total_month_tweets)
	
	* Create quintiles for females
	xtile volume_quintile = user_total_tweets, nquantiles(5)
	
	* Label the quintiles
	label define quint_lab 1 "Q1 (Lowest)" 2 "Q2" 3 "Q3" 4 "Q4" 5 "Q5 (Highest)"
	label values volume_quintile quint_lab
	
	* Collapse by quintile and months_from_birth
	collapse (mean) total_month_tweets, by(author_id volume_quintile months_from_birth)
	collapse (mean) total_month_tweets ///
			 (sd)   sd_total = total_month_tweets ///
			 (count) n = total_month_tweets, ///
			 by(volume_quintile months_from_birth)
	
	* Calculate pre-birth baseline for each quintile
	bysort volume_quintile: egen prebirth_avg = mean(total_month_tweets) if months_from_birth < 0
	bysort volume_quintile: egen prebirth_baseline = max(prebirth_avg)
	drop prebirth_avg
	
	* Normalize to pre-birth baseline
	gen normalized_tweets = (total_month_tweets / prebirth_baseline) * 100
	
	* Generate confidence intervals
	gen se = sd_total / sqrt(n)
	gen ci_lower_raw = total_month_tweets - 1.96 * se
	gen ci_upper_raw = total_month_tweets + 1.96 * se
	gen ci_lower = (ci_lower_raw / prebirth_baseline) * 100
	gen ci_upper = (ci_upper_raw / prebirth_baseline) * 100
	
	*--------------------------------------------------------------------------
	* STEP 3: Create normalized OVERALL trend lines
	*--------------------------------------------------------------------------
	* Pre-birth trend line (using overall average)
	gen pred_prebirth_raw = `pre_intercept' + `pre_slope' * months_from_birth ///
		if months_from_birth >= -18 & months_from_birth <= -1
	gen pred_prebirth = (pred_prebirth_raw / `overall_prebirth_avg') * 100
	
	* Post-birth trend line (using overall average)
	gen pred_postbirth_raw = `post_intercept' + `post_slope' * months_from_birth ///
		if months_from_birth >= 0 & months_from_birth <= 17
	gen pred_postbirth = (pred_postbirth_raw / `overall_prebirth_avg') * 100
	
	*--------------------------------------------------------------------------
	* STEP 4: Create the graph
	*--------------------------------------------------------------------------
	twoway ///
		(line normalized_tweets months_from_birth if volume_quintile==1, lwidth(medthick) lcolor(blue)) ///
		(line normalized_tweets months_from_birth if volume_quintile==2, lwidth(medthick) lcolor(green)) ///
		(line normalized_tweets months_from_birth if volume_quintile==3, lwidth(medthick) lcolor(orange)) ///
		(line normalized_tweets months_from_birth if volume_quintile==4, lwidth(medthick) lcolor(red)) ///
		(line normalized_tweets months_from_birth if volume_quintile==5, lwidth(medthick) lcolor(purple)) ///
		(line pred_prebirth months_from_birth, lwidth(thick) lcolor(black) lpattern(dash)) ///
		(line pred_postbirth months_from_birth, lwidth(thick) lcolor(black) lpattern(dash)) ///
		, xline(0, lpattern(dash) lcolor(black)) ///
		  yline(100, lpattern(dash) lcolor(gs10)) ///
		  ytitle("Tweet Volume (% of Pre-Birth Average)") ///
		  xtitle("Months from Birth") ///
		  title("Female Tweeting Frequency by Quintile with Overall Trend Lines") ///
		  subtitle("(Normalized to Pre-Birth Baseline = 100%)") ///
		  legend(order(1 2 3 4 5 6) ///
				 label(1 "Q1 (Lowest)") label(2 "Q2") label(3 "Q3") ///
				 label(4 "Q4") label(5 "Q5 (Highest)") ///
				 label(6 "Overall Trend") ///
				 position(2) ring(0)) ///
		  note("Note: Each quintile normalized to its own pre-birth average." ///
			   "Trend lines based on all female data combined." ///
			   "Pre-trend: months -18 to -1. Post-trend: months 0 to 17." ///
			   "Sample: 2,481 female accounts") ///
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
	graph export "$volume_figs/twt_behavior/quintiles/female_Q_trends.jpg", replace
restore

*------------------------------------------------------------------------------
* REGRESSION TABLES: Pre, Post, and Interaction (All Females)
*------------------------------------------------------------------------------
preserve
    * Keep only female accounts
    keep if female == 1
    
    * Collapse to get average tweets per user per month
    collapse (mean) total_month_tweets, by(author_id months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(months_from_birth)
    
    * Regression 1: Pre-birth period (-18 to -9)
    reg total_month_tweets months_from_birth if months_from_birth >= -18 & months_from_birth <= -1
    estimates store pre_birth
    
    * Regression 2: Post-birth period (0 to 17)
    reg total_month_tweets months_from_birth if months_from_birth >= 0 & months_from_birth <= 17
    estimates store post_birth
    
    * Regression 3: Interaction model
    keep if (months_from_birth >= -18 & months_from_birth <= -1) | ///
            (months_from_birth >= 0 & months_from_birth <= 17)
    
    * Create indicator for post-birth period
    gen post_birth = (months_from_birth >= 0)
    
    * Create interaction term
    gen post_X_months = post_birth * months_from_birth
    
    * Run regression with interaction
    reg total_month_tweets months_from_birth post_birth post_X_months
    estimates store interaction
    
    * Export to Word document
    esttab pre_birth post_birth interaction using "$volume_figs/twt_behavior/regressions/female_pre_post_reg.rtf", ///
        replace ///
        title("Female Tweeting Trends: Pre-Birth, Post-Birth, and Interaction Models") ///
        mtitles("Pre-Birth" "Post-Birth" "Interaction") ///
        b(3) se(3) ///
        star(* 0.10 ** 0.05 *** 0.01) ///
        stats(N r2 r2_a, fmt(0 3 3) labels("Observations" "R-squared" "Adj. R-squared")) ///
        nonotes ///
        addnotes("Pre-Birth: Months -18 to -1" ///
                 "Post-Birth: Months 0 to 17" ///
                 "Interaction: Tests difference in slopes between pre and post periods")
restore




*------------------------------------------------------------------------------
*------------------------------------------------------------------------------
*------------------------------------------------------------------------------
* PREGNANCY effect
*------------------------------------------------------------------------------
*------------------------------------------------------------------------------

*------------------------------------------------------------------------------
* ALL 5 QUINTILES PREGNANCY trend
*------------------------------------------------------------------------------
preserve
	* Keep only females
	keep if female == 1
	
	* Save the original data before any collapsing
	tempfile original_data
	save `original_data'
	
	*--------------------------------------------------------------------------
	* STEP 1: Calculate OVERALL trend lines (all quintiles combined)
	*--------------------------------------------------------------------------
	use `original_data', clear
	
	collapse (mean) total_month_tweets, by(author_id months_from_birth)
	collapse (mean) total_month_tweets, by(months_from_birth)
	
	* Pre-birth regression (-18 to -9)
	reg total_month_tweets months_from_birth if months_from_birth >= -18 & months_from_birth <= -9
	local pre_intercept = _b[_cons]
	local pre_slope = _b[months_from_birth]
	
	* Post-birth regression (0 to 17)
	reg total_month_tweets months_from_birth if months_from_birth >= 0 & months_from_birth <= 17
	local post_intercept = _b[_cons]
	local post_slope = _b[months_from_birth]
	
	* Calculate overall pre-birth average for normalization
	sum total_month_tweets if months_from_birth < 0
	local overall_prebirth_avg = r(mean)
	
	*--------------------------------------------------------------------------
	* STEP 2: Create quintiles and time series by quintile
	*--------------------------------------------------------------------------
	use `original_data', clear
	
	* Calculate total tweets per user
	bysort author_id: egen user_total_tweets = total(total_month_tweets)
	
	* Create quintiles for females
	xtile volume_quintile = user_total_tweets, nquantiles(5)
	
	* Label the quintiles
	label define quint_lab 1 "Q1 (Lowest)" 2 "Q2" 3 "Q3" 4 "Q4" 5 "Q5 (Highest)"
	label values volume_quintile quint_lab
	
	* Collapse by quintile and months_from_birth
	collapse (mean) total_month_tweets, by(author_id volume_quintile months_from_birth)
	collapse (mean) total_month_tweets ///
			 (sd)   sd_total = total_month_tweets ///
			 (count) n = total_month_tweets, ///
			 by(volume_quintile months_from_birth)
	
	* Calculate pre-birth baseline for each quintile
	bysort volume_quintile: egen prebirth_avg = mean(total_month_tweets) if months_from_birth < 0
	bysort volume_quintile: egen prebirth_baseline = max(prebirth_avg)
	drop prebirth_avg
	
	* Normalize to pre-birth baseline
	gen normalized_tweets = (total_month_tweets / prebirth_baseline) * 100
	
	* Generate confidence intervals
	gen se = sd_total / sqrt(n)
	gen ci_lower_raw = total_month_tweets - 1.96 * se
	gen ci_upper_raw = total_month_tweets + 1.96 * se
	gen ci_lower = (ci_lower_raw / prebirth_baseline) * 100
	gen ci_upper = (ci_upper_raw / prebirth_baseline) * 100
	
	*--------------------------------------------------------------------------
	* STEP 3: Create normalized OVERALL trend lines
	*--------------------------------------------------------------------------
	* Pre-birth trend line (using overall average)
	gen pred_prebirth_raw = `pre_intercept' + `pre_slope' * months_from_birth ///
		if months_from_birth >= -18 & months_from_birth <= -9
	gen pred_prebirth = (pred_prebirth_raw / `overall_prebirth_avg') * 100
	
	* Post-birth trend line (using overall average)
	gen pred_postbirth_raw = `post_intercept' + `post_slope' * months_from_birth ///
		if months_from_birth >= 0 & months_from_birth <= 17
	gen pred_postbirth = (pred_postbirth_raw / `overall_prebirth_avg') * 100
	
	*--------------------------------------------------------------------------
	* STEP 4: Create the graph
	*--------------------------------------------------------------------------
	twoway ///
		(line normalized_tweets months_from_birth if volume_quintile==1, lwidth(medthick) lcolor(blue)) ///
		(line normalized_tweets months_from_birth if volume_quintile==2, lwidth(medthick) lcolor(green)) ///
		(line normalized_tweets months_from_birth if volume_quintile==3, lwidth(medthick) lcolor(orange)) ///
		(line normalized_tweets months_from_birth if volume_quintile==4, lwidth(medthick) lcolor(red)) ///
		(line normalized_tweets months_from_birth if volume_quintile==5, lwidth(medthick) lcolor(purple)) ///
		(line pred_prebirth months_from_birth, lwidth(thick) lcolor(black) lpattern(dash)) ///
		(line pred_postbirth months_from_birth, lwidth(thick) lcolor(black) lpattern(dash)) ///
		, xline(0, lpattern(dash) lcolor(black)) ///
		  yline(100, lpattern(dash) lcolor(gs10)) ///
		  ytitle("Tweet Volume (% of Pre-Birth Average)") ///
		  xtitle("Months from Birth") ///
		  title("Female Tweeting Frequency by Quintile with Overall Trend Lines") ///
		  subtitle("(Normalized to Pre-Birth Baseline = 100%)") ///
		  legend(order(1 2 3 4 5 6) ///
				 label(1 "Q1 (Lowest)") label(2 "Q2") label(3 "Q3") ///
				 label(4 "Q4") label(5 "Q5 (Highest)") ///
				 label(6 "Overall Trend") ///
				 position(2) ring(0)) ///
		  note("Note: Each quintile normalized to its own pre-birth average." ///
			   "Trend lines based on all female data combined." ///
			   "Pre-trend: months -18 to -9. Post-trend: months 0 to 17." ///
			   "Sample: 2,481 female accounts") ///
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
	graph export "$volume_figs/twt_behavior/quintiles/female_Q_preg_trend.jpg", replace
restore



*------------------------------------------------------------------------------
* PREGNANCY REGRESSION TABLES: Pre, Post, and Interaction (All Females)
*------------------------------------------------------------------------------
preserve
    * Keep only female accounts
    keep if female == 1
    
    * Collapse to get average tweets per user per month
    collapse (mean) total_month_tweets, by(author_id months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(months_from_birth)
    
    * Regression 1: Pre-birth period (-18 to -9)
    reg total_month_tweets months_from_birth if months_from_birth >= -18 & months_from_birth <= -9
    estimates store pre_birth
    
    * Regression 2: Post-birth period (0 to 17)
    reg total_month_tweets months_from_birth if months_from_birth >= 0 & months_from_birth <= 17
    estimates store post_birth
    
    * Regression 3: Interaction model
    keep if (months_from_birth >= -18 & months_from_birth <= -9) | ///
            (months_from_birth >= 0 & months_from_birth <= 17)
    
    * Create indicator for post-birth period
    gen post_birth = (months_from_birth >= 0)
    
    * Create interaction term
    gen post_X_months = post_birth * months_from_birth
    
    * Run regression with interaction
    reg total_month_tweets months_from_birth post_birth post_X_months
    estimates store interaction
    
    * Export to Word document
    esttab pre_birth post_birth interaction using "$volume_figs/twt_behavior/regressions/female_preg_reg.rtf", ///
        replace ///
        title("Female Tweeting Trends: Pre-Pregnancy, Post-Birth, and Interaction Models") ///
        mtitles("Pre-Birth" "Post-Birth" "Interaction") ///
        b(3) se(3) ///
        star(* 0.10 ** 0.05 *** 0.01) ///
        stats(N r2 r2_a, fmt(0 3 3) labels("Observations" "R-squared" "Adj. R-squared")) ///
        nonotes ///
        addnotes("Pre-Pregnancy: Months -18 to -9" ///
                 "Post-Birth: Months 0 to 17" ///
                 "Interaction: Tests difference in slopes between pre and post periods")
restore
