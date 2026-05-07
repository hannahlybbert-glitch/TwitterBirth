******************* Variable Labeling ********************

** #1 - User info (full sample)
use "$cleaned/user_info_full_sample.dta", clear

label variable unique_id "Unique identifier for each author and birth"
label variable author_id "unique identifer for each Twitter user"
label variable username "Twitter username"
label variable name "Name attached to Twitter account"
label variable description "Twitter account bio"
label variable profile_image_url "url to account profile picture"
label variable user_created_at "Date of account creation"
label variable female "1- female, 0- male"
label variable race "1- black, 2- white, 3- asian, 4- hispanic, 5- other, -99- null"
label variable occupation "ChatGPT classified occupation"
label variable child_number "Child number _ being born"
label variable date_birth_tweet "Day of the tweet announcing the birth"
label variable days_from "Days separating birth tweet and actual birth of child"
label variable date_birth "Child birth date"
label variable following_count "How many accounts does this person follow?"
label variable followers_count "How many accounts are following this person?"
label variable lifetime_posts "Total number of tweets from this account since the user was created" 
label variable verified "Is this Twitter account verified?"
label variable verified_type "Type of Twitter verification"
label variable tweet_id "Unique identifer for each tweet"
label variable text "Content of the tweet"
label variable tweet_url "Twitter URL of tweet"
label variable has_picture "1- Tweet contains a picture, 0- no picture"
label variable media_url "Link to picture on tweet"
label variable like_count "# of likes on tweet"
label variable retweet_count "# of retweets on tweet"
label variable reply_count "# of replies on tweet"
label variable begin_date "First day of data scraped from this account"
label variable end_date "Last day of data scraped from this account"
label variable orig_qt_count "Total original + quote tweets (18mo pre/post birth)"
label variable rt_reply_count "Total retweet + replies (18mo pre/post birth)"

save "$cleaned/user_info_full_sample.dta", replace


** #1A - User info (first birth only)
use "$cleaned/user_info_first_child_NOTfull.dta", clear

label variable unique_id "Unique identifier for each author and their first birth"
label variable author_id "unique identifer for each Twitter user"
label variable username "Twitter username"
label variable name "Name attached to Twitter account"
label variable description "Twitter account bio"
label variable profile_image_url "url to account profile picture"
label variable user_created_at "Date of account creation"
label variable female "1- female, 0- male"
label variable race "1- black, 2- white, 3- asian, 4- hispanic, 5- other, -99- null"
label variable occupation "ChatGPT classified occupation"
label variable child_number "child number _ being born"
label variable date_birth_tweet "Day of the tweet announcing the birth"
label variable days_from "Days separating birth tweet and actual birth of child"
label variable date_birth "Child birth date"
label variable following_count "How many accounts does this person follow?"
label variable followers_count "How many accounts are following this person?"
label variable lifetime_posts "Total number of tweets from this account since the user was created" 
label variable verified "Is this Twitter account verified?"
label variable verified_type "Type of Twitter verification"
label variable tweet_id "Unique identifer for each tweet"
label variable text "Content of the tweet"
label variable tweet_url "Twitter URL of tweet"
label variable has_picture "1- Tweet contains a picture, 0- no picture"
label variable media_url "link to picture on tweet"
label variable like_count "# of likes on tweet"
label variable retweet_count "# of retweets on tweet"
label variable reply_count "# of replies on tweet"
label variable begin_date "First day of data scraped from this account"
label variable end_date "Last day of data scraped from this account"
label variable orig_qt_count "Total original + quote tweets (18mo pre/post birth)"
label variable rt_reply_count "Total retweet + replies (18mo pre/post birth)"

save "$cleaned/user_info_first_child_NOTfull.dta", replace


** #2 Tweet Volume 
use "$cleaned/tweet_volume_by_user_full_sample.dta", clear

label variable unique_id "Unique identifier for each author and birth"
label variable author_id "Unique identifer for each Twitter user"
label variable date "Running date variable, 18 months pre-birth until 18-months post-birth"
label variable orig_qt_count "# of original or quote tweets by the user that day"
label variable rt_reply_count "# of retweets or replies by the user that day"
label variable user_created_at "Date of account creation"
label variable date_birth "Child birth date"
label variable begin_date "Date 18 months pre-birth"
label variable end_date "Date 18 months post-birth"

save "$cleaned/tweet_volume_by_user_full_sample.dta", replace


** #3 Tweet Text
use "$cleaned/tweets_by_user_full_sample.dta", clear

label variable unique_id "Unique identifier for each Twitter user and their first birth"
label variable author_id "unique identifer for each Twitter user"
label variable tweet_id "Unique identifer for each tweet"
label variable created_at "Date of tweet post"
label variable text "Text of the tweet"
label variable like_count "# of likes on tweet"
label variable retweet_count "# of retweets on tweet"
label variable reply_count "# of replies on tweet"
label variable quote_count "# of quote tweets on tweet"
label variable tweet_url "Twitter URL of tweet"
label variable media_url "Link to picture on tweet (if applicable)"
label variable tweet_type "Type of tweet (original vs quote)"
label variable embedded_urls "Link to URL within the tweet (if applicable)"

save "$cleaned/tweets_by_user_full_sample.dta", replace

