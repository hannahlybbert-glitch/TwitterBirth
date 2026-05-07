******** SAMPLE SENTIMENT ANALYSIS ********

** Data from Python VADER analysis (sample)
// import delimited using "$sentiment/output/sentimentVADER/tweet_sentiment_FULL.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
// import delimited using "$sentiment/output/sentimentVADER/tweet_sentiment_FULL_1mo_drop.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
// import delimited using "$sentiment/output/sentimentVADER/vader_sentiment_Kcode_FULL.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
// import delimited using "$sentiment/output/tweetNLP/sentiment_scores10k_mypipe.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
import delimited using "$sentiment/output/tweetNLP/sentiment_scoresFULL.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear


** CLEANING / DATA PREP 
	* STRING --> INTEGERS
	gen tweet_id_clean = subinstr(tweet_id, "'", "", .)
	drop tweet_id
	rename tweet_id_clean tweet_id
	gen author_id_clean = subinstr(author_id, "'", "", .)
	drop author_id
	rename author_id_clean author_id

	* DATE VARIABLES
	destring created_at date_birth date_birth_tweet, replace
	format created_at date_birth date_birth_tweet %td

	* DESTRING 
	foreach var in like_count retweet_count reply_count quote_count neg	neu pos sentiment_score post_birth days_from_birth week_from_birth months_from_birth full_3years no_rt_reply tweet_postba acct_tweeted_postba female {
		destring `var', replace
	}


// 	** Generate needed variables
// 	gen months_from_birth = floor(days_from_birth / 30)
// 	gen week_from_birth = floor(days_from_birth / 7)

	* RESTRICT 18 pre/18 post (cannot be more than 18mo pre/post)
	keep if abs(months_from_birth) <= 18
	
order unique_id author_id tweet_id created_at date_birth date_birth_tweet text like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls

// save "$sentiment/output/sentimentVADER/tweet_sentiment_CLEAN.dta", replace
// save "$sentiment/output/sentimentVADER/tweet_sentiment_CLEAN_1mo_drop.dta", replace
// save "$sentiment/output/sentimentVADER/vader_sentiment_Kcode_CLEAN.dta", replace
// save "$sentiment/output/sentiment_scores10k.dta", replace
save "$sentiment/output/sentiment_scoresFULL.dta", replace

	drop if abs(days_from_birth) <= 14 // 
	save "$sentiment/output/sentiment_scores_1modrop.dta", replace



* --------------- REGRESSIONS ------------------ *
// use "$sentiment/output/sentiment_scores10k.dta", clear
use "$sentiment/output/sentiment_scoresFULL.dta", clear

areg sentiment_score post_birth, absorb(author_id)

** by Month
	* Pre: 18 → 0
	forvalues i = 18(-1)2 {
		gen _`i'pre = (months_from_birth == -`i')
	}

	* Post: 0 → 18
	forvalues i = 0/18 {
		gen _`i'post = (months_from_birth == `i')
	}


* ----- Plot BETAS ----- *
preserve
areg sentiment_score _*, absorb(author_id)
// areg sentiment_score _*post _*pre, absorb(author_id) baselevels // ommits _1pre

parmest, norestore // extract coefficient
keep if substr(parm,1,1) == "_"   // keeps only the dummies
* Add months variable back in
	gen month = .
	replace month = -real(substr(parm,2,strpos(parm,"pre")-2)) if strpos(parm,"pre")>0
	replace month =  real(substr(parm,2,strpos(parm,"post")-2)) if strpos(parm,"post")>0

* Rename vars
	rename estimate beta
	rename stderr se

* PLOT
twoway ///
    (rcap min95 max95 month, lcolor(gs10)) ///
    (scatter beta month, mcolor(blue)) ///
    (line beta month, lcolor(blue)) ///
    , yline(0, lcolor(red)) xline(0, lcolor(black)) ///
      xlabel(-18(2)18) ///
	  ylabel(-0.2(0.2)0.4) ///
      xtitle("Months from Birth") ///
      ytitle("Effect on Neutral Tweets") ///
      title("Fixed Effect Sentiment Score Coefficients (base = 1mo pre)") ///
	  legend(label(1 "95% CI") label(2 "Coefficient") position(2) ring(0))
