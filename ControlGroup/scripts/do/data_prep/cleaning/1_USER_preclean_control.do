* Author: Hannah Lybbert
* Created: 08/11/2026
* Purpose: Clean the data from the Control group API pull

use "$control_user/test/user_info.dta", clear


*=============================================================================
* SECTION 1: Variable Types
*=============================================================================

*--- Dates ---
	foreach var in seed_tweet_date account_created_at  {
		gen `var'_stata = date(substr(`var',1,10), "YMD") // remove time stamp
		format `var'_stata %td 
		count if missing(`var')
		drop `var'
		count if missing(`var'_stata)
		rename `var'_stata `var'
	}
	
*=============================================================================
* SECTION 2: Duplicates
*=============================================================================

* Duplicate accounts & null fields (numbers)
	duplicates report author_id tweet_id
	duplicates tag author_id, gen(dup_tag)
	drop if dup_tag==1 & abs(days_from) > 8 // taking care of duplicate announces
	drop dup_tag
	drop if missing(begin_date)	
	
	
	
* TO do
	* deduplicated (I think this is already done)
	* label variables
	* create variables we need
	* delete variables we dont (ex. week_start, filter_a/b)
	*save intermediate data
	* do volume clean and dtermine the final set of authors
	* create a new user clean do file and reduce down to only the authors we keep and add in the sample tweet metric and anything else we need.