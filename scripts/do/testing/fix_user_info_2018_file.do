// import delimited using "$raw/hand_coded_2018_master.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
//
//
// import delimited using "$raw/query_results_2013_01_01-2017_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
//
//
// import delimited using "$raw/query_results_2018_01_01-2018_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear




* fix mistake where I overwrote user info file
use "$cleaned/user_info.dta", clear

keep author_id followers_count description

tempfile user_info
sa `user_info'

import delimited using "$raw/user_info_2018_missing_bio.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

gen id = _n

sort author_id created_at

* keep unique authors with earliest timestamp of post
bysort author_id (created_at): drop if author_id[_n] == author_id[_n-1]
sort id

merge 1:1 author_id using `user_info'
sort id


* column order of final file
order query_id author_id username name tweet_id created_at text media_url assigned_to birth_announcement different_day days_from has_picture tweet_url profile_image_url like_count retweet_count reply_count quote_count user_created_at description followers_count following_count tweet_count verified verified_type start_time end_time processed_text text_classification pic_classification

drop id _merge 

export delimited using "$raw/user_info_2018.csv", replace quote