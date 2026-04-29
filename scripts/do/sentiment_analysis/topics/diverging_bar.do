* Author: Hannah Lybbert
* Created: 01/13/2026
* Purpose: Claude difference plot using probability variables not topics (take 2)



use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear


* ================== TWOWAY ATTEMPT ========================== *  
		* THis one works!

* ===================== ALL 19 TOPICS =============================== *

use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

* Step 1: Calculate mean probability per topic per account for pre and post
preserve
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

* Step 4: Calculate mean difference and 95% CI across authors
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

* Step 6: Calculate 95% confidence intervals
gen se = sd_diff / sqrt(n)
gen ci_lower = mean_diff - 1.96*se
gen ci_upper = mean_diff + 1.96*se

* Step 7: Sort by difference and create numeric position
gsort mean_diff
gen topic_order = _n

* Step 8: Create value labels for topics
labmask topic_order, values(topic)

* Step 9: Create plot with error bars using twoway
twoway (rcap ci_lower ci_upper topic_order, horizontal lcolor(gs10)) ///
       (scatter topic_order mean_diff, mcolor(navy) msymbol(O) msize(medium)), ///
    xline(0, lcolor(black) lpattern(solid)) ///
    xlabel(, format(%9.3f)) ///
    xtitle("Change in Topic Probability (Post - Pre)") ///
    ylabel(1(1)19, valuelabel angle(0) labsize(small)) ///
    ytitle("") ///
    graphregion(color(white)) plotregion(color(white)) ///
    title("Change in Tweet Topic Probabilities: Post vs Pre Birth") ///
    legend(off) ///
	note("Note: percentage point change in tweet topic probability." ///
	"Sample size = 4137 (8 accounts dropped off likely because had no average probabilities in pre/post period.)")

graph export "$tweetNLP_figs/topic_class/diverging_dot_probs.jpg", replace

restore
		
		
* ===================== SELECTION OF TOPICS =============================== *
		
* Step 1: Calculate mean probability per topic per account for pre and post
preserve
collapse (mean) diaries__daily_life family fashion__style film_tv__video ///
    fitness__health food__dining gaming learning__educational music ///
    news__social_concern, by(author_id post_birth)
		* Each author now has two rows (pre, post) with average probability of that topic in each period

* Step 2: Reshape to wide format (one row per author)
reshape wide diaries__daily_life family fashion__style film_tv__video ///
    fitness__health food__dining gaming learning__educational music ///
    news__social_concern, i(author_id) j(post_birth)
		* Each author has one row 

* Step 3: Calculate differences for each author
foreach var in diaries__daily_life family fashion__style film_tv__video ///
    fitness__health food__dining gaming learning__educational music ///
    news__social_concern {
    gen diff_`var' = `var'1 - `var'0
}

* Step 4: Calculate mean difference and 95% CI across authors
collapse (mean) mean_diaries=diff_diaries__daily_life mean_family=diff_family ///
    mean_fashion=diff_fashion__style mean_film=diff_film_tv__video ///
    mean_fitness=diff_fitness__health mean_food=diff_food__dining ///
    mean_gaming=diff_gaming mean_learning=diff_learning__educational ///
    mean_music=diff_music mean_news=diff_news__social_concern ///
    (sd) sd_diaries=diff_diaries__daily_life sd_family=diff_family ///
    sd_fashion=diff_fashion__style sd_film=diff_film_tv__video ///
    sd_fitness=diff_fitness__health sd_food=diff_food__dining ///
    sd_gaming=diff_gaming sd_learning=diff_learning__educational ///
    sd_music=diff_music sd_news=diff_news__social_concern ///
    (count) n_diaries=diff_diaries__daily_life n_family=diff_family ///
    n_fashion=diff_fashion__style n_film=diff_film_tv__video ///
    n_fitness=diff_fitness__health n_food=diff_food__dining ///
    n_gaming=diff_gaming n_learning=diff_learning__educational ///
    n_music=diff_music n_news=diff_news__social_concern
		* one row of data with the mean, sd, and count for each topic

* Step 5: Reshape for plotting
gen id = 1
reshape long mean_ sd_ n_, i(id) j(topic) string

rename (mean_ sd_ n_) (mean_diff sd_diff n)

* Step 6: Calculate 95% confidence intervals
gen se = sd_diff / sqrt(n)
gen ci_lower = mean_diff - 1.96*se
gen ci_upper = mean_diff + 1.96*se

* Step 7: Sort by difference and create numeric position
gsort mean_diff
gen topic_order = _n

* Step 8: Create value labels for topics
labmask topic_order, values(topic)

