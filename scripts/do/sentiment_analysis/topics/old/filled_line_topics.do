* Author: Hannah Lybbert
* Created: 12/01/2025
* Purpose: Filled Line chart tweet topics


// use "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN_noBM.dta", clear
// use "$sentiment/output/tweetNLP/NLP_topics_Karthik_noBM.dta", clear
use "$sentiment/output/topic_sentiment_FULL_Karthik.dta", clear


* --------- FILLED LINE CHART ----------*
preserve
* First, generate a copy
gen topic_grp = topic

* Collapse small categories into "other"
replace topic_grp = "other" if inlist(topic, ///
    "arts_&_culture", ///
    "fitness_&_health", ///
    "gaming", ///
    "learning_&_educational", ///
    "other_hobbies", ///
    "relationships", ///
    "science_&_technology", ///
    "travel_&_adventure", ///
    "youth_&_student_life")

levelsof topic_grp, local(groups)

foreach g of local groups {
    // Replace any character that isn't a letter, number, or underscore
    local clean = ustrregexra("`g'", "[^A-Za-z0-9_]", "_")
    gen count_`clean' = (topic_grp == "`g'")
}

collapse (sum) count_*, by(months_from_birth)

* compute row total
egen total = rowtotal(count_*)
foreach g of local groups {
    local clean = ustrregexra("`g'", "[^A-Za-z0-9_]", "_")
    gen share_`clean' = count_`clean' / total
}

gen zero = 0

gen cum1  = share_diaries___daily_life
gen cum2  = cum1 + share_family
gen cum3  = cum2 + share_sports
gen cum4  = cum3 + share_news___social_concern
gen cum5  = cum4 + share_food___dining
gen cum6  = cum5 + share_film_tv___video
gen cum7  = cum6 + share_fashion___style
gen cum8  = cum7 + share_business___entrepreneurs
gen cum9  = cum8 + share_celebrity___pop_culture
gen cum10 = cum9 + share_music
gen cum11 = cum10 + share_other   // should = 1

twoway ///
    (rarea cum11 cum10 months_from_birth, color(navy%80)) ///
    (rarea cum10 cum9  months_from_birth, color(eltblue%80)) ///
    (rarea cum9  cum8  months_from_birth, color(teal%80)) ///
    (rarea cum8  cum7  months_from_birth, color(emidblue%80)) ///
    (rarea cum7  cum6  months_from_birth, color(eblue%80)) ///
    (rarea cum6  cum5  months_from_birth, color(dkorange%80)) ///
    (rarea cum5  cum4  months_from_birth, color(maroon%80)) ///
    (rarea cum4  cum3  months_from_birth, color(cranberry%80)) ///
    (rarea cum3  cum2  months_from_birth, color(dkgreen%80)) ///
    (rarea cum2  cum1  months_from_birth, color(emerald%80)) ///
    (rarea cum1  zero  months_from_birth, color(gs14)) ///
    , ///
      legend(off) ///
      xtitle("Months from Birth") ///
      ytitle("Share of Tweets") ///
      ylabel(0(0.2)1) ///
      xlabel(-18(2)18) ///
      title("Topic Composition of Tweets Around Birth") ///
      yscale(range(0 1))
graph export "$tweetNLP_figs/topic_class/topics_main.jpg", replace

twoway ///
    (scatteri 0 0, mcolor(navy*0.3)  msymbol(square)  ) ///
    (scatteri 0 0, mcolor(navy*0.5)  msymbol(square)  ) ///
    (scatteri 0 0, mcolor(navy*0.7)  msymbol(square)  ) ///
    (scatteri 0 0, mcolor(navy*0.9)  msymbol(square)  ) ///
    (scatteri 0 0, mcolor(maroon*0.3)  msymbol(square) ) ///
    (scatteri 0 0, mcolor(maroon*0.5)  msymbol(square) ) ///
    (scatteri 0 0, mcolor(maroon*0.7)  msymbol(square) ) ///
    (scatteri 0 0, mcolor(maroon*0.9)  msymbol(square) ) ///
    (scatteri 0 0, mcolor(olive*0.3)   msymbol(square) ) ///
    (scatteri 0 0, mcolor(olive*0.6)   msymbol(square) ) ///
    (scatteri 0 0, mcolor(olive*0.9)   msymbol(square) ) ///
    ,
      xscale(off) yscale(off) ///
      xlabel(, nogrid) ylabel(, nogrid) ///
      xtitle("") ytitle("") ///
      legend(order( ///
        11 "Diaries & Daily Life" ///
        10 "Family" ///
        9  "Sports" ///
        8  "News & Social Concern" ///
        7  "Food & Dining" ///
        6  "Film/TV/Video" ///
        5  "Fashion & Style" ///
        4  "Business & Entrepreneurs" ///
        3  "Celebrity & Pop Culture" ///
        2  "Music" ///
        1  "Other" ///
      ) col(1) pos(3) ring(0))

