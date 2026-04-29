* Author:  Hannah Lybbert
* Created: 2026-04-14
* Updated: 2026-04-14
* Purpose: Check distribution of posts per author-month to identify outlier accounts

do "$dofile/set_globals_reddit.do"

* ----------------------------------------------------------------
* LOAD & FILTER
* ----------------------------------------------------------------
import delimited "$Reddit_final/births_and_posts_FULL.csv", ///
    bindquote(strict) maxquotedrows(unlimited) clear

keep if full_18_pre == 1
keep if months_from_birth >= -18 & months_from_birth <= 18
keep author months_from_birth subreddit

* ----------------------------------------------------------------
* COUNT POSTS PER AUTHOR-MONTH
* (each row = one post, so _N within author-month = post count)
* ----------------------------------------------------------------
bysort author months_from_birth: gen n_posts = _N
bysort author months_from_birth: keep if _n == 1

* ----------------------------------------------------------------
* OVERALL DISTRIBUTION OF POSTS PER AUTHOR-MONTH
* ----------------------------------------------------------------
di ""
di "===================================================="
di "POSTS PER AUTHOR-MONTH — overall"
di "===================================================="
tabstat n_posts, stats(mean sd p50 p75 p90 p95 p99 max)

* ----------------------------------------------------------------
* BY WINDOW: near birth (-4 to 4) vs. quiet pre-period (-18 to -10)
* ----------------------------------------------------------------
di ""
di "===================================================="
di "POSTS PER AUTHOR-MONTH — months -4 to 4 (near birth)"
di "===================================================="
tabstat n_posts if months_from_birth >= -4 & months_from_birth <= 4, ///
    stats(mean sd p50 p75 p90 p95 p99 max)

di ""
di "===================================================="
di "POSTS PER AUTHOR-MONTH — months -18 to -10 (pre-period)"
di "===================================================="
tabstat n_posts if months_from_birth >= -18 & months_from_birth <= -10, ///
    stats(mean sd p50 p75 p90 p95 p99 max)

* ----------------------------------------------------------------
* LIFETIME POSTS PER AUTHOR (within ±18 month window)
* ----------------------------------------------------------------
preserve
    collapse (sum) lifetime_posts = n_posts, by(author)
    di ""
    di "===================================================="
    di "LIFETIME POSTS PER AUTHOR (±18 month window)"
    di "===================================================="
    tabstat lifetime_posts, stats(mean sd p50 p75 p90 p95 p99 max)
restore

// * ----------------------------------------------------------------
// * HOW MANY AUTHOR-MONTHS EXCEED CANDIDATE THRESHOLDS?
// * ----------------------------------------------------------------
// di ""
// di "===================================================="
// di "AUTHOR-MONTHS ABOVE CANDIDATE THRESHOLDS"
// di "===================================================="
// foreach threshold in 50 100 200 500 1000 {
//     qui count if n_posts > `threshold'
//     local n_am = r(N)
//     qui bysort author: gen byte _flag = (n_posts > `threshold')
//     qui bysort author: egen _ever_flag = max(_flag)
//     qui count if _ever_flag == 1 & months_from_birth == -18
//     * Use distinct authors instead
//     qui levelsof author if n_posts > `threshold', local(flagged_authors)
//     local n_auth : word count `flagged_authors'
//     drop _flag _ever_flag
//     di "  n_posts > `threshold':  `n_am' author-months  |  ~`n_auth' unique authors"
// }
//
// * ----------------------------------------------------------------
// * SPOT CHECK: top 20 author-months by post count
// * ----------------------------------------------------------------
// di ""
// di "===================================================="
// di "TOP 20 AUTHOR-MONTHS BY POST COUNT"
// di "===================================================="
// gsort -n_posts
// list author months_from_birth n_posts in 1/20, noobs clean
