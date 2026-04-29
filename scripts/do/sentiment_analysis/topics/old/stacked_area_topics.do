* Author: Hannah Lybbert
* Created: 12/05/2025
* Purpose: Claude code stacked line and slope charts

use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear


* ============= MAIN ONE THAT WORKS (the one in the slides) ================ *

* First, collapse to get counts by month and topic
preserve

* Count tweets by month and topic
gen n_tweets = 1
collapse (sum) n_tweets, by(months_from_birth topic)

* Exclude diaries & daily life AND family
drop if topic == "diaries_&_daily_life"
drop if topic == "family"

* Create topic groupings
gen topic_grouped = topic

* Group specified topics into "Other"
replace topic_grouped = "other" if inlist(topic, "youth_&_student_life", "travel_&_adventure", "relationships", "arts_&_culture")
replace topic_grouped = "other" if inlist(topic, "fitness_&_health", "gaming", "learning_&_educational", "other_hobbies", "science_&_technology")

* Collapse again to aggregate the "other" category
collapse (sum) n_tweets, by(months_from_birth topic_grouped)

* Get total tweets per month
bysort months_from_birth: egen total_tweets_month = total(n_tweets)

* Calculate proportion
gen proportion = (n_tweets / total_tweets_month) * 100

* Encode the grouped topic variable
encode topic_grouped, gen(topic_num)

* Label the numeric topic variable (now with 9 topics)
label define topic_labels ///
    1 "Business & Entrepreneurs" ///
    2 "Celebrity & Pop Culture" ///
    3 "Fashion & Style" ///
    4 "Film, TV & Video" ///
    5 "Food & Dining" ///
    6 "Music" ///
    7 "News & Social Concern" ///
    8 "Other" ///
    9 "Sports"
label values topic_num topic_labels

********************************************************************************
* STACKED AREA CHART
********************************************************************************
* Drop the string topic variable since we now have topic_num
drop topic_grouped

* Reshape to wide format for stacked area chart
reshape wide n_tweets proportion, i(months_from_birth) j(topic_num)

