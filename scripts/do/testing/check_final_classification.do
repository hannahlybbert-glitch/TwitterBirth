// import delimited using "~/Desktop/TwitterBirth/data/testing/final_births_2025_02_11-2025_02_18.csv", clear stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) 
//
// keep query_id tweet_id classification pic_classification final_classification processed_text
// destring query_id, replace
//
// tempfile final
// sa `final'
//
//
// import delimited using "~/Desktop/TwitterBirth/data/testing/birthtweets_2025_02_11-2025_02_18.csv", clear stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) 
// destring query_id, replace
//
// merge 1:1 query_id tweet_id using `final', nogen
//
// // gen kw_flag = 0
// // replace kw_flag = 1 if regexm(processed_text, "(welcome to the family|new addition to the family|i had a baby|i gave birth)") == 1
// //
// //
// // tab kw_flag
//
// order tweet_id *classification text, before(tweet_url)
//
// destring final_classification tweet_count, replace
//
// count if final_classification == 1
// // count if final_classification == 1 & kw_flag == 1
//
//
// keep if final_classification == 1
//
// su tweet_count if final_classification == 1


import delimited using "~/Desktop/TwitterBirth/data/testing/hand_coded_2025_02_17-2025_02_24.csv", clear stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) 

destring query_id tweet_count birth_announcement, replace

keep if birth_announcement == 1


* Determine the average number of tweets per user
* Then do it for those that were classified by chatgpt as birth announcements 

gen date_account_created = date(substr(user_created_at,1,10),"YMD")
gen temp = date(date_birth,"YMD")
drop date_birth 
rename temp date_birth
// gen date_posted = date(substr(created_at,1,10), "YMD")
format date_account_created date_birth %td

gen days_account = date_birth - date_account_created

gen tweets_per_day = tweet_count / days_account

gen tweets_per_year = tweets_per_day * 365
gen tweets_per_period = tweets_per_year * 3


gen orig_per_pd = tweets_per_year * 0.16
gen orig_quo_per_pd = tweets_per_year * 0.25

// keep if classification == 1 & birth_announcement == 1

su orig_per_pd, d
su orig_quo_per_pd, d


* 16% of tweets are original tweets
* 40% are replies, 35% are retweets, 9% are quote tweets
* So either 16% or 25% is what we will anchor on (source is Pew)

gen eligible = 0
replace eligible = 1 if days_account > 547 

cdfplot orig_per_pd 
cdfplot orig_per_pd if eligible == 1

su orig_per_pd, d

su orig_per_pd if eligible == 1, d

keep if eligible == 1

keep author_id tweet_count days_account


bysort author_id: drop if author_id == author_id[_n-1]

* leaves us with X in a week

export delimited using "data/testing/handles_final_2025_02_11-2025_02_18.csv", quote replace






import delimited using "~/Desktop/TwitterBirth/data/testing/birthtweets_2025_02_17-2025_02_24.csv", clear stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) 
destring query_id, replace







