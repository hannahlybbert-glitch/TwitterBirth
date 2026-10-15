* Author: Hannah Lybbert
* Created: 10/15/2026
* Purpose: Compare treatment vs control pre-period (months -18 to -10) avg monthly orig+quote tweets
* Output:  pre_volume_share_by_bin.jpg, pre_volume_cdf.jpg (in $descriptives_control)

// do "$dofile/set_globals.do"

* ----------------------------------------------------------------
* Load data
* ----------------------------------------------------------------
use "$final/volume_control_treatment_sample.dta", clear

* treatment is already restricted to full_3years == 1; control is not
bysort treated: distinct author_id
keep if full_3years == 1
bysort treated: distinct author_id

* pre-pregnancy only; months -9 to -1 may already reflect treatment
keep if inrange(months_from_birth, -18, -10)

* ----------------------------------------------------------------
* One row per author: avg monthly tweets over months -18 to -10
* ----------------------------------------------------------------
* og/qt only (no rt/reply volume for controls)
* monthly og/qt totals, then average across the 9 months
collapse (first) og_qt_month_tweets, by(author_id treated months_from_birth)
collapse (mean) avg_month_pre = og_qt_month_tweets (count) n_months = og_qt_month_tweets, by(author_id treated)
label var avg_month_pre "Avg monthly orig+quote tweets, months -18 to -10"

* check: authors missing any of the 9 months
tab n_months treated, missing

label define treated_lbl 0 "Control" 1 "Treatment"
label values treated treated_lbl

tabstat avg_month_pre, by(treated) stats(n mean p5 p25 p50 p75 p95 max)

* ----------------------------------------------------------------
* Overlap: share of control inside the treatment p5-p95 range
* ----------------------------------------------------------------
sum avg_month_pre if treated == 1, detail
local t_p5  = r(p5)
local t_p95 = r(p95)

count if treated == 0
local n_c = r(N)
count if treated == 0 & inrange(avg_month_pre, `t_p5', `t_p95')
di "Control inside treatment p5-p95 [" %5.2f `t_p5' ", " %5.2f `t_p95' "]: " r(N) " of " `n_c' " (" %4.1f 100*r(N)/`n_c' "%)"

* ----------------------------------------------------------------
* Bins (log-style) and share of each group per bin
* ----------------------------------------------------------------
egen bin = cut(avg_month_pre), at(0 0.001 1 2 5 10 20 50 100 200 1000000) icodes
replace bin = bin + 1
label define bin_lbl 1 "0" 2 "<1" 3 "1-2" 4 "2-5" 5 "5-10" 6 "10-20" 7 "20-50" 8 "50-100" 9 "100-200" 10 "200+"
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
	    xlabel(1(1)10, valuelabel labsize($xtick_size)) ///
	    ylabel(, labsize($ytick_size)) ///
	    xtitle("Avg Monthly Tweets, Months -18 to -10", size($xtitle_size)) ///
	    ytitle("Percent of Authors in Group", size($ytitle_size)) ///
	    legend(order(1 "Treatment" 2 "Control") $leg_pos_ur cols(1)) ///
	    $region
	graph export "$descriptives_control/pre_volume_share_by_bin.$fig_format", width($fig_width) height($fig_height) replace
restore

* ----------------------------------------------------------------
* CDFs (x = avg + 1 on log scale, labeled in raw units)
* ----------------------------------------------------------------
cumul avg_month_pre, by(treated) gen(cdf) equal
gen avg_plus1 = avg_month_pre + 1
sort treated avg_plus1

twoway (line cdf avg_plus1 if treated == 1, connect(stairstep) lcolor("$col_main") lwidth($lw_main)) ///
       (line cdf avg_plus1 if treated == 0, connect(stairstep) lcolor("$col_pos") lwidth($lw_main)), ///
    xscale(log) ///
    xlabel(1 "0" 2 "1" 6 "5" 11 "10" 21 "20" 51 "50" 101 "100" 201 "200", labsize($xtick_size)) ///
    ylabel(0(0.2)1, labsize($ytick_size)) ///
    xtitle("Avg Monthly Tweets, Months -18 to -10", size($xtitle_size)) ///
    ytitle("Cumulative Share of Authors", size($ytitle_size)) ///
    legend(order(1 "Treatment" 2 "Control") $leg_pos_lr cols(1)) ///
    $region
graph export "$descriptives_control/pre_volume_cdf.$fig_format", width($fig_width) height($fig_height) replace

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

set seed 20261015

*--- Fine bins (10) ---
match_share bin keep_fine

*--- Coarse bins (4) ---
egen bin_coarse = cut(avg_month_pre), at(0 2 10 50 1000000) icodes
replace bin_coarse = bin_coarse + 1
label define bin_coarse_lbl 1 "0-2" 2 "2-10" 3 "10-50" 4 "50+"
label values bin_coarse bin_coarse_lbl
match_share bin_coarse keep_coarse

* check: kept control shares vs treatment shares
tab bin treated if treated == 1 | keep_fine == 1, col nofreq
tab bin_coarse treated if treated == 1 | keep_coarse == 1, col nofreq
