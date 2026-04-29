* Author:  Hannah Lybbert
* Created: 02/24/2026
* Purpose: Grouped bar chart of pre vs post mean topic probability across all 19 topics (conditional on tweeting)
*          Shows baseline probability level alongside post-birth level so magnitude of change is visible

do "$dofile/set_globals.do"

use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

preserve

* Step 1: Collapse to period-level mean probability for each topic
collapse (mean) arts__culture business__entrepreneurs celebrity__pop_culture ///
    diaries__daily_life family fashion__style film_tv__video fitness__health ///
    food__dining gaming learning__educational music news__social_concern ///
    other_hobbies relationships science__technology sports travel__adventure ///
    youth__student_life, by(post_birth)

* Step 2: Rename to short stubs for reshape
rename arts__culture             prob_arts
rename business__entrepreneurs   prob_business
rename celebrity__pop_culture    prob_celebrity
rename diaries__daily_life       prob_diaries
rename family                    prob_family
rename fashion__style            prob_fashion
rename film_tv__video            prob_film
rename fitness__health           prob_fitness
rename food__dining              prob_food
rename gaming                    prob_gaming
rename learning__educational     prob_learning
rename music                     prob_music
rename news__social_concern      prob_news
rename other_hobbies             prob_hobbies
rename relationships             prob_relationships
rename science__technology       prob_science
rename sports                    prob_sports
rename travel__adventure         prob_travel
rename youth__student_life       prob_youth

* Step 3: Reshape long — one row per topic x period
reshape long prob_, i(post_birth) j(topic) string
rename prob_ prob

* Convert to percentage points
replace prob = prob * 100

* Step 4: Reshape wide on post_birth — one row per topic, pre and post as columns
reshape wide prob, i(topic) j(post_birth)
rename (prob0 prob1) (pre_prob post_prob)

* Step 5: Clean topic labels (matching topic_prob_diff.do)
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

* Step 6: Plot — sorted ascending by pre-birth probability (highest at top)
graph hbar (asis) pre_prob post_prob, ///
    over(topic_clean, sort(1) label(labsize($ytopics_size))) ///
    bar(1, color($col_main)) ///
    bar(2, color($col_main%50)) ///
    legend(order(1 "Pre-Birth" 2 "Post-Birth") $leg_pos_ur size(medsmall)) ///
    ytitle("Average Topic Probability (%)", size($ytitle_size)) ///
    $region

graph export "$topics_out/topic_prob_prepost.$fig_format", replace

restore
