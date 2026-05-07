* Author: Hannah Lybbert
* Created: 01/07/2026
* Purpose: Descriptive figures for results

* --------------------------------------------------------*
* User info/demographics descriptives
		* All will be done with the 7510 sample (must have full 3 years of data)
use "$final/user_analysis_sample.dta", clear
	keep if full_3years == 1
	
	
* ----- Gender split ------ *
graph bar (percent), over(female, relabel(1 "Male" 2 "Female" 3 "Unknown")) ///
	ytitle("Share of Accounts") ///
	title("Gender Distribution in Sample") ///
	blabel(total, format(%9.1f)) ///
	graphregion(color(white)) ///
	asyvars ///
	bar(1, color(green)) bar(2, color(blue)) bar(3, color(red)) ///
	legend(label(1 "Unknown") label(2 "Male") label(3 "Female") position(3) ring(0))
graph export "$figures/descriptive_figs/user_info/gender_shares.png", replace


* ----- RACE split ------ *	
graph pie, over(race) ///
    title("Race Distribution in Sample") ///
    plabel(_all percent, format(%9.1f) size(medium)) ///
    graphregion(color(white)) ///
	legend(label(1 "Unknown") label(2 "Black") label(3 "White") label(4 "Asian") label(5 "Hispanic") label(6 "Other") position(2) ring(0))
graph export "$figures/descriptive_figs/user_info/race_shares.jpg", replace


* ----- Date Birth and Date Birth Tweet ----- *
hist date_birth, freq ///
    xtitle("Date of Birth") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Birth Dates in Sample") ///
    graphregion(color(white))
graph export "$figures/descriptive_figs/user_info/DOB_dist.jpg", replace

hist date_birth_tweet, freq color(red%70) ///
    xtitle("Date of Birth Tweet") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Date of Birth Tweets in Sample") ///
    graphregion(color(white))
graph export "$figures/descriptive_figs/user_info/date_BA_dist.jpg", replace

* Overlay
	twoway ///
		(histogram date_birth, freq color(blue%50)) ///
		(histogram date_birth_tweet, freq color(red%20)), ///
		xtitle("Date") ///
		ytitle("Number of Accounts") ///
		title("Distribution of Birth Dates and Birth Announcement Tweets") ///
		legend(order(1 "Date of Birth" 2 "Birth Announcement Tweet") position(11) ring(0)) ///
		graphregion(color(white))
	graph export "$figures/descriptive_figs/user_info/DOB_BA_overlay.jpg", replace


* ---- Account creation (age) ----- *
hist user_created_at, freq ///
    xtitle("Date of Account Creation") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Twitter Account Creation Dates") ///
    graphregion(color(white))
graph export "$figures/descriptive_figs/user_info/account_creation.jpg", replace


* ----- followers ----- *
asdoc tabstat followers_count, ///
		stat(count mean median sd min max) columns(statistics) long ///
		title(Followers Count) ///
		save($figures/descriptive_figs/user_info/user_sum_stats.doc) replace
asdoc tabstat following_count, ///
		stat(count mean median sd min max) columns(statistics) long ///
		title(Following Count) ///
		save($figures/descriptive_figs/user_info/user_sum_stats.doc) append
		
* ----- lifetime posts ----- *
sum lifetime_posts, d
asdoc tabstat lifetime_posts, ///
		stat(count mean median sd min max) columns(statistics) long ///
		title(Lifetime Posts - total tweets since account creation) ///
		save($figures/descriptive_figs/user_info/user_sum_stats.doc) append
hist lifetime_posts

* ----- original/quote tweet counts vs retweet/reply counts ---- *
asdoc tabstat orig_qt_count, ///
		stat(count mean median sd min max) columns(statistics) long ///
		title(3 year sample Original + Quote Tweets) ///
		save($figures/descriptive_figs/user_info/user_sum_stats.doc) append

asdoc tabstat rt_reply_count, ///
		stat(count mean median sd min max) columns(statistics) long ///
		title(3 year sample Retweet + Replies) ///
		save($figures/descriptive_figs/user_info/user_sum_stats.doc) append

* ----- days from birth that BA is posted ----- *
hist days_from, freq ///
    xtitle("Days separating birth tweet and actual birth of child (all accounts)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Difference in Time Between Birth Tweet and DOB") ///
    graphregion(color(white)) ///
	note("Note: Distribution for all 7510 accounts." ///
	"Positive = birth tweet before DOB, Negative = birth tweet after DOB")
graph export "$figures/descriptive_figs/user_info/days_from.jpg", replace

asdoc tabstat days_from, ///
		stat(count mean median sd min max) columns(statistics) long ///
		title(Days From - Days in between birth tweet and DOB (+ pre DOB/- post DOB)) ///
		save($figures/descriptive_figs/user_info/user_sum_stats.doc) append

		* Hand code error? Author id 535727941
			* looks like the birth date and birth date tweet should be swapped.
		* POsitive = before birth (19 more days until we meet luke!)
		* NEgative = after birth (4 days ago...)
		


