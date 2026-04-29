// * 2018 hand-coded file
import delimited using "$archive/hand_coded_2018.csv",  stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
// * 1,774 rows have already been hand-coded
//
// * code as not a birth if there is "god son" "god daughter" "god mother" "god father" "cousin" "nephew" "niece" "aunt" "uncle" "my sister" "my brother"
// replace birth_announcement = "0" if regexm(text, "( tia |god daughter|god son|nephew|cousin|niece|god father|god mother|aunt|uncle|granddad|grandma|grandfather|grandmother|my sister|my brother)") & missing(birth_announcement)
//
// * split into three files and then have a master file
// sort birth_announcement author_id created_at
//
// * split them into three files
// * min file
// * bolun file
// * master file (mine)
// * min and bolun get the top 6,000 split between the two of them
// * I code following the last one that they have and ignore the rest
//
// gen assigned_to = ""
// order assigned_to, before(birth_announcement)
//
// replace assigned_to = "Bolun" if _n <= 3000 & missing(birth_announcement)
// replace assigned_to = "Min" if _n > 3000 & _n <= 6000 & missing(birth_announcement)
// replace assigned_to = "Rory" if _n > 6000 & missing(birth_announcement)
//
//
// foreach name in Rory Bolun Min {
// 	preserve
// 	keep if assigned_to == "`name'"
// 	* individual files
// 	export delimited using "$raw/hand_coding/to_hand_code_`name'.csv", replace quote
// 	restore
// }
// 	* master file
// 	export delimited using "$raw/hand_coding/to_hand_code_master_2018.csv", replace quote




* Create hand_coding file for 2013-2017

import delimited using "$raw/hand_coding/to_hand_code_2013_01_01-2017_12_31.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear 


gen birth_announcement = ""

* Automatic hand-coding 

* code as not a birth if there is "god son" "god daughter" "god mother" "god father" "cousin" "nephew" "niece" "aunt" "uncle" "my sister" "my brother"
replace birth_announcement = "0" if regexm(lower(text), "( tia |god daughter|god son|nephew|cousin|niece|god father|god mother| aunt| aunty| auntie|uncle|granddad|grandma|grandfather|grandmother|my sister|my brother| tio | tita| tito)") & missing(birth_announcement)

* if we see the same exact tweet 10 or more times, just drop it
bysort text: gen n_identical = _N
replace birth_announcement = "0" if n_identical >= 10

* new announcements that some celebrity gave birth - need to do this because there are a bunch of repeat tweets with links in them (so they aren't exactly the same tweet - alternatively could just remove the link from the tweet - but i think this would be kind of annoying)
replace birth_announcement = "0" if regexm(lower(text), "(kenneth okonkwo|j.r. smith|paul okoye|shawn carter|sean carter|braxtonbowens |#porn| adam levine| andy murray|backstreet boy|benedict cumberbatch|ada james akins|odunlade adekola|allison holker|alma pelletero| t.i. and wife|arsenal fan tricks|chrissy teigen|ice-t|mark zuckerburg|josh duhamel|james corden|jason aldean|jill duggar|#justinbeiber|k-solo|kevin hart|kevin jonas|kim kardashian|jimmy fallon|christina aguilera)")

* weird form of quote tweeting or retweeting from earlier days of twitter it seems
replace birth_announcement = "0" if regexm(lower(text),`"(^"@)"')

* do months ago today, years ago today, weeks ago today myself (maybe) - people will still need to verify it is a birth announcement though
gen different_day = 1 if regexm(lower(text), "(months ago today|year ago today|weeks ago today|week ago today|days ago|exactly one year|exactly a year|exactly a week|exactly one)")

replace birth_announcement = "2" if regexm(lower(text), "(months ago today|year ago today|weeks ago today|week ago today|days ago|exactly one year|exactly a year|exactly a week|exactly one)")

* automatically added to youtube playlist and facebook album
replace birth_announcement = "0" if regexm(lower(text), ("@youtube playlist|photos on facebook in the album"))

* think about how to deal with ("photos on facebook in the album") tweets
replace birth_announcement = "0" if regexm(text, "( RT|^RT )")

drop text_classification pic_classification n_identical

* organize master file so that the ones I will do myself are at the bottom
* sort by user, then account

sort birth_announcement author_id tweet_id

export delimited using "$raw/hand_coding/to_hand_code_master_2013_2017.csv", replace quote
