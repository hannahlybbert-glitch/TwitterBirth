	* load in unlabeled tweets
	clear
	tempfile temp
	sa `temp', emptyok

	* Load in all of the results files from twitter API and append them together
	foreach type in narrow broad verybroad {
			
		import delimited using "$testing/birth_query_results_`type'.csv", ///
		clear stringcols(_all) bindquotes(strict) maxquotedrows(unlimited) varnames(1)
		
		append using `temp'
		sa `temp', replace
	}

	order birth_announcement, before(text)
		
	* export this file. This is what goes to Karthik
	export delimited using "$testing/all_query_results.csv", replace quote


	* Keep the narrow query results and test chatgpt api on them

	* Make query_id numeric to sort on it properly
	destring query_id, replace
	sort query_id tweet_id


	* Only need to keep identifiers and the text
		* If including pictures for classifier, then need to also keep has_picture and media_url
	keep query_id tweet_id text

	* narrow search queries are query_id 1-8
	keep if inrange(query_id,1,8)

	* Use this as a test set for chatgpt API classifier
	export delimited using "$testing/tweets_to_classify.csv", replace quote
	
	
	
	import delimited using "$testing/tweet_samples_hand_coded.csv", clear stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited)
	
	destring query_id, replace
	keep if query_id > 10
		
	export delimited using "$testing/tweets_to_classify_broad.csv", replace quote
