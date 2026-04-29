import delimited using "data/testing/tweet_counts_2025_02_17-2025_02_24.csv", ///
	clear stringcols(1) bindquotes(strict) varnames(1) maxquotedrows(unlimited) 
	
	collapse (sum) tweet_count, by(author_id)
	
	
import delimited using "data/testing/hand_coded_2025_02_17-2025_02_24.csv", ///
	clear stringcols(1) bindquotes(strict) varnames(1) maxquotedrows(unlimited) 
	
	
	gen stata_date = date(substr(created_at, 1,10), "YMD")
	gen stata_date_birth = date(date_birth, "YMD")
	
	gen dif_days = stata_date - stata_date_birth
	
	
	
	
	
	
	
	
	
	
	
// import delimited using "data/testing/tweet_types_test.csv", ///
// 	clear stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) 	
	

	destring tweet_count days_account, replace
// 	encode tweet_type, gen(type)
	
	replace tweet_type = "Quote" if tweet_type == "Quote Tweet"
	replace tweet_type = "Original" if tweet_type == "Original Tweet"
	
	drop if missing(tweet_id)
	
	gen clean_timestamp = subinstr(subinstr(created_at, "T", " ", .), "Z", "", .)
	gen datetime = clock(clean_timestamp, "YMDhms")
	format datetime %tc
	drop clean_timestamp

	gen date = dofc(datetime)
	format date %td
	
	* get start and end date
	bysort author_id: egen start = min(datetime)
	bysort author_id: egen end = max(datetime)
	
	format start end %tc
	gen hours_elapsed = (end - start) / 1000 / 3600
	
	bysort author_id: egen posts_in_period = count(tweet_id)
	
	foreach type in Reply Quote Original Retweet {
		di "`type'"
		gen `type' = 0
		replace `type' = 1 if tweet_type == "`type'"
	}
	


	collapse (mean) tweet_count days_account posts_in_period hours_elapsed (sum) Reply-Retweet, by(author_id)
	
	gen flag = 1 if posts_in_period < 10 & hours_elapsed < 100
	

	foreach type in Reply Quote Original Retweet {
		di "`type'"
		gen pct`type' = `type'/posts_in_period
	
	}
	
	egen allposts = sum(posts_in_period)
	egen alloriginal = sum(Original)
	
	su posts_in_period, d
	
	su posts_in_period if posts_in_period < 100
	
	su Original if posts_in_period < 100, d
	
	su pctOriginal
	su pctOriginal[aweight = posts_in_period]
	su pctOriginal if posts_in_period < 100

	
	tw scatter Original posts_in_period if posts_in_period < 100
	
	tw scatter pctOriginal posts_in_period
	
	* generally, if people post a lot, that means that not too many of their posts are original tweets
	* but still some accounts that just post ALOT
	* on average the 16% thing might be true, but actually will be a decent amount of variance
	* not sure that 16% will hold true for our sample
	
	* maybe just start with the accounts that do not post frequently (but still meet some min amount)
	* Figure out the minimum usable account and then get as many of those accounts as we can while staying within our total tweet constraint
	
	
	
	
	
	