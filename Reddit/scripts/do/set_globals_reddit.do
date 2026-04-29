* Author:  Hannah Lybbert
* Created: 2026-04-09
* Updated: 2026-04-09
* Purpose: Set globals for Reddit directories and figure style

clear
macro drop _all

* Set this to the appropriate file path for your project directory
global dir "D:/TwitterBirth/Reddit"

cd $dir

* ----------------------------------------------------------------
* DATA DIRECTORIES
* ----------------------------------------------------------------
global Reddit_cleaned  "$dir/data/intermediate/cleaned_raw"
global Reddit_BP       "$dir/data/intermediate/births_and_posts"
global Reddit_final    "$dir/data/final"
global Reddit_NLP_sent "$dir/data/NLP/sentiment"

* ----------------------------------------------------------------
* SCRIPT DIRECTORIES
* ----------------------------------------------------------------
global dofile "$dir/scripts/do"
global py     "$dir/scripts/py"

* ----------------------------------------------------------------
* OUTPUT DIRECTORIES
* ----------------------------------------------------------------
global output      "$dir/output"

* ----------------------------------------------------------------
* OUTPUT DIRECTORIES — final figures
* ----------------------------------------------------------------
global final_figs  "$dir/output/final_figs"
global vol_out     "$final_figs/volume_final"
global topics_out  "$final_figs/topics_final"
global sent_out    "$final_figs/sentiment_final"
global ext_out     "$final_figs/extensive_final"

* ================================================================
* FIGURE STYLE GLOBALS
* ================================================================

* ----------------------------------------------------------------
* COLORS — point estimates
* ----------------------------------------------------------------
global col_main       "#800020"           // single-series main color (Reddit)
global col_female     "orange"            // female series
global col_male       "purple"            // male series
global col_pos        "230 159 0"         // positive change (colorblind-friendly amber)
global col_neg        "0 114 178"         // negative change (colorblind-friendly blue)

* ----------------------------------------------------------------
* COLORS — confidence intervals (with transparency)
* ----------------------------------------------------------------
global col_ci_main    "gs10"              // single-series CI
global col_ci_female  "orange%50"         // female CI
global col_ci_male    "purple%50"         // male CI

* ----------------------------------------------------------------
* COLORS — reference lines
* ----------------------------------------------------------------
global col_xline      "gs8"              // vertical birth line (x=0)
global col_yline      "gs8"              // horizontal zero line (y=0)
global col_base       "edkblue"          // baseline period shading

* ----------------------------------------------------------------
* MARKERS — point estimates
* ----------------------------------------------------------------
global msym           "circle"            // main symbol
global msym_gender    "circle"            // symbol for gender series
global msize          "small"             // default marker size
global msize_dot      "large"             // marker size for dot plots

* baseline omitted-period indicator
global msym_base      "diamond"
global mcol_base      "black"
global msize_base     "small"
global baseline_point "scatteri 0 -1, msymbol($msym_base) mcolor($mcol_base) msize($msize_base)"

* ----------------------------------------------------------------
* LINES
* ----------------------------------------------------------------
global lw_main        "medthick"          // main series line width
global lw_ci          "thin"              // CI line width
global lw_dot_ci      "medium"            // dot plot CI line width
global lp_ref         "dash"              // reference line pattern

* ----------------------------------------------------------------
* TEXT SIZES — axis titles (the "Months from Birth" / "Share Active" labels)
* ----------------------------------------------------------------
global xtitle_size    "large"
global ytitle_size    "large"
global ytopics_size   "medsmall"

* ----------------------------------------------------------------
* TEXT SIZES — tick mark numbers
* ----------------------------------------------------------------
global xtick_size     "medlarge"
global ytick_size     "medlarge"

* ----------------------------------------------------------------
* X-AXIS  (event study: months from birth)
* ----------------------------------------------------------------
global xlab_months    "xlabel(-18(2)18, labsize($xtick_size))"
global xtitle_months  `"xtitle("Months from Birth", size($xtitle_size))"'
global xline_birth    "xline(0, lcolor($col_xline) lpattern($lp_ref))"

* ----------------------------------------------------------------
* Y-AXIS
* ----------------------------------------------------------------
global ylab           "ylabel(#6, labsize($ytick_size))"
global yline_zero     "yline(0, lcolor($col_yline) lpattern($lp_ref))"
global xline_zero     "xline(0, lcolor($col_xline) lpattern($lp_ref))"

* ----------------------------------------------------------------
* GRAPH REGION
* ----------------------------------------------------------------
global region         "graphregion(color(white)) plotregion(color(white))"

* ----------------------------------------------------------------
* LEGEND POSITIONS  (ring(0) = inside plot area)
* ----------------------------------------------------------------
global leg_pos_ul     "position(11) ring(0)"
global leg_pos_ur     "position(1)  ring(0)"
global leg_pos_ll     "position(7)  ring(0)"
global leg_pos_lr     "position(4)  ring(0)"
global leg_pos_bm     "position(6)  ring(0)"
global leg_off        "legend(off)"
global leg_gender     `"legend(order(3 4) label(3 "Female") label(4 "Male") $leg_pos_ur)"'
global leg_gender_line `"legend(order(1 2) label(1 "Female") label(2 "Male") $leg_pos_ur)"'
global leg_posneg     `"legend(order(2 "Increased" 3 "Decreased") $leg_pos_ur cols(1) size(small))"'

* ----------------------------------------------------------------
* FIGURE EXPORT
* ----------------------------------------------------------------
global fig_width      "1200"
global fig_height     "800"
global fig_format     "jpg"
