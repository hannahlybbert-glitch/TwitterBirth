/* 
Take the output from twitter api recent search and then output a csv
file that will be hand-coded for birth announcement tweets
*/

	clear
	tempfile sample
	sa `sample', emptyok

	* this file has the "very broad" search of "baby"
	import delimited using "$testing/birth_query_results_verybroad.csv", ///
	clear stringcols(_all) bindquotes(strict) varnames(1)

	tempfile temp
	sa `temp', replace

	* other broad searches
	import delimited using "$testing/birth_query_results_broad.csv", ///
	clear stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited)

	append using `temp'
	
* Get 300 tweet samples for the large sets of tweets
	foreach i in 11 14 15 {
		
		preserve
		keep if query == "`i'"
		set seed 0923485 
		sample 300, count
		
		append using `sample'
		sa `sample', replace
		restore
	}
	
	* Don't need to take a sample of query 13 sine only has 28 obs - so carry it over
	keep if query_id == "13"
	tempfile query13
	sa `query13'
	
	* Load the narrow searches
	import delimited using "$testing/birth_query_results_narrow.csv", ///
	clear stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) 
	append using `sample'
	append using `query13'
	
	export delimited using "$testing/tweet_samples.csv", replace quote
	
	


	
	
	
	
	
	
	



	
	
	
	
