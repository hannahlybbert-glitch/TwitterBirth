
use "$final/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years==1


	preserve
		drop if missing(rt_reply_count)
		hist total_month_tweets
	restore
	
	
* drop robert & see how we improve 
	* Robert was somehow posting > 1700 original posts per day
preserve
drop if author_id == "21109095"
sum total_tweets, d 
restore