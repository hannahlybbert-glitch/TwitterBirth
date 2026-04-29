* Author: Hannah Lybbert
* Created: 12/05/2025
* Purpose: Claude code difference dot plot 

*------ SHARE DOT PLOT ------ *
use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

preserve
	* First calculate aggregate share changes
	gen count_var = 1
	collapse (sum) total_n=count_var, by(post_birth topic)
	bysort post_birth: egen period_total = sum(total_n)
	gen proportion_agg = total_n / period_total * 100
	drop period_total
	reshape wide proportion_agg total_n, i(topic) j(post_birth)
	gen change = proportion_agg1 - proportion_agg0
	
	* Save aggregate changes
	tempfile aggregate
	save `aggregate'
	
	* Now calculate account-level changes for CIs
	restore
	preserve
	gen count_var = 1
	collapse (sum) n=count_var, by(author_id post_birth topic)
	bysort author_id post_birth: egen account_total = sum(n)
	gen proportion = n / account_total * 100
	keep author_id post_birth topic proportion
	reshape wide proportion, i(author_id topic) j(post_birth)
	replace proportion0 = 0 if proportion0 == .
	replace proportion1 = 0 if proportion1 == .
	gen change_account = proportion1 - proportion0
	
	* Calculate SE across accounts
	collapse (sd) sd_change=change_account (count) n_accounts=change_account, by(topic)
	gen se_change = sd_change / sqrt(n_accounts)
	
	* Merge with aggregate changes
	merge 1:1 topic using `aggregate', nogen
	
	* Calculate 95% CI
	gen change_ci_lower = change - 1.96 * se_change
	gen change_ci_upper = change + 1.96 * se_change
	
	* Clean up topic names for labels
	gen topic_clean = topic
	replace topic_clean = subinstr(topic_clean, "_&_", " & ", .)
	replace topic_clean = subinstr(topic_clean, "_", " ", .)
	replace topic_clean = proper(topic_clean)
	
	* Sort by change magnitude
	gsort -change
	gen order = _n
	
	* Create value labels manually for the y-axis
	label define order_labels ///
		1 "`=topic_clean[1]'" ///
		2 "`=topic_clean[2]'" ///
		3 "`=topic_clean[3]'" ///
		4 "`=topic_clean[4]'" ///
		5 "`=topic_clean[5]'" ///
		6 "`=topic_clean[6]'" ///
		7 "`=topic_clean[7]'" ///
		8 "`=topic_clean[8]'" ///
		9 "`=topic_clean[9]'" ///
		10 "`=topic_clean[10]'" ///
		11 "`=topic_clean[11]'" ///
		12 "`=topic_clean[12]'" ///
		13 "`=topic_clean[13]'" ///
		14 "`=topic_clean[14]'" ///
		15 "`=topic_clean[15]'" ///
		16 "`=topic_clean[16]'" ///
		17 "`=topic_clean[17]'" ///
		18 "`=topic_clean[18]'" ///
		19 "`=topic_clean[19]'"
	label values order order_labels
	
	* Create improved dot plot with confidence intervals
	twoway ///
		(rcap change_ci_upper change_ci_lower order, horizontal lcolor(gs10) lwidth(medthick)) ///
		(scatter order change if change >= 0, mcolor("230 159 0") msize(large) msymbol(O)) ///
		(scatter order change if change < 0, mcolor("0 114 178") msize(large) msymbol(O)), ///
		ylabel(1(1)19, valuelabel angle(0) labsize(vsmall)) ///
		ytitle("") ///
		xtitle("Change in Topic Share (Percentage Points)", size(medsmall)) ///
		xline(0, lcolor(red) lpattern(dash) lwidth(medium)) ///
		xlabel(, labsize(small) format(%3.1f)) ///
		title("Change in Tweet Topics: Pre vs Post Child Birth", size(medium)) ///
		subtitle("Aggregate-Level Changes with Account-Level CIs", size(small)) ///
		legend(order(2 "Increased" 3 "Decreased") position(2) cols(1) size(small) ring(0)) ///
		note("Change = aggregate proportion (post - pre)" ///
			 "CIs reflect variation in individual-level changes across 4,145 accounts" ///
			 "Pre-birth = months -18 to -1; Post-birth = months 1 to 18", size(vsmall)) ///
		graphregion(color(white)) plotregion(color(white)) 
	
	graph export "$tweetNLP_figs/topic_class/diff_dot_plot_SHARES.jpg", replace
	
	* Display results table
	list topic_clean change se_change change_ci_lower change_ci_upper proportion_agg0 proportion_agg1, ///
		clean noobs
	