graph export "$tweetNLP_figs/sentiment_coeffs.jpg", replace
restore



* --------------- Preliminary figures --------------- *
// use "$sentiment/output/sentimentVADER/tweet_sentiment_CLEAN.dta", clear
// use "$sentiment/output/sentimentVADER/tweet_sentiment_CLEAN_1mo_drop.dta", clear
// use "$sentiment/output/sentimentVADER/vader_sentiment_Kcode_CLEAN.dta", clear
// use "$sentiment/output/sentimentVADER/vader_posneg_Kcode_CLEAN.dta", clear
use "$sentiment/output/sentiment_scores_1modrop.dta", clear
// use "$sentiment/output/sentiment_scoresFULL.dta", clear

** Simple Sentiment pre/post
preserve
collapse (mean) sentiment_score, by(week_from_birth)

	* Average family rating pre/post birth
	sum sentiment_score if week_from_birth < 0
	local pre_birth_avg = r(mean)
	sum sentiment_score if week_from_birth >= 0
	local post_birth_avg = r(mean)

** PLOT (total tweets)
twoway (line sentiment_score week_from_birth, lwidth(medthick) lcolor(blue)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
	     yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
		 yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
         ytitle("Avg Sentiment by User by Week (Pos-Neg)") ///
         xtitle("Weeks from Birth") ///
         title("Tweeting Sentiment Pre/Post Birth (no Birth Month)") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78)
* Save graph
graph export "$tweetNLP_figs/sentiment_score_noBM.jpg", replace
// graph export "$sentiment_figs/tweet_sentiment_FULL_1mo_drop.jpg", replace
restore


** Simple Sentiment pre/post (MONTH)
preserve
collapse (mean) sentiment_score, by(months_from_birth)

	* Average family rating pre/post birth
	sum sentiment_score if months_from_birth < 0
	local pre_birth_avg = r(mean)
	sum sentiment_score if months_from_birth >= 0
	local post_birth_avg = r(mean)

** PLOT (total tweets)
twoway (line sentiment_score months_from_birth, lwidth(medthick) lcolor(blue)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
	     yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
		 yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
         ytitle("Avg Sentiment by User by Month (Pos-Neg)") ///
         xtitle("Months from Birth") ///
         title("Tweeting Sentiment Pre/Post Birth (no Birth Month)") ///
         graphregion(color(white)) ///
         xlabel(-18(2)18)
* Save graph
graph export "$tweetNLP_figs/sentiment_scoreMONTH_noBM.jpg", replace
// graph export "$sentiment_figs/tweet_sentiment_byMONTH_FULL_1mo_drop.jpg", replace
restore
	
	
*----------------- FILLED BAR -----------------*
// use "$sentiment/output/sentiment_scoresFULL.dta", clear
use "$sentiment/output/sentiment_scores_1modrop.dta", clear

// preserve
gen pos_count = (sentiment== "positive")
gen neg_count = (sentiment== "negative")
gen neu_count = (sentiment== "neutral")
collapse (sum) pos_count neg_count neu_count, by(months_from_birth)
gen total = pos_count+neg_count+neu_count
gen posi_share = pos_count/total
gen nega_share = neg_count/total
gen neut_share = neu_count/total

* Generate cumulative shares for stacked plotting
gen posi_cum = posi_share
gen neut_cum = posi_share + neut_share
gen nega_cum = posi_share + neut_share + nega_share   // should = 1
gen zero = 0

* Stacked filled area graph
twoway ///
    (rarea nega_cum neut_cum months_from_birth, color(eltblue)) ///      // negative area (top)
    (rarea neut_cum posi_cum months_from_birth, color(dknavy))  ///      // neutral area (middle)
    (rarea posi_cum zero months_from_birth, color(cranberry))         ///      // positive area (bottom)
    , ///
      legend(order(3 "Positive" 2 "Neutral" 1 "Negative") pos(6)) ///
      xtitle("Months from Birth") ///
      ytitle("Share of Tweets") ///
      ylabel(0(0.2)1) ///
      xlabel(-18(2)18) ///
      title("Tweet Sentiment Composition Around Birth (no Birth Month)") ///
      yscale(range(0 1))
graph export "$tweetNLP_figs/stacked_line_sentiment_noBM.jpg", replace
	
	
	
*----------------- CONFIDENCE INTERVAL TEST -----------------*
// use "$sentiment/output/sentiment_scoresFULL.dta", clear
use "$sentiment/output/sentiment_scores_1modrop.dta", clear

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
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
    (line sentiment_score months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
      yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
      yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Sentiment") ///
		  label(1 "95% CI") ///
		  position(2) ring(0)) ///
      ytitle("Avg Sentiment by User by Month") ///
      xtitle("Months from Birth") ///
      title("Tweeting Sentiment Pre/Post Birth (no BA)") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18) 