* Step 9: Create plot with error bars using twoway
twoway (rcap ci_lower ci_upper topic_order, horizontal lcolor(gs10)) ///
       (scatter topic_order mean_diff, mcolor(navy) msymbol(O) msize(medium)), ///
    xline(0, lcolor(black) lpattern(solid)) ///
    xlabel(, format(%9.3f)) ///
    xtitle("Change in Topic Probability (Post - Pre)") ///
    ylabel(1(1)10, valuelabel angle(0) labsize(small)) ///
    ytitle("") ///
    graphregion(color(white)) plotregion(color(white)) ///
    title("Change in Tweet Topic Probabilities: Post vs Pre Birth") ///
    legend(off)

restore







* ===================== DIVERGING BAR ATTEMPT =============================== *

preserve
* Step 1: Calculate mean probability per topic per account for pre and post
collapse (mean) diaries__daily_life family fashion__style film_tv__video ///
    fitness__health food__dining gaming learning__educational music ///
    news__social_concern, by(author_id post_birth)

* Step 2: Calculate mean across accounts for each period
collapse (mean) diaries__daily_life family fashion__style film_tv__video ///
    fitness__health food__dining gaming learning__educational music ///
    news__social_concern, by(post_birth)

* Step 3: Create identifier for reshape
gen id = 1

* Step 4: Reshape to calculate differences
reshape wide diaries__daily_life family fashion__style film_tv__video ///
    fitness__health food__dining gaming learning__educational music ///
    news__social_concern, i(id) j(post_birth)

* Step 5: Calculate differences (post - pre)
foreach var in diaries__daily_life family fashion__style film_tv__video ///
    fitness__health food__dining gaming learning__educational music ///
    news__social_concern {
    gen diff_`var' = `var'1 - `var'0
}

* Step 6: Reshape for plotting
keep diff_*
gen id2 = 1
reshape long diff_, i(id2) j(topic) string

* Step 7: Sort by difference (most negative to most positive)
gsort diff_
gen topic_order = _n

* Step 8: Create diverging bar chart
graph hbar diff_, over(topic, sort(topic_order) label(labsize(small))) ///
    ytitle("Change in Topic Probability (Post - Pre)") ///
    ylabel(, format(%9.3f)) ///
    yline(0, lcolor(black)) ///
    bar(1, fcolor(navy%70) lcolor(navy)) ///
    graphregion(color(white)) plotregion(color(white)) ///
    title("Change in Tweet Topic Probabilities: Post vs Pre Birth") ///
	note("Note: percentage point change in tweet topic probability)")

restore
	
	
	
* ========================= WITH CONFIDENCE INTERVALS ========================*

* Step 1: Calculate mean probability per topic per account for pre and post
preserve
collapse (mean) diaries__daily_life family fashion__style film_tv__video ///
    fitness__health food__dining gaming learning__educational music ///
    news__social_concern, by(author_id post_birth)

* Step 2: Reshape to wide format (one row per author)
reshape wide diaries__daily_life family fashion__style film_tv__video ///
    fitness__health food__dining gaming learning__educational music ///
    news__social_concern, i(author_id) j(post_birth)

* Step 3: Calculate differences for each author
foreach var in diaries__daily_life family fashion__style film_tv__video ///
    fitness__health food__dining gaming learning__educational music ///
    news__social_concern {
    gen diff_`var' = `var'1 - `var'0
}

* Step 4: Calculate mean difference and 95% CI across authors
collapse (mean) mean_diaries=diff_diaries__daily_life mean_family=diff_family ///
    mean_fashion=diff_fashion__style mean_film=diff_film_tv__video ///
    mean_fitness=diff_fitness__health mean_food=diff_food__dining ///
    mean_gaming=diff_gaming mean_learning=diff_learning__educational ///
    mean_music=diff_music mean_news=diff_news__social_concern ///
    (sd) sd_diaries=diff_diaries__daily_life sd_family=diff_family ///
    sd_fashion=diff_fashion__style sd_film=diff_film_tv__video ///
    sd_fitness=diff_fitness__health sd_food=diff_food__dining ///
    sd_gaming=diff_gaming sd_learning=diff_learning__educational ///
    sd_music=diff_music sd_news=diff_news__social_concern ///
    (count) n_diaries=diff_diaries__daily_life n_family=diff_family ///
    n_fashion=diff_fashion__style n_film=diff_film_tv__video ///
    n_fitness=diff_fitness__health n_food=diff_food__dining ///
    n_gaming=diff_gaming n_learning=diff_learning__educational ///
    n_music=diff_music n_news=diff_news__social_concern

