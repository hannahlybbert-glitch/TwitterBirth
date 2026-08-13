* Author: Hannah Lybbert
* Created: 05/07/2026
* Updated: 05/07/2026
* Purpose: Build final user dataset restricted to authors in the final volume analysis sample
		* MUST RUN build_volume_dataset.do first!

* ------ BUILD USER ANALYSIS DATASET ------ *
* Restrict to unique_ids in ogqt_volume_analysis_sample (full_3years==1, outliers trimmed)

use "$final/ogqt_volume_analysis_sample.dta", clear
	keep author_id
	duplicates drop author_id, force
	tempfile analysis_ids
	save `analysis_ids'

use "$cleaned/user_info_full_sample_CLEAN.dta", clear
merge m:1 author_id using `analysis_ids', keep(match) nogen
distinct author_id

* Merge in avg_weekly_tweets computed in lifetime_trim.do (single source of truth
* for this metric, rather than recomputing it here with a second copy of the
* REF_date / weeks_alive logic)
merge m:1 author_id using "$cleaned/lifetime_trim_authors.dta", keep(match) nogen keepusing(avg_weekly_tweets)
distinct author_id

sum avg_weekly_tweets, d

save "$final/user_analysis_sample.dta", replace
export delimited using "$final/user_analysis_sample.csv", replace quote delimiter(",") nolabel

