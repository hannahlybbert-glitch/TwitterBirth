import delimited using "/Users/rorylawson/Desktop/TwitterBirth/demographics_test.csv", ///
clear bindquotes(strict) maxquotedrows(unlimited) stringcols(_all) varnames(1)
ren num_children child_number

keep female-child_number *manual author_id

destring female_manual-child_number, replace

replace child_number = -99 if child_number == 99

foreach var of varlist female_manual-child_number {
	tab `var'
}

corr female_manual female



foreach var of varlist female-child_number {
// 	corr `var' `var'_manual	
	corr `var' `var'_manual if `var' != -99 & `var'_manual != -99
}

