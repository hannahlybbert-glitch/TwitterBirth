************* PERCENT CHANGE IN TWEET VOLUME *******************

***** Needed data and variables ******
use "$final/tweet_volume_by_user_full_sample_CLEAN.dta", clear


gen days_from_birth = date - date_birth
gen months_from_birth = floor(days_from_birth / 30)
gen total_tweets = orig_qt_count + rt_reply_count
gen week_from_birth = floor(days_from_birth / 7)

egen min_days = min(days_from_birth), by(unique_id)
gen not_546 = min_days > -546
egen max_days = max(days_from_birth), by(unique_id)
replace not_546 = 1 if max_days < 546 // No obs that didn't make it to 546 days post birth
drop if not_546 == 1


********** BEGIN TESTS **********
* Calculate average weekly tweets pre- and post-birth
preserve

* Create pre/post indicators
gen post_birth = (week_from_birth >= 0)

* Collapse to get mean tweets by user and period
collapse (mean) total_tweets, by(unique_id post_birth)

* Reshape to compare pre/post for each user
reshape wide total_tweets, i(unique_id) j(post_birth)

* Calculate percentage change for each user
gen pct_change = ((total_tweets1 - total_tweets0)/total_tweets0)*100

* Get summary statistics of the percentage change
sum pct_change, d

* Calculate mean pre and post values
mean total_tweets0 total_tweets1

* Calculate overall percentage change
di "Overall percentage change: " (r(table)[1,2] - r(table)[1,1])/r(table)[1,1]*100 "%"
restore


**** REGRESSION approach ****
* Using regression to estimate the percentage change
gen post_birth = (week_from_birth >= 0)
gen ln_tweets = ln(total_tweets + 0.1)  // Adding small constant for zero tweets
reg ln_tweets i.post_birth, cluster(unique_id)

* To interpret as percentage change:
di "Percentage change: " (exp(_b[1.post_birth]) - 1)*100 "%"