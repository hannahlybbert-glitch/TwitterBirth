use "$cleaned/user_info_full_sample.dta", clear

// check for duplicates
duplicates tag author_id, generate(dup_tag)
browse unique_id author_id tweet_id name days_from date_birth child_number text dup_tag if dup_tag > 0

*** Manually fix the child num variable and drop the ones that are not applicable

// AnaKarenBarraza✨
drop if author_id == "1038449551" & tweet_id == "917236521119477760"

// Benjamin Haab
replace child_number = 1 if author_id == "108672639" & tweet_id == "797954362509180930"
replace child_number = 2 if author_id == "108672639" & tweet_id == "1067255205127962632"

//Josh Curie
replace child_number = 1 if author_id == "112772571" & tweet_id == "675496847427944450"
replace child_number = 2 if author_id == "112772571" & tweet_id == "963087097451155457"

//Vanessa Di Gregorio (she/her)
replace child_number = 1 if author_id == "123442750" & tweet_id == "653561338413887488"
replace child_number = 2 if author_id == "123442750" & tweet_id == "984833588519751681"

// Melissa 
replace child_number = 1 if author_id == "126664098" & tweet_id == "385016266022744064"
replace child_number = 2 if author_id == "126664098" & tweet_id == "771408196539932674"

// RebeccaStJames
replace child_number = 1 if author_id == "14293974" & tweet_id == "432533504061358080"
replace child_number = 2 if author_id == "14293974" & tweet_id == "432533504061358080"

// Leanne Waters
replace child_number = 1 if author_id == "143332152" & tweet_id == "724786410557841409"
replace child_number = 2 if author_id == "143332152" & tweet_id == "983895145526562816"

// Nina Coleman-Moorer
replace child_number = 1 if author_id == "149130701" & tweet_id == "463433064971255808"
replace child_number = 2 if author_id == "149130701" & tweet_id == "463433064971255808"

// hazelle palminteri🌛
replace child_number = 1 if author_id == "1592978646" & tweet_id == "706203962886610944"
replace child_number = 2 if author_id == "1592978646" & tweet_id == "927990066013618176"

// while they were napping
replace child_number = 1 if author_id == "1870402382" & tweet_id == "524277149306339329"
replace child_number = 2 if author_id == "1870402382" & tweet_id == "524277149306339329"

// M. J. Gallagher (Final Fantasy mythology) --> third child was labled correctly
replace child_number = 1 if author_id == "2201196054" & tweet_id == "385016266022744064"

// Shakir Achmat
replace child_number = 1 if author_id == "268710058" & tweet_id == "292326684940718080"
replace child_number = 2 if author_id == "268710058" & tweet_id == "939029456118620162"

// Benjamin Vrbicek
replace child_number = 1 if author_id == "284159577" & tweet_id == "641979085758033920"
replace child_number = 2 if author_id == "284159577" & tweet_id == "641979085758033920"

// Just Piper
replace child_number = 1 if author_id == "29091818" & tweet_id == "318540470449999873"
replace child_number = 2 if author_id == "29091818" & tweet_id == "318540470449999873"

// John Glen Stevens
drop if author_id == "296463994" & tweet_id == "947877032549142528" // two posts for same kid

// david graham
replace child_number = 1 if author_id == "304038417" & tweet_id == "699154076215414784"
replace child_number = 2 if author_id == "304038417" & tweet_id == "699154076215414784"

// Doc Spera
replace child_number = 1 if author_id == "3045325045" & tweet_id == "865487409735127040"
replace child_number = 2 if author_id == "3045325045" & tweet_id == "865487409735127040"

// Josh Speer
replace child_number = 1 if author_id == "306255998" & tweet_id == "795995866574286848"
replace child_number = 2 if author_id == "306255998" & tweet_id == "1069975960412401672"

// Kelly Bazzle
replace child_number = 1 if author_id == "32420038" & tweet_id == "568008136881262592"
replace child_number = 2 if author_id == "32420038" & tweet_id == "1029467287458406401"

// Rebecca Green
replace child_number = 1 if author_id == "350642337" & tweet_id == "641296771117780992"
replace child_number = 2 if author_id == "350642337" & tweet_id == "930885134521212928"

// Tony Jeffries OLY --> second tweet was a third child post
replace child_number = 1 if author_id == "37115603" & tweet_id == "684123498483068928"

// MARA
replace child_number = 1 if author_id == "391952082" & tweet_id == "358712893660872704"
replace child_number = 2 if author_id == "391952082" & tweet_id == "575855019502739456"

// Ramon a. Claudio
replace child_number = 1 if author_id == "41762433" & tweet_id == "737750216019988480"
replace child_number = 2 if author_id == "41762433" & tweet_id == "737750216019988480"

// FarmersWife&Mummy🐑
replace child_number = 1 if author_id == "459985269" & tweet_id == "560911120005754880"
replace child_number = 2 if author_id == "459985269" & tweet_id == "839402312552566784"

// Morgan Simmons
replace child_number = 1 if author_id == "486978517" & tweet_id == "382546575085817856"
replace child_number = 2 if author_id == "486978517" & tweet_id == "652459285780283392"

// Matthew Homan
replace child_number = 1 if author_id == "55341703" & tweet_id == "696899860633686016"
replace child_number = 2 if author_id == "55341703" & tweet_id == "1031588552704970759"

// Chris
replace child_number = 2 if author_id == "574565029" & tweet_id == "385016266022744064"

// Amanda Merheb
replace child_number = 1 if author_id == "623382436" & tweet_id == "721788099886342144"
replace child_number = 2 if author_id == "623382436" & tweet_id == "1031286535755378688"

// Roger Cullins
replace child_number = 1 if author_id == "66706881" & tweet_id == "843678520266113028"
replace child_number = 2 if author_id == "66706881" & tweet_id == "1070753696735248384"

// Jordan
replace child_number = 1 if author_id == "70980919" & tweet_id == "435561139900911617"
replace child_number = 2 if author_id == "70980919" & tweet_id == "661520495188115456"

// Monique Sanchez
replace child_number = 1 if author_id == "731009060795908096" & tweet_id == "880722361670017024"
replace child_number = 2 if author_id == "731009060795908096" & tweet_id == "1028130634005278720"

// Dan Price
replace child_number = 1 if author_id == "73431681" & tweet_id == "516582742382112768"
replace child_number = 2 if author_id == "73431681" & tweet_id == "897606473747922945"

// Jason Tackett
replace child_number = 1 if author_id == "742721486" & tweet_id == "646645408370950144"
replace child_number = 2 if author_id == "742721486" & tweet_id == "898354121031507968"

// Aaron Running
replace child_number = 1 if author_id == "87273377" & tweet_id == "794941171713933313"
replace child_number = 2 if author_id == "87273377" & tweet_id == "1015375502427742209"

// Samuel Cantelon
replace child_number = 1 if author_id == "92492867" & tweet_id == "463512349924552705"
replace child_number = 2 if author_id == "92492867" & tweet_id == "910549153155092481"






** Save the fully edited file, now its clean
save "$cleaned/user_info_full_sample_multpl_children.dta". replace