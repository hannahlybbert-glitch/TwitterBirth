// import delimited using "$raw/tweets_by_user_2018.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
//
// tempfile tweets
// sa `tweets', replace
//
// import delimited using "$raw/birth_tweets_2018.csv", stringcols(_all) bindquotes(strict) varnames(1) maxquotedrows(unlimited) clear
//
// drop text processed_text query_id has_pic birth_announcement months_from like_count-quote_count start_time-end_time *classification media_url tweet_url
//
// merge 1:m author_id using `tweets', keep(match) nogen
//
// gen birth = 0
// replace birth = 1 if created_at == date_birth
//
// sort author_id created_at
//
//
// * Get a graph of tweet volume before and after having a child
