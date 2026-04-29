** MFT analysis


// import delimited using "$sentiment/output/multi_dim_classified_SAMPLE.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
//
// import delimited using "$sentiment/output/multi_dim_classified_SAMPLE_1mo_drop.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear


// import delimited using "$sentiment/output/multi_dim_classified_FULL.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

import delimited using "$sentiment/output/multi_dim_classified_FULL_1mo_drop.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear


browse
// import delimited using "$sentiment/output/fam_politics_classified_SAMPLE.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
// import delimited using "$sentiment/output/fam_politics_classified_bigseed_SAMPLE.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear


** CLEANING / DATA PREP 
	* STRING --> INTEGERS
	gen tweet_id_clean = subinstr(tweet_id, "'", "", .)
	drop tweet_id
	rename tweet_id_clean tweet_id
	gen author_id_clean = subinstr(author_id, "'", "", .)
	drop author_id
	rename author_id_clean author_id

	* DESTRING
	foreach var in date_birth female date_birth_tweet created_at days_from_birth week_from_birth months_from_birth full_3years no_rt_reply tweet_postba post_birth acct_tweeted_postba like_count retweet_count reply_count quote_count post family_sim politics_sim religion_sim sports_sim fam_pol_score {
		destring `var', replace
	}
	
	* DATE VARS
	format created_at date_birth date_birth_tweet %td

	* RESTRICT 18 pre/18 post
	keep if abs(months_from_birth) <= 18
	
order unique_id author_id date_birth female date_birth_tweet tweet_id text created_at days_from_birth week_from_birth months_from_birth post_birth tweet_postba acct_tweeted_postba like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls full_3years no_rt_reply 

**# Uncomment this when I run the full sample
// save "$sentiment/output/multi_dim_classified_CLEAN.dta", replace
save "$sentiment/output/multi_dim_classified_1mo_drop_CLEAN.dta", replace


****************************** FIGURES ************************************
// use "$sentiment/output/multi_dim_classified_CLEAN.dta", clear
use "$sentiment/output/multi_dim_classified_1mo_drop_CLEAN.dta", clear

************ FAMILY **************
preserve
collapse (mean) family_sim, by(week_from_birth)

	* Average family rating pre/post birth
	sum family_sim if week_from_birth < 0
	local pre_birth_avg = r(mean)

	sum family_sim if week_from_birth > 0
	local post_birth_avg = r(mean)

** PLOT (total tweets)
twoway (line family_sim week_from_birth, lwidth(medthick) lcolor(blue)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
		 yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
		 ytitle("Avg Family-Tweet score") ///
         xtitle("Weeks from Birth") ///
         title("How 'family oriented' are tweets pre/post Birth?") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78)
* Save graph
graph export "$MFT_figs/fam_sim.jpg", replace
// graph export "$MFT_figs/fam_sim_1mo_drop.jpg", replace
restore


** Fam sim pre/post (MONTH)
preserve
collapse (mean) family_sim, by(months_from_birth)

	* Average family rating pre/post birth
	sum family_sim if months_from_birth < 0
	local pre_birth_avg = r(mean)

	sum family_sim if months_from_birth > 0
	local post_birth_avg = r(mean)

** PLOT (total tweets)
twoway (line family_sim months_from_birth, lwidth(medthick) lcolor(blue)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
		 yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
         ytitle("Avg Sentiment by User by Month") ///
         xtitle("Months from Birth") ///
         title("How 'family oriented' are tweets pre/post Birth?") ///
         graphregion(color(white)) ///
         xlabel(-18(2)18)
* Save graph
graph export "$MFT_figs/fam_sim_month.jpg", replace
// graph export "$MFT_figs/fam_sim_month_1mo_drop.jpg", replace
restore




************ POLITICS **************
** Pol Sim pre/post
preserve
collapse (mean) politics_sim, by(week_from_birth)

	* Average politics rating pre/post birth
	sum politics_sim if week_from_birth < 0
	local pre_birth_avg = r(mean)

	sum politics_sim if week_from_birth > 0
	local post_birth_avg = r(mean)

** PLOT (total tweets)
twoway (line politics_sim week_from_birth, lwidth(medthick) lcolor(blue)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
		 yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
		 ytitle("Avg Politics-Tweet score") ///
         xtitle("Weeks from Birth") ///
         title("How 'politically oriented' are tweets pre/post Birth?") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78)
* Save graph
graph export "$MFT_figs/pol_sim.jpg", replace
// graph export "$MFT_figs/pol_sim_1mo_drop.jpg", replace
restore


** Pol sim pre/post (MONTH)
preserve
collapse (mean) politics_sim, by(months_from_birth)

	* Average politics rating pre/post birth
	sum politics_sim if months_from_birth < 0
	local pre_birth_avg = r(mean)

	sum politics_sim if months_from_birth > 0
	local post_birth_avg = r(mean)

** PLOT (total tweets)
twoway (line politics_sim months_from_birth, lwidth(medthick) lcolor(blue)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
		 yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
         ytitle("Avg Sentiment by User by Month") ///
         xtitle("Months from Birth") ///
         title("How 'politically oriented' are tweets pre/post Birth?") ///
         graphregion(color(white)) ///
         xlabel(-18(2)18)
* Save graph
graph export "$MFT_figs/pol_sim_month.jpg", replace
// graph export "$MFT_figs/pol_sim_month_1mo_drop.jpg", replace
restore


**** CONFIDENCE INTERVAL FIGURES ****

// use "$sentiment/output/multi_dim_classified_CLEAN.dta", clear
use "$sentiment/output/multi_dim_classified_1mo_drop_CLEAN.dta", clear

** FAMILY
preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) family_sim (sd) sd_family_sim = family_sim (count) n = family_sim, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_family_sim / sqrt(n)
	gen ci_lower = family_sim - 1.96 * se
	gen ci_upper = family_sim + 1.96 * se
	* Compute pre/post averages for dashed lines
	sum family_sim if months_from_birth < 0
	local pre_birth_avg = r(mean)
	sum family_sim if months_from_birth >= 0
	local post_birth_avg = r(mean)
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
    (line family_sim months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
      yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
      yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
	  legend(order(2 1) ///
		  label(2 "Avg Family-Tweet") ///
		  label(1 "95% CI") ///
		  position(2) ring(0)) ///
      ytitle("Avg 'Family' tweet score by Month") ///
      xtitle("Months from Birth") ///
      title("Family-Oriented Tweets Pre/Post Birth (95% CIs, no BM)") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18)
// graph export "$MFT_figs/family_CI.jpg", replace
graph export "$MFT_figs/family_CI_1mo_drop.jpg", replace
restore


*** FAMILY - POLITICS SCORE
preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) fam_pol_score (sd) sd_fam_pol = fam_pol_score (count) n = fam_pol_score, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_fam_pol / sqrt(n)
	gen ci_lower = fam_pol_score - 1.96 * se
	gen ci_upper = fam_pol_score + 1.96 * se
	* Compute pre/post averages for dashed lines
	sum fam_pol_score if months_from_birth < 0
	local pre_birth_avg = r(mean)
	sum fam_pol_score if months_from_birth >= 0
	local post_birth_avg = r(mean)
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
    (line fam_pol_score months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
      yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
      yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
	  legend(order(1) ///
		  label(1 "95% CI") ///
		  position(2) ring(0)) ///
      ytitle("Avg family-politics score by Month") ///
      xtitle("Months from Birth") ///
      title("Family-Poitics Score Pre/Post Birth (95% CIs, no BM)") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18)
// graph export "$MFT_figs/fam_pol_CI.jpg", replace
graph export "$MFT_figs/fam_pol_CI_1mo_drop.jpg", replace
restore


** POLITICS
preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) politics_sim (sd) sd_politics_sim = politics_sim (count) n = politics_sim, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_politics_sim / sqrt(n)
	gen ci_lower = politics_sim - 1.96 * se
	gen ci_upper = politics_sim + 1.96 * se
	* Compute pre/post averages for dashed lines
	sum politics_sim if months_from_birth < 0
	local pre_birth_avg = r(mean)
	sum politics_sim if months_from_birth >= 0
	local post_birth_avg = r(mean)
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
    (line politics_sim months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
      yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
      yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
	  legend(order(2 1) ///
		  label(2 "Avg Political-Tweet") ///
		  label(1 "95% CI") ///
		  position(2) ring(0)) ///
      ytitle("Avg 'Political' tweet score by Month") ///
      xtitle("Months from Birth") ///
      title("Politics-Oriented Tweets Pre/Post Birth (95% CIs, no BM)") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18)
// graph export "$MFT_figs/politics_CI.jpg", replace
graph export "$MFT_figs/politics_CI_1mo_drop.jpg", replace
restore