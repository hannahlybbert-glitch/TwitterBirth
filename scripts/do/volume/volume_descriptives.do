* Author: Hannah Lybbert
* Created: Jan 5, 2026
* Purpose: Account numbers (sample size info)


* Load data
use "$final/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years==1
	

**# Remove preserve/restore when I'm certain
preserve
	summarize total_month_tweets, detail
	local p95 = r(p95)
	drop if total_month_tweets >= `p95' & !missing(total_month_tweets)
	distinct author_id
	distinct author_id if !missing(rt_reply_count)
restore	





use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear

** Account Sample Breakdown for Volume analysis given not all accounts have retweet/reply volume data available
* Original sample - 8440
	distinct author_id
	
* Sample with full 3 years of Original + Quote data - 7510
	distinct author_id if full_3years == 1

* Sample with full 3 years of ALL volume measures (OG, QT, RT, RPLY) - 6353 (~85% of usable accounts for volume analysis have rt/reply data too)
	distinct author_id if full_3years == 1 & !missing(rt_reply_count)
	

** Account sample breakdown by date of account creation
* Accounts withe Birth announcement - 8440
	distinct author_id 
	
* Accounts created at least 18 months pre birth - 7510
	distinct author_id if full_3years == 1

* Accounts created at least 24 months pre birth - 7144
	distinct author_id if account_24_mo_old == 1

* Accounts created at least 30 months pre birth - 6791
	distinct author_id if account_30_mo_old == 1 
	
	
use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years == 1
bysort unique_id: gen n_obs = _N
	sum n_obs, d
bysort author_id: gen n_obs_aid = _N
	sum n_obs_aid, d
	
preserve	
keep if full_3years ==1
// drop if months_from_birth == -19 | months_from_birth == 18
bysort unique_id: gen n_obs = _N
	sum n_obs, d
restore
//	
// // testing something
// bysort unique_id: egen min_date = min(date)
// bysort unique_id: gen full_3years_TEST = (begin_date >= min_date)
	

