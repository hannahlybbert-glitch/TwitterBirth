**** Distributions for Devin ****

use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
	keep if acct_tweeted_postBA == 1 & full_3years == 1
	
* 1. All tweets, total number of tweets per account during 3 year period
preserve
	bysort author_id: egen total_tweets = count(tweet_id)
	bysort author_id: keep if _n == 1
hist total_tweets, bin(50) freq ///
    xtitle("Originall Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Tweets per Account") ///
    graphregion(color(white))
graph export "$figures/descriptive_figs/hist_tweet_totals.jpg", replace
restore

** Overlayed Histograms option
preserve
	bysort author_id: egen tweets_pre = total(post == 0)
	bysort author_id: egen tweets_post = total(post == 1)
	bysort author_id: keep if _n == 1
	
	keep author_id tweets_pre tweets_post
	reshape long tweets_, i(author_id) j(period) string
	rename tweets_ total_tweets
	label define periodlbl 1 "Pre-Birth" 2 "Post-Birth"
twoway ///
    (histogram total_tweets if period=="pre", bin(50) freq color(navy%50)) ///
    (histogram total_tweets if period=="post", bin(50) freq color(purple%50)), ///
    legend(order(1 "Pre-Birth" 2 "Post-Birth")) ///
    xtitle("Total Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Tweets per Account: Pre vs Post Birth") ///
    graphregion(color(white)) ///
	legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0))
graph export "$figures/descriptive_figs/hist_prepost_totals.jpg", replace
restore

* 1A. All tweets, by gender
// Female
preserve
	bysort author_id: egen total_tweets = count(tweet_id)
	bysort author_id: keep if _n == 1
	keep if female == 1
hist total_tweets, bin(50) freq ///
    xtitle("Total Tweets per Female Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Tweets per Female Account") ///
    graphregion(color(white))
graph export "$figures/descriptive_figs/hist_tweet_totals_female.jpg", replace
restore

// Male
preserve
	bysort author_id: egen total_tweets = count(tweet_id)
	bysort author_id: keep if _n == 1
	keep if female == 0
hist total_tweets, bin(50) freq ///
    xtitle("Total Tweets per Male Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution Tweets per Male Account") ///
    graphregion(color(white))
graph export "$figures/descriptive_figs/hist_tweet_totals_male.jpg", replace
restore

** FEMALE pre/post Overlayed Histograms option
preserve
	bysort author_id: egen tweets_pre = total(post == 0)
	bysort author_id: egen tweets_post = total(post == 1)
	collapse(max) tweets_pre tweets_post, by(author_id female)
	
	keep if female == 1
	keep author_id tweets_pre tweets_post
	reshape long tweets_, i(author_id) j(period) string
	rename tweets_ total_tweets
	label define periodlbl 1 "Pre-Birth" 2 "Post-Birth"
twoway ///
    (histogram total_tweets if period=="pre", bin(50) color(navy%50)) ///
    (histogram total_tweets if period=="post", bin(50) color(red%50)), ///
    legend(order(1 "Pre-Birth" 2 "Post-Birth")) ///
    xtitle("Total Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Tweets per Female Account: Pre vs Post Birth") ///
    graphregion(color(white)) ///
	legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0))
graph export "$figures/descriptive_figs/hist_prepost_totals_female.jpg", replace
restore

** MALE pre/post Overlayed Histograms option
preserve
	bysort author_id: egen tweets_pre = total(post == 0)
	bysort author_id: egen tweets_post = total(post == 1)
	collapse(max) tweets_pre tweets_post, by(author_id female)

	keep if female == 0
	keep author_id tweets_pre tweets_post
	reshape long tweets_, i(author_id) j(period) string
	rename tweets_ total_tweets
	label define periodlbl 1 "Pre-Birth" 2 "Post-Birth"
twoway ///
    (histogram total_tweets if period=="pre", bin(50) color(navy%50)) ///
    (histogram total_tweets if period=="post", bin(50) color(blue%50)), ///
    legend(order(1 "Pre-Birth" 2 "Post-Birth")) ///
    xtitle("Total Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Tweets per Male Account: Pre vs Post Birth") ///
    graphregion(color(white)) ///
	legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0))
graph export "$figures/descriptive_figs/hist_prepost_totals_male.jpg", replace
restore

** Gender Overlayed Histograms option
preserve
	bysort author_id: egen tweets_fem = total(female == 1)
	bysort author_id: egen tweets_male = total(female == 0)
	collapse(max) tweets_fem tweets_male, by(author_id)

	keep author_id tweets_fem tweets_male
	reshape long tweets_, i(author_id) j(gender) string
	rename tweets_ total_tweets
	keep if total_tweets > 1
	label define periodlbl 1 "Female" 2 "Male"
