use "$cleaned/tweet_volume_by_user.dta", clear

// gen statadate = date(substr(date,1,10),"YMD")
// format statadate %td

* convert all dates to statadates
foreach var in user_created_at date_birth begin_date end_date date {
	gen temp = date(substr(`var',1,10),"YMD")
	drop `var'
	gen `var' = temp
	format `var' %td
	drop temp
}

* variable for number of days of data
bysort author_id (date): gen Ndays = date[_N] - date[1]

gen birth = 0 
replace birth = 1 if date_birth == date

* these are accounts that had a child before they created their account
unique author_id if date_birth < user_created_at

* time periods are a little screwy - want 1.5 years before and after the birth of child (account creation only dictates when we can start seeing tweets)
* for now, drop these people

bysort author_id: egen sumbirth = sum(birth)
drop if sumbirth == 0

unique author_id // 2015 accounts

* We actually want data for 36 months

gen t = date - date_birth 

// gen year = year(date)
// gen month = month(date)
//
// gen modate = ym(year, month)
// format modate %tm
//
// gen mobirth = ym(year, month) if birth == 1
// format mobirth %tm
// bysort author_id (mobirth): replace mobirth=mobirth[1]
//
// sort author_id t
//
// gen tm = modate - mobirth

//
// * trim the time period so we have equal number of days on each side
// keep if abs(t) <= 546
//
// * we should keep 546 days after
// unique author_id if t == 546

* get a numeric id
destring author_id, gen(id)



 





