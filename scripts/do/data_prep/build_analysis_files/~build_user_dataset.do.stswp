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

save "$final/user_analysis_sample.dta", replace
