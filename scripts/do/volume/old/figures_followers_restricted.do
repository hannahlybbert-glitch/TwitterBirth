********************** FIGURES - tweets by follower percentiles (restricted) *************************

****************************************************
******* Followers_count *********
use "$final/tweet_volume_by_user_full_sample_CLEAN.dta", clear

merge m:1 unique_id using "$final/user_analysis_sample.dta", keepusing(followers_count)
drop _merge

* Generate variables for figs (same as above)
gen days_from_birth = date - date_birth
gen months_from_birth = floor(days_from_birth / 30)
gen week_from_birth = floor(days_from_birth / 7)
gen total_tweets = orig_qt_count + rt_reply_count

** Percentiles based off of user data full sample breakdown (pct change slightly after merge, likely because of dropped/missing observations)
gen followers_90pct = (followers_count >= 2974)
gen followers_75pct = (followers_count >= 894)
gen followers_10pct = (followers_count <= 41)
gen followers_25pct = (followers_count <= 117)
gen followers_moreavg = (followers_count >= 7356)
gen followers_50pct = (followers_count <= 322)

** Restrict sample
egen min_days = min(days_from_birth), by(unique_id)
gen not_546 = min_days > -546
egen max_days = max(days_from_birth), by(unique_id)
replace not_546 = 1 if max_days < 546 

drop if not_546 == 1


