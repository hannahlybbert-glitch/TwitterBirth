* Author: Hannah Lybbert
* Created: 04/27/2026
* Updated: 04/27/2026
* Purpose: Distribution of avg tweets/week per author based on lifetime_posts and account age as of April 2025

do "$dofile/set_globals.do"

* Keep only authors in the og/qt volume analysis sample
use "$final/ogqt_volume_analysis_sample.dta", clear
keep author_id
duplicates drop
tempfile volume_authors
save `volume_authors'

use "$final/user_analysis_sample.dta", clear
merge m:1 author_id using `volume_authors', keep(match) nogen

* Reference date: July 7, 2025 (when the 2013-2017 user data was pulled)
local ref_date = mdy(7, 17, 2025)

* Days since account creation as of the reference date
gen days_active = `ref_date' - user_created_at

* Drop accounts created after the reference date (days_active <= 0)
drop if days_active <= 0

* Weeks since account creation as of the reference date
gen weeks_active = days_active / 7

* Avg tweets per week for each author
gen avg_tweets_per_week = lifetime_posts / weeks_active

* Distribution
summarize avg_tweets_per_week, detail