* Generate cumulative proportions for stacking
gen cum1 = proportion1
forvalues i = 2/9 {
    local j = `i' - 1
    gen cum`i' = cum`j' + proportion`i'
}

* Create the stacked area chart (now with 9 topics)
twoway ///
    (area cum1 months_from_birth, color("0 114 178") fintensity(80)) ///
    (rarea cum1 cum2 months_from_birth, color("230 159 0") fintensity(80)) ///
    (rarea cum2 cum3 months_from_birth, color("86 180 233") fintensity(80)) ///
    (rarea cum3 cum4 months_from_birth, color("0 158 115") fintensity(80)) ///
    (rarea cum4 cum5 months_from_birth, color("240 228 66") fintensity(80)) ///
    (rarea cum5 cum6 months_from_birth, color("204 121 167") fintensity(80)) ///
    (rarea cum6 cum7 months_from_birth, color("213 94 0") fintensity(80)) ///
    (rarea cum7 cum8 months_from_birth, color("0 114 178*.7") fintensity(80)) ///
    (rarea cum8 cum9 months_from_birth, color("230 159 0*.7") fintensity(80)), ///
    xlabel(-18(3)18, labsize(small)) ///
    ylabel(0(20)100, angle(0) labsize(small)) ///
    xtitle("Months from Birth", size(medium)) ///
    ytitle("Percentage of Tweets (%)", size(medium)) ///
    xline(0, lcolor(red) lpattern(dash) lwidth(medium) lstyle(foreground)) ///
    title("Topic Composition of Tweets Around Birth Event", size(medium)) ///
    subtitle("Stacked area chart showing % of tweets by topic", size(small)) ///
    note("Red line indicates month of birth (month 0). 'Other' includes: Youth/Student, Travel, Relationships," ///
         "Arts/Culture, Fitness, Gaming, Education, Other Hobbies, Science/Tech. Excludes Family and Daily Life topics.", size(vsmall)) ///
    legend(order(1 "Business" 2 "Celebrity" 3 "Fashion" 4 "Film/TV" ///
        5 "Food" 6 "Music" 7 "News" 8 "Other" 9 "Sports") ///
        cols(2) size(small) position(3) ring(1)) ///
    graphregion(color(white)) plotregion(color(white))

graph export "$tweetNLP_figs/topic_class/stacked_area_nofam.jpg", replace width(2400)

restore




********************************************************************************
* STACKED AREA CHART AND SLOPE CHARTS FOR TOPIC COMPOSITION AROUND BIRTH
********************************************************************************

use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

* First, collapse to get counts by month and topic
preserve

* Count tweets by month and topic
gen n_tweets = 1
collapse (sum) n_tweets, by(months_from_birth topic)

* Exclude diaries & daily life
drop if topic == "diaries_&_daily_life"

* Create topic groupings
gen topic_grouped = topic

* Group specified topics into "Other"
replace topic_grouped = "other" if inlist(topic, "youth_&_student_life", "travel_&_adventure", "relationships", "arts_&_culture")
replace topic_grouped = "other" if inlist(topic, "fitness_&_health", "gaming", "learning_&_educational", "other_hobbies", "science_&_technology")

* Collapse again to aggregate the "other" category
collapse (sum) n_tweets, by(months_from_birth topic_grouped)

* Get total tweets per month
bysort months_from_birth: egen total_tweets_month = total(n_tweets)

* Calculate proportion
gen proportion = (n_tweets / total_tweets_month) * 100

* Encode the grouped topic variable
encode topic_grouped, gen(topic_num)

* Label the numeric topic variable (now with 10 topics)
label define topic_labels ///
    1 "Business & Entrepreneurs" ///
    2 "Celebrity & Pop Culture" ///
    3 "Family" ///
    4 "Fashion & Style" ///
    5 "Film, TV & Video" ///
    6 "Food & Dining" ///
    7 "Music" ///
    8 "News & Social Concern" ///
    9 "Other" ///
    10 "Sports"
label values topic_num topic_labels

********************************************************************************
* STACKED AREA CHART
********************************************************************************
* Drop the string topic variable since we now have topic_num
drop topic_grouped

* Reshape to wide format for stacked area chart
reshape wide n_tweets proportion, i(months_from_birth) j(topic_num)

* Generate cumulative proportions for stacking
gen cum1 = proportion1
forvalues i = 2/10 {
    local j = `i' - 1
    gen cum`i' = cum`j' + proportion`i'
}

* Create the stacked area chart (now with 10 topics)
twoway ///
    (area cum1 months_from_birth, color("0 114 178") fintensity(80)) ///
    (rarea cum1 cum2 months_from_birth, color("230 159 0") fintensity(80)) ///
    (rarea cum2 cum3 months_from_birth, color("86 180 233") fintensity(80)) ///
    (rarea cum3 cum4 months_from_birth, color("0 158 115") fintensity(80)) ///
    (rarea cum4 cum5 months_from_birth, color("240 228 66") fintensity(80)) ///
    (rarea cum5 cum6 months_from_birth, color("204 121 167") fintensity(80)) ///
    (rarea cum6 cum7 months_from_birth, color("213 94 0") fintensity(80)) ///
    (rarea cum7 cum8 months_from_birth, color("0 114 178*.7") fintensity(80)) ///
    (rarea cum8 cum9 months_from_birth, color("230 159 0*.7") fintensity(80)) ///
    (rarea cum9 cum10 months_from_birth, color("86 180 233*.7") fintensity(80)), ///
    xlabel(-18(3)18, labsize(small)) ///
    ylabel(0(20)100, angle(0) labsize(small)) ///
    xtitle("Months from Birth", size(medium)) ///
    ytitle("Percentage of Tweets (%)", size(medium)) ///
    xline(0, lcolor(red) lpattern(dash) lwidth(medium) lstyle(foreground)) ///
    title("Topic Composition of Tweets Around Birth Event", size(medium)) ///
    subtitle("Stacked area chart showing % of tweets by topic", size(small)) ///
    note("Red line indicates month of birth (month 0). 'Other' includes: Youth/Student, Travel, Relationships," ///
         "Arts/Culture, Fitness, Gaming, Education, Other Hobbies, Science/Tech", size(vsmall)) ///
    legend(order(1 "Business" 2 "Celebrity" 3 "Family" 4 "Fashion" ///
        5 "Film/TV" 6 "Food" 7 "Music" 8 "News" 9 "Other" 10 "Sports") ///
        cols(2) size(small) position(3) ring(1)) ///
    graphregion(color(white)) plotregion(color(white))

