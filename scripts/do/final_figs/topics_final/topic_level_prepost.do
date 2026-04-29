* Author:  Hannah Lybbert
* Created: 02/24/2026
* Purpose: Grouped bar chart of pre vs post tweet volume per topic per account per month (unconditional)
*          Aggregates over ALL sample accounts (including those who stop tweeting post-birth)
*          Rate = total topic tweets / (N_total_accounts * N_months_in_period)

do "$dofile/set_globals.do"

use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

* ----------------------------------------------------------------
* Step 1: Scalars — total sample accounts and distinct months per period
* ----------------------------------------------------------------
preserve
    keep author_id
    duplicates drop
    count
    scalar N_total = r(N)
restore

preserve
    keep months_from_birth post_birth
    duplicates drop
    count if post_birth == 0
    scalar M_pre = r(N)
    count if post_birth == 1
    scalar M_post = r(N)
restore

* ----------------------------------------------------------------
* Step 2: Aggregate tweets by topic and period, compute rate
*         Interpretation: tweets per topic per account per month
* ----------------------------------------------------------------
preserve

    gen count_var = 1
    collapse (sum) n_tweets = count_var, by(post_birth topic)

    gen rate = n_tweets / (N_total * M_pre)  if post_birth == 0
    replace rate = n_tweets / (N_total * M_post) if post_birth == 1

    * Clean topic labels
    gen topic_clean = topic
    replace topic_clean = subinstr(topic_clean, "_&_", " & ", .)
    replace topic_clean = subinstr(topic_clean, "_", " ", .)
    replace topic_clean = proper(topic_clean)

    * Reshape wide: one row per topic with pre and post rates
    keep post_birth topic_clean rate
    reshape wide rate, i(topic_clean) j(post_birth)
    rename (rate0 rate1) (pre_rate post_rate)

    * ----------------------------------------------------------------
    * Step 3: Plot — sorted ascending by pre-birth volume (highest at top)
    * ----------------------------------------------------------------
    graph hbar (asis) pre_rate post_rate, ///
        over(topic_clean, sort(1) label(labsize($ytopics_size))) ///
        bar(1, color($col_main)) ///
        bar(2, color($col_main%50)) ///
        legend(order(1 "Pre-Birth" 2 "Post-Birth") $leg_pos_ur size(medsmall)) ///
        ytitle("Tweets per Account per Month", size($ytitle_size)) ///
        $region

    graph export "$topics_out/topic_level_prepost.$fig_format", replace

restore
