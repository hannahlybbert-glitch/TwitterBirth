* Author: Hannah Lybbert
* Created: 10/19/2026
* Purpose: Compare treatment vs control lifetime avg weekly tweets (avg_weekly_tweets)
* Output:  lifetime_avg_share_by_bin.jpg, lifetime_avg_hist.jpg, lifetime_avg_cdf.jpg (in $descriptives_control)

// do "$dofile/set_globals.do"

* ----------------------------------------------------------------
* Load data
* ----------------------------------------------------------------
* control: profiles that passed Filter A + B (one row per author)
use "$control_user/user_info.dta", clear
keep author_id avg_weekly_tweets
gen treated = 0
tempfile control
save `control'

* treatment: analysis sample (one row per author, full_3years == 1)
use "$final/user_analysis_sample.dta", clear
keep author_id avg_weekly_tweets
gen treated = 1

append using `control'

label define treated_lbl 0 "Control" 1 "Treatment"
label values treated treated_lbl

* check: missing avg_weekly_tweets by group
tab treated if missing(avg_weekly_tweets)
drop if missing(avg_weekly_tweets)

tabstat avg_weekly_tweets, by(treated) stats(n mean sd p5 p25 p50 p75 p95 max)

* ----------------------------------------------------------------
* Overlap: share of control inside the treatment p5-p95 range
* ----------------------------------------------------------------
sum avg_weekly_tweets if treated == 1, detail
local t_p5  = r(p5)
local t_p95 = r(p95)

count if treated == 0
local n_c = r(N)
count if treated == 0 & inrange(avg_weekly_tweets, `t_p5', `t_p95')
di "Control inside treatment p5-p95 [" %5.2f `t_p5' ", " %5.2f `t_p95' "]: " r(N) " of " `n_c' " (" %4.1f 100*r(N)/`n_c' "%)"

* two-sample KS test of equal distributions
ksmirnov avg_weekly_tweets, by(treated)

* ----------------------------------------------------------------
* Bins (log-style) and share of each group per bin
* ----------------------------------------------------------------
* both groups are capped at ~80/week by Filter B, so top bin is 40+
egen bin = cut(avg_weekly_tweets), at(0 0.5 1 2 5 10 20 40 1000000) icodes
replace bin = bin + 1
label define bin_lbl 1 "<0.5" 2 "0.5-1" 3 "1-2" 4 "2-5" 5 "5-10" 6 "10-20" 7 "20-40" 8 "40+"
label values bin bin_lbl

preserve
	gen one = 1
	collapse (sum) n = one, by(treated bin)
	bysort treated: egen n_grp = total(n)
	gen pct = 100 * n / n_grp

	* table: counts, shares, controls per treated author in each bin
	reshape wide n n_grp pct, i(bin) j(treated)
	foreach v in n0 n1 pct0 pct1 {
		replace `v' = 0 if missing(`v')
	}
	gen ctrl_per_treat = n0 / n1
	list bin n1 pct1 n0 pct0 ctrl_per_treat, sepby(bin) noobs abbreviate(14)

	* side-by-side bars
	gen x1 = bin - 0.2
	gen x0 = bin + 0.2
	twoway (bar pct1 x1, barwidth(0.4) color("$col_main")) ///
	       (bar pct0 x0, barwidth(0.4) color("$col_pos")), ///
	    xlabel(1 "<0.5" 2 "0.5-1" 3 "1-2" 4 "2-5" 5 "5-10" 6 "10-20" 7 "20-40" 8 "40+", labsize($xtick_size)) ///
	    ylabel(, labsize($ytick_size)) ///
	    xtitle("Lifetime Avg Weekly Tweets", size($xtitle_size)) ///
	    ytitle("Percent of Authors in Group", size($ytitle_size)) ///
	    legend(order(1 "Treatment" 2 "Control") $leg_pos_ur cols(1)) ///
	    $region
	graph export "$descriptives_control/lifetime_avg_share_by_bin.$fig_format", width($fig_width) height($fig_height) replace
restore

