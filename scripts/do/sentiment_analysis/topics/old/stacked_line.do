* Author: Hannah Lybbert
* Created: 01/13/2026
* Purpose: Claude code stacked line and stacked area chart (take 2)


use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

* =================== STACKED LINE =========================================== *

* Step 1: Calculate mean probability per topic per account per month
preserve
collapse (mean) family relationships news__social_concern sports, ///
    by(author_id months_from_birth)

* Step 2: Calculate mean across accounts for each month
collapse (mean) family relationships news__social_concern sports, ///
    by(months_from_birth)

* Step 3: Create stacked area chart
graph twoway ///
    (area family months_from_birth, color(blue%70)) ///
    (area relationships months_from_birth, color(orange%70)) ///
    (area news__social_concern months_from_birth, color(green%70)) ///
    (area sports months_from_birth, color(gray%30)), ///
    xtitle("Months from Birth") ///
    ytitle("Average Topic Probability") ///
    xline(0, lcolor(black) lpattern(dash)) ///
    xlabel(, format(%9.0f)) ///
    ylabel(, format(%9.2f)) ///
	xlabel(-18(2)18) ///
    legend(size(small) cols(2) ///
        order(1 "Family" 2 "Relationships" 3 "News/Social Concern" ///
              4 "Sports") position(6)) ///
    graphregion(color(white)) plotregion(color(white)) ///
    title("Topic Probability Over Time Relative to Birth")

graph export "$tweetNLP_figs/topic_class/stacked_line.jpg", replace width(2400)

restore


* ============================ STACKED AREA ============================= *

* Step 1: Calculate mean probability per topic per account per month
preserve
collapse (mean) sports food__dining music news__social_concern relationships, ///
    by(author_id months_from_birth)

* Step 2: Calculate mean across accounts for each month
collapse (mean) sports food__dining music news__social_concern relationships, ///
    by(months_from_birth)

* Step 3: Calculate total probability and proportions
egen total_prob = rowtotal(sports food__dining music news__social_concern relationships)

foreach var in sports food__dining music news__social_concern relationships {
    gen prop_`var' = `var' / total_prob
}

* Step 4: Create cumulative variables for stacking
gen cum_sports = prop_sports
gen cum_food = cum_sports + prop_food__dining
gen cum_music = cum_food + prop_music
gen cum_news = cum_music + prop_news__social_concern
gen cum_relationships = cum_news + prop_relationships

* Step 5: Create 100% stacked area chart
graph twoway ///
    (area cum_relationships months_from_birth, color("255 102 0"%70)) ///
    (area cum_news months_from_birth, color("51 153 102"%70)) ///
    (area cum_music months_from_birth, color("0 102 204"%70)) ///
    (area cum_food months_from_birth, color("153 51 255"%70)) ///
    (area cum_sports months_from_birth, color("204 0 102"%70)), ///
    xtitle("Months from Birth") ///
    ytitle("Proportion of Topic Probability") ///
    xline(0, lcolor(black) lpattern(dash)) ///
    xlabel(, format(%9.0f)) ///
	xlabel(-18(3)18) ///
    ylabel(0(0.2)1, format(%9.1f)) ///
    legend(size(small) cols(2) ///
        order(5 "Sports" 4 "Food/Dining" 3 "Music" ///
              2 "News/Social Concern" 1 "Relationships")) ///
    graphregion(color(white)) plotregion(color(white)) ///
    title("Topic Proportion Over Time Relative to Birth")

graph export "$tweetNLP_figs/topic_class/stacked_areaT2.jpg", replace width(2400)

restore