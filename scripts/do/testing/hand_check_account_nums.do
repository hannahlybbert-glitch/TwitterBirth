* Author: Hannah Lybbert
* Created: Dec 19, 2025
* Purpose: Hand checking accounts in the 95th and 99th percentile of tweeting
				* Note the handchecking wasn't during the years in the sample because Twitter wouldn't allow me to scroll that far back. More recent trends


use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years== 1
	
	sum total_month_tweets if !missing(rt_reply_count), d


*---------- 95th percentile (monthly total tweets > 419) ---------- *

	distinct author_id if total_month_tweets >= 419 & !missing(rt_reply_count )
		* 1118 accounts in 95th percentile (1118/6353 = ~ 18% of full sample)
		
	browse if total_month_tweets > 419 & !missing(rt_reply_count)
	
** Accounts to Hand check in 95th percentile
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear

	* 1. 1000997042
		browse if author_id == "1000997042"
			* own tweets but literally tweeting at the wall (texting on twitter)
	* 2. 123665680
		browse if author_id == "123665680"
			* LOTS of reposting 
	* 3. 130706525
		browse if author_id == "130706525"
			* almost a play by play tweet during sports games (instant reacting)
	* 4. 15956591
		browse if author_id == "15956591"
			* a lot of reposting but also a lot of his own tweets
	* 5. 21262048
		browse if author_id == "21262048"
			* play by play sports tweeting (although I don't think the topic identifier would pick these up, ex "Big-time run by Carson Beck.")
	* 6. 271264274
		browse if author_id == "271264274"
			* Reposting
	* 7. 3312016813
		browse if author_id == "3312016813"
			* Reposting
	* 8. 41899031
		browse if author_id == "41899031"
			* Reposting
	* 9. 580993867
		browse if author_id == "580993867"
			* sports tweeting (soccer)
	* 10. 805981550
		browse if author_id == "805981550"
		
		
		
* ---------- 95th percentile original + quote tweets ---------- *
use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years== 1
	
egen tot_orig_month_tweets = sum(orig_qt_count), by(unique_id months_from_birth) 
	
	sum tot_orig_month_tweets, d
	
distinct author_id if tot_orig_month_tweets > 197
	* ~18% of accounts had one month in the 95th percentile

browse if tot_orig_month_tweets > 197


** Accounts to hand check
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear

browse if author_id == "10117182" 
	* all original posts (looks like there might be some connection to her website though)

browse if author_id == "134572731" 
	* most posts contain link to another source ex. google or "http://justunfollow.com/?r=tw"

browse if author_id == "286424184" 
	* all facebook links tweeted as text and looking at the facebook posts they are reposts of facebook posts

browse if author_id == "429535892" 
	* mostly tweeting at a wall (own text tweets) but some that look like they're linked to instagram (her own posts on insta)

browse if author_id == "700408260" 
	* mostly quote tweets which I guess are counted as original tweets based on how we defined it when the data was collected
	
		
		
* ======================================================================= *
	
		
use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years== 1


*---------- 99th percentile (monthly total tweets > 1119) ---------- *

distinct author_id if total_month_tweets > 1119 & !missing(rt_reply_count)
	* 322 accounts (~5% of full sample = 322/6353)
	
browse if total_month_tweets > 1119 & !missing(rt_reply_count)


** Accounts to Hand check in 99th percentile
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear

	browse if author_id == "101180245" 
		* tweeting at a wall (quote, original, and retweets)

	browse if author_id == "1021713506" 
		* Original tweets with some of his own writing and then a FB link (?)

	browse if author_id == "1023792180" 
		* tweeting at a wall (qt, og, rt)
	
	browse if author_id == "102414799" 
		* lots of sports tweeting (og, qt, rt)

	browse if author_id == "1028031492390367236" 
		* insane amount of quote tweets

	browse if author_id == "1031238529" 
		* retweets and quote tweets


use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years== 1
	
*---------- 99th percentile (original and quote tweets > 554) ---------- *
egen tot_orig_month_tweets = sum(orig_qt_count), by(unique_id months_from_birth)
	
	sum tot_orig_month_tweets, d


distinct author_id if tot_orig_month_tweets > 554
	* 393 accounts (~5.2% of full sample = 393/7510)
	
browse if tot_orig_month_tweets > 554

** Hand check these accounts for 99th pctl orig+qt 
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear

	browse if author_id == "1296835951" 
		* mostly reposts, but her og/qt are all tweeting at a wall

	browse if author_id == "153877627" 
		* tweeting at a wall

	browse if author_id == "188406252" 
		* play by play broadcaster

	browse if author_id == "2406217715" 
		* tweeting at a wall

	browse if author_id == "3220735670" 
		* 50/50 quote tweets and original

	browse if author_id == "413109930" 
		* lots of twitter follower tracking reposts from this website fllwrs.com
		* "one person followed me // automatically checked by http://fllwrs.com"
		* also a sports reporter so lots of play by play action





* IMPORTANT ONES TO CHECK
browse if author_id == "21109095"  // this guy is reposting stuff from other SM on twitter...




* total month tweets > 35000
browse if author_id == "112673246" 

browse if author_id == "1128097813" 

**# FLAG! This one is actually original content but a TON
browse if author_id == "1128164360" 

browse if author_id == "113031449" 

browse if author_id == "113185445" 

browse if author_id == "1132780508" 


* total sample tweets > 33317
browse if author_id == "1132780508" 

browse if author_id == "113680538" 

browse if author_id == "1139666538" 

browse if author_id == "114584605" 

browse if author_id == "1151400870" 

browse if author_id == "115192185" 



* total sample tweets > 151914
browse if author_id == "115192185" 

browse if author_id == "1152529320" 

browse if author_id == "115277336" 

browse if author_id == "114584605" 

browse if author_id == "1151400870" 

browse if author_id == "115192185" 





