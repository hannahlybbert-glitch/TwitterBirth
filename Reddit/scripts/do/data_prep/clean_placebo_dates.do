* Author: Hannah Lybbert
* Created: 04/03/2026
* Updated: 04/03/2026
* Purpose: Import and clean placebo births_and_posts data for Stata analysis

* ----------------------------------------------------------------
* Import
* ----------------------------------------------------------------
// import delimited using "$Reddit_BP/placebo_births_and_posts.csv", ///
// 	stringcols(_all) varnames(1) bindquotes(strict) clear
	
import delimited using "$Reddit_final/treatment_control_births_posts.csv", ///
	stringcols(_all) varnames(1) bindquotes(strict) clear

* ----------------------------------------------------------------
* Convert created_utc datetime string to Stata date
* ----------------------------------------------------------------
gen double created_utc_date = dofc(clock(created_utc, "YMDhms"))
format created_utc_date %tdNN/DD/CCYY
drop created_utc
rename created_utc_date created_utc

* ----------------------------------------------------------------
* Convert date_birth and date_birth_post: trim timestamp, then convert
* (values have nanosecond precision e.g. "2021-05-03 17:22:27.710021856")
* ----------------------------------------------------------------
foreach var in date_birth date_birth_post {
	gen str10 `var'_str = word(`var', 1)
	gen double `var'_date = date(`var'_str, "YMD")
	format `var'_date %tdNN/DD/CCYY
	drop `var' `var'_str
	rename `var'_date `var'
}

* ----------------------------------------------------------------
* Fill date_birth and date_birth_post uniformly within each author
* (these are author-level constants — same value across all posts)
* ----------------------------------------------------------------
foreach var in date_birth date_birth_post {
	bysort author: egen double `var'_fill = max(`var')
	replace `var' = `var'_fill
	drop `var'_fill
	format `var' %tdNN/DD/CCYY
}

* ----------------------------------------------------------------
* Destring numeric variables
* ----------------------------------------------------------------
destring score num_comments days_from days_from_birth weeks_from_birth ///
	months_from_birth birth_post post full_18_pre one_year_pre ///
	full_18_post posted_after_birth treated, replace

* ----------------------------------------------------------------
* Label key variables
* ----------------------------------------------------------------
label var created_utc        "Date of post"
label var date_birth         "Assigned placebo birth date"
label var date_birth_post    "Assigned placebo birth post date"
label var days_from          "Days between birth and birth post (drawn from treatment dist.)"
label var days_from_birth    "Days from placebo birth date"
label var weeks_from_birth   "Weeks from placebo birth date"
label var months_from_birth  "Months from placebo birth date"
label var birth_post         "=1 if post is the assigned placebo birth post"
label var post               "=1 if post is on or after placebo birth date"
label var full_18_pre        "=1 if author has posts >= 18 months pre-birth"
label var one_year_pre       "=1 if author has posts >= 12 months pre-birth"
label var full_18_post       "=1 if author has posts >= 18 months post-birth"
label var posted_after_birth "=1 if author posted after placebo birth"
label var treated            "=1 if treated (always 0 for placebo)"

* ----------------------------------------------------------------
* Label key variables
* ----------------------------------------------------------------
// save "$Reddit_BP/placebo_births_and_posts.dta", replace
save "$Reddit_final/treatment_control_births_posts.csv", replace