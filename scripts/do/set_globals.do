* Set globals for directories
clear
macro drop _all
* Set this to the appropriate file path for your project directory
**# H - Changed directory from E:/ to D:/
global dir "D:/TwitterBirth"

cd $dir

* data
global raw "$dir/data/raw"
global cleaned "$dir/data/cleaned"
global intermediate "$dir/data/cleaned/intermediate"
global final "$dir/data/final"
global volume_analysis "$dir/data/volume_analysis"
global backup "$dir/data/backup_files"
global testing "$dir/data/testing"
global archive "$dir/data/archive"
global hand_coding "$dir/data/raw/hand_coding"
global RA_training "$dir/data/raw/hand_coding/RA_training"
global sentiment "$dir/data/sentiment_analysis"

* Control Data
global control_volume "$dir/ControlGroup/data/3_post_volume/anniversary"
global control_user "$dir/ControlGroup/data/2_user_profiles/anniversary"
global control_cleaned "$dir/ControlGroup/data/cleaned"

* Reddit data
global Reddit_cleaned "$dir/Reddit/data/intermediate/cleaned_raw"
global Reddit_BP "$dir/Reddit/data/intermediate/births_and_posts"
global Reddit_final "$dir/Reddit/data/final"

* scripts
global dofile "$dir/scripts/do"
global py "$dir/scripts/py"

* output
global output "$dir/output"
global figures "$dir/output/figures"
global volume_figs "$dir/output/volume"
global quitting_figs "$dir/output/volume/quitting"
global sentiment_figs "$dir/output/sentiment_analysis/figures/sentiment"
global tweetNLP_figs "$dir/output/sentiment_analysis/figures/tweetNLP"
global MFT_figs "$dir/output/sentiment_analysis/figures/MFT"
global classif_figs "$dir/output/sentiment_analysis/figures/classification"
global family_figs "$dir/output/sentiment_analysis/figures/tweetNLP/topic_class/family"
global politics_figs "$dir/output/sentiment_analysis/figures/tweetNLP/topic_class/politics"
global sports_figs "$dir/output/sentiment_analysis/figures/tweetNLP/topic_class/sports"

* control output 
global volume_control "$dir/ControlGroup/output/volume"

* ----------------------------------------------------------------
* OUTPUT DIRECTORIES — final figures
* ----------------------------------------------------------------
global final_figs      "$dir/output/final_figs"
global vol_out         "$final_figs/volume_final"
global topics_out      "$final_figs/topics_final"
global sent_out        "$final_figs/sentiment_final"
global ext_out         "$final_figs/extensive_final"

* ================================================================
* FIGURE STYLE GLOBALS
* ================================================================

* ----------------------------------------------------------------
* COLORS — point estimates
* ----------------------------------------------------------------
global col_main       "#34628D"           // single-series main color
global col_female     "orange"         // female series
global col_male       "purple"         // male series
global col_pos        "230 159 0"      // positive change (colorblind-friendly amber)
global col_neg        "0 114 178"      // negative change (colorblind-friendly blue)

* ----------------------------------------------------------------
* COLORS — confidence intervals (with transparency)
* ----------------------------------------------------------------
global col_ci_main    "gs10"           // single-series CI
global col_ci_female  "orange%50"      // female CI
global col_ci_male    "purple%50"      // male CI

* ----------------------------------------------------------------
* COLORS — reference lines
* ----------------------------------------------------------------
global col_xline      "gs8"            // vertical birth line (x=0)
global col_yline      "gs8"            // horizontal zero line (y=0)
global col_base       "edkblue"        // baseline period shading

* ----------------------------------------------------------------
* MARKERS — point estimates
* ----------------------------------------------------------------
global msym           "circle"         // main symbol
global msym_gender    "circle"         // symbol for gender series
global msize          "small"          // default marker size
global msize_dot      "large"          // marker size for dot plots

* baseline omitted-period indicator
global msym_base      "diamond"
global mcol_base      "black"
global msize_base     "small"
global baseline_point "scatteri 0 -1, msymbol($msym_base) mcolor($mcol_base) msize($msize_base)"

* ----------------------------------------------------------------
* LINES
* ----------------------------------------------------------------
global lw_main        "medthick"       // main series line width
global lw_ci          "thin"           // CI line width
global lw_dot_ci	  "medium"		// dot plot CI line width
global lp_ref         "dash"           // reference line pattern

* ----------------------------------------------------------------
* TEXT SIZES — axis titles (the "Months from Birth" / "Positivity" labels)
* ----------------------------------------------------------------
global xtitle_size    "large"          // x-axis title size
global ytitle_size    "large"          // y-axis title size
global ytopics_size   "medsmall"             // y-axis title size for topics figures

* ----------------------------------------------------------------
* TEXT SIZES — tick mark numbers
* ----------------------------------------------------------------
global xtick_size     "medlarge"            // x-axis tick number size
global ytick_size     "medlarge"            // y-axis tick number size

* ----------------------------------------------------------------
* X-AXIS  (event study: months from birth)
* ----------------------------------------------------------------
global xlab_months    "xlabel(-18(2)18, labsize($xtick_size))"
global xtitle_months  `"xtitle("Months from Birth", size($xtitle_size))"'
global xline_birth    "xline(0, lcolor($col_xline) lpattern($lp_ref))"

* ----------------------------------------------------------------
* Y-AXIS
* ----------------------------------------------------------------
global ylab           "ylabel(#6, labsize($ytick_size))"  // default y-axis tick labels (~6 auto ticks)
global yline_zero     "yline(0, lcolor($col_yline) lpattern($lp_ref))"
global xline_zero     "xline(0, lcolor($col_xline) lpattern($lp_ref))"  // zero ref for horizontal dot plots

* ----------------------------------------------------------------
* GRAPH REGION
* ----------------------------------------------------------------
global region         "graphregion(color(white)) plotregion(color(white))"

* ----------------------------------------------------------------
* LEGEND POSITIONS  (ring(0) = inside plot area)
* Use inside legend() option: legend(... $leg_pos_ul)
* ----------------------------------------------------------------
global leg_pos_ul     "position(11) ring(0)"   // upper left
global leg_pos_ur     "position(1)  ring(0)"   // upper right
global leg_pos_ll     "position(7)  ring(0)"   // lower left
global leg_pos_lr     "position(4)  ring(0)"   // lower right
global leg_pos_bm     "position(6)  ring(0)"   // bottom middle
global leg_off        "legend(off)"
global leg_gender     `"legend(order(3 4) label(3 "Female") label(4 "Male") $leg_pos_ur)"'  // use when plots 1+2 are CI bands
global leg_gender_line `"legend(order(1 2) label(1 "Female") label(2 "Male") $leg_pos_ur)"'  // use when no CI bands
global leg_posneg     `"legend(order(2 "Increased" 3 "Decreased") $leg_pos_ur cols(1) size(small))"'

* ----------------------------------------------------------------
* FIGURE EXPORT
* ----------------------------------------------------------------
global fig_width      "1200"
global fig_height     "800"
global fig_format     "jpg"            // swap to "pdf" for final submission