* correlation matrix or heatmap for engagement metrics by followers bins
// need code here

* % with complete 18 month pre birth data (PYRAMID)
	// distinct author_id if full_3years ==1 / distinct author_id
	
* % with no rt_reply_count (PYRAMID)
	// distinct author_id if missing(rt_reply_count) / distinct author_id if full_3years ==1
	



* --------------------------------------------------------*
* VOLUME descriptives
* --------------------------------------------------------*
**# Should I show summary stats of the analysis sample we use? - YES
// use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
// keep if full_3years == 1

use "$final/tweet_volume_analysis_sample.dta", clear


asdoc tabstat total_month_tweets, ///
	stat(count mean median sd min max) columns(statistics) long ///
	title(Total Monthly Tweets) ///
	save($figures/descriptive_figs/volume/sum_stats.doc) replace
	
	
* 3. Summary statistics
	bysort author_id: egen mo_tweets_pre = mean(cond(post_birth==0, total_month_tweets, .))
	bysort author_id: egen mo_tweets_post = mean(cond(post_birth==1, total_month_tweets, .))
	bysort author_id: keep if _n == 1
		
	* Full 3 years of Data AND Tweeted Post BA
	asdoc tabstat total_month_tweets mo_tweets_pre mo_tweets_post, ///
		stat(count mean median sd min max) columns(statistics) long ///
		title(Final Sample - Total Monthly Tweets) ///
		save($figures/descriptive_figs/volume/sum_stats.doc) replace
	asdoc tabstat total_month_tweets mo_tweets_pre mo_tweets_post if female ==1, ///
		stat(count mean median sd min max) columns(statistics) long ///
		title(Female - Total Monthly Tweets) ///
		save($figures/descriptive_figs/volume/sum_stats.doc) append
	asdoc tabstat total_month_tweets mo_tweets_pre mo_tweets_post if female ==0, ///
		stat(count mean median sd min max) columns(statistics) long ///
		title(Male - Total Monthly Tweets) ///
		save($figures/descriptive_figs/volume/sum_stats.doc) append

	
* 1. All tweets, total number of tweets per account during 3 year period
hist total_month_tweets, bin(50) freq ///
    xtitle("Total Monthly Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Total Tweets per Account") ///
    graphregion(color(white)) ///
	note("Note: Sample size is 6,328 accounts. Must have full 3 years of data.")
graph export "$figures/descriptive_figs/volume/hist_tweet_totals.jpg", replace

* 1a. Overlayed total tweets pre/post
twoway ///
    (histogram total_month_tweets if post_birth == 0, bin(50) freq color(gray)) ///
    (histogram total_month_tweets if post_birth == 1, bin(50) freq color(orange%50)), ///
    xtitle("Total Monthly Tweets per Account (3-Year Period)") ///
    ytitle("Accounts") ///
    title("Distribution of Total Tweets per Account: Pre vs Post Birth") ///
    legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0)) ///
    graphregion(color(white)) ///
    note("Note: Sample size is 6,328 accounts. Must have full 3 years of data.")
graph export "$figures/descriptive_figs/volume/tweet_totals_prepost.jpg", replace


* 1A. All tweets, by gender
// Female
preserve
	keep if female == 1
hist total_month_tweets, bin(50) freq ///
    xtitle("Total Monthly Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Monthly Tweets per Female Account") ///
    graphregion(color(white)) ///
	note("Note: Sample size is 2,756 female accounts (~45% of accounts with gender). Must have full 3 years of data.")
graph export "$figures/descriptive_figs/volume/hist_tweet_totals_female.jpg", replace
restore

// Male
preserve
	keep if female == 0
hist total_month_tweets, bin(50) freq ///
    xtitle("Total Original + Quote Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Original/Quote Tweets per Male Account") ///
    graphregion(color(white)) ///
	note("Note: Sample size is 3,347 male accounts (~55% of accounts with gender). Must have full 3 years of data.")
graph export "$figures/descriptive_figs/volume/hist_tweet_totals_male.jpg", replace
restore

** FEMALE pre/post Overlayed Histograms option
preserve
	keep if female == 1
twoway ///
    (histogram total_month_tweets if post_birth==0, bin(50) color(navy%50)) ///
    (histogram total_month_tweets if post_birth==1, bin(50) color(red%50)), ///
    legend(order(1 "Pre-Birth" 2 "Post-Birth")) ///
    xtitle("Total Monthly Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Monthly Tweets per Female Account: Pre vs Post") ///
    graphregion(color(white)) ///
	legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0)) ///
	note("Note: Sample size is 2,756 female accounts (~45% of accounts with gender). Must have full 3 years of data.")
