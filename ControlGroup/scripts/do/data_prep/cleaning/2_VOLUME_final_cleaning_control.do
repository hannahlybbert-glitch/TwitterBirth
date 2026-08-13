* Author: Hannah Lybbert
* Created: 08/12/2026
* Purpose: Clean the volume data from the Control group API pull


use "$control_volume/test/post_volume_filtered.dta", clear

*=============================================================================
* SECTION 1: Variable Types
*=============================================================================

*--- Integers ---
	foreach var in original_quote_count {
		destring `var', replace
	}

*--- Dates ---
	foreach var in date  {
		gen `var'_stata = date(substr(`var',1,10), "YMD") // remove time stamp
		format `var'_stata %td 
		count if missing(`var')
		drop `var'
		count if missing(`var'_stata)
		rename `var'_stata `var'
	}

	

	
*=============================================================================
* SECTION 2: Generate Variables
*=============================================================================

merge m:1 author_id using "$control_cleaned/test/user_info_control_preclean.dta", keepusing(days_from date_birth_placebo date_seed_tweet)
drop if _merge ==2
drop _merge

*--- Days/Weeks/Months from birth ---
	gen days_from_birth = date - date_birth_placebo
	gen week_from_birth = floor(days_from_birth / 7)
	gen months_from_birth = floor(days_from_birth / 30)

*--- Post (if day is pre/post birth) ---
	gen post_birth = (date_birth_placebo < date)
	replace post_birth = 1 if date_birth_placebo == date
	
