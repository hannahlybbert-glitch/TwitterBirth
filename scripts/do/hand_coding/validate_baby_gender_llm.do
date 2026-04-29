* Author: Hannah Lybbert
* Created: 02/18/2026
* Purpose: Validate LLM child gender predictions against hand-coded sample of 200
*          Compares child_gender_prediction.dta (LLM output) vs baby_gender_sample200.dta (hand-coded)

log using "$testing/llm_gender_validation_results.log", replace text

********************************************************************************
* Step 1: Get unique_id linkage for the 200-sample
*         (baby_gender_sample200.dta only has tweet_id, not unique_id)
********************************************************************************

use "$cleaned/user_info_full_sample.dta", clear

* Keep only what we need to bridge tweet_id -> unique_id
keep tweet_id unique_id

tempfile id_bridge
save `id_bridge'


********************************************************************************
* Step 2: Load hand-coded sample and add unique_id
********************************************************************************

use "$testing/baby_gender_sample200.dta", clear

* Rename hand-coded variable before merging in LLM predictions
rename baby_girl baby_girl_hand
label var baby_girl_hand "Hand-coded: baby gender (0=boy, 1=girl, -99=unknown)"

merge 1:1 tweet_id using `id_bridge', keep(master match) nogen

count if missing(unique_id)
if r(N) > 0 {
	di as error "WARNING: `r(N)' observations could not be linked to unique_id — check merge"
}

tempfile hand_coded
save `hand_coded'


********************************************************************************
* Step 3: Merge in LLM predictions
********************************************************************************

use "$raw/child_gender_prediction.dta", clear

rename baby_girl baby_girl_llm
label var baby_girl_llm "LLM prediction: baby gender (0=boy, 1=girl, -99=unknown)"

rename gender_confidence llm_confidence
label var llm_confidence "LLM confidence score (0-100)"

merge 1:1 unique_id using `hand_coded', keep(match) nogen


********************************************************************************
* Step 4: Basic distributions — confirm marginals match your earlier tab
********************************************************************************

di ""
di "===== HAND-CODED DISTRIBUTION ====="
tab baby_girl_hand

di ""
di "===== LLM PREDICTION DISTRIBUTION (validation sample only) ====="
tab baby_girl_llm

di ""
di "===== LLM CONFIDENCE DISTRIBUTION ====="
tab llm_confidence


********************************************************************************
* Step 5: Full confusion matrix (all 3 classes: boy=0, girl=1, unknown=-99)
********************************************************************************

di ""
di "===== CONFUSION MATRIX (rows=hand-coded, cols=LLM) ====="
tab baby_girl_hand baby_girl_llm, row col


********************************************************************************
* Step 6: Overall accuracy and Cohen's Kappa (3-class)
*         kap computes kappa for categorical agreement
********************************************************************************

di ""
di "===== COHEN'S KAPPA (3-class: boy/girl/unknown) ====="
* Note: kap expects (rater1, rater2) — here hand=gold standard, llm=model
kap baby_girl_hand baby_girl_llm

* Raw agreement rate
gen agree = (baby_girl_hand == baby_girl_llm)
sum agree
di "Overall raw agreement: " r(mean)*100 "% (" r(N) " obs)"
drop agree


********************************************************************************
* Step 7: Restricted accuracy — exclude cases where either rater said "unknown"
*         This is the more meaningful accuracy for definitive predictions
********************************************************************************

di ""
di "===== RESTRICTED ANALYSIS: Both gave definitive answer (not -99) ====="

gen definitive = (baby_girl_hand != -99 & baby_girl_llm != -99)
tab definitive

preserve
	keep if definitive == 1
	di "Confusion matrix — definitive predictions only:"
	tab baby_girl_hand baby_girl_llm, row col

	di "Cohen's Kappa — definitive predictions only:"
	kap baby_girl_hand baby_girl_llm

	gen agree = (baby_girl_hand == baby_girl_llm)
	sum agree
	di "Accuracy (definitive only): " r(mean)*100 "% (" r(N) " obs)"