restore











* =============================================================================================
use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

* ------------ LEVELS DOT PLOT ----------- *
preserve
	gen count_var = 1
	collapse (sum) n=count_var, by(author_id post_birth topic)
	
	* Exclude diaries & daily life
	drop if topic == "diaries_&_daily_life"
	
	* For each account-period-topic, we have the count
	* Reshape to get pre and post for each account
	keep author_id post_birth topic n
	reshape wide n, i(author_id topic) j(post_birth)
	
	* Fill missing with 0
	replace n0 = 0 if n0 == .
	replace n1 = 0 if n1 == .
	
	* Calculate change in absolute tweets for each account-topic
	gen change_account_level = n1 - n0
	
	* Get SE across accounts
	collapse (mean) mean_change_level=change_account_level ///
		(sd) sd_change_level=change_account_level ///
		(count) n_accounts=change_account_level, by(topic)
	
	gen se_change_level = sd_change_level / sqrt(n_accounts)
	
	* Merge with aggregate level changes
	tempfile account_se
	save `account_se'
restore

preserve
	
	* Count tweets by account, period, and topic
	gen count_var = 1
	collapse (sum) n=count_var, by(author_id post_birth topic)
	
	* Exclude diaries & daily life
	drop if topic == "diaries_&_daily_life"
	
	* Calculate tweets per account per period for each topic
	bysort post_birth topic: egen topic_tweets = sum(n)
	bysort post_birth topic: egen n_distinct_accounts = count(author_id)
	gen tweets_per_account = topic_tweets / n_distinct_accounts
	
	* Keep one row per period-topic
	bysort post_birth topic: keep if _n == 1
	keep post_birth topic tweets_per_account n_distinct_accounts
	
	* Calculate absolute change in level
	reshape wide tweets_per_account n_distinct_accounts, i(topic) j(post_birth)
	gen change_level = tweets_per_account1 - tweets_per_account0
	
	* Merge with SE
	merge 1:1 topic using `account_se', nogen
	
	* Calculate 95% CI
	gen change_ci_lower = change_level - 1.96 * se_change_level
	gen change_ci_upper = change_level + 1.96 * se_change_level
	
	* Clean up topic names
	gen topic_clean = topic
	replace topic_clean = subinstr(topic_clean, "_&_", " & ", .)
	replace topic_clean = subinstr(topic_clean, "_", " ", .)
	replace topic_clean = proper(topic_clean)
	
	* Sort by change
	gsort -change_level
	gen order = _n
	
	* Create labels
	label define order_labels ///
		1 "`=topic_clean[1]'" ///
		2 "`=topic_clean[2]'" ///
		3 "`=topic_clean[3]'" ///
		4 "`=topic_clean[4]'" ///
		5 "`=topic_clean[5]'" ///
		6 "`=topic_clean[6]'" ///
		7 "`=topic_clean[7]'" ///
		8 "`=topic_clean[8]'" ///
		9 "`=topic_clean[9]'" ///
		10 "`=topic_clean[10]'" ///
		11 "`=topic_clean[11]'" ///
		12 "`=topic_clean[12]'" ///
		13 "`=topic_clean[13]'" ///
		14 "`=topic_clean[14]'" ///
		15 "`=topic_clean[15]'" ///
		16 "`=topic_clean[16]'" ///
		17 "`=topic_clean[17]'" ///
		18 "`=topic_clean[18]'"
	label values order order_labels
	
	* Create dot plot for LEVELS
	twoway ///
		(rcap change_ci_upper change_ci_lower order, horizontal lcolor(gs10) lwidth(medthick)) ///
		(scatter order change_level if change_level >= 0, mcolor("230 159 0") msize(large) msymbol(O)) ///
		(scatter order change_level if change_level < 0, mcolor("0 114 178") msize(large) msymbol(O)), ///
		ylabel(1(1)18, valuelabel angle(0) labsize(vsmall)) ///
		xlabel(-10(2)1) ///
		ytitle("") ///
		xtitle("Change in Tweets per Account", size(medsmall)) ///
		xline(0, lcolor(red) lpattern(dash) lwidth(medium)) ///
		xlabel(, labsize(small) format(%3.1f)) ///
		title("Change in Tweet Volume by Topic: Pre vs Post Child Birth", size(medium)) ///
		subtitle("Absolute Level Changes (Tweets per Account per Period)", size(small)) ///
		legend(order(2 "Increased" 3 "Decreased") position(2) cols(1) size(small) ring(0)) ///
		note("Change = average tweets per account (post - pre)" ///
			 "Among accounts that tweeted about each topic" ///
			 "Pre-birth = months -18 to -1; Post-birth = months 1 to 18", size(vsmall)) ///
		graphregion(color(white)) plotregion(color(white)) ///
		note("Note: Removed 'diaries and daily life'")
	
	graph export "$tweetNLP_figs/topic_class/diff_dot_plot_LEVELS_noDDL.jpg", replace
