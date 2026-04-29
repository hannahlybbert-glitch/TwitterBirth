* Author:  Hannah Lybbert
* Created: 02/23/2026
* Updated: 02/23/2026
* Purpose: Export pre/post/change summary tables for topic level and topic probability analyses

do "$dofile/set_globals.do"

use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear


* ================================================================
* Part 1: Topic level (tweet count per account) summary table
* ================================================================

* ----------------------------------------------------------------
* Block 1a: Account-level SEs
* ----------------------------------------------------------------
preserve
	gen count_var = 1
	collapse (sum) n=count_var, by(author_id post_birth topic)

	keep author_id post_birth topic n
	reshape wide n, i(author_id topic) j(post_birth)

	replace n0 = 0 if n0 == .
	replace n1 = 0 if n1 == .

	gen change_account_level = n1 - n0

	collapse (mean) mean_change_level=change_account_level ///
		(mean) mean_n0=n0 mean_n1=n1 ///
		(sd) sd_change_level=change_account_level ///
		(count) n_accounts=change_account_level, by(topic)

	gen se_change_level = sd_change_level / sqrt(n_accounts)

	tempfile account_se
	save `account_se'
restore

* ----------------------------------------------------------------
* Block 1b: Aggregate pre/post/change + export
* ----------------------------------------------------------------
preserve
	gen count_var = 1
	collapse (sum) n=count_var, by(author_id post_birth topic)

	bysort post_birth topic: egen topic_tweets = sum(n)
	bysort post_birth topic: egen n_distinct_accounts = count(author_id)
	gen tweets_per_account = topic_tweets / n_distinct_accounts

	bysort post_birth topic: keep if _n == 1
	keep post_birth topic tweets_per_account n_distinct_accounts

	reshape wide tweets_per_account n_distinct_accounts, i(topic) j(post_birth)
	gen change_level = tweets_per_account1 - tweets_per_account0

	merge 1:1 topic using `account_se', nogen

	gen ci_lower = change_level - 1.96 * se_change_level
	gen ci_upper = change_level + 1.96 * se_change_level

	* Clean topic names
	gen topic_clean = topic
	replace topic_clean = subinstr(topic_clean, "_&_", " & ", .)
	replace topic_clean = subinstr(topic_clean, "_", " ", .)
	replace topic_clean = proper(topic_clean)

	gsort -change_level

	keep topic_clean tweets_per_account0 tweets_per_account1 change_level ///
		se_change_level ci_lower ci_upper n_accounts
	rename (tweets_per_account0 tweets_per_account1 change_level se_change_level) ///
	       (tweets_per_account_pre tweets_per_account_post change se)
	order topic_clean tweets_per_account_pre tweets_per_account_post change se ci_lower ci_upper n_accounts

	export delimited using "$topics_out/topic_level_diff_table.csv", replace
restore