graph export "$tweetNLP_figs/topic_class/stacked_area.jpg", replace width(2400)

restore




















use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear

********************************************************************************
* SLOPE CHARTS
********************************************************************************

* Prepare data for slope charts
preserve

* Count tweets by month and topic
gen n_tweets = 1
collapse (sum) n_tweets, by(months_from_birth topic)

* Exclude diaries & daily life
drop if topic == "diaries_&_daily_life"

* Get total tweets per month
bysort months_from_birth: egen total_tweets_month = total(n_tweets)

* Calculate proportion
gen proportion = (n_tweets / total_tweets_month) * 100

* Create period indicators for -18 to +18 comparison
gen period_full = 1 if months_from_birth < 0 & months_from_birth != 0
replace period_full = 2 if months_from_birth > 0

* Create period indicators for -9 to +9 comparison
gen period_narrow = 1 if months_from_birth >= -9 & months_from_birth < 0
replace period_narrow = 2 if months_from_birth > 0 & months_from_birth <= 9

********************************************************************************
* SLOPE CHART 1: -18 to +18 (excluding month 0)
********************************************************************************

// preserve
drop if period_full == .
collapse (mean) avg_proportion=proportion, by(topic period_full)

* Reshape to wide
reshape wide avg_proportion, i(topic) j(period_full)

* Calculate change
gen change = avg_proportion2 - avg_proportion1
gen abs_change = abs(change)

* Sort by absolute change to show biggest movers
gsort -abs_change

* Create a rank variable for positioning
gen rank = _n

* Reshape back to long for plotting
gen topic_label = topic
reshape long avg_proportion, i(topic) j(period)

* Create labels for the periods
gen period_label = "Pre-Birth" if period == 1
replace period_label = "Post-Birth" if period == 2

* Sort for proper line drawing
sort topic period

* Create the slope chart
twoway ///
    (line avg_proportion period if topic == topic[1], lcolor("0 114 178") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[3], lcolor("230 159 0") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[5], lcolor("86 180 233") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[7], lcolor("0 158 115") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[9], lcolor("240 228 66") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[11], lcolor("204 121 167") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[13], lcolor("213 94 0") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[15], lcolor("102 194 165") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[17], lcolor("252 141 98") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[19], lcolor("141 160 203") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[21], lcolor("231 138 195") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[23], lcolor("166 216 84") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[25], lcolor("255 217 47") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[27], lcolor("229 196 148") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[29], lcolor("179 179 179") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[31], lcolor("128 128 128") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[33], lcolor("77 77 77") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[35], lcolor("200 100 150") lwidth(medium)) ///
    (scatter avg_proportion period, mcolor(black) msize(small)), ///
    xlabel(1 "Pre-Birth" 2 "Post-Birth", noticks) ///
    ylabel(0(2)20, angle(0) labsize(small)) ///
    ytitle("Average % of Tweets", size(medium)) ///
    xtitle("") ///
    title("Change in Topic Composition: Pre vs Post Birth", size(medium)) ///
    subtitle("Comparing 18 months before birth (months -18 to -1) vs 18 months after (months 1-18)", size(small)) ///
    legend(order(1 "arts_&_culture" 2 "business_&_entrepreneurs" 3 "celebrity_&_pop_culture" ///
        4 "family" 5 "fashion_&_style" 6 "film_tv_&_video" 7 "fitness_&_health" ///
        8 "food_&_dining" 9 "gaming" 10 "learning_&_educational" 11 "music" ///
        12 "news_&_social_concern" 13 "other_hobbies" 14 "relationships" ///
        15 "science_&_technology" 16 "sports" 17 "travel_&_adventure" ///
        18 "youth_&_student_life") cols(3) size(vsmall) position(6)) ///
    graphregion(color(white)) plotregion(color(white))

// graph export "slope_chart_full.png", replace width(2400)

