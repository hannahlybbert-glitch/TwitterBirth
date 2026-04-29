* Author: Hannah Lybbert
* Created: 01/09/2025
* Purpose: Sentiment Data Descriptives


* HISTOGRAMS / DISTRIBUTIONS

use "$sentiment/output/sentiment_analysis_sample.dta", clear

* 4A. Positive, negative, neutral, compound
hist neg, bin(50) freq ///
	xtitle("Negative Sentiment Score of Tweet (0-1 Least to Most Negative)") ///
	ytitle("Number of Tweets") ///
	title("Distribution of Tweets with Negative Sentiment Scores")
graph export "$tweetNLP_figs/hist_NEG.jpg", replace

hist pos, bin(50) freq ///
	xtitle("Positive Sentiment Score of Tweet (0-1 Least to Most Positive)") ///
	ytitle("Number of Tweets") ///
	title("Distribution of Tweets with Positive Sentiment Scores")
graph export "$tweetNLP_figs/hist_POS.jpg", replace

// hist neu, bin(50) freq ///
// 	xtitle("Neutral Sentiment Score of Tweet (0-1 Least to Most Neutral)") ///
// 	ytitle("Number of Tweets") ///
// 	title("Distribution of Tweets with Neutral Sentiment Scores")
// graph export "$tweetNLP_figs/hist_NEU.jpg", replace

hist sentiment_score, bin(50) freq ///
	xtitle("Sentiment Score of Tweet (Pos-Neg)") ///
	ytitle("Number of Tweets") ///
	title("Distribution of Sentiment Scores of Tweets")
graph export "$tweetNLP_figs/hist_sentimscore.jpg", replace


* AVERAGED BY ACCOUNT ACROSS PERIOD
* 1. Sentiment Score
preserve
	* Average sentiment score per account (overall)
	bysort author_id: egen avg_score = mean(sentiment_score)
	bysort author_id: keep if _n == 1
	
	keep author_id avg_score
 
	* Plot distribution of average sentiment
	twoway ///
		(histogram avg_score, bin(50) color(gray) density), ///
		xtitle("Average Sentiment Score <---(-)--------(+)--->") ///
		ytitle("Density of Accounts") ///
		title("Distribution of Average Sentiment by Account") ///
		graphregion(color(white)) ///
		note("Sentiment score averaged by account across entire period")
	graph export "$tweetNLP_figs/sentiment_full_period.jpg", replace
restore

* 2. Positivity
preserve
	* Average sentiment score per account (overall)
	bysort author_id: egen avg_score = mean(pos)
	bysort author_id: keep if _n == 1
	
	keep author_id avg_score
 
	* Plot distribution of average sentiment
	twoway ///
		(histogram avg_score, bin(50) color(gray) density), ///
		xtitle("Average Positivity <---(-)--------(+)--->") ///
		ytitle("Density of Accounts") ///
		title("Distribution of Average Positivity by Account") ///
		graphregion(color(white)) ///
		note("Positivity score averaged by account across entire period")
	graph export "$tweetNLP_figs/pos_full_period.jpg", replace
restore

* 3. Negativity
preserve
	* Average sentiment score per account (overall)
	bysort author_id: egen avg_score = mean(neg)
	bysort author_id: keep if _n == 1
	
	keep author_id avg_score
 
	* Plot distribution of average sentiment
	twoway ///
		(histogram avg_score, bin(50) color(gray) density), ///
		xtitle("Average Negativity <---(-)--------(+)--->") ///
		ytitle("Density of Accounts") ///
		title("Distribution of Average Positivity by Account") ///
		graphregion(color(white)) ///
		note("Negativity score averaged by account across entire period")
	graph export "$tweetNLP_figs/neg_full_period.jpg", replace
restore



* 5. By account calculate the pos/neg/neu score pre/post birth
** SENTIMENT SCORE 
preserve
	* Average sentiment score per account pre and post birth
	bysort author_id (post): egen score_pre  = mean(cond(post==0, sentiment_score, .))
	bysort author_id (post): egen score_post = mean(cond(post==1, sentiment_score, .))
	bysort author_id: keep if _n == 1

	keep author_id score_pre score_post
	reshape long score_, i(author_id) j(period) string
	rename score_ avg_score
	replace period = "Pre-Birth"  if period == "pre"
	replace period = "Post-Birth" if period == "post"
 
* 5. Plot distributions of average sentiment
twoway ///
	(histogram avg_score if period=="Pre-Birth",  bin(50) color(navy%50) density) ///
	(histogram avg_score if period=="Post-Birth", bin(50) color(purple%50) density), ///
	legend(order(1 "Pre-Birth" 2 "Post-Birth")) ///
	xtitle("Average Sentiment Score <---(-)--------(+)--->") ///
	ytitle("Denstiy of Accounts") ///
	title("Distribution of Average Sentiment: Pre vs Post Birth") ///
	graphregion(color(white)) ///
	legend(order(1 "Pre-Birth" 2 "Post-Birth") position(1) ring(0)) ///
	note("Sentiment score averaged by account in pre and post periods")
graph export "$tweetNLP_figs/sentiment_prepost.jpg", replace
restore

** POSITIVE 
preserve
	* Average positivity per account pre and post birth
	bysort author_id (post): egen score_pre  = mean(cond(post==0, pos, .))
	bysort author_id (post): egen score_post = mean(cond(post==1, pos, .))
	bysort author_id: keep if _n == 1

	keep author_id score_pre score_post
	reshape long score_, i(author_id) j(period) string
	rename score_ avg_score
	replace period = "Pre-Birth"  if period == "pre"
	replace period = "Post-Birth" if period == "post"

* 5. Plot distributions of average sentiment
twoway ///
	(histogram avg_score if period=="Pre-Birth",  bin(50) color(navy%50) density) ///
	(histogram avg_score if period=="Post-Birth", bin(50) color(red%50) density), ///
	legend(order(1 "Pre-Birth" 2 "Post-Birth")) ///
	xtitle("Average Positive Sentiment Score") ///
	ytitle("Density of Accounts") ///
	title("Distribution of Average Positivity: Pre vs Post Birth") ///
	graphregion(color(white)) ///
	legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0)) ///
	note("Positivity averaged by account in pre and post periods")
graph export "$tweetNLP_figs/positivity_prepost.jpg", replace
restore

** NEGATIVE 
preserve
	bysort author_id (post): egen score_pre  = mean(cond(post==0, neg, .))
	bysort author_id (post): egen score_post = mean(cond(post==1, neg, .))
	bysort author_id: keep if _n == 1
	keep author_id score_pre score_post
	reshape long score_, i(author_id) j(period) string
	rename score_ avg_scores

	replace period = "Pre-Birth"  if period == "pre"
	replace period = "Post-Birth" if period == "post"

twoway ///
    (histogram avg_score if period=="Pre-Birth",  bin(50) color(navy%40) density) ///
    (histogram avg_score if period=="Post-Birth", bin(50) color(blue%40) density), ///
    legend(order(1 "Pre-Birth" 2 "Post-Birth")) ///
    xtitle("Average Negative Sentiment Score") ///
    ytitle("Density of Accounts") ///
    title("Distribution of Average Negativity: Pre vs Post Birth") ///
    graphregion(color(white)) ///
	legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0)) ///
	note("Negativity score averaged by account in pre and post periods")
graph export "$tweetNLP_figs/negativity_prepost.jpg", replace
restore