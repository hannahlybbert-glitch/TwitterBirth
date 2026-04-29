# Twitter Birth Project - Stata Script Tracking

**Purpose:** This document tracks all Stata .do scripts in the data preparation and hand-coding pipeline, documenting what each script does, its input files, and output files.

**Date Created:** 2026-02-09

---

## Pipeline Overview

The Stata scripts handle:

1. **Hand Coding Management** → Manual validation of birth announcements
2. **Data Preparation** → Merging Python outputs (2018 + 2013-2017 data)
3. **Final Cleaning** → Creating analysis-ready datasets
4. **Descriptive Analysis** → Summary statistics and visualizations

**Key Workflow:**
- Python scripts → Raw CSVs → Hand coding validation → Stata data prep → Final analysis datasets

---

## scripts/do/hand_coding/

**Purpose:** Managing manual validation of birth announcement tweets and inter-rater reliability

| Script | Description | Input Files | Output Files | Key Operations |
|--------|-------------|-------------|--------------|----------------|
| `hand_coding_split_2018.do` | Automatically pre-codes 2013-2017 tweets using keyword patterns and flags ones for manual review. | `data/raw/hand_coding/to_hand_code_2013_01_01-2017_12_31.csv` | `data/raw/hand_coding/to_hand_code_master_2013_2017.csv` | Uses regexm to identify non-births (relatives, celebrities); removes duplicate tweets (≥10 identical); flags anniversary posts and retweets; auto-codes as "0" or "2"; sorts for manual coding assignment |
| `RA_eval.do` | Evaluates consistency across multiple research assistant coders by calculating correlations with reference coder (Rory). | `data/raw/hand_coding/RA_training/first_500_Rory.csv`, `data/raw/hand_coding/RA_training/hand_coded_[Names].csv` (18 RAs) | `data/raw/hand_coding/RA_training/RA_Corr.tex` | Loads reference coder and 18 RA files; merges on tweet_id; cleans inconsistent values; calculates correlation matrix between all raters; counts false negatives/positives per RA |
| `merge_hand_coded_2013_2017.do` | Consolidates hand-coded results from multiple sources (auto-coded, Rory, and 18 RAs) into master dataset with conflict resolution. | `data/raw/hand_coding/2013_2017/partially_hand_coded_master_2013_2017.csv`, `data/raw/hand_coding/2013_2017/first_500_rory.csv`, `data/raw/hand_coding/2013_2017/hand_coded_[Names].csv` | `data/raw/hand_coding/2013_2017/hand_coded_master_2013_2017.csv` | Loads auto-coded and Rory's coded tweets; appends 18 RA-coded files; merges on tweet_id and assigned_to; handles repeat births (removes duplicates within 546 days); creates birth_tweet_number to track first/second births per account |

**Key Insight:** The hand coding workflow uses automatic pre-coding, multiple human coders (18 RAs + Rory), and inter-rater reliability checks to validate birth announcements.

---

## scripts/do/data_prep/

**Purpose:** Core data preparation scripts that merge, clean, and create final analysis datasets

### Main Preparation Scripts

| Script | Description | Input Files | Output Files | Key Operations |
|--------|-------------|-------------|--------------|----------------|
| `prep_data.do` | **MASTER data preparation script** merging 2018 and 2013-2017 tweet volume and user demographic data. | **2018:** `data/raw/tweet_volume_by_user_2018.csv`, `data/raw/retweet_reply_volume_by_user_2018.csv`, `data/raw/user_info_with_demographics_2018.csv`<br>**2013-2017:** `data/raw/tweet_volume_by_user_2013_2017.csv`, `data/raw/retweet_reply_volume_by_user_2013_2017.csv`, `data/raw/user_info_with_demographics_2013_2017.csv`, `data/raw/user_info_genderx2check.dta`<br>**Tweets:** `data/raw/tweets_by_user_2013_2017.csv` | `data/cleaned/tweet_volume_by_user_2018.dta`, `data/cleaned/tweet_volume_by_user_2013_2017.dta`, `data/cleaned/tweet_volume_by_user_full_sample.dta`, `data/cleaned/user_info_full_sample.dta`, `data/cleaned/tweets_by_user_full_sample.dta`, `data/raw/tweets_by_user_full_sample.csv` | Merges volume data (original+quote vs retweet+reply) by author_id and date; appends 2018 + 2013-2017; merges user demographics; creates unique_id (author_id + birth_date); validates data completeness |
| `final_cleaning_3_datasets.do` | **FINAL CLEANING** of three main datasets: converts variable types, creates derived variables, removes outliers and invalid records. | `data/cleaned/user_info_full_sample.dta`, `data/cleaned/tweet_volume_by_user_full_sample.dta`, `data/cleaned/tweets_by_user_full_sample.dta` | **FINAL DATASETS:**<br>`data/final/user_info_full_sample_CLEAN.dta`<br>`data/final/tweet_volume_by_user_full_sample_CLEAN.dta`<br>`data/final/tweets_by_user_full_sample_CLEAN.dta` | Converts strings to numeric/date; removes duplicates; validates birth announcement timing (±14 days); drops multiple births per account; keeps only first birth; creates time-relative variables (days/weeks/months from birth); merges to add indicators (full_3years, no_rt_reply, acct_tweeted_postBA) |
| `prep_2018_tweet_text_data.do` | Prepares 2018 tweet text data by identifying first births per account and merging with user info. | `data/cleaned/user_info_full_sample.dta`, `data/raw/tweets_by_user_2018.csv` | `data/cleaned/user_info_first_child_NOTfull.dta`, `data/raw/tweets_by_user_2018_matching.dta`, `data/raw/tweets_by_user_2018_matching.csv` | Removes duplicate births (keeps first per account); merges tweet text with user info; fills missing created_at with date_birth_tweet for birth announcement tweets |

