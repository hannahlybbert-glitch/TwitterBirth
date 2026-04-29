* Take the tweet ids and the columns that have been filled out
* run a correlation between my responses and theirs 

clear all
set more off

import delimited using "$RA_training/first_500_Rory.csv", bindquotes(strict) maxquotedrows(unlimited) stringcols(_all) clear

rename birth_announcement Rory_birth
tab Rory_birth

keep Rory_birth tweet_id text author_id

tempfile Rory
sa `Rory'


local Names Gavin Claire Jonas Alex Julia Sarah Robert Sonia Justin Zoe Jerry Jake Meklet Ben Emily Christian
	
foreach name in `Names' {
	import delimited using "$RA_training/hand_coded_`name'.csv", bindquotes(strict) maxquotedrows(unlimited) stringcols(_all) clear
	
	tempfile `name'
	
	gen `name'_birth = birth_announcement
	keep `name'_birth tweet_id
	
	sa ``name''
}

use `Rory', clear

foreach name in `Names' {
	merge 1:1 tweet_id using ``name'', nogen
}

sort author_id tweet_id

replace Emily_birth = "0" if Emily_birth == "p"

replace Julia_birth = "0" if Julia_birth == "UNSURE"
replace Robert_birth = "0" if Robert_birth == "0!"
replace Robert_birth = "1" if Robert_birth == "1!"

destring *birth, replace

replace Alex_birth = 0 if Alex_birth == 9

* get correlation matrix as well as 
correlate *birth
foreach name in `Names' {
	tab `name'_birth
	
	** number of times that they code as 0 when I coded as 1 (False negative)
	count if Rory_birth == 1 & `name'_birth == 0
	
	** number of times that they code as 1 when I coded as 0 (False positive)
	count if Rory_birth == 0 & `name'_birth == 1
}

* check to see if I got any wrong
egen RAs_coded_as1 = rowtotal(`Names')
// drop Rory_birth

* if only 25% of RAs agree with me, check to see if I got it wrong
// browse if RAs_coded_as1 <=4 & Rory_birth == 1

* create a correlation table with just the RAs
local i = 1
foreach name in `Names' {
	gen RA_`i' = `name'_birth
	label var RA_`i' "RA `i'"
	local i = `i' + 1
}

// correlate RA*

estpost correlate RA*, matrix 
esttab  using "$RA_training/RA_Corr.tex", replace unstack noobs not nostar label nonumber booktabs