graph export "$tweetNLP_figs/topic_class/topics_legend.jpg", replace

restore



* --------- FILLED LINE CHART (no diaries & daily life) ----------*
preserve
* First, generate a copy
drop if topic == "diaries_&_daily_life"
gen topic_grp = topic
drop if topic == "diaries_&_daily_life"

* Collapse small categories into "other"
replace topic_grp = "other" if inlist(topic, ///
    "arts_&_culture", ///
    "fitness_&_health", ///
    "gaming", ///
    "learning_&_educational", ///
    "other_hobbies", ///
    "relationships", ///
    "science_&_technology", ///
    "travel_&_adventure", ///
    "youth_&_student_life")

levelsof topic_grp, local(groups)

foreach g of local groups {
    local clean = ustrregexra("`g'", "[^A-Za-z0-9_]", "_")
    gen count_`clean' = (topic_grp == "`g'")
}


collapse (sum) count_*, by(months_from_birth)

* compute row total
egen total = rowtotal(count_*)
foreach g of local groups {
    local clean = ustrregexra("`g'", "[^A-Za-z0-9_]", "_")
    gen share_`clean' = count_`clean' / total
}

gen cum1  = share_family
gen cum2  = cum1 + share_sports
gen cum3  = cum2 + share_news___social_concern
gen cum4  = cum3 + share_food___dining
gen cum5  = cum4 + share_film_tv___video
gen cum6  = cum5 + share_fashion___style
gen cum7  = cum6 + share_business___entrepreneurs
gen cum8  = cum7 + share_celebrity___pop_culture
gen cum9  = cum8 + share_music
gen cum10 = cum9 + share_other   // should = 1
gen zero = 0


twoway ///
    (rarea cum10 cum9 months_from_birth, color(navy%80)) ///
    (rarea cum9  cum8 months_from_birth, color(eltblue%80)) ///
    (rarea cum8  cum7 months_from_birth, color(teal%80)) ///
    (rarea cum7  cum6 months_from_birth, color(emidblue%80)) ///
    (rarea cum6  cum5 months_from_birth, color(eblue%80)) ///
    (rarea cum5  cum4 months_from_birth, color(dkorange%80)) ///
    (rarea cum4  cum3 months_from_birth, color(maroon%80)) ///
    (rarea cum3  cum2 months_from_birth, color(cranberry%80)) ///
    (rarea cum2  cum1 months_from_birth, color(dkgreen%80)) ///
    (rarea cum1  zero months_from_birth, color(emerald%80)) ///
    , ///
      legend(off) ///
      xtitle("Months from Birth") ///
      ytitle("Share of Tweets") ///
      ylabel(0(0.2)1) ///
      xlabel(-18(2)18) ///
      title("Topic Composition of Tweets Around Birth") ///
      yscale(range(0 1))
graph export "$tweetNLP_figs/topic_class/topics_main.jpg", replace

twoway ///
    (scatteri 0 0, mcolor(navy%80) msymbol(square)) ///
    (scatteri 0 0, mcolor(eltblue%80) msymbol(square)) ///
    (scatteri 0 0, mcolor(teal%80) msymbol(square)) ///
    (scatteri 0 0, mcolor(emidblue%80) msymbol(square)) ///
    (scatteri 0 0, mcolor(eblue%80) msymbol(square)) ///
    (scatteri 0 0, mcolor(dkorange%80) msymbol(square)) ///
    (scatteri 0 0, mcolor(maroon%80) msymbol(square)) ///
    (scatteri 0 0, mcolor(cranberry%80) msymbol(square)) ///
    (scatteri 0 0, mcolor(dkgreen%80) msymbol(square)) ///
    (scatteri 0 0, mcolor(emerald%80) msymbol(square)) ///
    ,
      xscale(off) yscale(off) ///
      xlabel(, nogrid) ylabel(, nogrid) ///
      xtitle("") ytitle("") ///
      legend(order( ///
        1  "Other" ///
        2  "Music" ///
        3  "Celebrity & Pop Culture" ///
        4  "Business & Entrepreneurs" ///
        5  "Fashion & Style" ///
        6  "Film/TV/Video" ///
        7  "Food & Dining" ///
        8  "News & Social Concern" ///
        9  "Sports" ///
        10 "Family" ///
      ) col(1) pos(3) ring(0) symxsize(*1.3) size(small))

graph export "$tweetNLP_figs/topic_class/topics_legend.jpg", replace

restore