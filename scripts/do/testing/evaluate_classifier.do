
local dates "2025_02_11-2025_02_18"

* load hand coded tweets
import delimited using "$testing/hand_coded_`dates'.csv", clear stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited)
* keep queries 1-8 (narrow queries)

destring query_id, replace
// keep if inrange(query_id, 1,8)

// egen ID = group(query_id tweet_id)
// sort query_id tweet_id

gen birth_announcement = loose

tempfile temp
sa `temp'

* Load in the chatgpt classified tweets
import delimited using "$testing/classified_tweets_`dates'.csv", clear stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) 

rename text processed_text

destring query_id, replace
// keep if inrange(query_id, 1,8)
// sort query_id tweet_id

// egen ID = group(query_id tweet_id)
merge 1:1 query_id tweet_id using `temp', nogen keep(match)

destring birth_announcement, replace


* TEMP CODE: OUTPUTTING FILE OF CLASSIFIED TWEETS
preserve
drop if classification == "0"
export delimited using "$testing/GPT_coded_births.csv", replace quote
restore

* for v1 - very simple prompt, zero-shot
// destring is_birth_announcement, replace 
// gen correct = cond(birth_announcement == is_birth_announcement,1,0)

* for v2 - used different prompt, with few shot examples, majority voting with n = 3 and validation step
// destring *classification, replace
// gen initialcorrect = cond(initial_classification == birth_announcement,1,0)
// gen finalcorrect = cond(final_classification == birth_announcement,1,0)
// gen is_birth_announcement = initial_classification

// * v3 - removed validation step and made to be zero shot again - majority voting with n = 5
// destring classification, replace
// gen correct = cond(classification == birth_announcement,1,0)
// gen is_birth_announcement = classification

// * COT improved prompt and implement chain of thought majority voting with n = 3
destring classification, replace
gen correct = cond(classification == birth_announcement,1,0)
gen is_birth_announcement = classification

* this is temporary, can always just get removed


* dummy for if chat gpt disagrees with my hand-coding
gen mismatch = 0
replace mismatch = 1 if birth_announcement != is_birth_announcement

* dummy for when chatgpt does not code as a birth announcement
gen negative = 0 
replace negative = 1 if is_birth_announcement == 0


* false positive rate
quietly su is_birth_announcement if birth_announcement == 0
di "False pos rate = " round(r(mean)*100,.01) "%"
quietly count if is_birth_announcement == 1 & birth_announcement == 0
di "Chatgpt labeled " r(N) " as birth announcements"
quietly count if birth_announcement == 1
di "When there should have been " r(N)


* false negative rate
quietly su negative if birth_announcement == 1
di "False neg rate = " round(r(mean)*100,.01) "%"
quietly count if is_birth_announcement == 1 & birth_announcement == 1
di "Chatgpt correctly labeled " r(N) " birth announcements"
quietly count if is_birth_announcement == 0 & birth_announcement == 1
di "But missed out on " r(N) " true positives"


order is_birth_announcement birth_announcement text processed_text, after(tweet_id)

tab is_birth_announcement
tab birth_announcement



* Determine the average number of tweets per user
* Then do it for those that were classified by chatgpt as birth announcements 

destring tweet_count, replace
gen date_account_created = date(substr(user_created_at,1,10),"YMD")
gen date_posted = date(substr(created_at,1,10), "YMD")
format date_account_created date_posted %td

gen days_account = date_posted - date_account_created

gen tweets_per_day = tweet_count / days_account

gen tweets_per_year = tweets_per_day * 365
gen tweets_per_period = tweets_per_year * 3


gen orig_per_pd = tweets_per_year * 0.16
gen orig_quo_per_pd = tweets_per_year * 0.25

// keep if classification == 1 & birth_announcement == 1

su orig_per_pd if classification == 1 & birth_announcement == 1, d
su orig_quo_per_pd if classification == 1 & birth_announcement == 1

su orig_per_pd
su orig_quo_per_pd



* 16% of tweets are original tweets
* 40% are replies, 35% are retweets, 9% are quote tweets
* So either 16% or 25% is what we will anchor on (source is Pew)

gen eligible = 0
replace eligible = 1 if days_account > 547 & is_birth_announcement == 1 &


cdfplot tweets_per_period if eligible == 1
