* Author:  Hannah Lybbert
* Created: 10/13/2026
* Purpose: Average monthly original+quote tweets per control author, pre-pregnancy (-18 to -10) vs pregnancy (-9 to -1)
* Output:  avg_tweets_pre_period_control.dta

// do "$dofile/set_globals.do"

* Load data
use "$control_cleaned/test/tweet_volume_control_CLEAN.dta", clear
keep if inrange(months_from_birth, -18, -1)

* ----------------------------------------------------------------
* Monthly totals per author
* ----------------------------------------------------------------
collapse (sum) month_tweets = orig_qt_count, by(author_id months_from_birth)

gen period = cond(months_from_birth <= -10, 1, 2)
label define period_lbl 1 "Pre-pregnancy (-18 to -10)" 2 "Pregnancy (-9 to -1)"
label values period period_lbl

* ----------------------------------------------------------------
* Average monthly tweets per author by period
* ----------------------------------------------------------------
collapse (mean) avg_tweets = month_tweets, by(author_id period)
reshape wide avg_tweets, i(author_id) j(period)

rename avg_tweets1 avg_tweets_prepreg
rename avg_tweets2 avg_tweets_preg
label var avg_tweets_prepreg "Avg monthly orig+quote tweets, months -18 to -10"
label var avg_tweets_preg    "Avg monthly orig+quote tweets, months -9 to -1"

sum avg_tweets_prepreg avg_tweets_preg, detail
save "$control_cleaned/test/avg_tweets_pre_period_control.dta", replace
