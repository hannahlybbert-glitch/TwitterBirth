
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
	
graph export "$tweetNLP_figs/topic_class/diff_plot_CI.png", replace
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