graph export "$figures/descriptive_figs/volume/hist_prepost_totals_female.jpg", replace
restore

** MALE pre/post Overlayed Histograms option
preserve
	keep if female == 0
twoway ///
    (histogram total_month_tweets if post_birth==0, bin(50) color(navy%50)) ///
    (histogram total_month_tweets if post_birth==1, bin(50) color(blue%50)), ///
    legend(order(1 "Pre-Birth" 2 "Post-Birth")) ///
    xtitle("Total Monthly Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Monthly Tweets per Male Account: Pre vs Post") ///
    graphregion(color(white)) ///
	legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0)) ///
	note("Note: Sample size is 3,347 male accounts (~55% of accounts with gender). Must have full 3 years of data.")
graph export "$figures/descriptive_figs/volume/hist_prepost_totals_male.jpg", replace
restore

** Gender Overlayed Histograms option
preserve
twoway ///
    (histogram total_month_tweets if female==1, bin(50) freq color(red%50)) ///
    (histogram total_month_tweets if female==0, bin(50) freq color(blue%50)), ///
    legend(order(1 "Female" 2 "Male")) ///
    xtitle("Total Monthly Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Monthly Tweets per Account: Female vs Male") ///
    graphregion(color(white)) ///
	legend(order(1 "Female" 2 "Male") position(3) ring(0)) ///
	note("Note: Sample size = 6,103 accounts (45% female, 55% male). Must have full 3 years of data.")
graph export "$figures/descriptive_figs/volume/hist_prepost_totals_gender.jpg", replace
restore


* GENDER PANEL pre/post
preserve  
* Separate by gender
	hist total_month_tweets if female == 1, bin(50) freq color(red%70) ///
		xtitle("Total Monthly Tweets per Account (3-Year Period)") ///
		ytitle("Accounts") ///
		title("Female Accounts") ///
		graphregion(color(white)) ///
		ylabel(0(300000)1500000) ///
        yscale(range(0 1500000)) ///
		note("Note: Sample size is 2,756 female accounts (~45% of accounts" ///
		"with gender). Must have full 3 years of data.") ///
		name(fem, replace)

	hist total_month_tweets if female == 0, bin(50) freq ///
		xtitle("Total Original + Quote Tweets per Account (3-Year Period)") ///
		ytitle("Accounts") ///
		title("Male Accounts") ///
		graphregion(color(white)) ///
		ylabel(0(300000)1500000) ///
        yscale(range(0 1500000)) ///
		note("Note: Sample size is 3,347 male accounts (~55% of accounts" ///
		"with gender). Must have full 3 years of data.") ///
			graphregion(color(white)) ///
			name(male, replace)

    graph combine fem male, ///
        title("Distribution of Monthly Tweet Activity by Gender") ///
        graphregion(color(white)) ///
		note("Note: Sample size = 6,103 accounts (45% female, 55% male). Must have full 3 years of data.")
    graph export "$figures/descriptive_figs/volume/hist_prepost_gender_panels.jpg", replace
restore


* --------------------------------------------------------*
* TWEET TEXT descriptives
* --------------------------------------------------------*
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
	keep if acct_tweeted_postBA == 1 & full_3years == 1
	
* 1. All tweets, total number of tweets per account during 3 year period
preserve
	bysort author_id: egen total_tweets = count(tweet_id)
	bysort author_id: keep if _n == 1
hist total_tweets, bin(50) freq ///
    xtitle("Total Original + Quote Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Original + Quote Tweets per Account") ///
    graphregion(color(white)) ///
	note("Note: Sample size is 4,145 accounts. Must have full 3 years of data and tweeted once after the birth announcement")
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
    xtitle("Total Original + Quote Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Original/Quote Tweets per Account: Pre vs Post Birth") ///
    graphregion(color(white)) ///
	legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0)) ///
	note("Note: Sample size is 4,145 accounts. Must have full 3 years of data and tweeted once after the birth announcement")
graph export "$figures/descriptive_figs/hist_prepost_totals.jpg", replace
restore

* 1A. All tweets, by gender
// Female
preserve
	bysort author_id: egen total_tweets = count(tweet_id)
	bysort author_id: keep if _n == 1
	keep if female == 1
hist total_tweets, bin(50) freq ///
    xtitle("Total Original + Quote Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Original/Quote Tweets per Female Account") ///
    graphregion(color(white)) ///
	note("Note: Sample size is 1,681 female accounts (~42% of accounts with gender)." ///
	"Must have full 3 years of data and tweeted once after the birth announcement")
graph export "$figures/descriptive_figs/hist_tweet_totals_female.jpg", replace
restore

// Male
preserve
	bysort author_id: egen total_tweets = count(tweet_id)
	bysort author_id: keep if _n == 1
	keep if female == 0
