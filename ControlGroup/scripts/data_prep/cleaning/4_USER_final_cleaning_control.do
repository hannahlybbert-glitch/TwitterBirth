* Author: Hannah Lybbert
* Created: 08/11/2026
* Purpose: Making sure we only keep authors who passed the volume restriction


*=============================================================================
* SECTION 2: Keep only authors that passed volume filter
*=============================================================================

use "$control_cleaned/test/tweet_volume_control_CLEAN.dta", clear

* --- Collapse the daily volume panel down to the set of authors who survived the volume pull/filter ---
	keep author_id
	duplicates drop author_id, force

di "Authors who survived the volume pull"
	distinct author_id

* --- Merge onto user data, keeping only authors present in the volume data ---
merge 1:1 author_id using "$control_cleaned/test/user_info_control_preclean.dta", keep(match) nogen

di "Authors after merge (user info x volume survivors)"
	distinct author_id

save "$control_cleaned/test/user_info_control_CLEAN.dta", replace



