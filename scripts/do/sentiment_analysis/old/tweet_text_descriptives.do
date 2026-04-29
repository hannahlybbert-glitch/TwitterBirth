
** Text cleaning descriptives **
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
	gen rand = runiform()
	sort rand
	keep in 1/10000
	drop rand

export delimited using "$sentiment/tweets_by_user_original_10k.csv", replace quote delimiter(",") nolabel


import delimited using "$sentiment/tweets_with_lang10k.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
	* 13.73% non english and missing lang (link included, m1)
	* 9.4% non english (link included, m1)
	* 17.2% non english and missing (link included, m2)
	* 16.9% non english (link include, m2)
	
	
	* Drop link
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
		gen text_nolink = ustrregexra(text, "https?://[^ ]+", "")
		drop if missing(text_nolink)
		drop text
		rename text_nolink text
	gen rand = runiform()
	sort rand
	keep in 1/10000
	drop rand
export delimited using "$sentiment/tweets_by_user_original_10k_nolink.csv", replace quote delimiter(",") nolabel

import delimited using "$sentiment/tweets_with_lang10k_nolink.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
	* 11.78% non english and missing (no link, m1)
	* 10.32% non english (no link, m1)
	* 9.07% non english and missing (no link, m2)
	* 7.43% non english (no link, m2)
	

	* Non english --> 9.4%
	import delimited using "$sentiment/tweets_with_lang10k.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

	
	
* ------------------------------------------------------------- *
	
use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
	* link included --> 1,048,678 tweets have links (~59%)
	preserve
	gen has_word = ustrregexm(text, "https?://[^ ]+")
	tab has_word
	drop has_word

	* link only tweets --> 53,309 just link tweets (~3%)
	gen text_nolink = ustrregexra(text, "https?://[^ ]+", "")
	count if missing(text_nolink)
	restore

	* hashtags --> 456,150 with hashtags (~25%)
	preserve
		gen has_hashtag = ustrregexm(text_nohash, "#")
		tab has_hashtag
		gen text_nohash = ustrregexra(text, "#", "")
		count if missing(text_nohash)
		
	restore
	
	* @ --> 319,613 with tags (~18%)
	preserve
		gen has_tag = ustrregexm(text, "@")
		tab has_tag
		gen text_notag = ustrregexra(text, "@", "")
		count if missing(text_notag)
	restore
	


	
	
	
	
** Take out link, hashtag, and taging

use "$cleaned/tweets_by_user_full_sample_CLEAN.dta", clear
	* No link
		gen text_nolink = ustrregexra(text, "https?://[^ ]+", "")
		drop if missing(text_nolink)
		drop text
		rename text_nolink text
	* No #
		gen text_nohash = ustrregexra(text, "#[^ ]+", "")
		drop if missing(text_nohash)
		drop text
		rename text_nohash text
	* No @
		gen text_notag = ustrregexra(text, "@[^ ]+", "")
		drop if missing(text_notag)
		drop text
		rename text_notag text
	gen rand = runiform()
	sort rand
	keep in 1/10000
	drop rand
export delimited using "$sentiment/tweets_by_user_original_10k_nocloud.csv", replace quote delimiter(",") nolabel

import delimited using "$sentiment/tweets_with_lang10k_nocloud.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear

	gen rand = runiform()
	sort rand
	keep in 1/200