### Analysis & Descriptive Scripts

| Script | Description | Input Files | Output Files | Key Operations |
|--------|-------------|-------------|--------------|----------------|
| `descriptives.do` | Creates descriptive statistics, summary tables, and visualization figures for user demographics and tweet volumes. | `data/cleaned/user_info_full_sample_CLEAN.dta`, `data/final/tweet_volume_analysis_sample.dta`, `data/cleaned/tweets_by_user_full_sample_CLEAN.dta` | **Figures:** `output/figures/descriptive_figs/user_info/gender_shares.png`, `race_shares.png`, `DOB_dist.png`, `date_BA_dist.png`, `DOB_BA_overlay.png`, `account_creation.png`, `user_sum_stats.doc`<br>**Volume figs:** `output/figures/descriptive_figs/volume/sum_stats.doc`, histograms for gender/period splits | Creates bar/pie/histograms for demographics; generates summary statistics tables (asdoc); overlays pre/post histograms; creates gender-stratified analyses and panel figures |
| `percent_changes.do` | Calculates percentage changes in tweeting volume between pre- and post-birth periods. | `data/final/tweet_volume_by_user_full_sample_CLEAN.dta` | None (summary statistics output) | Creates post-birth indicator; collapses to mean tweets by user and period; reshapes wide for comparison; calculates percentage change; regression approach with log transformation and cluster-robust standard errors |
| `volume_FE.do` | Estimates individual fixed effects models of tweeting behavior with monthly indicators relative to birth. | `data/final/tweet_volume_by_user_full_sample_CLEAN.dta` | `output/volume/fixed_effects/tot_tweets_FE.jpg`, `output/volume/fixed_effects/orig_tweets_FE_beyondBA.jpg` | Creates monthly dummies pre/post birth; runs absorb regression (areg) with author_id fixed effects; extracts and plots coefficients with confidence intervals |
| `numbers_for_appendix.do` | Generates count statistics and descriptive numbers for different data subsets and time periods. | Multiple CSV imports: `data/raw/query_results_2018_*.csv`, `data/raw/classified_*.csv`, `data/raw/hand_coding/*.csv`, `data/cleaned/user_info.dta`, `data/cleaned/tweets_by_user.dta`, `data/cleaned/user_info_full_sample.dta`, `data/cleaned/tweet_volume_by_user_full_sample.dta` | None (generates output statistics) | Counts unique records, tabs classifications, creates sample counts for 2018, 2013-2017, and full sample periods |

### Old/Archive Scripts (data_prep/cleaning_prep/old/)

| Script | Description | Input Files | Output Files | Key Operations |
|--------|-------------|-------------|--------------|----------------|
| `volume_analysis.do` | Converts dates in tweet volume data and creates time-relative variables for birth event analysis. | `data/cleaned/tweet_volume_by_user.dta` | None (generates variables in memory) | Date conversion to Stata format; generates days from birth (t), birth indicator, numeric author IDs; filters for accounts with birth events |
| `track_nonrandom_rt_reply_volume.do` | Marks non-randomly selected accounts and exports to CSV. | `data/raw/retweet_reply_volume_by_user_2013_2017.csv` | `data/raw/nonrandom_retweet_reply_volume_2013_2017.csv` | Imports CSV; creates random selection indicator variable (0 for non-random); exports modified data |
| `variable_labeling.do` | Applies descriptive labels to three key datasets (user info full sample, tweet volume, tweet text). | `data/cleaned/user_info_full_sample.dta`, `data/cleaned/user_info_first_child_NOTfull.dta`, `data/cleaned/tweet_volume_by_user_full_sample.dta`, `data/cleaned/tweets_by_user_full_sample.dta` | Same input files (replaced with labeled versions) | Adds variable labels describing all fields (demographics, dates, engagement metrics, tweet counts) |

