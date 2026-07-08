* Author: Hannah Lybbert
* Created: 07/08/2026
* Purpose: Extract a sample of 404 authors from our user data (user_info_full_sample_CLEAN.dta) to compare their features against the test Control Group user info from the X API using anniversary posts instead of birth announcements)


use "$final/user_info_full_sample_CLEAN.dta", clear

set seed 12345
sample 138, count

* Remove embedded line breaks and tabs from description (the row-splitter)
replace description = subinstr(description, char(13), " ", .)
replace description = subinstr(description, char(10), " ", .)
replace description = subinstr(description, char(9), " ", .)

* Optional: collapse any resulting double spaces
replace description = stritrim(description)

order author_id date_birth_tweet username description user_created_at followers_count following_count lifetime_posts verified
keep author_id date_birth_tweet username description user_created_at followers_count following_count lifetime_posts verified

export delimited "$testing/sample_authors.csv", replace quote




* Only accounts with births March 2013
use "$final/user_info_full_sample_CLEAN.dta", clear

keep if date_birth_tweet <= 19450
set seed 12345
sample 138, count

* Remove embedded line breaks and tabs from description (the row-splitter)
replace description = subinstr(description, char(13), " ", .)
replace description = subinstr(description, char(10), " ", .)
replace description = subinstr(description, char(9), " ", .)

* Optional: collapse any resulting double spaces
replace description = stritrim(description)

orderauthor_id date_birth_tweet username description user_created_at followers_count following_count lifetime_posts verified
keep author_id date_birth_tweet username description user_created_at followers_count following_count lifetime_posts verified

export delimited "$testing/sample_authors_2013.csv", replace quote