twoway ///
    (histogram total_tweets if gender=="fem", bin(50) freq color(red%50)) ///
    (histogram total_tweets if gender=="male", bin(50) freq color(blue%50)), ///
    legend(order(1 "Female" 2 "Male")) ///
    xtitle("Total Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Tweets per Account: Female vs Male") ///
    graphregion(color(white)) ///
	legend(order(1 "Female" 2 "Male") position(3) ring(0))
graph export "$figures/descriptive_figs/hist_prepost_totals_gender.jpg", replace
restore




*******************************************************************************
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
	keep if acct_tweeted_postBA == 1 & full_3years == 1
// 	gen months_from_birth = floor(days_from_birth / 30)
// 	gen week_from_birth = floor(days_from_birth / 7)
// 	keep if abs(week_from_birth) <= 78

// merge m:1 unique_id using "$cleaned/user_info_full_sample_CLEAN.dta", force keepusing(female)
// drop if _merge == 2	
// drop _merge
** Link info
	gen text_nolink = ustrregexra(text, "https?://[^ ]+", "")
	gen only_link = missing(text_nolink)
// 	drop if missing(text_nolink)
	
* 2. When https links are removed (try to have on same graph as all tweets)
** Overlayed Histograms option
preserve
	bysort author_id: egen tweets_link = total(only_link == 1 | only_link==0)
	bysort author_id: egen tweets_nolink = total(only_link == 0)
	collapse(max) tweets_link tweets_nolink, by(author_id)

	keep author_id tweets_link tweets_nolink
	reshape long tweets_, i(author_id) j(link) string
	rename tweets_ total_tweets
	keep if total_tweets > 1
	label define periodlbl 1 "Totals with Link" 2 "Totals without Link"
twoway ///
    (histogram total_tweets if link=="link", bin(50) freq color(navy%50)) ///
    (histogram total_tweets if link=="nolink", bin(50) freq color(orange%50)), ///
    legend(order(1 "Totals with Link" 2 "Totals without Link")) ///
    xtitle("Total Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Tweets per Account: Link included vs excluded") ///
    graphregion(color(white)) ///
	legend(order(1 "With Link" 2 "Without Link") position(3) ring(0))
graph export "$figures/descriptive_figs/hist_link_totals.jpg", replace
restore


* 3. Summary statistics (avg tweets per account, avg tweets per account without link, avg tweets pre birth, avg tweets post birth)
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear

	bysort author_id: egen total_tweets = count(tweet_id)
	bysort author_id: egen tweets_pre = total(post == 0)
	bysort author_id: egen tweets_post = total(post == 1)
	bysort author_id: keep if _n == 1
	
	* All 8440 Accounts
	asdoc tabstat total_tweets tweets_pre tweets_post, ///
		stat(count mean sd min max) columns(statistics) long ///
		title(Full Sample - 8,440) ///
		save($figures/descriptive_figs/sum_stats.doc) replace
	asdoc tabstat total_tweets tweets_pre tweets_post if female ==1, ///
		stat(count mean sd min max) columns(statistics) long ///
		title(Female Full Sample) ///
		save($figures/descriptive_figs/sum_stats.doc) append
	asdoc tabstat total_tweets tweets_pre tweets_post if female ==0, ///
		stat(count mean sd min max) columns(statistics) long ///
		title(Male Full Sample) ///
		save($figures/descriptive_figs/sum_stats.doc) append
		
	* Full 3 years of Data
	keep if full_3years == 1
	asdoc tabstat total_tweets tweets_pre tweets_post, ///
		stat(count mean sd min max) columns(statistics) long ///
		title(Active full 3-years - 7,509) ///
		save($figures/descriptive_figs/sum_stats.doc) append
	asdoc tabstat total_tweets tweets_pre tweets_post if female ==1, ///
		stat(count mean sd min max) columns(statistics) long ///
		title(Female Active full 3-years) ///
		save($figures/descriptive_figs/sum_stats.doc) append
	asdoc tabstat total_tweets tweets_pre tweets_post if female ==0, ///
		stat(count mean sd min max) columns(statistics) long ///
		title(Male Active full 3-years) ///
		save($figures/descriptive_figs/sum_stats.doc) append
		
	* Full 3 years of Data AND Tweeted Post BA
	keep if acct_tweeted_postBA == 1
	asdoc tabstat total_tweets tweets_pre tweets_post, ///
		stat(count mean sd min max) columns(statistics) long ///
		title(Final Sample - 4,145) ///
		save($figures/descriptive_figs/sum_stats.doc) append
	asdoc tabstat total_tweets tweets_pre tweets_post if female ==1, ///
		stat(count mean sd min max) columns(statistics) long ///
		title(Female Final Sample) ///
		save($figures/descriptive_figs/sum_stats.doc) append
	asdoc tabstat total_tweets tweets_pre tweets_post if female ==0, ///
		stat(count mean sd min max) columns(statistics) long ///
		title(Male Final Sample) ///
		save($figures/descriptive_figs/sum_stats.doc) append
	
	
