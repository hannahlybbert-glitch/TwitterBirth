*** MERGE classified and sentiment analysis into one

import delimited using "$sentiment/output/multi_dim_classified_FULL.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
save "$sentiment/output/multi_dim_classified_FULL.dta", replace

import delimited using "$sentiment/output/tweet_sentiment_FULL.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
save "$sentiment/output/tweet_sentiment_FULL.dta", replace
	
	drop if missing(author_id)

merge 1:1 tweet_id author_id using "$sentiment/output/multi_dim_classified_FULL.dta", keepusing(family_sim politics_sim religion_sim sports_sim fam_pol_score)
drop _merge

save "$sentiment/output/sentiment_MFT_FULL.dta", replace