graph export "$tweetNLP_figs/sentiment_score95CI.jpg", replace
restore
	
** Positive 
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
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
    (line pos months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
      yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
      yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Positivity") ///
		  label(1 "95% CI") ///
		  position(2) ring(0)) ///
      ytitle("Avg Positivity by User") ///
      xtitle("Months from Birth") ///
      title("Positive Tweeting Pre/Post Birth (no BA)") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18) 
graph export "$tweetNLP_figs/pos_score95CI.jpg", replace
restore

** NEGATIVE
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
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
    (line neg months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
      yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
      yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Negativity") ///
		  label(1 "95% CI") ///
		  position(2) ring(0)) ///
      ytitle("Avg Negativity by User") ///
      xtitle("Months from Birth") ///
      title("Negative Tweeting Pre/Post Birth (no BA)") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18) 
graph export "$tweetNLP_figs/neg_score95CI.jpg", replace
restore

** NEUTRAL
preserve
	* Collapse to mean and standard deviation by month
	collapse (mean) neu (sd) sd_compound = neu (count) n = neu, by(months_from_birth)
	* Standard error and 95% confidence intervals
	gen se = sd_compound / sqrt(n)
	gen ci_lower = neu - 1.96 * se
	gen ci_upper = neu + 1.96 * se
	* Compute pre/post averages for dashed lines
	sum neu if months_from_birth < 0
	local pre_birth_avg = r(mean)
	sum neu if months_from_birth >= 0
	local post_birth_avg = r(mean)