* Step 5: Reshape for plotting
gen id = 1
reshape long mean_ sd_ n_, i(id) j(topic) string

rename (mean_ sd_ n_) (mean_diff sd_diff n)

* Step 6: Calculate 95% confidence intervals
gen se = sd_diff / sqrt(n)
gen ci_lower = mean_diff - 1.96*se
gen ci_upper = mean_diff + 1.96*se

* Step 7: Sort by difference
gsort mean_diff
gen topic_order = _n

* Step 8: Create diverging bar chart with confidence intervals
graph hbar mean_diff ci_lower ci_upper, ///
    over(topic, sort(topic_order) label(labsize(small))) ///
    ytitle("Change in Topic Probability (Post - Pre)") ///
    ylabel(, format(%9.3f)) ///
    yline(0, lcolor(black)) ///
    bar(1, fcolor(navy%70) lcolor(navy)) ///
    bar(2, fcolor(none) lcolor(gs8) lwidth(thin)) ///
    bar(3, fcolor(none) lcolor(gs8) lwidth(thin)) ///
    legend(order(1 "Mean Change" 2 "95% CI") size(small)) ///
    graphregion(color(white)) plotregion(color(white)) ///
    title("Change in Tweet Topic Probabilities: Post vs Pre Birth")

restore



* ========================== This one became a dot plot... ================*

* Step 1: Calculate mean probability per topic per account for pre and post
preserve
collapse (mean) diaries__daily_life family fashion__style film_tv__video ///
    fitness__health food__dining gaming learning__educational music ///
    news__social_concern, by(author_id post_birth)

* Step 2: Reshape to wide format (one row per author)
reshape wide diaries__daily_life family fashion__style film_tv__video ///
    fitness__health food__dining gaming learning__educational music ///
    news__social_concern, i(author_id) j(post_birth)

* Step 3: Calculate differences for each author
foreach var in diaries__daily_life family fashion__style film_tv__video ///
    fitness__health food__dining gaming learning__educational music ///
    news__social_concern {
    gen diff_`var' = `var'1 - `var'0
}

* Step 4: Calculate mean difference and 95% CI across authors
collapse (mean) mean_diaries=diff_diaries__daily_life mean_family=diff_family ///
    mean_fashion=diff_fashion__style mean_film=diff_film_tv__video ///
    mean_fitness=diff_fitness__health mean_food=diff_food__dining ///
    mean_gaming=diff_gaming mean_learning=diff_learning__educational ///
    mean_music=diff_music mean_news=diff_news__social_concern ///
    (sd) sd_diaries=diff_diaries__daily_life sd_family=diff_family ///
    sd_fashion=diff_fashion__style sd_film=diff_film_tv__video ///
    sd_fitness=diff_fitness__health sd_food=diff_food__dining ///
    sd_gaming=diff_gaming sd_learning=diff_learning__educational ///
    sd_music=diff_music sd_news=diff_news__social_concern ///
    (count) n_diaries=diff_diaries__daily_life n_family=diff_family ///
    n_fashion=diff_fashion__style n_film=diff_film_tv__video ///
    n_fitness=diff_fitness__health n_food=diff_food__dining ///
    n_gaming=diff_gaming n_learning=diff_learning__educational ///
    n_music=diff_music n_news=diff_news__social_concern

* Step 5: Reshape for plotting
gen id = 1
reshape long mean_ sd_ n_, i(id) j(topic) string

rename (mean_ sd_ n_) (mean_diff sd_diff n)

* Step 6: Calculate 95% confidence intervals
gen se = sd_diff / sqrt(n)
gen ci_lower = mean_diff - 1.96*se
gen ci_upper = mean_diff + 1.96*se

* Step 7: Sort by difference
gsort mean_diff
gen topic_order = _n

* Step 8: Create plot with error bars using twoway
graph dot mean_diff, over(topic, sort(topic_order)) ///
    marker(1, msize(large) mcolor(navy)) ///
    ytitle("Change in Topic Probability (Post - Pre)") ///
    ylabel(, format(%9.3f)) ///
    yline(0, lcolor(black)) ///
    graphregion(color(white)) plotregion(color(white)) ///
    title("Change in Tweet Topic Probabilities: Post vs Pre Birth")
    
* Alternative: Use coefplot if installed (cleaner for CIs)
* ssc install coefplot
* coefplot (scatter topic_order mean_diff, msymbol(O) mcolor(navy)), ///
*     se(se) ciopts(lcolor(gs8)) xline(0) vertical recast(bar)

restore


