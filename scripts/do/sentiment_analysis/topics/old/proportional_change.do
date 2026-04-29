** Proportional Change Chart **

use "$sentiment/output/tweetNLP/NLP_topic_classifier_CLEAN_noBM.dta", clear

* Calculate proportions of each topic within each period
preserve

* Count tweets by period and topic
collapse (count) n=topic, by(post_birth topic)

* Get total tweets per period
bysort post_birth: egen total = sum(n)

* Calculate proportion
gen proportion = n / total * 100

* Reshape to wide format
keep post_birth topic proportion
reshape wide proportion, i(topic) j(post_birth)

* Calculate percentage point change
gen change = proportion1 - proportion0

* Label for clarity
label variable change "Percentage point change (Post - Pre)"
label variable proportion0 "Pre-period %"
label variable proportion1 "Post-period %"

* Sort by change magnitude
gsort -change

* Create dot plot
graph dot change, over(topic, sort(change) label(labsize(small))) ///
    marker(1, msize(medium)) ///
    yline(0, lcolor(black) lwidth(thin)) ///
    ytitle("Change in proportion (percentage points)") ///
    title("Change in Tweet Topics: Post vs Pre Period") ///
    note("Positive values indicate topic increased in post period")

restore