// 	graph export "$tweetNLP_figs/topic_class/diff_dot_plot_LEVELS.jpg", replace

	
	* Display results with account counts
	list topic_clean change_level se_change_level change_ci_lower change_ci_upper ///
		tweets_per_account0 tweets_per_account1 n_distinct_accounts0 n_distinct_accounts1, ///
		clean noobs
	
restore










* ====================== OLD ITERATION CODE (not right) ============================== *

preserve
	* Count tweets by account, period, and topic
	gen count_var = 1
	collapse (sum) n=count_var, by(author_id post_birth topic)
	
	* Get total tweets per account per period
	bysort author_id post_birth: egen account_total = sum(n)
	
	* Calculate proportion for each account-period-topic
	gen proportion_account = n / account_total * 100
	
	* Now get the aggregate proportion (what we'll plot)
	* This is total tweets of topic / total tweets in period
	bysort post_birth topic: egen total_topic = sum(n)
	bysort post_birth: egen total_period = sum(n)
	gen proportion_aggregate = total_topic / total_period * 100
	
	* Keep one row per period-topic for aggregate proportions
	bysort post_birth topic: keep if _n == 1
	keep post_birth topic proportion_aggregate
	
	* Also need to calculate account-level changes for CIs
	restore
	preserve
	
	* Count tweets by account, period, and topic
	gen count_var = 1
	collapse (sum) n=count_var, by(author_id post_birth topic)
	
	* Get total tweets per account per period
	bysort author_id post_birth: egen account_total = sum(n)
	
	* Calculate proportion for each account-period-topic
	gen proportion = n / account_total * 100
	
	* Reshape to wide format (account-topic level, Pre vs Post)
	keep author_id post_birth topic proportion
	reshape wide proportion, i(author_id topic) j(post_birth)
	
	* Fill in missing values with 0
	replace proportion0 = 0 if proportion0 == .
	replace proportion1 = 0 if proportion1 == .
	
	* Calculate change for each account-topic
	gen change_account = proportion1 - proportion0
	
	* Get aggregate-level change and account-level SE
	* First, get the aggregate proportions
	bysort topic: egen sum_n0 = sum(proportion0)
	bysort topic: egen sum_n1 = sum(proportion1)
	bysort topic: egen count_accounts = count(change_account)
	
	* For aggregate change, we need total tweets per topic per period
	restore
	preserve
	gen count_var = 1
	collapse (sum) total_n=count_var, by(post_birth topic)
	bysort post_birth: egen period_total = sum(total_n)
	gen proportion_agg = total_n / period_total * 100
	drop period_total
	reshape wide proportion_agg total_n, i(topic) j(post_birth)
	gen change = proportion_agg1 - proportion_agg0
	
	* Now merge with account-level data to get SE
	tempfile aggregate
	save `aggregate'
	
	restore
	preserve
	gen count_var = 1
	collapse (sum) n=count_var, by(author_id post_birth topic)
	bysort author_id post_birth: egen account_total = sum(n)
	gen proportion = n / account_total * 100
	keep author_id post_birth topic proportion
	reshape wide proportion, i(author_id topic) j(post_birth)
	replace proportion0 = 0 if proportion0 == .
	replace proportion1 = 0 if proportion1 == .
	gen change_account = proportion1 - proportion0
	
	* Calculate SE across accounts
	collapse (sd) sd_change=change_account (count) n_accounts=change_account, by(topic)
	gen se_change = sd_change / sqrt(n_accounts)
	
	* Merge with aggregate changes
	merge 1:1 topic using `aggregate', nogen
	
	* Calculate 95% CI
	gen change_ci_lower = change - 1.96 * se_change
	gen change_ci_upper = change + 1.96 * se_change
	
	* Clean up topic names for labels
	gen topic_clean = topic
	replace topic_clean = subinstr(topic_clean, "_&_", " & ", .)
	replace topic_clean = subinstr(topic_clean, "_", " ", .)
	replace topic_clean = proper(topic_clean)
	
	* Sort by change magnitude
	gsort -change
	gen order = _n
	
	* Create value labels manually for the y-axis
	label define order_labels ///
		1 "`=topic_clean[1]'" ///
		2 "`=topic_clean[2]'" ///
		3 "`=topic_clean[3]'" ///
		4 "`=topic_clean[4]'" ///
		5 "`=topic_clean[5]'" ///
		6 "`=topic_clean[6]'" ///
		7 "`=topic_clean[7]'" ///
		8 "`=topic_clean[8]'" ///
		9 "`=topic_clean[9]'" ///
		10 "`=topic_clean[10]'" ///
		11 "`=topic_clean[11]'" ///
		12 "`=topic_clean[12]'" ///
		13 "`=topic_clean[13]'" ///
		14 "`=topic_clean[14]'" ///
		15 "`=topic_clean[15]'" ///
		16 "`=topic_clean[16]'" ///
		17 "`=topic_clean[17]'" ///
		18 "`=topic_clean[18]'" ///
		19 "`=topic_clean[19]'"
	label values order order_labels
	
	* Create improved dot plot with confidence intervals
	twoway ///
		(rcap change_ci_upper change_ci_lower order, horizontal lcolor(gs10) lwidth(medthick)) ///
		(scatter order change if change >= 0, mcolor("230 159 0") msize(large) msymbol(O)) ///
		(scatter order change if change < 0, mcolor("0 114 178") msize(large) msymbol(O)), ///
		ylabel(1(1)19, valuelabel angle(0) labsize(vsmall)) ///
		ytitle("") ///
		xtitle("Change in Topic Share (Percentage Points)", size(medsmall)) ///
		xline(0, lcolor(red) lpattern(dash) lwidth(medium)) ///
		xlabel(, labsize(small) format(%3.1f)) ///
		title("Change in Tweet Topics: Pre vs Post Child Birth", size(medium)) ///
		subtitle("Aggregate-Level Changes with Account-Level CIs", size(small)) ///
		legend(order(2 "Increased" 3 "Decreased") position(2) cols(1) size(small) ring(0)) ///
		note("Change = aggregate proportion (post - pre)" ///
			 "CIs reflect variation across 4,145 accounts" ///
			 "Pre-birth = months -18 to -1; Post-birth = months 1 to 18", size(vsmall)) ///
		graphregion(color(white)) plotregion(color(white)) 
	
	graph export "$tweetNLP_figs/topic_class/diff_dot_plot.jpg", replace
	
	* Display results table
	list topic_clean change se_change change_ci_lower change_ci_upper proportion_agg0 proportion_agg1, ///
		clean noobs sepby(order)
	
restore




* ====================== PREVIOUS CODE (not right) ============================== *

use "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN_noBM.dta", clear
* ------------ SLOPE GRAPH ------------------*
* Calculate proportions of each topic within each period
preserve
	* Create a counting variable
	gen count_var = 1

	* Count tweets by period and topic
	collapse (sum) n=count_var, by(post_birth topic)

	* Get total tweets per period
	bysort post_birth: egen total = sum(n)

	* Calculate proportion
	gen proportion = n / total * 100

	* Reshape to wide format
	keep post_birth topic proportion
	reshape wide proportion, i(topic) j(post_birth)

	* Calculate percentage point change
	gen change = proportion1 - proportion0

	* Label for clarity
	label variable change "Percentage point change (Post - Pre)"
	label variable proportion0 "Pre-period %"
	label variable proportion1 "Post-period %"

	* Sort by change magnitude
	gsort -change

* Create dot plot
graph dot change, over(topic, sort(change) label(labsize(small))) ///
    marker(1, msize(medium)) ///
    yline(0, lcolor(black) lwidth(thin)) ///
    ytitle("Change in proportion (percentage points)") ///
    title("Change in Tweet Topics: Post vs Pre Period") ///
    note("Positive values indicate topic increased in post period")
	
graph export "$tweetNLP_figs/topic_class/diff_plot.png", replace
restore


*** My own CI ***
use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear
preserve
	* Create a counting variable
	gen count_var = 1

	* Count tweets by period and topic
	collapse (sum) n=count_var, by(post_birth topic)

	* Get total tweets per period
	bysort post_birth: egen total = sum(n)

	* Calculate proportion
	gen proportion = n / total * 100
	
	* Calculate standard error for proportion
	* SE = sqrt(p*(1-p)/n) where p is proportion (as decimal)
	gen p_decimal = proportion / 100
	gen se = sqrt(p_decimal * (1 - p_decimal) / total) * 100
	
	* Calculate 95% CI
	gen ci_lower = proportion - 1.96 * se
	gen ci_upper = proportion + 1.96 * se

	* Reshape to wide format
	keep post_birth topic proportion se ci_lower ci_upper
	reshape wide proportion se ci_lower ci_upper, i(topic) j(post_birth)

	* Calculate percentage point change
	gen change = proportion1 - proportion0
	
	* Calculate SE for the difference
	* SE(diff) = sqrt(SE1^2 + SE0^2)
	gen se_change = sqrt(se1^2 + se0^2)
	
	* Calculate 95% CI for change
	gen change_ci_lower = change - 1.96 * se_change
	gen change_ci_upper = change + 1.96 * se_change

	* Label for clarity
	label variable change "Percentage point change (Post - Pre)"
	label variable proportion0 "Pre-period %"
	label variable proportion1 "Post-period %"

	* Sort by change magnitude
	gsort -change
	gen order = _n
	
	* Encode topic as a labeled numeric variable
	encode topic, gen(topic_encoded)

* Create dot plot with confidence intervals
graph dot change change_ci_lower change_ci_upper, ///
    over(topic, sort(change) label(labsize(small))) ///
    marker(1, msize(medium)) marker(2, msize(vsmall)) marker(3, msize(vsmall)) ///
    linetype(line) ///
    yline(0, lcolor(black) lwidth(thin)) ///
    ytitle("Change in proportion (percentage points)") ///
    title("Change in Tweet Topics Pre/Post Child Birth") ///
    subtitle("With 95% Confidence Intervals") ///
    note("Positive values indicate topic increased in post period") ///
    legend(order(1 "Change" 2 "95% CI lower" 3 "95% CI upper") size(small)) ///
	note("Note: Calculated using proportion of tweets in pre and post periods labeled as the given topic")
	
// graph export "$tweetNLP_figs/topic_class/diff_plot_CI.png", replace
restore

















*********************************************************
use "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN_noBM.dta", clear
* Calculate proportions of each topic within each period
preserve

* Create a counting variable
gen count_var = 1

* Count tweets by period and topic
collapse (sum) n=count_var, by(post_birth topic)

* Get total tweets per period
bysort post_birth: egen total = sum(n)

* Calculate proportion
gen proportion = n / total * 100

* Calculate standard error for proportion
* SE = sqrt(p*(1-p)/n) where p is proportion (as decimal)
gen p_decimal = proportion / 100
gen se = sqrt(p_decimal * (1 - p_decimal) / total) * 100

* Calculate 95% CI
gen ci_lower = proportion - 1.96 * se
gen ci_upper = proportion + 1.96 * se

* Reshape to wide format
keep post_birth topic proportion se ci_lower ci_upper
reshape wide proportion se ci_lower ci_upper, i(topic) j(post_birth)

* Calculate percentage point change
gen change = proportion1 - proportion0

* Calculate SE for the difference
* SE(diff) = sqrt(SE1^2 + SE0^2)
gen se_change = sqrt(se1^2 + se0^2)

* Calculate 95% CI for change
gen change_ci_lower = change - 1.96 * se_change
gen change_ci_upper = change + 1.96 * se_change

* Label for clarity
label variable change "Percentage point change (Post - Pre)"
label variable proportion0 "Pre-period %"
label variable proportion1 "Post-period %"

* Sort by change magnitude
gsort -change
gen order = _n

* Encode topic as a labeled numeric variable
encode topic, gen(topic_encoded)

* Create dot plot with confidence intervals
graph twoway ///
    (rcap change_ci_lower change_ci_upper order, horizontal lcolor(gs10)) ///
    (scatter order change, mcolor(navy) msize(medium)), ///
    ylabel(1(1)19, valuelabel angle(0) labsize(vsmall)) ///
    ysc(reverse) ///
    ytitle("") ///
    xtitle("Change in proportion (percentage points)") ///
    xline(0, lcolor(black) lwidth(thin)) ///
    title("Change in Tweet Topics: Post vs Pre Period") ///
    subtitle("With 95% Confidence Intervals") ///
    note("Positive values indicate topic increased in post period") ///
    legend(off)
graph export "$tweetNLP_figs/topic_class/diff_plot_CI.png", replace

restore






** OLD NOTES **
*** DIFFERENCE CHART ****
// use "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN_noBM.dta", clear
//
// * ---------------------------------
// * 1. Collapse to get counts per topic × post_birth
// * ---------------------------------
// * Create numeric 1 for each tweet
// gen tweet_num = 1
//
// * Collapse counts by topic × post_birth
// collapse (sum) n = tweet_num, by(topic post_birth)
//
// * Compute total tweets per period
// egen total_period = total(n), by(post_birth)
//
// * Compute share of each topic within its period
// gen share = n / total_period
//
// * ---------------------------------
// * 2. Reshape wide: create columns share_0 and share_1
// * ---------------------------------
// reshape wide share, i(topic) j(post_birth)
//
// * Now each topic has:
// * share_0 → pre-birth share
// * share_1 → post-birth share
//
// * ---------------------------------
// * 3. Compute difference
// * ---------------------------------
// gen diff = share_1 - share_0
//
// * ---------------------------------
// * 4. Determine line color: green if positive, red if negative
// * ---------------------------------
// gen linecolor = cond(diff >= 0, "green", "red")
//
// * ---------------------------------
// * 5. Optional: sort topics by difference magnitude
// * ---------------------------------
// gsort -abs(diff)
//
// * ---------------------------------
// * 6. Plot: simple bar chart for difference (red/green)
// * ---------------------------------
// graph bar (asis) diff, over(topic, gap(0)) ///
//     bar(1, color(linecolor)) ///
//     ytitle("Change in Topic Share (Post - Pre)") ///
//     xtitle("Topic") ///
//     ylabel(-0.2(0.05)0.2) ///
//     title("Change in Tweet Topics Pre/Post Birth") ///
//     legend(off) ///
//     blabel(bar, format(%5.2f))
//
// * ---------------------------------
// * 7. Export figure
// * ---------------------------------
// graph export "$tweetNLP_figs/topic_class/diff_plot.png", replace
//

*********************************************************





// *************************************************************
// * 1. PREP AND COLLAPSE DATA
// *************************************************************
//
// * Keep only variables needed
// keep topic post_birth
//
// * Collapse to get count of tweets by topic × period
// contract topic post_birth
// rename _freq n
//
// * Compute total tweets in each period
// bys post: egen total_period = total(n)
//
// * Compute share of tweets within each period
// gen share = n / total_period
//
// *************************************************************
// * 2. RESHAPE TO WIDE AND COMPUTE DIFFERENCE
// *************************************************************
//
// reshape wide share, i(topic) j(post_birth)
//
// * share0 = pre-birth, share1 = post-birth
// gen diff = share1 - share0
//
//
// *************************************************************
// * 3. COLOR ENCODING (GREEN = INCREASE, RED = DECREASE)
// *************************************************************
//
// gen color = cond(diff >= 0, "green", "red")
//
//
// *************************************************************
// * 4. PLOT DIFFERENCE: GREEN = POSITIVE, RED = NEGATIVE
// *************************************************************
//
// * Sort topics so largest increase appears at top
// gsort -diff
//
// * Create the graph
// twoway ///
//     (bar diff topic if diff >= 0, horizontal barwidth(0.7) color(green%70)) ///
//     (bar diff topic if diff < 0,  horizontal barwidth(0.7) color(red%70)) ///
//     , ///
//     ylab(, angle(horizontal)) ///
//     ytitle("Topic") ///
//     xtitle("Change in Share of Tweets (Post − Pre)") ///
//     xline(0, lcolor(black) lwidth(thin)) ///
//     title("Difference in Topic Prevalence After Birth") ///
//     legend(off)
// graph export "$tweetNLP_figs/topic_class/diff_plot.png", replace