restore

********************************************************************************
* SLOPE CHART 2: -9 to +9 (excluding month 0)
********************************************************************************

preserve
drop if period_narrow == .
collapse (mean) avg_proportion=proportion, by(topic period_narrow)

* Reshape to wide
reshape wide avg_proportion, i(topic) j(period_narrow)

* Calculate change
gen change = avg_proportion2 - avg_proportion1
gen abs_change = abs(change)

* Sort by absolute change to show biggest movers
gsort -abs_change

* Create a rank variable for positioning
gen rank = _n

* Reshape back to long for plotting
gen topic_label = topic
reshape long avg_proportion, i(topic) j(period)

* Create labels for the periods
gen period_label = "Pre-Birth" if period == 1
replace period_label = "Post-Birth" if period == 2

* Sort for proper line drawing
sort topic period

* Create the slope chart
twoway ///
    (line avg_proportion period if topic == topic[1], lcolor("0 114 178") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[3], lcolor("230 159 0") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[5], lcolor("86 180 233") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[7], lcolor("0 158 115") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[9], lcolor("240 228 66") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[11], lcolor("204 121 167") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[13], lcolor("213 94 0") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[15], lcolor("102 194 165") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[17], lcolor("252 141 98") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[19], lcolor("141 160 203") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[21], lcolor("231 138 195") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[23], lcolor("166 216 84") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[25], lcolor("255 217 47") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[27], lcolor("229 196 148") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[29], lcolor("179 179 179") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[31], lcolor("128 128 128") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[33], lcolor("77 77 77") lwidth(medium)) ///
    (line avg_proportion period if topic == topic[35], lcolor("200 100 150") lwidth(medium)) ///
    (scatter avg_proportion period, mcolor(black) msize(small)), ///
    xlabel(1 "Pre-Birth" 2 "Post-Birth", noticks) ///
    ylabel(0(2)20, angle(0) labsize(small)) ///
    ytitle("Average % of Tweets", size(medium)) ///
    xtitle("") ///
    title("Change in Topic Composition: Pre vs Post Birth (9-Month Window)", size(medium)) ///
    subtitle("Comparing 9 months before birth (months -9 to -1) vs 9 months after (months 1-9)", size(small)) ///
    legend(order(1 "arts_&_culture" 2 "business_&_entrepreneurs" 3 "celebrity_&_pop_culture" ///
        4 "family" 5 "fashion_&_style" 6 "film_tv_&_video" 7 "fitness_&_health" ///
        8 "food_&_dining" 9 "gaming" 10 "learning_&_educational" 11 "music" ///
        12 "news_&_social_concern" 13 "other_hobbies" 14 "relationships" ///
        15 "science_&_technology" 16 "sports" 17 "travel_&_adventure" ///
        18 "youth_&_student_life") cols(3) size(vsmall) position(6)) ///
    graphregion(color(white)) plotregion(color(white))

graph export "slope_chart_narrow.png", replace width(2400)

restore