* ----------------------------------------------------------------
* Block 1c: Unconditional mean — same denominator as SE (for comparison)
* Pre/post = mean(n0), mean(n1) across all accounts in either period
* ----------------------------------------------------------------
preserve
	use `account_se', clear

	gen ci_lower = mean_change_level - 1.96 * se_change_level
	gen ci_upper = mean_change_level + 1.96 * se_change_level

	gen topic_clean = topic
	replace topic_clean = subinstr(topic_clean, "_&_", " & ", .)
	replace topic_clean = subinstr(topic_clean, "_", " ", .)
	replace topic_clean = proper(topic_clean)

	gsort -mean_change_level

	keep topic_clean mean_n0 mean_n1 mean_change_level se_change_level ci_lower ci_upper n_accounts
	rename (mean_n0 mean_n1 mean_change_level se_change_level) ///
	       (tweets_per_account_pre tweets_per_account_post change se)
	order topic_clean tweets_per_account_pre tweets_per_account_post change se ci_lower ci_upper n_accounts

	export delimited using "$topics_out/topic_level_diff_acct_table.csv", replace
restore


* ================================================================
* Part 2: Topic probability (percentage point) summary table
* ================================================================
preserve

* Step 1: Mean probability per account per period
collapse (mean) arts__culture business__entrepreneurs celebrity__pop_culture ///
    diaries__daily_life family fashion__style film_tv__video fitness__health ///
    food__dining gaming learning__educational music news__social_concern ///
    other_hobbies relationships science__technology sports travel__adventure ///
    youth__student_life, by(author_id post_birth)

* Step 2: Reshape wide — one row per author
reshape wide arts__culture business__entrepreneurs celebrity__pop_culture ///
    diaries__daily_life family fashion__style film_tv__video fitness__health ///
    food__dining gaming learning__educational music news__social_concern ///
    other_hobbies relationships science__technology sports travel__adventure ///
    youth__student_life, i(author_id) j(post_birth)

* Step 3: Author-level differences
foreach var in arts__culture business__entrepreneurs celebrity__pop_culture ///
    diaries__daily_life family fashion__style film_tv__video fitness__health ///
    food__dining gaming learning__educational music news__social_concern ///
    other_hobbies relationships science__technology sports travel__adventure ///
    youth__student_life {
    gen diff_`var' = `var'1 - `var'0
}

* Step 4: Collapse — mean/SD/N of diff + mean of pre and post
collapse (mean) mean_arts=diff_arts__culture mean_business=diff_business__entrepreneurs ///
    mean_celebrity=diff_celebrity__pop_culture mean_diaries=diff_diaries__daily_life ///
    mean_family=diff_family mean_fashion=diff_fashion__style ///
    mean_film=diff_film_tv__video mean_fitness=diff_fitness__health ///
    mean_food=diff_food__dining mean_gaming=diff_gaming ///
    mean_learning=diff_learning__educational mean_music=diff_music ///
    mean_news=diff_news__social_concern mean_hobbies=diff_other_hobbies ///
    mean_relationships=diff_relationships mean_science=diff_science__technology ///
    mean_sports=diff_sports mean_travel=diff_travel__adventure ///
    mean_youth=diff_youth__student_life ///
    (sd) sd_arts=diff_arts__culture sd_business=diff_business__entrepreneurs ///
    sd_celebrity=diff_celebrity__pop_culture sd_diaries=diff_diaries__daily_life ///
    sd_family=diff_family sd_fashion=diff_fashion__style ///
    sd_film=diff_film_tv__video sd_fitness=diff_fitness__health ///
    sd_food=diff_food__dining sd_gaming=diff_gaming ///
    sd_learning=diff_learning__educational sd_music=diff_music ///
    sd_news=diff_news__social_concern sd_hobbies=diff_other_hobbies ///
    sd_relationships=diff_relationships sd_science=diff_science__technology ///
    sd_sports=diff_sports sd_travel=diff_travel__adventure ///
    sd_youth=diff_youth__student_life ///
    (count) n_arts=diff_arts__culture n_business=diff_business__entrepreneurs ///
    n_celebrity=diff_celebrity__pop_culture n_diaries=diff_diaries__daily_life ///
    n_family=diff_family n_fashion=diff_fashion__style ///
    n_film=diff_film_tv__video n_fitness=diff_fitness__health ///
    n_food=diff_food__dining n_gaming=diff_gaming ///
    n_learning=diff_learning__educational n_music=diff_music ///
    n_news=diff_news__social_concern n_hobbies=diff_other_hobbies ///
    n_relationships=diff_relationships n_science=diff_science__technology ///
    n_sports=diff_sports n_travel=diff_travel__adventure ///
    n_youth=diff_youth__student_life ///
    (mean) pre_arts=arts__culture0 pre_business=business__entrepreneurs0 ///
    pre_celebrity=celebrity__pop_culture0 pre_diaries=diaries__daily_life0 ///
    pre_family=family0 pre_fashion=fashion__style0 ///
    pre_film=film_tv__video0 pre_fitness=fitness__health0 ///
    pre_food=food__dining0 pre_gaming=gaming0 ///
    pre_learning=learning__educational0 pre_music=music0 ///
    pre_news=news__social_concern0 pre_hobbies=other_hobbies0 ///
    pre_relationships=relationships0 pre_science=science__technology0 ///
    pre_sports=sports0 pre_travel=travel__adventure0 ///
    pre_youth=youth__student_life0 ///
    (mean) post_arts=arts__culture1 post_business=business__entrepreneurs1 ///
    post_celebrity=celebrity__pop_culture1 post_diaries=diaries__daily_life1 ///
    post_family=family1 post_fashion=fashion__style1 ///
    post_film=film_tv__video1 post_fitness=fitness__health1 ///
    post_food=food__dining1 post_gaming=gaming1 ///
    post_learning=learning__educational1 post_music=music1 ///
    post_news=news__social_concern1 post_hobbies=other_hobbies1 ///
    post_relationships=relationships1 post_science=science__technology1 ///
    post_sports=sports1 post_travel=travel__adventure1 ///
    post_youth=youth__student_life1

* Step 5: Reshape long for plotting-style format
gen id = 1
reshape long mean_ sd_ n_ pre_ post_, i(id) j(topic) string
rename (mean_ sd_ n_ pre_ post_) (mean_diff sd_diff n mean_pre mean_post)

* Step 6: Compute SEs and convert to percentage points
gen se = sd_diff / sqrt(n)
gen ci_lower = (mean_diff - 1.96*se) * 100
gen ci_upper = (mean_diff + 1.96*se) * 100
replace mean_diff = mean_diff * 100
replace mean_pre  = mean_pre  * 100
replace mean_post = mean_post * 100
replace se        = se        * 100

* Step 7: Clean topic labels
gen topic_clean = topic
replace topic_clean = "Arts & Culture"           if topic == "arts"
replace topic_clean = "Business & Entrepreneurs" if topic == "business"
replace topic_clean = "Celebrity & Pop Culture"  if topic == "celebrity"
replace topic_clean = "Diaries & Daily Life"     if topic == "diaries"
replace topic_clean = "Family"                   if topic == "family"
replace topic_clean = "Fashion & Style"          if topic == "fashion"
replace topic_clean = "Film, TV & Video"         if topic == "film"
replace topic_clean = "Fitness & Health"         if topic == "fitness"
replace topic_clean = "Food & Dining"            if topic == "food"
replace topic_clean = "Gaming"                   if topic == "gaming"
replace topic_clean = "Other Hobbies"            if topic == "hobbies"
replace topic_clean = "Learning & Educational"   if topic == "learning"
replace topic_clean = "Music"                    if topic == "music"
replace topic_clean = "News & Social Concern"    if topic == "news"
replace topic_clean = "Relationships"            if topic == "relationships"
replace topic_clean = "Science & Technology"     if topic == "science"
replace topic_clean = "Sports"                   if topic == "sports"
replace topic_clean = "Travel & Adventure"       if topic == "travel"
replace topic_clean = "Youth & Student Life"     if topic == "youth"

gsort mean_diff

keep topic_clean mean_pre mean_post mean_diff se ci_lower ci_upper n
rename (mean_pre mean_post mean_diff se) (prob_pre_pp prob_post_pp change_pp se_pp)
order topic_clean prob_pre_pp prob_post_pp change_pp se_pp ci_lower ci_upper n

export delimited using "$topics_out/topic_prob_diff_table.csv", replace

restore
