* Load in hand_coded file
import delimited using "$raw/hand_coding/2013_2017/partially_hand_coded_master_2013_2017.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

local n = _N
di `n'

* save as tempfile
tempfile temp
sa `temp'

* these were either hand-coded within the spreadsheet, or were automatically done based on keywords
keep if assigned_to == "Auto" | (assigned_to == "Rory" & !missing(birth))
tempfile already_done
sa `already_done'

* load in hand-coded by Rory
import delimited using "$raw/hand_coding/2013_2017/first_500_rory.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
gen assigned_to = "Rory"

keep tweet_id birth_announcement different_day days_from assigned_to

* merge with 
merge 1:1 tweet_id assigned_to using `temp'
assert !missing(birth) if assigned_to == "Rory" 
keep if _merge == 3
drop _merge

tempfile Rory
sa `Rory'

* then load in the the hand-coded by all the other RAs
local Names Gavin Claire Jonas Alex Julia Sarah Robert Sonia Justin Zoe Jake Meklet Ben Emily Christian
clear
tempfile master
sa `master', emptyok
foreach Name in `Names' {
	import delimited using "$raw/hand_coding/2013_2017/hand_coded_`Name'.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
	
	di "`Name'"
	tab birth, m
	
	gen assigned_to = "`Name'"
	keep tweet_id birth_announcement different_day days_from assigned_to
	
	merge 1:1 tweet_id assigned_to using `temp'
	keep if _merge == 3
	drop _merge
	
	assert inlist(birth_announcement, "1", "0")
	assert !missing(birth) if assigned_to == "`Name'" 
	
	
	append using `master'
	sa `master', replace
}

append using `Rory'
append using `already_done'

* make sure that all observations are in the file
assert `n' == _N

tab birth, m


* Deal with repeat birth announcements and deal with accounts with multiple births
gen date_posted = date(substr(created_at,1,10), "YMD")
format date_posted %td

sort author_id tweet_id

egen group = group(author_id birth_announcement)
bysort group (tweet_id): gen n = _N

* change the newer tweet(s) to not a birth announcement if the tweet(s) is/are within 546 days of one another
bysort group: gen repeat = 1 if date_posted[_n] - date_posted[_n-1] < 546 
replace birth_announcement = "0" if repeat == 1

tab birth, m
drop repeat group n

* now create a new grouping variable for accounts 
egen group2 = group(author_id birth_announcement)
* get a number for the first and second birth we record from an individual
bysort group2 (date_posted): gen birth_tweet_number = _n if birth_announcement == "1"
//
// drop group2 date_posted n
//
// * unique id for each birth
// egen unique_id = group(author_id birth_tweet_number)

export delimited using "$raw/hand_coding/2013_2017/hand_coded_master_2013_2017.csv", quote replace



