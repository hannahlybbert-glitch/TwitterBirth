* classification_analysis

import delimited using "$sentiment/output/text_onedoc.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
	* 

// import delimited using "$sentiment/output/text_onedoc_sample.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

import delimited using "C:\Users\hlybbert\Downloads\tweetnlp_topics.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

	* 1785508
	duplicates tag author_id post_birth, gen(tag_pair)
	bysort author_id: egen uniq_posts = total(n_unique_post)
	* which gives me 1,779,535 tweets from 4,152 authors
	


use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
	keep if full_3years == 1 & acct_tweeted_postBA == 1
	
bysort author_id: egen has_pre = max(tweet_postBA == 0)

count if has_pre == 0



gen has2019 = strpos(text, "2019") > 0
tab has2019
