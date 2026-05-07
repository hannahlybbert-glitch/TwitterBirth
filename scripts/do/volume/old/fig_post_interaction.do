*************** FIGURE - change in likes post birth (restricted sample) *********************

use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear

merge m:1 unique_id using "$final/user_analysis_sample.dta", keepusing(date_birth followers_count user_created_at) 
drop _merge

** Generate needed variables
	gen days_from_birth = created_at - date_birth
	gen months_from_birth = floor(days_from_birth / 30)
	gen week_from_birth = floor(days_from_birth / 7)
	gen post_interaction = like_count + retweet_count + reply_count + quote_count
** Generate averages by user
	egen total_interaction = sum(post_interaction), by(author_id week_from_birth)
	egen total_likes = sum(like_count), by(author_id week_from_birth)
	egen total_posts = sum(1), by(author_id week_from_birth)
	gen avg_interact_per_post = total_interaction/total_posts
	gen avg_likes_per_post = total_likes/total_posts

** Restrict sample
	gen days_alive = user_created_at - date_birth 
	drop if days_alive > -546

*Avg likes on each post per author per week
// collapse (mean) post_interaction, by(author_id week_from_birth)
// collapse (mean) post_interaction, by(week_from_birth)

** Follower Percentiles
	gen followers_10pct = (followers_count <= 41)
	gen followers_25pct = (followers_count <= 117)
	gen followers_50pct = (followers_count <= 322)
	gen followers_75pct = (followers_count >= 894)
	gen followers_90pct = (followers_count >= 2974)


** Generate averages by user




**1. TOTAL POST INTERACTION (all follower counts)
preserve
collapse (mean) post_interaction, by(author_id week_from_birth)
collapse (mean) post_interaction, by(week_from_birth)

** PLOT (total interaction)
twoway (line post_interaction week_from_birth, lwidth(medthick) lcolor(blue)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Interaction on Tweet per week") ///
         xtitle("Weeks from Birth") ///
         title("Average Interaction per Tweet per Week pre/post birth (all)") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78)
* Save graph
graph export "$figures/post_interaction/restricted/post_interaction_all.jpg", replace
restore

**1A. by month - TOTAL POST INTERACTION (all follower counts)
preserve
collapse (mean) post_interaction, by(author_id months_from_birth)
collapse (mean) post_interaction, by(months_from_birth)

** PLOT (total interaction)
twoway (line post_interaction months_from_birth, lwidth(medthick) lcolor(blue)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Interaction on Tweet per month") ///
         xtitle("Weeks from Birth") ///
         title("Average Interaction per Tweet per month pre/post birth (all)") ///
         graphregion(color(white)) ///
         xlabel(-19(2)19)
* Save graph
graph export "$figures/post_interaction/restricted/post_interaction_all_bymonth.jpg", replace
restore


**2. TOTAL POST INTERACTION (90pct followers)
preserve
collapse (mean) post_interaction, by(author_id week_from_birth followers_90pct)
collapse (mean) post_interaction, by(week_from_birth followers_90pct)

** PLOT (total interaction)
twoway (line post_interaction week_from_birth if followers_90pct == 1, lcolor(eltblue) lwidth(medthick)) ///
    (line post_interaction week_from_birth if followers_90pct == 0, lcolor(gray) lwidth(medthick)), ///
         xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Interaction on Tweet per week") ///
         xtitle("Weeks from Birth") ///
         title("Average Interaction per Tweet per Week pre/post birth (90pct followers)") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78) ///
		 legend(label(1 "> 90pct") label(2 "Others") position(2) ring(0))
* Save graph
graph export "$figures/post_interaction/restricted/post_interaction_90pct_followers.jpg", replace
restore


**2A. by month - TOTAL POST INTERACTION (90pct followers)
preserve
collapse (mean) post_interaction, by(author_id months_from_birth followers_90pct)
collapse (mean) post_interaction, by(months_from_birth followers_90pct)

** PLOT (total interaction)
twoway (line post_interaction months_from_birth if followers_90pct == 1, lcolor(eltblue) lwidth(medthick)) ///
    (line post_interaction months_from_birth if followers_90pct == 0, lcolor(gray) lwidth(medthick)), ///
         xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Interaction on Tweet per month") ///
         xtitle("Weeks from Birth") ///
         title("Average Interaction per Tweet per Month pre/post birth (90pct followers)") ///
         graphregion(color(white)) ///
         xlabel(-19(2)19) ///
		 legend(label(1 "> 90pct") label(2 "Others") position(2) ring(0))