* 3a. Figuring out Numbers (acct breakdown)
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
	bysort author_id: egen total_tweets = count(tweet_id)
	keep if acct_tweeted_postBA == 1 & full_3years == 1 // 4145 total accounts

	



* 4. Histograms/distributions for sentiment analysis
// use "$sentiment/output/sentiment_scoresFULL.dta", clear
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


**# No longer doing neutral
// ** NEUTRAL 
// preserve
// 	bysort author_id (post): egen score_pre  = mean(cond(post==0, neu, .))
// 	bysort author_id (post): egen score_post = mean(cond(post==1, neu, .))
// 	bysort author_id: keep if _n == 1
// 	keep author_id score_pre score_post
// 	reshape long score_, i(author_id) j(period) string
// 	rename score_ avg_score
//
// 	replace period = "Pre-Birth"  if period == "pre"
// 	replace period = "Post-Birth" if period == "post"
//
// twoway ///
// 	(histogram avg_score if period=="Pre-Birth",  bin(50) color(navy%50) density) ///
// 	(histogram avg_score if period=="Post-Birth", bin(50) color(orange%50) density), ///
// 	legend(order(1 "Pre-Birth" 2 "Post-Birth")) ///
// 	xtitle("Average Neutral Sentiment Score") ///
// 	ytitle("Density of Accounts") ///
// 	title("Distribution of Average Neutrality: Pre vs Post Birth") ///
// 	graphregion(color(white)) ///
// 	legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0))
// graph export "$tweetNLP_figs/neutrality_prepost.jpg", replace
// restore





**** Who do we have Volume data for but no text data (post BA)
use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	gen post_BA = (date > date_birth_tweet)
	replace post_BA = 1 if date == date_birth_tweet
// 	replace post_BA = 1 if date_birth == date
	preserve
	drop if full_3years != 1
    collapse (sum) total_tweets, by(author_id post_BA)
	distinct author_id if post_BA == 1 & total_tweets >0
	distinct author_id if post_BA == 1 & total_tweets >1
	distinct author_id
	restore









************ OTHER NOTES ************

** GENDER PANEL pre/post
// preserve
//     bysort author_id female: egen tweets_pre = total(post == 0)
//     bysort author_id female: egen tweets_post = total(post == 1)
//     collapse (max) tweets_pre tweets_post, by(author_id female)
//     reshape long tweets_, i(author_id female) j(period) string
//     rename tweets_ total_tweets
//     keep if total_tweets > 1
//
//     * Separate by gender
//     twoway ///
//         (histogram total_tweets if female == 1 & period == "pre", bin(50) freq color(sky%50)) ///
//         (histogram total_tweets if female == 1 & period == "post", bin(50) freq color(red%50)), ///
//         legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0)) ///
//         title("Female Accounts") ///
//         xtitle("Total Tweets per Account (3-Year Period)") ///
//         ytitle("Number of Accounts") ///
// 		ylabel(0(100)400) ///
//         yscale(range(0 400)) ///
//         graphregion(color(white)) ///
//         name(fem, replace)
//
//     twoway ///
//         (histogram total_tweets if female == 0 & period == "pre", bin(50) freq color(sky%50)) ///
//         (histogram total_tweets if female == 0 & period == "post", bin(50) freq color(blue%50)), ///
//         legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0)) ///
//         title("Male Accounts") ///
//         xtitle("Total Tweets per Account (3-Year Period)") ///
//         ytitle("Number of Accounts") ///
// 		ylabel(0(100)400) ///
//         yscale(range(0 400)) ///
//         graphregion(color(white)) ///
//         name(male, replace)
//
//     graph combine fem male, ///
//         title("Distribution of Tweet Activity by Gender and Period") ///
//         graphregion(color(white))
//     graph export "$figures/descriptive_figs/hist_prepost_gender_panels.jpg", replace
// restore