* ------------- OLD CODE (first try) --------------------------- *
// * First, collapse to get counts by month and topic
// preserve
//
// * Count tweets by month and topic
// gen n_tweets = 1
// collapse (sum) n_tweets, by(months_from_birth topic)
//
// * Get total tweets per month
// bysort months_from_birth: egen total_tweets_month = total(n_tweets)
//
// * Calculate proportion
// gen proportion = (n_tweets / total_tweets_month) * 100
//
// * Create a numeric topic variable for graphing (if not already numeric)
// * Encode topic if it's a string
// capture confirm string variable topic
// if !_rc {
//     encode topic, gen(topic_num)
// } 
// else {
//     gen topic_num = topic
// }
//
// * Label the numeric topic variable
// label define topic_labels ///
//     1 "Arts & Culture" ///
//     2 "Business & Entrepreneurs" ///
//     3 "Celebrity & Pop Culture" ///
//     4 "Diaries & Daily Life" ///
//     5 "Family" ///
//     6 "Fashion & Style" ///
//     7 "Film, TV & Video" ///
//     8 "Fitness & Health" ///
//     9 "Food & Dining" ///
//     10 "Gaming" ///
//     11 "Learning & Educational" ///
//     12 "Music" ///
//     13 "News & Social Concern" ///
//     14 "Other Hobbies" ///
//     15 "Relationships" ///
//     16 "Science & Technology" ///
//     17 "Sports" ///
//     18 "Travel & Adventure" ///
//     19 "Youth & Student Life"
// label values topic_num topic_labels
//
// ********************************************************************************
// * STACKED AREA CHART
// ********************************************************************************
// * Drop the string topic variable since we now have topic_num
// drop topic
//
// * Reshape to wide format for stacked area chart
// reshape wide n_tweets proportion, i(months_from_birth) j(topic_num)
//
// * Generate cumulative proportions for stacking
// gen cum1 = proportion1
// forvalues i = 2/19 {
//     local j = `i' - 1
//     gen cum`i' = cum`j' + proportion`i'
// }
//
// * Create the stacked area chart
// twoway ///
//     (area cum1 months_from_birth, color("0 114 178") fintensity(80)) ///
//     (rarea cum1 cum2 months_from_birth, color("230 159 0") fintensity(80)) ///
//     (rarea cum2 cum3 months_from_birth, color("86 180 233") fintensity(80)) ///
//     (rarea cum3 cum4 months_from_birth, color("0 158 115") fintensity(80)) ///
//     (rarea cum4 cum5 months_from_birth, color("240 228 66") fintensity(80)) ///
//     (rarea cum5 cum6 months_from_birth, color("204 121 167") fintensity(80)) ///
//     (rarea cum6 cum7 months_from_birth, color("213 94 0") fintensity(80)) ///
//     (rarea cum7 cum8 months_from_birth, color("0 114 178*.7") fintensity(80)) ///
//     (rarea cum8 cum9 months_from_birth, color("230 159 0*.7") fintensity(80)) ///
//     (rarea cum9 cum10 months_from_birth, color("86 180 233*.7") fintensity(80)) ///
//     (rarea cum10 cum11 months_from_birth, color("0 158 115*.7") fintensity(80)) ///
//     (rarea cum11 cum12 months_from_birth, color("240 228 66*.7") fintensity(80)) ///
//     (rarea cum12 cum13 months_from_birth, color("204 121 167*.7") fintensity(80)) ///
//     (rarea cum13 cum14 months_from_birth, color("213 94 0*.7") fintensity(80)) ///
//     (rarea cum14 cum15 months_from_birth, color("0 114 178*.5") fintensity(80)) ///
//     (rarea cum15 cum16 months_from_birth, color("230 159 0*.5") fintensity(80)) ///
//     (rarea cum16 cum17 months_from_birth, color("86 180 233*.5") fintensity(80)) ///
//     (rarea cum17 cum18 months_from_birth, color("0 158 115*.5") fintensity(80)) ///
//     (rarea cum18 cum19 months_from_birth, color("240 228 66*.5") fintensity(80)), ///
//     xlabel(-18(3)18, labsize(small)) ///
//     ylabel(0(20)100, angle(0) labsize(small)) ///
//     xtitle("Months from Birth", size(medium)) ///
//     ytitle("Percentage of Tweets (%)", size(medium)) ///
//     xline(0, lcolor(red) lpattern(dash) lwidth(medium) lstyle(foreground)) ///
//     title("Topic Composition of Tweets Around Birth Event", size(medium)) ///
//     subtitle("Stacked area chart showing % of tweets by topic", size(small)) ///
//     note("Red line indicates month of birth (month 0)", size(vsmall)) ///
//     legend(order(1 "Arts & Culture" 2 "Business" 3 "Celebrity" 4 "Daily Life" ///
//         5 "Family" 6 "Fashion" 7 "Film/TV" 8 "Fitness" 9 "Food" 10 "Gaming" ///
//         11 "Education" 12 "Music" 13 "News" 14 "Hobbies" 15 "Relationships" ///
//         16 "Science/Tech" 17 "Sports" 18 "Travel" 19 "Youth/Student") ///
//         cols(3) size(vsmall) position(3) ring(1)) ///
//     graphregion(color(white)) plotregion(color(white))
//
// // graph export "stacked_area_topics.png", replace width(2400)
//
// restore