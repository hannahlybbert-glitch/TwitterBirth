* Author: Hannah Lybbert
* Created: 01/22/2026
* Purpose: How does post interaction change over time



use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear

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
// graph export "$figures/post_interaction/restricted/likes_all_bymonth.jpg", replace
restore



** 1. LIKES (all, by month) 
preserve
collapse (mean) like_count, by(author_id months_from_birth)

collapse (mean) like_count ///
         (sd)   sd_like   = like_count ///
         (count) n_authors = like_count, ///
         by(months_from_birth)

	gen se = sd_like / sqrt(n_authors)
	gen ci_lower  = like_count - 1.96 * se
	gen ci_upper   = like_count + 1.96 * se
	
** PLOT (total likes)
twoway ///
	(rcap ci_upper ci_lower months_from_birth, lcolor(gs8)) ///
	(line like_count months_from_birth, lwidth(medthick) lcolor(red)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
      ytitle("Avg Likes per Tweet per Month") ///
      xtitle("Month from Birth") ///
      title("Avg Likes per Tweet per Month pre/post birth") ///
	  legend(label(1 "95% CI") label(2 "Avg Likes") position(2) ring(0)) ///
      graphregion(color(white)) ///
      xlabel(-18(2)18)
* Save graph
graph export "$figures/post_interaction/likes.jpg", replace
restore

** 2. REPLIES (all, by month) 
preserve
collapse (mean) reply_count, by(author_id months_from_birth)

collapse (mean) reply_count ///
         (sd)   sd_reply  = reply_count ///
         (count) n_authors = reply_count, ///
         by(months_from_birth)

	gen se = sd_reply / sqrt(n_authors)
	gen ci_lower  = reply_count - 1.96 * se
	gen ci_upper   = reply_count + 1.96 * se
	
** PLOT (total likes)
twoway ///
	(rcap ci_upper ci_lower months_from_birth, lcolor(gs8)) ///
	(line reply_count months_from_birth, lwidth(medthick) lcolor(blue)) ///
    , xline(0, lpattern(dash) lcolor(edkblue)) ///
      ytitle("Avg Replies per Tweet per Month") ///
      xtitle("Month from Birth") ///
      title("Avg Replies per Tweet per Month pre/post birth") ///
	  legend(label(1 "95% CI") label(2 "Avg Replies") position(2) ring(0)) ///
      graphregion(color(white)) ///
      xlabel(-18(2)18)
* Save graph
graph export "$figures/post_interaction/replies.jpg", replace
restore