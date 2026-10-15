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
	rename original_quote_count orig_qt_count

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

merge m:1 author_id using "$control_cleaned/test/user_info_control_preclean.dta", keepusing(user_created_at days_from date_birth_placebo date_seed_tweet avg_weekly_tweets)
drop if _merge ==2
drop _merge

*--- Days/Weeks/Months from birth ---
	gen days_from_birth = date - date_birth_placebo
	gen week_from_birth = floor(days_from_birth / 7)
	gen months_from_birth = floor(days_from_birth / 30)

*--- Post (if day is pre/post birth) ---
	gen post_birth = (date_birth_placebo < date)
	replace post_birth = 1 if date_birth_placebo == date


*=============================================================================
* SECTION 3: Full Window available
*=============================================================================

*--- Full 3 years indicator ---
	egen min_days = min(days_from_birth), by(author_id)
	gen full_3years = (abs(min_days) >= 540) // account at least 540 days pre birth (~18 months)
	egen max_days = max(days_from_birth), by(author_id)

*--- Keep only 18 months of data [-18, 17]
	drop if abs(days_from_birth) > 547 // also drops authors not in user_info (missing placebo date)
	drop if months_from_birth == -19 | months_from_birth == 18 // drop if month is larger than the panel size


*=============================================================================
* SECTION 4: Monthly and Sample Total Vars
*=============================================================================

*--- Monthly Orig_QT ---
	egen og_qt_month_tweets = sum(orig_qt_count), by(author_id months_from_birth)
	replace og_qt_month_tweets = . if missing(orig_qt_count)
	egen og_qt_sample_tweets = sum(orig_qt_count), by(author_id)
	replace og_qt_sample_tweets = . if missing(orig_qt_count)


*=============================================================================
* SECTION 5: Organize and Save
*=============================================================================

drop min_days max_days
order author_id user_created_at date_birth_placebo date_seed_tweet date orig_qt_count days_from
sort author_id date

save "$control_cleaned/test/tweet_volume_control_CLEAN.dta", replace
