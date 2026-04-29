* Author:  Hannah Lybbert
* Created: 2026-04-13
* Updated: 2026-04-13
* Purpose: Horizontal bar chart of tweet volume per topic per account per month (unconditional, full sample)
*          Aggregates over ALL sample accounts (including those who stop tweeting post-birth)
*          Rate = total topic tweets / (N_total_accounts * N_total_months)

do "$dofile/set_globals.do"

use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

* ----------------------------------------------------------------
* Step 1: Scalars — total sample accounts and distinct months
* ----------------------------------------------------------------
preserve
    keep author_id
    duplicates drop
    count
    scalar N_total = r(N)
restore

preserve
    keep months_from_birth
    duplicates drop
    count
    scalar M_total = r(N)
restore

* ----------------------------------------------------------------
* Step 2: Aggregate tweets by topic, compute rate
*         Interpretation: tweets per topic per account per month
* ----------------------------------------------------------------
preserve

    gen count_var = 1
    collapse (sum) n_tweets = count_var, by(topic)

    gen rate = n_tweets / (N_total * M_total)

    * Clean topic labels
    gen topic_clean = topic
    replace topic_clean = subinstr(topic_clean, "_&_", " & ", .)
    replace topic_clean = subinstr(topic_clean, "_", " ", .)
    replace topic_clean = proper(topic_clean)

    * ----------------------------------------------------------------
    * Step 3: Plot — sorted ascending by volume (highest at top)
    * ----------------------------------------------------------------
    graph hbar (asis) rate, ///
        over(topic_clean, sort(1) label(labsize($ytopics_size))) ///
        bar(1, color($col_main)) ///
        ytitle("Tweets per Account per Month", size($ytitle_size)) ///
        $region

    graph export "$topics_out/topic_level.$fig_format", replace

restore
