* Check distribution of the age of the account/when the account was started to understand if sample is skewed.

import delimited using "$hand_coding/2018/hand_coded_master_2018.csv" , bindquotes(strict) maxquotedrows(unlimited) stringcols(_all) clear

gen date_user_created = date(substr(user_created_at,1,10), "YMD")
format date_user_created %td

gen year_user_created = year(date_user_created)

tab year_user_created

tab year_user_created if !missing(birth_announcement)

tw (hist year_user_created, col(blue%30) width(1) frequency discrete) ///
 (hist year_user_created if !missing(birth_announcement) | !missing(birth_announcement), width(1) col(red%30) frequency discrete), ///
 legend(order(1 "All" 2 "Hand-Coded So Far") ring(0) pos(2)) xlabel(2006(1)2017, nogrid) ytitle("Number of Accounts") ylabel(,nogrid format(%12.0fc))

gen month_user_created = month(date_user_created)

tab year_user_created if _n > 35000 & _n < 50000 & missing(birth_announcement) & missing(assigned_to)

tab year_user_created if _n >= 50000 & missing(birth_announcement) & missing(assigned_to)


import delimited using "$hand_coding/hand_coded_master_2013_2017.csv" , bindquotes(strict) maxquotedrows(unlimited) stringcols(_all) clear
gen date_user_created = date(substr(user_created_at,1,10), "YMD")
format date_user_created %td

gen date_posted = date(substr(created_at,1,10), "YMD")
format date_posted %td
gen account_age = date_posted - date_user_created

gen year_posted = year(date_posted)
tab year_posted if birth_announcement == "0"

gen has_pre_period = 0
replace has_pre_period = 1 if account_age > 547

tab has_pre_period if missing(birth_announcement) & missing(assigned_to)

drop date_user_created date_posted

// replace assigned_to = "Auto" if has_pre_period == 0

gsort -has_pre_period assigned_to author_id tweet_id 


// export delimited using "$hand_coding/coded_pre_period_hand_coded_master_2013_2017.csv", replace quote
