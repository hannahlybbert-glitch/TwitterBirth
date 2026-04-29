* Author:  Hannah Lybbert
* Created: 2026-04-13
* Updated: 2026-04-13
* Purpose: Volume descriptive figures for Reddit post sample

do "$dofile/set_globals_reddit.do"

global vol_desc_out "$output/descriptives/volume"
capture mkdir "$output/descriptives"
capture mkdir "$vol_desc_out"

* ----------------------------------------------------------------
* LOAD & FILTER — window only
* ----------------------------------------------------------------
import delimited "$Reddit_final/births_and_posts_FULL.csv", ///
    bindquote(strict) maxquotedrows(unlimited) clear

keep if full_18_pre == 1
keep if months_from_birth >= -18 & months_from_birth <= 18

* ----------------------------------------------------------------
* FIGURE 1: Distribution of total posts per author (window)
* Each row = one post; count rows per author within window
* ----------------------------------------------------------------
preserve
    bysort author: gen total_posts = _N
    bysort author: keep if _n == 1

    gen total_posts_capped = min(total_posts, 200)

    hist total_posts_capped, bin(50) freq ///
        xtitle("Total Sample Posts", size($xtitle_size)) ///
        ytitle("Number of Authors", size($ytitle_size)) ///
        color($col_main%70) ///
        $region
    graph export "$vol_desc_out/hist_posts_window.$fig_format", replace
restore

* ----------------------------------------------------------------
* FIGURE 2: Distribution of posts pre vs post birth (overlaid)
* Pre:  months_from_birth in [-18, -1]
* Post: months_from_birth in [0, 18]
* ----------------------------------------------------------------
preserve
    gen byte post_birth = (months_from_birth >= 0)

    bysort author post_birth: gen period_posts = _N
    bysort author post_birth: keep if _n == 1

    gen period_posts_capped = min(period_posts, 100)

    twoway ///
        (histogram period_posts_capped if post_birth == 0, bin(50) freq color(gs4%50)) ///
        (histogram period_posts_capped if post_birth == 1, bin(50) freq color(purple%50)), ///
        xtitle("Total Posts in Period", size($xtitle_size)) ///
        ytitle("Number of Authors", size($ytitle_size)) ///
        legend(order(1 "Pre-Birth" 2 "Post-Birth") $leg_pos_ur) ///
        $region
    graph export "$vol_desc_out/hist_posts_prepost.$fig_format", replace
restore
