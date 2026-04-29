import delimited using "$raw/classified_text_GPT4_2018_01_01-2018_12_31.csv",  stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

import delimited using "$raw/classified_images_2018_01_01-2018_12_31.csv",  stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

import delimited using "$raw/to_hand_code_2018_01_01-2018_12_31.csv",  stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

* 2013-2017 query results
import delimited using "$raw/query_results_2013_01_01-2017_12_31.csv",  stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

gen year = substr(created_at, 1,4)



// import delimited using "$raw/birth_tweets_2018.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear


import delimited using "$raw/tweet_volume_by_user_2018.csv", stringcols(_all) varnames(1) clear


import delimited using "$raw/hand_coded_2018_master.csv",  stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear


tab birth
bysort author_id (tweet_id): gen birth_num = _n

gen has_link = 0
replace has_link = 1 if regexm(text, "https") & has_pic == "0"

* extract link from tweet
gen after_dots = "https" + regexs(1) if regexm(text, "https([^ ]*)")


bysort author_id


// gen start = date(substr(start_date_with_data, 1,10),"YMD")
gen begin_date = date(substr(begin_date_dt,1,10),"YMD")
gen end = date(substr(end_date_with_data, 1,10),"YMD")
format begin_date %td







// import delimited using "E:\TwitterBirth\data\archive\user_info_2018_test.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

