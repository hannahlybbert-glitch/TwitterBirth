** 1. USER INFO
use "$cleaned/user_info_full_sample_CLEAN.dta", clear

	* unique id = 8506
	* author id = 8461
	* diff = 35	(33 are second announcements in the period, 1 is a mis-coded birthday)
		* tweet ID of birthdate duplicate 1046773781379903492 --> drop?
		* John Glen Stevens 947877032549142528 --> also duplicate
		* Would drop two announcements and no accounts
		
duplicates tag author_id, generate(dup_tag)  

// Drop the second observation so we can have a unique_id (one per account)
	sort author_id

	* Within each author_id group, assign order
	by author_id: gen obs_order = _n
	
* Diff 8506-8476 = 30
	* needed to drop second announcements to be able to merge the data.
* Diff 8461 - 8441 = 20


** 2. VOLUME
use "$cleaned/tweet_volume_by_user_full_sample_CLEAN.dta", clear
	
	* unique id = 8476
	* author id = 8441
	* diff = 35
	* I had to drop the second child observation for the X2 in one period from the user info so I could merge the data together 

** 3. TWEET TEXT
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear

	* unique id = 8473
	* author id = 8467
	* diff = 6