---

## Final Analysis Datasets

Based on the scripts analyzed, the **final cleaned analysis-ready datasets** are:

### **1. User Information Dataset**
- **File:** `data/final/user_info_full_sample_CLEAN.dta`
- **Created by:** `final_cleaning_3_datasets.do`
- **Contains:** User demographics (gender, race, occupation, child info), account metadata, birth announcement dates
- **Sample:** First birth only per account, validated birth announcements

### **2. Tweet Volume Dataset**
- **File:** `data/final/tweet_volume_by_user_full_sample_CLEAN.dta`
- **Created by:** `final_cleaning_3_datasets.do`
- **Contains:** Daily tweet counts for 18 months pre/post birth, time-relative variables (days/weeks/months from birth)
- **Structure:** Panel data (author_id × date)
- **Used for:** Longitudinal analysis of tweeting behavior changes

### **3. Tweet Text Dataset**
- **File:** `data/final/tweets_by_user_full_sample_CLEAN.dta`
- **Created by:** `final_cleaning_3_datasets.do`
- **Contains:** Full tweet text, engagement metrics (likes, retweets, quotes, replies), sentiment scores
- **Used for:** Text analysis, sentiment analysis, content analysis

---

## Key Data Flow (Python → Stata)

**Python Outputs (CSV)** → **Stata Input:**

1. **Volume data:**
   - Python: `data/raw/tweet_volume_by_user_{year}.csv`
   - Python: `data/raw/retweet_reply_volume_by_user_{year}.csv`
   - Stata: Merged in `prep_data.do` → `data/cleaned/tweet_volume_by_user_full_sample.dta`

2. **User demographics:**
   - Python: `data/raw/user_info_with_demographics_{year}.csv`
   - Stata: Loaded in `prep_data.do` → `data/cleaned/user_info_full_sample.dta`

3. **Tweet text:**
   - Python: `data/raw/tweets_by_user_{year}.csv`
   - Stata: Loaded in `prep_data.do` → `data/cleaned/tweets_by_user_full_sample.dta`

4. **Hand-coded validation:**
   - Python: `data/raw/hand_coding/to_hand_code_*.csv`
   - Stata: Processed in `hand_coding_split_2018.do` → `data/raw/hand_coding/hand_coded_master_{year}.csv`

**Final Cleaning:** All three datasets cleaned in `final_cleaning_3_datasets.do` → saved to `data/final/` directory

---

## Directory Path Variables (Globals)

Based on `set_globals.do`, these global macros map to actual directories:

**Data directories:**
- `$raw` → `data/raw`
- `$cleaned` → `data/cleaned`
- `$final` → `data/final`
- `$volume_analysis` → `data/volume_analysis`
- `$backup` → `data/backup_files`
- `$testing` → `data/testing`
- `$archive` → `data/archive`
- `$hand_coding` → `data/raw/hand_coding`
- `$RA_training` → `data/raw/hand_coding/RA_training`
- `$sentiment` → `data/sentiment_analysis`

**Scripts directories:**
- `$dofile` → `scripts/do`
- `$py` → `scripts/py`

**Output directories:**
- `$output` → `output`
- `$figures` → `output/figures`
- `$volume_figs` → `output/volume`
- `$quitting_figs` → `output/volume/quitting`
- `$sentiment_figs` → `output/sentiment_analysis/figures/sentiment`
- `$tweetNLP_figs` → `output/sentiment_analysis/figures/tweetNLP`
- `$MFT_figs` → `output/sentiment_analysis/figures/MFT`
- `$classif_figs` → `output/sentiment_analysis/figures/classification`

---

## Notes

- The hand-coding process involved 18 research assistants plus a reference coder (Rory)
- Inter-rater reliability was evaluated using correlation analysis
- Data covers two time periods: 2018 and 2013-2017, which are merged into "full_sample"
- Only first births per account are kept in final analysis
- Birth announcements must occur within ±14 days of actual birth date
- Time-relative variables allow pre/post birth comparisons
- Fixed effects models account for individual-level heterogeneity
