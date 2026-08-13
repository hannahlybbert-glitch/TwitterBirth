* Author: Hannah Lybbert
* Created: Aug 12, 2026
* Purpose: Build the control and treatment dataset


*=============================================================================
* SECTION 1: Load control volume data, align names with treatment
*=============================================================================
use "$control_cleaned/test/tweet_volume_control_CLEAN.dta", clear

di "Control authors going into append"
	distinct author_id

tempfile control
save `control'


*=============================================================================
* SECTION 2: Load treatment volume data and append control
*=============================================================================
use "$final/ogqt_volume_analysis_sample.dta", clear

di "Treatment authors going into append"
	distinct author_id

* treated == 1 for every row here already (see build_volume_dataset.do)
append using `control'

di "Authors after appending treatment + control"
	distinct author_id
tab treated


*=============================================================================
* SECTION 3: Save
*=============================================================================
save "$final/volume_control_treatment_sample.dta", replace
