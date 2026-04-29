* Author:  Hannah Lybbert
* Created: 2026-04-13
* Updated: 2026-04-14
* Purpose: User-level descriptive figures for Reddit birth post sample

do "$dofile/set_globals_reddit.do"

global desc_out "$output/descriptives/user"
capture mkdir "$output/descriptives"
capture mkdir "$desc_out"

* ----------------------------------------------------------------
* LOAD & FILTER — birth posts only
* ----------------------------------------------------------------
import delimited "$Reddit_final/births_and_posts_FULL.csv", ///
    bindquote(strict) maxquotedrows(unlimited) clear

keep if full_18_pre == 1
keep if birth_post == 1

* ----------------------------------------------------------------
* CONSOLE: Sample counts
* ----------------------------------------------------------------
preserve
    duplicates drop author, force
    count
    local n_all = r(N)
    count if full_18_pre == 1
    local n_full18 = r(N)
restore

di ""
di "===================================================="
di "SAMPLE COUNTS (birth_post == 1)"
di "===================================================="
di "Unique authors with a birth post:         `n_all'"
di "  of which full_18_pre == 1:              `n_full18'"
di "===================================================="
di ""

* All subreddits with birth posts, sorted by frequency
tab subreddit, sort

* ----------------------------------------------------------------
* FIGURE 1: Gender split (Male / Female / Unknown)
* ----------------------------------------------------------------
tempvar gender_cat
gen `gender_cat' = .
replace `gender_cat' = 1 if female == 0
replace `gender_cat' = 2 if female == 1
replace `gender_cat' = 3 if female == -99
label define gender_lbl 1 "Male" 2 "Female" 3 "Unknown", replace
label values `gender_cat' gender_lbl

graph bar (percent), over(`gender_cat') ///
    ytitle("Share of Authors", size($ytitle_size)) ///
    blabel(total, format(%9.1f) size(medlarge)) ///
    asyvars ///
    bar(1, color($col_male%60)) bar(2, color($col_female%60)) bar(3, color(gs10%60)) ///
    legend(label(1 "Male") label(2 "Female") label(3 "Unknown") $leg_pos_ur) ///
    $region
graph export "$desc_out/gender_shares.$fig_format", replace

* ----------------------------------------------------------------
* FIGURE 2: Date of birth distribution
* ----------------------------------------------------------------
gen date_birth_num = date(substr(date_birth, 1, 10), "YMD")
format date_birth_num %td

hist date_birth_num, freq ///
    xtitle("Date of Birth", size($xtitle_size)) ///
    ytitle("Number of Authors", size($ytitle_size)) ///
    color($col_main%70) ///
    xlabel(, format(%tdMonCCYY)) ///
    $region
graph export "$desc_out/DOB_dist.$fig_format", replace

* ----------------------------------------------------------------
* FIGURE 3: Days-from-birth distribution (capped at ±30)
* days_from: negative = birth post before DOB, positive = after
* ----------------------------------------------------------------
destring days_from, replace force

gen days_from_28 = max(min(days_from, 28), -28)

hist days_from_28, freq gap(0) ///
    xtitle("Days Between Birth Post and Date of Birth", size($xtitle_size)) ///
    ytitle("Number of Authors", size($ytitle_size)) ///
    color($col_main%70) ///
    xlabel(-28(7)28) ///
    $region
graph export "$desc_out/days_from_dist.$fig_format", replace

* ----------------------------------------------------------------
* FIGURE 3a: Days-from-birth distribution (capped at ±7)
* ----------------------------------------------------------------
gen days_from_capped = max(min(days_from, 7), -7)

hist days_from_capped, freq width(2) gap(0) ///
    xtitle("Days Between Birth Post and Date of Birth", size($xtitle_size)) ///
    ytitle("Number of Authors", size($ytitle_size)) ///
    color($col_main%70) ///
    xlabel(-7(1)7) ///
    $region
graph export "$desc_out/days_from_dist_capped.$fig_format", replace

* ----------------------------------------------------------------
* FIGURE 4: All 13 subreddits (birth posts)
* ----------------------------------------------------------------
preserve
    contract subreddit
    gsort _freq        // lowest to highest so highest bar appears at top

    local ylabels ""
    forvalues i = 1/`=_N' {
        local sub = subreddit[`i']
        local ylabels `"`ylabels' `i' "`sub'""'
    }
    gen rank = _n

    twoway bar _freq rank, horizontal barwidth(0.7) ///
        color($col_main%70) ///
        xtitle("Number of Birth Posts", size($xtitle_size)) ///
        ytitle("") ///
        ylabel(`ylabels', labsize(mlarge) angle(0)) ///
        $region
    graph export "$desc_out/subreddits_all.$fig_format", replace
restore
