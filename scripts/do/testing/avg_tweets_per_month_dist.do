* Author: Hannah Lybbert
* Created: 04/27/2026
* Updated: 04/27/2026
* Purpose: Distribution of avg tweets/month per author based on lifetime_posts and account age as of April 2025

do "$dofile/set_globals.do"

* Keep only authors in the og/qt volume analysis sample
use "$final/ogqt_volume_analysis_sample.dta", clear
keep author_id
duplicates drop
tempfile volume_authors
save `volume_authors'

use "$final/user_analysis_sample.dta", clear
merge m:1 author_id using `volume_authors', keep(match) nogen

* Reference date: April 2025
local ref_year  = 2025
local ref_month = 4

* Convert user_created_at to year and month components
gen created_year  = year(user_created_at)
gen created_month = month(user_created_at)

* Months since account creation as of April 2025
gen months_active = (`ref_year' - created_year) * 12 + (`ref_month' - created_month)

* Drop accounts created after April 2025 (months_active <= 0)
drop if months_active <= 0

* Avg tweets per month for each author
gen avg_tweets_per_month = lifetime_posts / months_active

* Distribution
summarize avg_tweets_per_month, detail