* Save graph
graph export "$figures/post_interaction/restricted/post_interaction_90pct_followers_bymo.jpg", replace
restore


**3. LIKES (all) 
preserve
collapse (mean) like_count, by(author_id week_from_birth)
collapse (mean) like_count, by(week_from_birth)

** PLOT (total likes)
twoway (line like_count week_from_birth, lwidth(medthick) lcolor(red)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Likes per Tweet per week") ///
         xtitle("Month from Birth") ///
         title("Avg Likes per Tweet per Week pre/post birth (all)") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78)
* Save graph
// graph export "$figures/post_interaction/restricted/likes_all.jpg", replace
restore

**3A. LIKES (all, by month) 
preserve
collapse (mean) like_count, by(author_id months_from_birth)
collapse (mean) like_count, by(months_from_birth)

** PLOT (total likes)
twoway (line like_count months_from_birth, lwidth(medthick) lcolor(red)) ///
       , xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Likes per Tweet per month") ///
         xtitle("Month from Birth") ///
         title("Avg Likes per Tweet per Month pre/post birth (all)") ///
         graphregion(color(white)) ///
         xlabel(-19(2)19)
* Save graph
graph export "$figures/post_interaction/restricted/likes_all_bymonth.jpg", replace
restore


**4. LIKES (90pct followers)
preserve
collapse (mean) like_count, by(author_id week_from_birth followers_90pct)
collapse (mean) like_count, by(week_from_birth followers_90pct)

** PLOT (total tweets)
twoway (line like_count week_from_birth if followers_90pct == 1, lcolor(magenta) lwidth(medthick)) ///
    (line like_count week_from_birth if followers_90pct == 0, lcolor(gray) lwidth(medthick)), ///
         xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Likes on Tweet per week") ///
         xtitle("Weeks from Birth") ///
         title("Average Likes per Tweet per Week pre/post birth (90pct followers)") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78) ///
		 legend(label(1 "> 90pct") label(2 "Others") position(2) ring(0))
* Save graph
graph export "$figures/post_interaction/restricted/likes_90pct_followers.jpg", replace
restore


**4A. month level - LIKES (90pct followers)
preserve
collapse (mean) like_count, by(author_id months_from_birth followers_90pct)
collapse (mean) like_count, by(months_from_birth followers_90pct)

** PLOT (total tweets)
twoway (line like_count months_from_birth if followers_90pct == 1, lcolor(magenta) lwidth(medthick)) ///
    (line like_count months_from_birth if followers_90pct == 0, lcolor(gray) lwidth(medthick)), ///
         xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Likes on Tweet per month (users w/ 90pct followers)") ///
         xtitle("Months from Birth") ///
         title("Average Likes per Tweet per Month pre/post birth (90pct followers)") ///
         graphregion(color(white)) ///
         xlabel(-19(2)19) ///
		 legend(label(1 "> 90pct") label(2 "Others") position(2) ring(0))
* Save graph
graph export "$figures/post_interaction/restricted/likes_90pctfollowers_bymonth.jpg", replace
restore



**5. LIKES (75pct followers)
preserve
collapse (mean) like_count, by(author_id week_from_birth followers_75pct)
collapse (mean) like_count, by(week_from_birth followers_75pct)

** PLOT (total tweets)
twoway (line like_count week_from_birth if followers_75pct == 1, lcolor(orange) lwidth(medthick)) ///
    (line like_count week_from_birth if followers_75pct == 0, lcolor(gray) lwidth(medthick)), ///
         xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Likes on Tweet per week (users w/ 90pct followers)") ///
         xtitle("Weeks from Birth") ///
         title("Average Likes per Tweet per Week pre/post birth (75pct followers)") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78) ///
		 legend(label(1 "> 75pct") label(2 "Others") position(2) ring(0))
* Save graph
graph export "$figures/post_interaction/restricted/likes_75pct_followers.jpg", replace
restore


**5A. by month - LIKES (75pct followers)
preserve
collapse (mean) like_count, by(author_id months_from_birth followers_75pct)
collapse (mean) like_count, by(months_from_birth followers_75pct)

