* Author:  Hannah Lybbert
* Created: 02/20/2026
* Purpose: Diverging dot plot of post-pre change in tweet topic probabilities across all 19 topics
			* Did the composition of what people tweet about change after birth?

do "$dofile/set_globals.do"

use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

preserve

* Step 1: Calculate mean probability per topic per account for pre and post
collapse (mean) arts__culture business__entrepreneurs celebrity__pop_culture ///
    diaries__daily_life family fashion__style film_tv__video fitness__health ///
    food__dining gaming learning__educational music news__social_concern ///
    other_hobbies relationships science__technology sports travel__adventure ///
    youth__student_life, by(author_id post_birth)

* Step 2: Reshape to wide format (one row per author)
reshape wide arts__culture business__entrepreneurs celebrity__pop_culture ///
    diaries__daily_life family fashion__style film_tv__video fitness__health ///
    food__dining gaming learning__educational music news__social_concern ///
    other_hobbies relationships science__technology sports travel__adventure ///
    youth__student_life, i(author_id) j(post_birth)

* Step 3: Calculate differences for each author
foreach var in arts__culture business__entrepreneurs celebrity__pop_culture ///
    diaries__daily_life family fashion__style film_tv__video fitness__health ///
    food__dining gaming learning__educational music news__social_concern ///
    other_hobbies relationships science__technology sports travel__adventure ///
    youth__student_life {
    gen diff_`var' = `var'1 - `var'0
}

* Step 4: Calculate mean difference and SD across authors
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
    n_youth=diff_youth__student_life

* Step 5: Reshape for plotting
gen id = 1
reshape long mean_ sd_ n_, i(id) j(topic) string
rename (mean_ sd_ n_) (mean_diff sd_diff n)

* Step 6: Calculate 95% confidence intervals and convert to percentage points
gen se = sd_diff / sqrt(n)
gen ci_lower = (mean_diff - 1.96*se) * 100
gen ci_upper = (mean_diff + 1.96*se) * 100
replace mean_diff = mean_diff * 100

* Step 7: Create clean topic labels (matching topic_level_diff.do)
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

* Step 8: Sort by difference and assign plot order
gsort mean_diff
gen topic_order = _n
labmask topic_order, values(topic_clean)

* Step 9: Plot
twoway ///
    (rcap ci_lower ci_upper topic_order, horizontal lcolor($col_ci_main) lwidth($lw_dot_ci)) ///
    (scatter topic_order mean_diff, mcolor($col_main) msymbol($msym) msize($msize_dot)), ///
    $xline_zero ///
    xlabel(, format(%3.1f) labsize($xtick_size)) ///
    xtitle("Change in Topic Probability", size($xtitle_size)) ///
    ylabel(1(1)19, valuelabel angle(0) labsize($ytopics_size)) ///
    ytitle("") ///
    $leg_off ///
    $region

graph export "$topics_out/topic_prob_diff.$fig_format", replace

restore
