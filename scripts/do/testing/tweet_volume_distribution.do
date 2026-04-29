* Load in file with tweet volume
import delimited using "$raw/tweet_volume_by_user_2018.csv", stringcols(_all) varnames(1) clear

unique author_id

destring tweet_count, replace

egen tag = tag(author_id date)
egen days_data = total(tag), by(author_id)
drop tag

su days_data

gen begin_stata = date(substr(begin_date,1,10),"YMD") 
gen end_stata = date(substr(end_date,1,10),"YMD")

format *stata %td

* make sure we have the correct number of days of data
gen days_test = end_stata - begin_stata + 1
count if days_test != days_data
// assert days_test == days_data

* shows if there are entries that shouldn't be in there
tab author_id if days_test != days_data

* keep if they have enough pre-period
drop if days_data < 1095 
collapse (sum) tweet_count, by(author_id)

su tweet_count, d

// kdensity tweet_count

// keep if tweet_count <= 1500 & tweet_count >= 50
unique author_id if tweet_count < 50
drop if tweet_count < 50

sort tweet_count
gen cumsum = sum(tweet_count)

* this is the number of accounts we can pull data from given a specified number of tweets
count if cumsum < 790000

* this is the cumulative sum for accounts that tweet at least 50  times in the period and at most once per day on average
di cumsum[_N]

count if tweet_count <= 1095 & tweet_count > 50

// count if tweet_count < 50

import delimited using "$raw/retweet_reply_volume_by_user_2018.csv", stringcols(_all) varnames(1) clear

unique author_id

destring rt_reply_count, replace

egen tag = tag(author_id date)
egen days_data = total(tag), by(author_id)
drop tag

su days_data

gen begin_stata = date(substr(begin_date,1,10),"YMD") 
gen end_stata = date(substr(end_date,1,10),"YMD")

format *stata %td

* make sure we have the correct number of days of data
gen days_test = end_stata - begin_stata + 1
count if days_test != days_data
// assert days_test == days_data

* shows if there are entries that shouldn't be in there
tab author_id if days_test != days_data

collapse (sum) rt_reply_count, by(author_id)


* Work with the 2013_2017 data
import delimited using "$raw/tweet_volume_by_user_2013_2017.csv", stringcol(_all) varnames(1) clear

unique unique_id

destring tweet_count, replace

egen tag = tag(unique_id date)
egen days_data = total(tag), by(unique_id)
drop tag

su days_data

gen begin_stata = date(substr(begin_date,1,10),"YMD") 
gen end_stata = date(substr(end_date,1,10),"YMD")

format *stata %td

* make sure we have the correct number of days of data
gen days_test = end_stata - begin_stata + 1
count if days_test != days_data
// assert days_test == days_data

* shows if there are entries that shouldn't be in there
tab unique_id if days_test != days_data

unique unique_id if days_test != days_data

* keep if they have enough pre-period
// drop if days_data < 1095 
collapse (sum) tweet_count, by(unique_id author_id begin_stata end_stata date_birth user_created_at days_data)

su tweet_count, d

// kdensity tweet_count

// keep if tweet_count <= 1500 & tweet_count >= 50
unique unique_id if tweet_count < 50
drop if tweet_count < 50

* check for enough pre-period
gen birth_stata = date(substr(date_birth,1,10),"YMD")
gen length_pre = birth_stata - begin_stata + 1

keep if length_pre >= 546


sort tweet_count
gen cumsum = sum(tweet_count)

* this is the number of accounts we can pull data from given a specified number of tweets
count if cumsum < 1000000
* 2,800 accounts with highest tweeting account doing so 826 times in sample

* this is the cumulative sum for accounts that tweet at least 50  times in the period and at most once per day on average
di cumsum[_N]

count if tweet_count <= 1095 & tweet_count > 50

count if cumsum > 1000000 & cumsum < 2000000
count if cumsum > 1000000 & cumsum < 1500000
su tweet_count if  cumsum < 2000000
su tweet_count if cumsum < 1500000
* 3,700 accounts with highest tweeting account doing so 1,529 times

// count if tweet_count < 50

// import delimited using "$raw/hand_coding/2013_2017/hand_coded_master_2013_2017.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear


import delimited using "$raw/retweet_reply_volume_by_user_2013_2017.csv", stringcols(_all) varnames(1) clear


unique unique_id

destring rt_reply_count, replace

egen tag = tag(unique_id date)
egen days_data = total(tag), by(unique_id)
drop tag

su days_data

gen begin_stata = date(substr(begin_date,1,10),"YMD") 
gen end_stata = date(substr(end_date,1,10),"YMD")

format *stata %td

* make sure we have the correct number of days of data
gen days_test = end_stata - begin_stata + 1
count if days_test != days_data
// assert days_test == days_data

* shows if there are entries that shouldn't be in there
tab unique_id if days_test != days_data

unique unique_id if days_test != days_data

* keep if they have enough pre-period
// drop if days_data < 1095 
collapse (sum) rt_reply, by(unique_id author_id begin_stata end_stata date_birth user_created_at days_data)

su rt_reply_count, d



