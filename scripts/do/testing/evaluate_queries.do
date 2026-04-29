* Reload the hand-coded files back in and do analysis of yield, user eligibility, duplicate tweets, and duplicate accounts *

	import delimited using "$testing/tweet_samples_hand_coded.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
	
	* evaluate the quality of each search query
	duplicates tag tweet_id, gen(dup)

	bysort query_id: egen n_tweets = count(tweet_id)

	destring birth_announcement, replace
	destring like_count, replace

	unique tweet_id if birth_announcement == 1

	gen hit_rate = .

	levelsof query_id, local(queries)
	foreach i in `queries' {
		di "Query: " "`i'"
		
		quietly su birth_announcement if query == "`i'"
		di "Hit rate= " round(r(mean),0.0001) * 100 "%"
		
		
		quietly replace hit_rate = r(mean) if query == "`i'"
		di "---------------------"
	}

	egen group = group(tweet_id)

	bysort group (query): gen groupsize = _N

	* There are 4 birth announcements that are duplicated once in the data
	tab groupsize if birth_announcement == 1 

	* get a variable with links between the groups
	bysort group (query): gen overlapped = query_id[1] + "," + query_id[2] if groupsize == 2
	encode overlapped, gen(overlap_id)

	tab overlapped

	* collapse hit rate into a dataset
	collapse sample = n_tweets hit_rate (sum) dup, by(query_id)
	
	sort query_id
	
	sa "$testing/query_metrics.dta", replace
	
	
	* load in the full dataset
	import delimited using "$testing/all_query_results.csv", ///
		clear stringcols(_all) bindquotes(strict) maxquotedrows(unlimited) varnames(1)

	* Determine how many hours elapsed for each query
	gen double datetime = clock(created_at, "YMD#hms##")
	format datetime %tc
	sort query_id datetime
	* convert milliseconds to hours
	bysort query_id (datetime): gen elapsed_hours = (datetime[_N] - datetime[1]) / 3600000
	drop datetime
	
	* get total number of tweets
	gen one = 1
	collapse (mean) elapsed_hours (sum) total_tweets = one, by(query_id)
	
	merge 1:1 query_id using "$testing/query_metrics.dta", keep(match) nogen
	
	* Conservatively assume that hourly rate from afternoon is 1/12 of total tweets in day (instead of 1/24th)
		* then multiply by 7 days per week, 52 weeks per year to get yearly hits and yearly tweets
	gen yearly_hits = hit_rate * total_tweets * 52 if elapsed_hours > 100
	replace yearly_hits = ((hit_rate * total_tweets) / elapsed_hours) * 12 * 7 * 52 if elapsed_hours < 2
	gen yearly_tweets = total_tweets * 52 if elapsed_hours > 100
	replace yearly_tweets = (total_tweets / elapsed_hours) * 12 * 7 * 52 if elapsed_hours < 2
	
	format yearly* %10.0fc
	
	destring query_id, replace
	sort query_id
	
	gen type = "broad" if inlist(query_id, 11,14,15)
	replace type = "narrow" if inrange(query_id,1,8) | query_id == 13
	
	order query_id type total_tweets sample elapsed_hours dup hit_rate yearly_hits yearly_tweets
	
	drop if missing(type)
	
	collapse (sum) yearly_hits yearly_tweets (mean) hit_rate, by(type)