restore

drop definitive


********************************************************************************
* Step 8: Where does the model disagree with "unknown"?
*         How often does LLM say definitive when you said unknown (and vice versa)?
********************************************************************************

di ""
di "===== UNKNOWN DISAGREEMENT ANALYSIS ====="

* LLM called it definitive, hand said unknown
count if baby_girl_hand == -99 & baby_girl_llm != -99
di "LLM gave definitive answer when hand-coder said unknown: " r(N)

* Hand coder was definitive, LLM said unknown
count if baby_girl_hand != -99 & baby_girl_llm == -99
di "Hand-coder definitive but LLM said unknown: " r(N)

* Both said unknown
count if baby_girl_hand == -99 & baby_girl_llm == -99
di "Both said unknown: " r(N)


********************************************************************************
* Step 9: Asymmetric error analysis — among definitive cases, is misclassification
*         symmetric (boy→girl as often as girl→boy)?
********************************************************************************

di ""
di "===== DIRECTIONAL ERRORS (among cases where both gave definitive answer) ====="

* False negatives: hand says girl (1), LLM says boy (0)
count if baby_girl_hand == 1 & baby_girl_llm == 0
di "Hand=girl, LLM=boy (false negative for girl): " r(N)

* False positives: hand says boy (0), LLM says girl (1)
count if baby_girl_hand == 0 & baby_girl_llm == 1
di "Hand=boy, LLM=girl (false positive for girl): " r(N)

* Model said unknown when hand said girl
count if baby_girl_hand == 1 & baby_girl_llm == -99
di "Hand=girl, LLM=unknown: " r(N)

* Model said unknown when hand said boy
count if baby_girl_hand == 0 & baby_girl_llm == -99
di "Hand=boy, LLM=unknown: " r(N)


********************************************************************************
* Step 10: Confidence-stratified accuracy
*          Does higher confidence predict better accuracy?
*          This helps you decide if you should apply a confidence threshold
********************************************************************************

di ""
di "===== ACCURACY BY CONFIDENCE LEVEL ====="

gen agree = (baby_girl_hand == baby_girl_llm)

* Define confidence bins
gen conf_bin = .
replace conf_bin = 1 if llm_confidence >= 0  & llm_confidence <= 39
replace conf_bin = 2 if llm_confidence >= 40 & llm_confidence <= 59
replace conf_bin = 3 if llm_confidence >= 60 & llm_confidence <= 89
replace conf_bin = 4 if llm_confidence >= 90 & llm_confidence <= 100
label define conf_lbl 1 "Very low (0-39)" 2 "Low (40-59)" 3 "Medium (60-89)" 4 "High (90-100)"
label values conf_bin conf_lbl

table conf_bin, statistic(mean agree) statistic(count agree) nformat(%5.3f)

* Also look at the distribution of confidence scores for correct vs wrong predictions
di ""
di "Mean confidence when CORRECT:"
sum llm_confidence if agree == 1

di "Mean confidence when WRONG:"
sum llm_confidence if agree == 0

drop agree conf_bin


********************************************************************************
* Step 11: Browse misclassified cases for qualitative review
*          (uncomment when running interactively)
********************************************************************************

di ""
di "===== MISCLASSIFIED CASES ====="

gen misclassified = (baby_girl_hand != baby_girl_llm)
count if misclassified == 1
di "Total misclassified: " r(N)

* Uncomment to inspect errors interactively:
* browse username description text baby_girl_hand baby_girl_llm llm_confidence if misclassified == 1
* browse username description text baby_girl_hand baby_girl_llm llm_confidence if baby_girl_hand == 1 & baby_girl_llm == 0
* browse username description text baby_girl_hand baby_girl_llm llm_confidence if baby_girl_hand == 0 & baby_girl_llm == 1

drop misclassified


di ""
di "===== VALIDATION COMPLETE ====="

log close