hist total_tweets, bin(50) freq ///
    xtitle("Total Original + Quote Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Original/Quote Tweets per Male Account") ///
    graphregion(color(white)) ///
	note("Note: Sample size is 2,336 male accounts (~58% of accounts with gender)." ///
	"Must have full 3 years of data and tweeted once after the birth announcement")
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
    xtitle("Total Original + Quote Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Original/Quote Tweets per Female Account: Pre vs Post Birth") ///
    graphregion(color(white)) ///
	legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0)) ///
	note("Note: Sample size is 1,681 female accounts (~42% of accounts with gender)." ///
	"Must have full 3 years of data and tweeted once after the birth announcement")
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
    xtitle("Total Original + Quote Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Original/Quote Tweets per Male Account: Pre vs Post Birth") ///
    graphregion(color(white)) ///
	note("Note: Sample size is 2,336 male accounts (~58% of accounts with gender)." ///
	"Must have full 3 years of data and tweeted once after the birth announcement") ///
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
    xtitle("Total Original + Quote Tweets per Account (3-Year Period)") ///
    ytitle("Number of Accounts") ///
    title("Distribution of Original/Quote Tweets per Account: Female vs Male") ///
    graphregion(color(white)) ///
	legend(order(1 "Female" 2 "Male") position(3) ring(0)) ///
	note("Note: Sample size = 4,017 accounts (42% female, 58% male)" ///
	"Must have full 3 years of data and tweeted once after the birth announcement")
graph export "$figures/descriptive_figs/hist_prepost_totals_gender.jpg", replace
restore


* GENDER PANEL pre/post
preserve
    bysort author_id female: egen tweets_pre = total(post == 0)
    bysort author_id female: egen tweets_post = total(post == 1)
    collapse (max) tweets_pre tweets_post, by(author_id female)
    reshape long tweets_, i(author_id female) j(period) string
    rename tweets_ total_tweets
    keep if total_tweets > 1

    * Separate by gender
    twoway ///
        (histogram total_tweets if female == 1 & period == "pre", bin(50) freq color(sky%50)) ///
        (histogram total_tweets if female == 1 & period == "post", bin(50) freq color(red%50)), ///
        legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0)) ///
        title("Female Accounts") ///
        xtitle("Total Original + Quote Tweets per Account (3-Year Period)") ///
        ytitle("Number of Accounts") ///
		ylabel(0(100)400) ///
        yscale(range(0 400)) ///
        graphregion(color(white)) ///
        name(fem, replace)

    twoway ///
        (histogram total_tweets if female == 0 & period == "pre", bin(50) freq color(sky%50)) ///
        (histogram total_tweets if female == 0 & period == "post", bin(50) freq color(blue%50)), ///
        legend(order(1 "Pre-Birth" 2 "Post-Birth") position(3) ring(0)) ///
        title("Male Accounts") ///
        xtitle("Total Original + Quote Tweets per Account (3-Year Period)") ///
        ytitle("Number of Accounts") ///
		ylabel(0(100)400) ///
        yscale(range(0 400)) ///
        graphregion(color(white)) ///
        name(male, replace)

    graph combine fem male, ///
        title("Distribution of Original/Quote Tweet Activity by Gender and Period") ///
        graphregion(color(white)) ///
		note("Note: Sample size = 4,017 accounts (42% female, 58% male)" ///
		"Must have full 3 years of data and tweeted once after the birth announcement")
    graph export "$figures/descriptive_figs/hist_prepost_gender_panels.jpg", replace
restore



* 3. Summary statistics (avg original tweets per account, avg tweets per account without link, avg tweets pre birth, avg tweets post birth)
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years==1 & acct_tweeted_postBA == 1

	bysort author_id: egen total_tweets = count(tweet_id)
	bysort author_id: egen tweets_pre = total(post == 0)
	bysort author_id: egen tweets_post = total(post == 1)
	bysort author_id: keep if _n == 1
		
	* Full 3 years of Data AND Tweeted Post BA
	asdoc tabstat total_tweets tweets_pre tweets_post, ///
		stat(count mean median sd min max) columns(statistics) long ///
		title(Final Sample - Total Original/Quote Tweets) ///
		save($figures/descriptive_figs/sum_stats.doc) replace
	asdoc tabstat total_tweets tweets_pre tweets_post if female ==1, ///
		stat(count mean median sd min max) columns(statistics) long ///
		title(Female - Total Original/Quote Tweets) ///
		save($figures/descriptive_figs/sum_stats.doc) append
	asdoc tabstat total_tweets tweets_pre tweets_post if female ==0, ///
		stat(count mean median sd min max) columns(statistics) long ///
		title(Male - Total Original/Quote Tweets) ///
		save($figures/descriptive_figs/sum_stats.doc) append
