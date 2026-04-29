* Author:  Hannah Lybbert
* Created: 2026-04-13
* Updated: 2026-04-13
* Purpose: Pie chart of tweet share by topic — top 5 categories + family + other

do "$dofile/set_globals.do"

use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

* ----------------------------------------------------------------
* Step 1: Count tweets by topic and clean labels
* ----------------------------------------------------------------
preserve

    gen count_var = 1
    collapse (sum) n_tweets = count_var, by(topic)

    * Clean topic labels
    gen topic_clean = topic
    replace topic_clean = subinstr(topic_clean, "_&_", " & ", .)
    replace topic_clean = subinstr(topic_clean, "_", " ", .)
    replace topic_clean = proper(topic_clean)

    * Flag family separately, rank remaining by volume
    gen is_family = (topic_clean == "Family")
    gsort is_family -n_tweets
    gen rank = _n if is_family == 0

    * Group: keep top 5 non-family + family, rest into "Other"
    replace topic_clean = "Other" if is_family == 0 & rank > 5

    * Re-collapse so "Other" is one row
    collapse (sum) n_tweets, by(topic_clean)

    * ----------------------------------------------------------------
    * Step 2: Pie chart — top 5 topics + family + other
    * ----------------------------------------------------------------
    graph pie [fweight=n_tweets], over(topic_clean) ///
        plabel(_all percent, format(%9.1f) size(small)) ///
        pie(1, color(teal%60))         ///
        pie(2, color(maroon%60))       ///
        pie(3, color(forest_green%60)) ///
        pie(4, color(dkorange%60))     ///
        pie(5, color(navy%60))         ///
        pie(6, color(gs10%60))    ///
        pie(7, color(cranberry%60))         ///
        $region

    graph export "$topics_out/topic_shares.$fig_format", replace

restore

* ----------------------------------------------------------------
* Step 3: Horizontal bar chart — all categories, sorted by share
* ----------------------------------------------------------------
preserve

    gen count_var = 1
    collapse (sum) n_tweets = count_var, by(topic)

    * Clean topic labels
    gen topic_clean = topic
    replace topic_clean = subinstr(topic_clean, "_&_", " & ", .)
    replace topic_clean = subinstr(topic_clean, "_", " ", .)
    replace topic_clean = proper(topic_clean)

    * Compute share
    egen total_tweets = sum(n_tweets)
    gen share = n_tweets / total_tweets * 100

    graph hbar (asis) share, ///
        over(topic_clean, sort(1) label(labsize($ytopics_size))) ///
        bar(1, color($col_main)) ///
        ytitle("Share of Tweets (%)", size($ytitle_size)) ///
        $region

    graph export "$topics_out/topic_shares_bar.$fig_format", replace

restore
