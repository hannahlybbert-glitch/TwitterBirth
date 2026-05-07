clear all

use "D:\TwitterBirth\data\cleaned\intermediate\user_info_full_sample.dta"

replace unique_id = regexs(1) if regexm(unique_id, "^(.*)T")

// gen truncated_ID = regexs(1) if regexm(unique_id, "^(.*)T")

browse unique_id truncated_ID




187324370_2017-01-31T15:25:37.000Z
706544427259600896_2016-09-26T12:04:09.000Z