twoway ///
    (rcap ci_upper ci_lower months_from_birth, lcolor(navy)) ///
    (line neu months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
      yline(`pre_birth_avg', lcolor(red) lpattern(dash)) ///
      yline(`post_birth_avg', lcolor(green) lpattern(dash)) ///
	  legend(order(2 1 3 4) ///
		  label(2 "Avg Neutrality") ///
		  label(1 "95% CI") ///
		  position(2) ring(0)) ///
      ytitle("Avg Neutrality by User by Month") ///
      xtitle("Months from Birth") ///
      title("Neutral Tweeting Pre/Post Birth (no BA)") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18) 
graph export "$tweetNLP_figs/neu_score95CI.jpg", replace
restore


*----------------- BY GENDER -----------------*
// use "$sentiment/output/sentiment_scoresFULL.dta", clear
use "$sentiment/output/sentiment_scores_1modrop.dta", clear
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
      legend(order(2 "Female Avg" 1 "Female 95% CI" ///
                   4 "Male Avg"   3 "Male 95% CI") ///
             position(2) ring(0)) ///
      ytitle("Avg Sentiment") ///
      xtitle("Months from Birth") ///
      title("Sentiment Around Birth by Gender") ///
      graphregion(color(white)) ///
      xlabel(-18(2)18)
graph export "$tweetNLP_figs/sentiment_gender.jpg", replace
restore



*** Averages pre/post male/female ***
preserve
* Collapse to month × gender
collapse (mean) sentiment_score (sd) sd_compound = sentiment_score (count) n = sentiment_score, ///
    by(months_from_birth female)

* Compute SE and 95% CI
gen se       = sd_compound / sqrt(n)
gen ci_lower = sentiment_score - 1.96 * se
gen ci_upper = sentiment_score + 1.96 * se

* Female averages
sum sentiment_score if female==1 & months_from_birth < 0
local fem_pre_avg = r(mean)
sum sentiment_score if female==1 & months_from_birth >= 0
local fem_post_avg = r(mean)

* Male averages
sum sentiment_score if female==0 & months_from_birth < 0
local male_pre_avg = r(mean)
sum sentiment_score if female==0 & months_from_birth >= 0
local male_post_avg = r(mean)

twoway ///
    (rcap ci_upper ci_lower months_from_birth if female==1, lcolor(red)) ///
    (line sentiment_score months_from_birth if female==1, lcolor(red) lwidth(medthick)) ///
    (rcap ci_upper ci_lower months_from_birth if female==0, lcolor(blue)) ///
    (line sentiment_score months_from_birth if female==0, lcolor(blue) lwidth(medthick)) ///
    , ///
      yline(`fem_pre_avg',  lcolor(ebg)  lpattern(dash)) ///
      yline(`fem_post_avg', lcolor(gray)  lpattern(dash)) ///
      yline(`male_pre_avg', lcolor(ebg) lpattern(dash)) ///
      yline(`male_post_avg', lcolor(gray) lpattern(dash)) ///
      xlabel(-18(2)18) ///
      xtitle("Months from Birth") ///
      ytitle("Avg Sentiment") ///
      title("Sentiment Around Birth by Gender (no Birth Month)") ///
      graphregion(color(white)) ///
      legend(order(2 "Female Avg"  ///
                   4 "Male Avg") ///
             position(4) ring(0))
graph export "$tweetNLP_figs/sentiment_score_gende_noBM.jpg", replace
restore



* --------------- HAND CODED SAMPLE ---------------*
import delimited using "$sentiment/output/LLM_topic_classifier100.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
tempfile LLM_classif
save `LLM_classif', replace

import delimited using "$sentiment/output/tweetNLP/NLP_topic_classifier100.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
merge 1:1 tweet_id using `LLM_classif'
drop _merge

** CLEANING / DATA PREP 
	* STRING --> INTEGERS
	gen tweet_id_clean = subinstr(tweet_id, "'", "", .)
	drop tweet_id
	rename tweet_id_clean tweet_id
	gen author_id_clean = subinstr(author_id, "'", "", .)
	drop author_id
	rename author_id_clean author_id

	* DATE VARIABLES
	destring created_at date_birth date_birth_tweet, replace
	format created_at date_birth date_birth_tweet %td

	* DESTRING 
	foreach var in like_count retweet_count reply_count quote_count post_birth days_from_birth week_from_birth months_from_birth full_3years no_rt_reply tweet_postba acct_tweeted_postba female family_prob family_flag  {
		destring `var', replace
	}
	order unique_id author_id tweet_id created_at date_birth date_birth_tweet text like_count retweet_count reply_count quote_count tweet_type tweet_url embedded_urls media_urls


gen LLM_family_flag = (classification=="family")
gen hand_family_flag = (hand_topic=="1")

label variable family_prob "P(family tweet) tweetNLP"
label variable family_flag "If P(family tweet) > 0.5 tweetNLP"
label variable classification "LLM tweet classification (1-family, 2-politics, 3-other)"
label variable LLM_family_flag "Family related tweet LLM"
label variable hand_family_flag "Hand coded family related tweet"
label variable hand_topic "Hand coded topic (1-family, 2-politics, 3-sports, 0-other)"

rename family_flag NLP_family_flag
rename family_prob NLP_family_prob
rename classification LLM_classification
rename reasoning LLM_reasoning


save "$sentiment/output/handcode100_t1.dta", replace	

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
// merge m:1 unique_id using "$final/user_analysis_sample.dta", keepusing(date_birth user_created_at)
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