** PLOT (total tweets)
twoway (line like_count months_from_birth if followers_75pct == 1, lcolor(orange) lwidth(medthick)) ///
    (line like_count months_from_birth if followers_75pct == 0, lcolor(gray) lwidth(medthick)), ///
         xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Likes on Tweet per month (users w/ 90pct followers)") ///
         xtitle("Weeks from Birth") ///
         title("Average Likes per Tweet per Month pre/post birth (75pct followers)") ///
         graphregion(color(white)) ///
         xlabel(-19(2)19) ///
		 legend(label(1 "> 75pct") label(2 "Others") position(2) ring(0))
* Save graph
graph export "$figures/post_interaction/restricted/likes_75pct_followers_bymonth.jpg", replace
restore


**6. LIKES (10th percentile vs 50th percentile followers)
preserve
drop if followers_count > 677 // users in the 50th percentile or less of followers
collapse (mean) like_count, by(author_id week_from_birth followers_10pct)
collapse (mean) like_count, by(week_from_birth followers_10pct)

** PLOT (total tweets)
twoway (line like_count week_from_birth if followers_10pct == 1, lcolor(pink) lwidth(medthick)) ///
    (line like_count week_from_birth if followers_10pct == 0, lcolor(gray) lwidth(medthick)), ///
         xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Likes on Tweet per week") ///
         xtitle("Weeks from Birth") ///
         title("Average Likes per Tweet per Week pre/post birth (50pct vs 10pct)") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78) ///
		 legend(label(1 "< 10pct") label(2 "> 10pct, < 50pct") position(2) ring(0))
* Save graph
graph export "$figures/post_interaction/restricted/likes_10_50pct_followers.jpg", replace
restore



**6A. per month - LIKES (10th percentile vs 50th percentile followers)
preserve
drop if followers_count > 677 // users in the 50th percentile or less of followers
collapse (mean) like_count, by(author_id months_from_birth followers_10pct)
collapse (mean) like_count, by(months_from_birth followers_10pct)

** PLOT (total tweets)
twoway (line like_count months_from_birth if followers_10pct == 1, lcolor(pink) lwidth(medthick)) ///
    (line like_count months_from_birth if followers_10pct == 0, lcolor(gray) lwidth(medthick)), ///
         xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Likes on Tweet per Month") ///
         xtitle("Weeks from Birth") ///
         title("Average Likes per Tweet per Month pre/post birth (50pct vs 10pct)") ///
         graphregion(color(white)) ///
         xlabel(-19(2)19) ///
		 legend(label(1 "< 10pct followers") label(2 "> 10pct, < 50pct followers") position(2) ring(0))
* Save graph
graph export "$figures/post_interaction/restricted/likes_10_50pct_followers_bymonth.jpg", replace
restore



**7. LIKES (25th percentile vs 50th percentile followers)
preserve
drop if followers_count > 677 // users in the 50th percentile or less of followers
collapse (mean) like_count, by(author_id week_from_birth followers_25pct)
collapse (mean) like_count, by(week_from_birth followers_25pct)

** PLOT (total tweets)
twoway (line like_count week_from_birth if followers_25pct == 1, lcolor(blue) lwidth(medthick)) ///
    (line like_count week_from_birth if followers_25pct == 0, lcolor(red) lwidth(medthick)), ///
         xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Likes on Tweet per week") ///
         xtitle("Weeks from Birth") ///
         title("Average Likes per Tweet per Week pre/post birth (50pct vs 25pct)") ///
         graphregion(color(white)) ///
         xlabel(-78(13)78) ///
		 legend(label(1 "< 25pct") label(2 "> 25pct") position(2) ring(0))
* Save graph
graph export "$figures/post_interaction/restricted/likes_25_50pct_followers.jpg", replace
restore


**7A. by month - LIKES (25th percentile vs 50th percentile followers)
preserve
drop if followers_count > 677 // users in the 50th percentile or less of followers
collapse (mean) like_count, by(author_id months_from_birth followers_25pct)
collapse (mean) like_count, by(months_from_birth followers_25pct)

** PLOT (total tweets)
twoway (line like_count months_from_birth if followers_25pct == 1, lcolor(blue) lwidth(medthick)) ///
    (line like_count months_from_birth if followers_25pct == 0, lcolor(red) lwidth(medthick)), ///
         xline(0, lpattern(dash) lcolor(edkblue)) ///
         ytitle("Avg Likes on Tweet per month") ///
         xtitle("Weeks from Birth") ///
         title("Average Likes per Tweet per Month pre/post birth (50pct vs 25pct)") ///
         graphregion(color(white)) ///
         xlabel(-19(2)19) ///
		 legend(label(1 "< 25pct") label(2 "> 25pct") position(2) ring(0))
