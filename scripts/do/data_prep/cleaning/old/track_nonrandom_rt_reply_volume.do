* this is just so that we can differentiate between randomly selected and non-randomly selected accounts. 250 accounts were selected non-randomly (they are older accounts)
import delimited using "$raw/retweet_reply_volume_by_user_2013_2017.csv", stringcols(_all) varnames(1) clear

gen random = 0

* save the data for the non-random ones. 
export delimited using "$raw/nonrandom_retweet_reply_volume_2013_2017.csv", replace quote

