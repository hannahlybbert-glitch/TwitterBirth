// Author: Hannah Lybbert
// Created: 01/26/2026
// Purpose: MALES --> Normalized Q1 + trend line + regressions 

*------------------------------------------------------------------------------
* Q1 MALE ONLY with trend lines
*------------------------------------------------------------------------------
preserve
	* Keep only  Males
	keep if female == 0
	
	* Save the original data before any collapsing
	tempfile original_data
	save `original_data'
	
	*--------------------------------------------------------------------------
	* STEP 1: Calculate Q1 for males
	*--------------------------------------------------------------------------
	use `original_data', clear
	
	* Calculate total tweets per user
	bysort author_id: egen user_total_tweets = total(total_month_tweets)
	
	* Create quintiles for  Males
	xtile volume_quintile = user_total_tweets, nquantiles(5)
	
	* Keep only Q1
	keep if volume_quintile == 1
	
	save `original_data', replace
	
	*--------------------------------------------------------------------------
	* STEP 2: Calculate trend lines for Q1  Males
	*--------------------------------------------------------------------------
	use `original_data', clear
	
	collapse (mean) total_month_tweets, by(author_id months_from_birth)
	collapse (mean) total_month_tweets, by(months_from_birth)
	
	* Pre-birth regression (-18 to -9)
	reg total_month_tweets months_from_birth if months_from_birth >= -18 & months_from_birth <= -9
	local pre_intercept = _b[_cons]
	local pre_slope = _b[months_from_birth]
	
	* Post-birth regression (1 to 17)
	reg total_month_tweets months_from_birth if months_from_birth >= 0 & months_from_birth <= 17
	local post_intercept = _b[_cons]
	local post_slope = _b[months_from_birth]
	
	* Calculate pre-birth average for normalization
	sum total_month_tweets if months_from_birth < 0
	local prebirth_avg = r(mean)
	
	*--------------------------------------------------------------------------
	* STEP 3: Create Q1 time series
	*--------------------------------------------------------------------------
	use `original_data', clear
	
	* Collapse by months_from_birth
	collapse (mean) total_month_tweets, by(author_id months_from_birth)
	collapse (mean) total_month_tweets ///
			 (sd)   sd_total = total_month_tweets ///
			 (count) n = total_month_tweets, ///
			 by(months_from_birth)
	
	* Calculate pre-birth baseline
	egen prebirth_avg_check = mean(total_month_tweets) if months_from_birth < 0
	egen prebirth_baseline = max(prebirth_avg_check)
	drop prebirth_avg_check
	
	* Normalize to pre-birth baseline
	gen normalized_tweets = (total_month_tweets / prebirth_baseline) * 100
	
	* Generate confidence intervals
	gen se = sd_total / sqrt(n)
	gen ci_lower_raw = total_month_tweets - 1.96 * se
	gen ci_upper_raw = total_month_tweets + 1.96 * se
	gen ci_lower = (ci_lower_raw / prebirth_baseline) * 100
	gen ci_upper = (ci_upper_raw / prebirth_baseline) * 100
	
	*--------------------------------------------------------------------------
	* STEP 4: Create normalized trend lines
	*--------------------------------------------------------------------------
	* Pre-birth trend line
	gen pred_prebirth_raw = `pre_intercept' + `pre_slope' * months_from_birth ///
		if months_from_birth >= -18 & months_from_birth <= -9
	gen pred_prebirth = (pred_prebirth_raw / `prebirth_avg') * 100
	
	* Post-birth trend line
	gen pred_postbirth_raw = `post_intercept' + `post_slope' * months_from_birth ///
		if months_from_birth >= 0 & months_from_birth <= 17
	gen pred_postbirth = (pred_postbirth_raw / `prebirth_avg') * 100
	
	*--------------------------------------------------------------------------
	* STEP 5: Create the graph
	*--------------------------------------------------------------------------
	twoway ///
		(rcap ci_upper ci_lower months_from_birth, lcolor(blue%30)) ///
		(line normalized_tweets months_from_birth, lwidth(medthick) lcolor(blue)) ///
		(line pred_prebirth months_from_birth, lwidth(thick) lcolor(black) lpattern(dash)) ///
		(line pred_postbirth months_from_birth, lwidth(thick) lcolor(black) lpattern(dash)) ///
		, xline(0, lpattern(dash) lcolor(edkblue)) ///
		  yline(100, lpattern(dash) lcolor(gs10)) ///
		  ytitle("Tweet Volume (% of Pre-Birth Average)") ///
		  xtitle("Months from Birth") ///
		  title("Q1 Male Tweeting Frequency with Trend Lines") ///
		  subtitle("(Lowest Volume Quintile, Normalized to Pre-Birth Baseline = 100%)") ///
		  legend(order(2 3) label(2 "Q1  Males") label(3 "Trend Lines") ///
				 position(2) ring(0)) ///
		  note("Note: Q1 = lowest 20% of male tweeters." ///
			   "Pre-trend: months -18 to -9. Post-trend: months 0 to 17." ///
			   "Sample: ~638 male accounts") ///
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
	graph export "$volume_figs/twt_behavior/quintiles/Q1_male_trendlines.jpg", replace
restore


*------------------------------------------------------------------------------
* COMPARISON 1: Pre (-18 to -9) vs Post (0 to 17)
* PREGENANCY effect
*------------------------------------------------------------------------------
preserve
    * Keep only male accounts
    keep if female == 0
    
    * Collapse to get average tweets per user per month
    collapse (mean) total_month_tweets, by(author_id months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(months_from_birth)
    
    * Keep only the periods of interest
    keep if (months_from_birth >= -18 & months_from_birth <= -9) | ///
            (months_from_birth >= 0 & months_from_birth <= 17)
    
    * Create indicator for post-birth period
    gen post_birth = (months_from_birth >= 1)
    * Create interaction term
    gen post_X_months = post_birth * months_from_birth
    
    * Run regression with interaction
    reg total_month_tweets months_from_birth post_birth post_X_months
    
    * Test if slopes are different
    test post_X_months = 0
    
restore



*------------------------------------------------------------------------------
* Q1 MALE ONLY with trend lines (-18 to -1, 0-17)
*------------------------------------------------------------------------------
preserve
	* Keep only  Males
	keep if female == 0
	
	* Save the original data before any collapsing
	tempfile original_data
	save `original_data'
	
	*--------------------------------------------------------------------------
	* STEP 1: Calculate Q1 for  Males
	*--------------------------------------------------------------------------
	use `original_data', clear
	
	* Calculate total tweets per user
	bysort author_id: egen user_total_tweets = total(total_month_tweets)
	
	* Create quintiles for  Males
	xtile volume_quintile = user_total_tweets, nquantiles(5)
	
	* Keep only Q1
	keep if volume_quintile == 1
	
	save `original_data', replace
	
	*--------------------------------------------------------------------------
	* STEP 2: Calculate trend lines for Q1  Males
	*--------------------------------------------------------------------------
	use `original_data', clear
	
	collapse (mean) total_month_tweets, by(author_id months_from_birth)
	collapse (mean) total_month_tweets, by(months_from_birth)
	
	* Pre-birth regression (-18 to -9)
	reg total_month_tweets months_from_birth if months_from_birth >= -18 & months_from_birth <= 0
	local pre_intercept = _b[_cons]
	local pre_slope = _b[months_from_birth]
	
	* Post-birth regression (1 to 17)
	reg total_month_tweets months_from_birth if months_from_birth >= 0 & months_from_birth <= 17
	local post_intercept = _b[_cons]
	local post_slope = _b[months_from_birth]
	
	* Calculate pre-birth average for normalization
	sum total_month_tweets if months_from_birth < 0
	local prebirth_avg = r(mean)
	
	*--------------------------------------------------------------------------
	* STEP 3: Create Q1 time series
	*--------------------------------------------------------------------------
	use `original_data', clear
	
	* Collapse by months_from_birth
	collapse (mean) total_month_tweets, by(author_id months_from_birth)
	collapse (mean) total_month_tweets ///
			 (sd)   sd_total = total_month_tweets ///
			 (count) n = total_month_tweets, ///
			 by(months_from_birth)
	
	* Calculate pre-birth baseline
	egen prebirth_avg_check = mean(total_month_tweets) if months_from_birth < 0
	egen prebirth_baseline = max(prebirth_avg_check)
	drop prebirth_avg_check
	
	* Normalize to pre-birth baseline
	gen normalized_tweets = (total_month_tweets / prebirth_baseline) * 100
	
	* Generate confidence intervals
	gen se = sd_total / sqrt(n)
	gen ci_lower_raw = total_month_tweets - 1.96 * se
	gen ci_upper_raw = total_month_tweets + 1.96 * se
	gen ci_lower = (ci_lower_raw / prebirth_baseline) * 100
	gen ci_upper = (ci_upper_raw / prebirth_baseline) * 100
	
	*--------------------------------------------------------------------------
	* STEP 4: Create normalized trend lines
	*--------------------------------------------------------------------------
	* Pre-birth trend line
	gen pred_prebirth_raw = `pre_intercept' + `pre_slope' * months_from_birth ///
		if months_from_birth >= -18 & months_from_birth <= 0
	gen pred_prebirth = (pred_prebirth_raw / `prebirth_avg') * 100
	
	* Post-birth trend line
	gen pred_postbirth_raw = `post_intercept' + `post_slope' * months_from_birth ///
		if months_from_birth >= 0 & months_from_birth <= 17
	gen pred_postbirth = (pred_postbirth_raw / `prebirth_avg') * 100
	
	*--------------------------------------------------------------------------
	* STEP 5: Create the graph
	*--------------------------------------------------------------------------
	twoway ///
		(rcap ci_upper ci_lower months_from_birth, lcolor(blue%30)) ///
		(line normalized_tweets months_from_birth, lwidth(medthick) lcolor(blue)) ///
		(line pred_prebirth months_from_birth, lwidth(thick) lcolor(black) lpattern(dash)) ///
		(line pred_postbirth months_from_birth, lwidth(thick) lcolor(black) lpattern(dash)) ///
		, xline(0, lpattern(dash) lcolor(edkblue)) ///
		  yline(100, lpattern(dash) lcolor(gs10)) ///
		  ytitle("Tweet Volume (% of Pre-Birth Average)") ///
		  xtitle("Months from Birth") ///
		  title("Q1 Male Tweeting Frequency with Trend Lines") ///
		  subtitle("(Lowest Volume Quintile, Normalized to Pre-Birth Baseline = 100%)") ///
		  legend(order(2 3) label(2 "Q1 Males") label(3 "Trend Lines") ///
				 position(2) ring(0)) ///
		  note("Note: Q1 = lowest 20% of male tweeters." ///
			   "Pre-trend: months -18 to -1. Post-trend: months 0 to 17." ///
			   "Sample: ~638 male accounts") ///
		  graphregion(color(white)) ///
		  xlabel(-18(2)18)
	graph export "$volume_figs/twt_behavior/quintiles/Q1_male_pre_post.jpg", replace
restore


*------------------------------------------------------------------------------
* COMPARISON 2: Pre (-18 to -1) vs Post (0 to 17)
* BIRTH effect 
*------------------------------------------------------------------------------
preserve
    * Keep only male accounts
    keep if female == 0
    
    * Collapse to get average tweets per user per month
    collapse (mean) total_month_tweets, by(author_id months_from_birth)
    collapse (mean) total_month_tweets ///
             (sd)   sd_total = total_month_tweets ///
             (count) n = total_month_tweets, ///
             by(months_from_birth)
    
    * Keep only the periods of interest
    keep if (months_from_birth >= -18 & months_from_birth <= -1) | ///
            (months_from_birth >= 0 & months_from_birth <= 17)
    
    * Create indicator for post-birth period
    gen post_birth = (months_from_birth >= 0)
    * Create interaction term
    gen post_X_months = post_birth * months_from_birth
    
    * Run regression with interaction
    reg total_month_tweets months_from_birth post_birth post_X_months
    
    * Test if slopes are different
    test post_X_months = 0
    
restore