* ----------------------------------------------------------------
* Overlaid density histograms (same bins for both groups)
* ----------------------------------------------------------------
twoway (histogram avg_weekly_tweets if treated == 1, density start(0) width(2) color("$col_main%50") lcolor("$col_main")) ///
       (histogram avg_weekly_tweets if treated == 0, density start(0) width(2) color("$col_pos%50") lcolor("$col_pos")), ///
    xlabel(0(10)80, labsize($xtick_size)) ///
    ylabel(, labsize($ytick_size)) ///
    xtitle("Lifetime Avg Weekly Tweets", size($xtitle_size)) ///
    ytitle("Density", size($ytitle_size)) ///
    legend(order(1 "Treatment" 2 "Control") $leg_pos_ur cols(1)) ///
    $region
graph export "$descriptives_control/lifetime_avg_hist.$fig_format", width($fig_width) height($fig_height) replace

* ----------------------------------------------------------------
* CDFs (x = avg + 1 on log scale, labeled in raw units)
* ----------------------------------------------------------------
cumul avg_weekly_tweets, by(treated) gen(cdf) equal
gen avg_plus1 = avg_weekly_tweets + 1
sort treated avg_plus1

twoway (line cdf avg_plus1 if treated == 1, connect(stairstep) lcolor("$col_main") lwidth($lw_main)) ///
       (line cdf avg_plus1 if treated == 0, connect(stairstep) lcolor("$col_pos") lwidth($lw_main)), ///
    xscale(log) ///
    xlabel(1 "0" 2 "1" 3 "2" 6 "5" 11 "10" 21 "20" 41 "40" 81 "80", labsize($xtick_size)) ///
    ylabel(0(0.2)1, labsize($ytick_size)) ///
    xtitle("Lifetime Avg Weekly Tweets", size($xtitle_size)) ///
    ytitle("Cumulative Share of Authors", size($ytitle_size)) ///
    legend(order(1 "Treatment" 2 "Control") $leg_pos_lr cols(1)) ///
    $region
graph export "$descriptives_control/lifetime_avg_cdf.$fig_format", width($fig_width) height($fig_height) replace

* ----------------------------------------------------------------
* Share of control kept if resampled to the treatment bin shares
* ----------------------------------------------------------------
* K = max controls such that every bin can supply K * (treatment share);
* binding bin = smallest n0 / p1. Then drop controls at random within bin.
capture program drop match_share
program define match_share
	args binvar flag
	preserve
		gen one = 1
		collapse (sum) n = one, by(treated `binvar')
		reshape wide n, i(`binvar') j(treated)
		replace n0 = 0 if missing(n0)
		replace n1 = 0 if missing(n1)
		egen N0 = total(n0)
		egen N1 = total(n1)
		gen p1  = n1 / N1
		gen cap = n0 / p1   // total controls this bin could support
		qui sum cap
		gen keep_n = floor(r(min) * p1)
		egen kept = total(keep_n)
		list `binvar' n1 p1 n0 keep_n cap, noobs abbreviate(14)
		di "Controls kept: " kept[1] " of " N0[1] " (" %4.1f 100*kept[1]/N0[1] "%)"
		keep `binvar' keep_n
		tempfile caps
		save `caps'
	restore
	merge m:1 `binvar' using `caps', nogen
	gen double u = runiform()
	bysort treated `binvar' (u): gen `flag' = (_n <= keep_n) if treated == 0
	drop u keep_n
end

set seed 20261019

*--- Fine bins (8) ---
match_share bin keep_fine

*--- Coarse bins (4) ---
egen bin_coarse = cut(avg_weekly_tweets), at(0 2 10 40 1000000) icodes
replace bin_coarse = bin_coarse + 1
label define bin_coarse_lbl 1 "0-2" 2 "2-10" 3 "10-40" 4 "40+"
label values bin_coarse bin_coarse_lbl
match_share bin_coarse keep_coarse

* check: kept control shares vs treatment shares
tab bin treated if treated == 1 | keep_fine == 1, col nofreq
tab bin_coarse treated if treated == 1 | keep_coarse == 1, col nofreq