* Save graph
graph export "$figures/post_interaction/restricted/likes_25_50pct_followers_bymo.jpg", replace
restore




****************** T TESTS ******************
*** Diagnostic test ***
preserve
gen postbirth = week_from_birth >= 0
keep if followers_75pct == 1
collapse (mean) like_count, by(author_id postbirth)
reshape wide like_count, i(author_id) j(postbirth) // one author per line (orig_qt_count1 = post birth)
gen change_in_likes = like_count1 - like_count0
sum change_in_likes, d

ttest like_count1 == like_count0
restore
* NOTE: The difference is not significant, meaning that there is likely some other correlation occuring after birth (decrease in posting) for those with lots of followers



**************************** EXPERIMENTING ****************************
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
merge m:1 unique_id using "$final/user_analysis_sample.dta", keepusing(date_birth followers_count) 
drop _merge
** Generate needed variables
gen days_from_birth = created_at - date_birth
gen months_from_birth = floor(days_from_birth / 30)
gen week_from_birth = floor(days_from_birth / 7)
gen post_interaction = like_count + retweet_count + reply_count + quote_count
** Restrict sample
egen min_days = min(days_from_birth), by(unique_id)
gen not_546 = min_days > -546 | min_days < -549
egen max_days = max(days_from_birth), by(unique_id)
replace not_546 = 1 if max_days < 546 | max_days > 549
drop if not_546 == 1

** Follower Percentiles
gen followers_10pct = (followers_count <= 41)
gen followers_25pct = (followers_count <= 117)
gen followers_50pct = (followers_count <= 322)
gen followers_75pct = (followers_count >= 894)
gen followers_90pct = (followers_count >= 2974)
// // gen post_count = 1 
// collapse (count) like_count, by(author_id week_from_birth)
// rename like_count post_count 
// merge 1:m author_id week_from_birth using "$cleaned/tweets_by_user_full_sample_CLEAN.dta", keepusing(post_count)



collapse (mean) like_count, by(author_id week_from_birth)



// collapse (mean) like_count, by(week_from_birth)




**************************** OTHER NOTES ****************************

// **7. LIKES (50th percentile/median)
// preserve
// collapse (mean) like_count, by(author_id week_from_birth followers_50pct)
// collapse (mean) like_count, by(week_from_birth followers_50pct)
//
// ** PLOT (total tweets)
// twoway (line like_count week_from_birth if followers_50pct == 1, lcolor(blue) lwidth(medthick)) ///
//     (line like_count week_from_birth if followers_50pct == 0, lcolor(red) lwidth(medthick)), ///
//          xline(0, lpattern(dash) lcolor(edkblue)) ///
//          ytitle("Avg Likes on Tweet per week") ///
//          xtitle("Weeks from Birth") ///
//          title("Average Likes/Tweet/Week pre/post birth (median split followers)") ///
//          graphregion(color(white)) ///
//          xlabel(-78(13)78) ///
// 		 legend(label(1 "< 50pct") label(2 "> 50pct") position(2) ring(0))
// * Save graph
// graph export "$figures/post_interaction/restricted/likes_50pct_followers.jpg", replace
// restore
//
//
//
// **6. Original Tweet behavior (followers 50th percentile) 4251 obs (<50pct), 4267 obs (>50pct)
// preserve
// collapse (mean) orig_qt_count, by(week_from_birth followers_50pct) 
// ** PLOT
// twoway ///
//     (line orig_qt_count week_from_birth if followers_50pct == 1, lcolor(blue) lwidth(medthick)) ///
//     (line orig_qt_count week_from_birth if followers_50pct == 0, lcolor(red) lwidth(medthick)), ///
//     xline(0, lpattern(dash) lcolor(edkblue)) ///
//     ytitle("Avg Tweets per User") ///
//     xtitle("Weeks from Birth") ///
//     title("Tweeting Behavior Pre/Post Birth (median split followers)") ///
//     graphregion(color(white)) ///
//     xlabel(-78(13)78) ///
//     legend(label(1 "< 50pct") label(2 "> 50pct") position(2) ring(0))
// * Save graph
// graph export "$figures/twt_behavior/followers_pct/orig_50pct_followers.jpg", replace
// restore
