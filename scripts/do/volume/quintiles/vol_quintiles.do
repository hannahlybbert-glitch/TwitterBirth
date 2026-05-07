// Author: Hannah Lybbert
// Created: 01/26/2026
// Purpose: Volume figs by quintile and gender

use "$final/tweet_volume_analysis_sample.dta", clear


*--------------------------------------------------------------------------
* LOOP 1: SETUP
*--------------------------------------------------------------------------

* First, calculate total tweets per user across all months
bysort author_id: egen user_total_tweets = total(total_month_tweets)

* Create quintiles based on user's total tweet volume
xtile volume_quintile = user_total_tweets, nquantiles(5)

* Label the quintiles for clarity
label define quint_lab 1 "Q1 (Lowest)" 2 "Q2" 3 "Q3" 4 "Q4" 5 "Q5 (Highest)"
label values volume_quintile quint_lab

* Label female variable if not already labeled
label define female_lab 0 "Male" 1 "Female"
label values female female_lab

*--------------------------------------------------------------------------
* LOOP 1: Create 5 graphs (one for each quintile, all genders combined)
*--------------------------------------------------------------------------
forvalues q = 1/5 {
	preserve
		keep if volume_quintile == `q'
		
		collapse (mean) total_month_tweets, by(author_id months_from_birth)
		collapse (mean) total_month_tweets ///
				 (sd)   sd_total = total_month_tweets ///
				 (count) n = total_month_tweets, ///
				 by(months_from_birth)
		
		gen se = sd_total / sqrt(n)
		gen ci_lower = total_month_tweets - 1.96 * se
		gen ci_upper = total_month_tweets + 1.96 * se
		
		twoway ///
			(rcap ci_upper ci_lower months_from_birth, lcolor(gs8)) ///
			(line total_month_tweets months_from_birth, lwidth(medthick) lcolor(purple)) ///
			, xline(0, lpattern(dash) lcolor(edkblue)) ///
			  ytitle("Average Total Tweets per User") ///
			  xtitle("Months from Birth") ///
			  title("Tweeting Frequency: Quintile `q'") ///
			  legend(label(1 "95% CI") label(2 "Avg Tweets") position(2) ring(0)) ///
			  graphregion(color(white)) ///
			  xlabel(-18(2)18) ///
          note("Note: Quintiles based on user's total tweet volume across all months." ///
               "Sample Size = ~1,172 accounts (20% of 5,862)")

graph export "$volume_figs/twt_behavior/quintiles/Q`q'.jpg", replace
	restore
}




use "$final/tweet_volume_analysis_sample.dta", clear

*--------------------------------------------------------------------------
* LOOP 2 SETUP: Calculate quintiles SEPARATELY by gender
*--------------------------------------------------------------------------
* First, calculate total tweets per user across all months (if not already done)
cap drop user_total_tweets_gender
bysort author_id: egen user_total_tweets_gender = total(total_month_tweets)

* Create quintiles SEPARATELY for each gender (only for those with gender data)
cap drop volume_quintile_gender
gen volume_quintile_gender = .
xtile temp_quint = user_total_tweets_gender if female==0, nquantiles(5)
replace volume_quintile_gender = temp_quint if female==0
drop temp_quint
xtile temp_quint = user_total_tweets_gender if female==1, nquantiles(5)
replace volume_quintile_gender = temp_quint if female==1
drop temp_quint

* Label the gender-specific quintiles
label define quint_gender_lab 1 "Q1 (Lowest)" 2 "Q2" 3 "Q3" 4 "Q4" 5 "Q5 (Highest)"
label values volume_quintile_gender quint_gender_lab

*--------------------------------------------------------------------------
* LOOP 2: Create 5 graphs (one for each quintile, split by gender)
* NOW COMPARING SAME QUINTILE ACROSS GENDERS (e.g., Q1 female vs Q1 male)
*--------------------------------------------------------------------------
forvalues q = 1/5 {
	preserve
		keep if volume_quintile_gender == `q' & !missing(female)
		
		* Collapse by female AND months_from_birth
		collapse (mean) total_month_tweets, by(author_id female months_from_birth)
		collapse (mean) total_month_tweets ///
				 (sd)   sd_total = total_month_tweets ///
				 (count) n = total_month_tweets, ///
				 by(female months_from_birth)
		
		gen se = sd_total / sqrt(n)
		gen ci_lower = total_month_tweets - 1.96 * se
		gen ci_upper = total_month_tweets + 1.96 * se
		
		* Create lines and CIs for each gender (0=Male, 1=Female)
		twoway ///
			(rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue%30)) ///
			(rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red%30)) ///
			(line total_month_tweets months_from_birth if female==0, lwidth(medthick) lcolor(blue)) ///
			(line total_month_tweets months_from_birth if female==1, lwidth(medthick) lcolor(red)) ///
			, xline(0, lpattern(dash) lcolor(edkblue)) ///
			  ytitle("Average Total Tweets per User") ///
			  xtitle("Months from Birth") ///
			  title("Tweeting Frequency by Gender: Quintile `q'") ///
			  legend(order(3 4) label(3 "Male") label(4 "Female") position(2) ring(0)) ///
			  graphregion(color(white)) ///
			  xlabel(-18(2)18) ///
			  note("Note: Quintiles calculated separately by gender" ///
			  "Sample size: ~496 female accounts (20% of 2,481), and ~638 male accounts (20% of 3,190)")
		graph export "$volume_figs/twt_behavior/quintiles/Q`q'_gender.jpg", replace
	restore
}