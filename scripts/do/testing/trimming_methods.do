* Author: Hannah Lybbert
* Created: 07/27/2026
* Purpose: Correlation between different trimming methods to make sure we are trimming consistent with our treatment group


* --------------------------------------------------------
* ---------------- METHOD COMPARISON: 1 vs 4 -------------- *
* Does trimming on lifetime avg weekly tweets (Method 4 - the only metric
* available for the control group) retain roughly the same treatment authors
* as trimming on sample-period og/qt volume (Method 1 - current approach)?
* --------------------------------------------------------

* --- Method 1 metric: total og/qt tweets during the 3-year sample, rescaled to a
*     weekly rate (divide by 156 weeks) so it's on the same footing as Method 4's
*     avg_weekly_tweets. Dividing by a constant is a pure rescaling - it doesn't
*     change rank order, so this doesn't change which authors would be trimmed. ---
use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years == 1
	keep author_id og_qt_sample_tweets
	duplicates drop author_id, force
	gen avg_weekly_sample_tweets = og_qt_sample_tweets / 156
	tempfile volume_piece
	save `volume_piece'

* --- Method 4 metric: lifetime tweets per week alive ---
use "$cleaned/user_info_full_sample_CLEAN.dta", clear

	gen REF_date = mdy(4,15,2025) if year(date_birth_tweet) == 2018
	replace REF_date = mdy(7,17,2025) if inrange(year(date_birth_tweet), 2013, 2017)
	format REF_date %td

	gen weeks_alive = (REF_date - user_created_at) / 7
	gen avg_weekly_tweets = lifetime_posts / weeks_alive

	keep author_id avg_weekly_tweets

* --- Restrict to authors who have BOTH metrics, so the two trims are being
*     judged on the same population (same authors underlie both p95 cutoffs) ---
	merge 1:1 author_id using `volume_piece', keep(match) nogen
	distinct author_id

* --- Each method's own p95 cutoff, computed on this shared population ---
	summarize avg_weekly_sample_tweets, detail
		local p95_m1 = r(p95)
	summarize avg_weekly_tweets, detail
		local p95_m4 = r(p95)

	gen retained_m1 = !missing(avg_weekly_sample_tweets) & avg_weekly_sample_tweets <= `p95_m1'
	gen retained_m4 = !missing(avg_weekly_tweets)         & avg_weekly_tweets       <= `p95_m4'

* --- Author overlap ---
	tab retained_m1 retained_m4, cell

	count if retained_m1 == 1 & retained_m4 == 1
		local both = r(N)
	count if retained_m1 == 1 | retained_m4 == 1
		local either = r(N)
	count if retained_m1 == 1
		local n_m1 = r(N)
	count if retained_m4 == 1
		local n_m4 = r(N)

	display "Jaccard index (retained by both / retained by either): " %4.3f `both'/`either'
	display "% of Method 1-retained also retained by Method 4: " %4.1f 100*`both'/`n_m1'
	display "% of Method 4-retained also retained by Method 1: " %4.1f 100*`both'/`n_m4'

* --- Metric correlation (secondary/supporting check) ---
	* Spearman: rank correlation, robust to the heavy right-skew in tweet counts
	spearman avg_weekly_sample_tweets avg_weekly_tweets
	* Pearson: correlation on raw values - sensitive to outliers/skew, reported alongside
	* Spearman for completeness so we can see how much the skew is driving the difference
	pwcorr avg_weekly_sample_tweets avg_weekly_tweets, sig

	
	
	
	
// * --------------------------------------------------------
// * ---------------- SAMPLE BASED TRIMMING ---------------- *
// * Volume metric, static weeks in sample for all authors
// * --------------------------------------------------------
//
// use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
// 	keep if full_3years ==1
//	
// * -------------------------------
// * METHOD 1:
// 	* trim based on total og/qt DURING the 3-year sample
// * -------------------------------
//
// distinct author_id
// summarize og_qt_sample_tweets, detail
// 	local p95 = r(p95)
// 	drop if og_qt_sample_tweets > `p95' & !missing(og_qt_sample_tweets)	
// distinct author_id
//
// * -------------------------------
// * METHOD 2:
// 	* trim based on total og/qt PER WEEK DURING the 3-year sample
// 	* to be in the sample, each author had to have 156 collected weeks of data (no more, no less)
// * -------------------------------
//
// distinct author_id
// gen sample_tweets_per_week = og_qt_sample_tweets/156
// summarize sample_tweets_per_week, detail
// 	local p95 = r(p95)
// 	drop if sample_tweets_per_week > `p95' & !missing(sample_tweets_per_week)
// distinct author_id
//
//
// * --------------------------------------------------------
// * ---------------- LIFETIME-BASED TRIMMING ---------------- *
// * User metric, varying weeks for each author.
// * --------------------------------------------------------
//
// use "$cleaned/user_info_full_sample_CLEAN.dta", clear
//
//
// * -------------------------------
// * METHOD 3:
// 	* trim based on total lifetime tweets
// * -------------------------------
//
// distinct author_id
// summarize lifetime_posts, detail
// 	local p95 = r(p95)
// 	drop if lifetime_posts > `p95' & !missing(lifetime_posts)
//
// distinct author_id
//
// * -------------------------------
// * METHOD 4:
// 	* trim based on LIFETIME tweets PER WEEK (lifetime tweets/(day rory pulled - created at))
// * -------------------------------
//
// gen REF_date = mdy(4,15,2025) if year(date_birth_tweet) == 2018
// replace REF_date = mdy(7,17,2025) if inrange(year(date_birth_tweet), 2013, 2017)
// format REF_date %td
// count if missing(REF_date) // should be 0 - flags birth years outside 2013-2018
//
// gen weeks_alive = (REF_date - user_created_at) / 7
// gen avg_weekly_tweets = lifetime_posts / weeks_alive
//
// distinct author_id
// summarize avg_weekly_tweets, detail
// 	local p95 = r(p95)
// 	drop if avg_weekly_tweets > `p95' & !missing(avg_weekly_tweets)