**1. Original Tweet behavior (followers 90th percentile) 857 obs
preserve
collapse (mean) orig_qt_count, by(week_from_birth followers_90pct) 
** PLOT
twoway ///
    (line orig_qt_count week_from_birth if followers_90pct == 1, lcolor(red) lwidth(medthick)) ///
    (line orig_qt_count week_from_birth if followers_90pct == 0, lcolor(gray) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avg Tweets per User") ///
    xtitle("Weeks from Birth") ///
    title("Tweeting Behavior Pre/Post Birth (90pct followers, restr.)") ///
    graphregion(color(white)) ///
    xlabel(-78(13)78) ///
    legend(label(1 "> 90pct") label(2 "Others") position(2) ring(0))
* Save graph
graph export "$figures/twt_behavior/followers_pct/restricted/orig_90pct_fwrs_restricted.jpg", replace
restore


**2. Original Tweet behavior (followers 75th percentile) 2133 obs
preserve
collapse (mean) orig_qt_count, by(week_from_birth followers_75pct) 
** PLOT
twoway ///
    (line orig_qt_count week_from_birth if followers_75pct == 1, lcolor(dkorange) lwidth(medthick)) ///
    (line orig_qt_count week_from_birth if followers_75pct == 0, lcolor(gray) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avg Tweets per User") ///
    xtitle("Weeks from Birth") ///
    title("Tweeting Behavior Pre/Post Birth (>75pct followers, restr.)") ///
    graphregion(color(white)) ///
    xlabel(-78(13)78) ///
    legend(label(1 "> 75pct") label(2 "Others") position(2) ring(0))
* Save graph
graph export "$figures/twt_behavior/followers_pct/restricted/orig_75pct_fwrs_restricted.jpg", replace
restore



**4. Original Tweet behavior (followers 10th percentile) 851 obs
preserve
collapse (mean) orig_qt_count, by(week_from_birth followers_10pct) 
** PLOT
twoway ///
    (line orig_qt_count week_from_birth if followers_10pct == 1, lcolor(blue) lwidth(medthick)) ///
    (line orig_qt_count week_from_birth if followers_10pct == 0, lcolor(gray) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avg Tweets per User") ///
    xtitle("Weeks from Birth") ///
    title("Tweeting Behavior Pre/Post Birth (10pct followers, restr.)") ///
    graphregion(color(white)) ///
    xlabel(-78(13)78) ///
    legend(label(1 "< 10pct") label(2 "Others") position(2) ring(0))
* Save graph
graph export "$figures/twt_behavior/followers_pct/restricted/orig_10pct_fwrs_restricted.jpg", replace
restore


**5. Original Tweet behavior (followers 25th percentile) 2134 obs
preserve
collapse (mean) orig_qt_count, by(week_from_birth followers_25pct) 
** PLOT
twoway ///
    (line orig_qt_count week_from_birth if followers_25pct == 1, lcolor(ebblue) lwidth(medthick)) ///
    (line orig_qt_count week_from_birth if followers_25pct == 0, lcolor(gray) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avg Tweets per User") ///
    xtitle("Weeks from Birth") ///
    title("Tweeting Behavior Pre/Post Birth (25pct followers, restr.)") ///
    graphregion(color(white)) ///
    xlabel(-78(13)78) ///
    legend(label(1 "< 25pct") label(2 "Others") position(2) ring(0))
* Save graph
graph export "$figures/twt_behavior/followers_pct/restricted/orig_25pct_fwrs_restricted.jpg", replace
restore


**6. Original Tweet behavior (followers 50th percentile) 4251 obs (<50pct), 4267 obs (>50pct)
preserve
collapse (mean) orig_qt_count, by(week_from_birth followers_50pct) 
** PLOT
twoway ///
    (line orig_qt_count week_from_birth if followers_50pct == 1, lcolor(blue) lwidth(medthick)) ///
    (line orig_qt_count week_from_birth if followers_50pct == 0, lcolor(red) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avg Tweets per User") ///
    xtitle("Weeks from Birth") ///
    title("Tweeting Behavior Pre/Post Birth (median split followers, restr.)") ///
    graphregion(color(white)) ///
    xlabel(-78(13)78) ///
    legend(label(1 "< 50pct") label(2 "> 50pct") position(2) ring(0))
* Save graph
graph export "$figures/twt_behavior/followers_pct/restricted/orig_50pct_fwrs_restricted.jpg", replace
restore



**7. 10th vs 90th pctl
preserve
drop if followers_count > 41 & followers_count < 2974
collapse (mean) orig_qt_count, by(week_from_birth followers_90pct) 
** PLOT
twoway ///
    (line orig_qt_count week_from_birth if followers_90pct == 1, lcolor(red) lwidth(medthick)) ///
    (line orig_qt_count week_from_birth if followers_90pct == 0, lcolor(blue) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avg Tweets per User") ///
    xtitle("Weeks from Birth") ///
    title("Tweeting Behavior Pre/Post Birth (10th vs 90th pct followers, restr.)") ///
    graphregion(color(white)) ///
    xlabel(-78(13)78) ///
    legend(label(1 "90th pct") label(2 "10th pct") position(2) ring(0))
* Save graph
graph export "$figures/twt_behavior/followers_pct/restricted/orig_90pct_10pct_restricted.jpg", replace
restore


**8. 25th vs 75th pctl
preserve
drop if followers_count > 117 & followers_count < 894
collapse (mean) orig_qt_count, by(week_from_birth followers_75pct) 
** PLOT
twoway ///
    (line orig_qt_count week_from_birth if followers_75pct == 1, lcolor(dkorange) lwidth(medthick)) ///
    (line orig_qt_count week_from_birth if followers_75pct == 0, lcolor(ebblue) lwidth(medthick)), ///
    xline(0, lpattern(dash) lcolor(edkblue)) ///
    ytitle("Avg Tweets per User") ///
    xtitle("Weeks from Birth") ///
    title("Tweeting Behavior Pre/Post Birth (25th vs 75th pct followers, restr.)") ///
    graphregion(color(white)) ///
    xlabel(-78(13)78) ///
    legend(label(1 "75th pct") label(2 "25th pct") position(2) ring(0))
* Save graph
graph export "$figures/twt_behavior/followers_pct/restricted/orig_75pct_25pct_restricted.jpg", replace
restore




****************** T TESTS ******************
use "$final/tweet_volume_by_user_full_sample_CLEAN.dta", clear
merge m:1 unique_id using "$final/user_analysis_sample.dta", keepusing(followers_count)
drop _merge

* Generate variables for figs (same as above)
gen days_from_birth = date - date_birth
gen months_from_birth = floor(days_from_birth / 30)
gen week_from_birth = floor(days_from_birth / 7)
gen total_tweets = orig_qt_count + rt_reply_count

gen followers_90pct = (followers_count >= 2974)
gen followers_75pct = (followers_count >= 894)
gen followers_10pct = (followers_count <= 41)
gen followers_25pct = (followers_count <= 117)
gen followers_moreavg = (followers_count >= 7356)
gen followers_50pct = (followers_count <= 322)

// gen follower_group = .
// replace follower_group = 1 if followers_90pct==1 | followers_75pct==1   // high
// replace follower_group = 0 if followers_10pct==1 | followers_25pct==1   // low

gen follower_group = .
replace follower_group = 1 if followers_50pct == 0   // high
replace follower_group = 0 if followers_50pct== 1    // low

*** Diagnostic test ***
preserve
gen postbirth = week_from_birth >= 0
collapse (mean) total_tweets, by(unique_id postbirth follower_group)
reshape wide total_tweets, i(unique_id) j(postbirth)
gen change_in_tweets = total_tweets1 - total_tweets0
sum change_in_tweets, d

ttest total_tweets1 == total_tweets0 if follower_group == 1 // high-following
ttest total_tweets1 == total_tweets0 if follower_group == 0 // low-following

ttest change_in_tweets, by(follower_group)
restore



*********************** NOTES **************************
// *!! NOT VERY INFORMATIVE !!*
// **3. Original Tweet behavior (average split) 482 obs
// // this data is highly skewed to the left (more accounts with fewer followers) such that the mean is greater than the 90th percentile.
// preserve
// collapse (mean) orig_qt_count, by(week_from_birth followers_moreavg) 
// ** PLOT
// twoway ///
//     (line orig_qt_count week_from_birth if followers_moreavg == 1, lcolor(red) lwidth(medthick)) ///
//     (line orig_qt_count week_from_birth if followers_moreavg == 0, lcolor(blue) lwidth(medthick)), ///
//     xline(0, lpattern(dash) lcolor(edkblue)) ///
//     ytitle("Avg Tweets per User") ///
//     xtitle("Weeks from Birth") ///
//     title("Tweeting Behavior Pre/Post Birth, restr.") ///
//     graphregion(color(white)) ///
//     xlabel(-78(13)78) ///
//     legend(label(1 "> avg (7356)") label(2 "< avg") position(2) ring(0))
// * Save graph
// graph export "$figures/followers_percentiles/restricted/orig_avg_split_fwrs_restricted.jpg", replace
// restore