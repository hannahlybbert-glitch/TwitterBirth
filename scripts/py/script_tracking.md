# Twitter Birth Project - Script Tracking

**Purpose:** This document tracks all Python scripts in the Twitter scraping and analysis pipeline, documenting what each script does, its input files, and output files.

**Date Created:** 2026-02-09

---

## Pipeline Overview

Based on the scripts analyzed, the complete data flow is:

1. **Initial Twitter Query** → `data/raw/query_results_*.csv`
   - Script: `twitter_scraping_code/get_tweets.py`
   - Raw scraped tweets from Twitter's full archive API

2. **Text Classification** → `data/raw/classified_text_*.csv`
   - Script: `batch_classify_text.py`
   - LLM classifies tweets as birth announcements (YES/NO)

3. **Image Classification** → `data/raw/classified_images_*.csv`
   - Script: `batch_classify_images.py`
   - LLM analyzes images from flagged tweets

4. **Hand Coding/Validation** → `data/raw/hand_coding/{year}/hand_coded_master_{year}.csv`
   - Manual validation of LLM-flagged birth announcements

5. **Longitudinal Data Collection**
   - Script: `twitter_scraping_code/get_tweet_volume_by_user.py`
   - Output: `data/raw/tweet_volume_by_user_{year}.csv` and `data/raw/user_info_{year}.csv`
   - Collects 18-month pre/post birth tweet volumes

6. **Tweet Content Collection**
   - Script: `twitter_scraping_code/get_tweets_by_user.py`
   - Output: `data/raw/tweets_by_user_{year}.csv`
   - Full tweet text for longitudinal analysis

7. **Demographics Extraction** → `data/raw/user_info_with_demographics_{year}.csv`
   - Scripts: `LLM_demographics/get_demographics_update.py`, `LLM_demographics/get_child_gender.py`
   - Predicts user demographics and child gender using multimodal LLM

8. **Sentiment Analysis** → `data/raw/tweet_sentiment_{year}.csv`
   - Script: `sentiment_analysis.py`
   - Analyzes emotional content of tweets over time

---

## scripts/py/twitter_scraping_code/

**Purpose:** Core scripts for querying Twitter API and collecting longitudinal data

| Script | Description | Input Files | Output Files |
|--------|-------------|-------------|--------------|
| `get_tweets.py` | Queries Twitter full archive API for 10 different birth announcement search patterns across 2013-2017 period. | None (API source) | `data/raw/query_results_2013_01_01-2017_12_31.csv` |
| `get_tweet_volume_by_user.py` | Fetches daily original tweet counts for users during pre and post-birth event windows and creates user info file. | `data/raw/hand_coding/{year}/hand_coded_master_{year}.csv` | `data/raw/tweet_volume_by_user_{year}.csv`, `data/raw/user_info_{year}.csv` (or `user_info_{year}_missing_bio.csv`) |
| `get_tweets_by_user.py` | Fetches original and quoted tweets for users from full archive within specified time windows and saves engagement metrics. | `data/raw/tweet_volume_by_user_2013_2017.csv` | `data/raw/tweets_by_user_2013_2017.csv` |
| `get_rt_reply_volume.py` | Fetches daily retweet and reply counts for users around birth events to analyze engagement patterns. | `data/raw/hand_coding/{year}/hand_coded_master_{year}.csv` | `data/raw/retweet_reply_volume_by_user_{year}.csv` |
| `grab_missing_user_info.py` | Fetches missing user metadata (bio, follower counts) from Twitter API for 2018 dataset and merges with tweet data. | `data/raw/user_info_missing_bio_2018.csv` | `data/raw/user_info_2018.csv` |

**Key Insight:** `get_tweets.py` appears to be the **original raw data collection script** that queries Twitter's full archive API.

---

## scripts/py/ (Root Production Scripts)

**Purpose:** Main production scripts for text/image classification, sentiment analysis, and data cleaning

| Script | Description | Input Files | Output Files |
|--------|-------------|-------------|--------------|
| `batch_classify_text.py` | Classifies tweets as birth announcements using OpenAI's GPT-4 Batch API with chain-of-thought reasoning, preprocessing text to remove links, mentions, and unwanted emojis. | `data/raw/query_results_2013_01_01-2017_12_31.csv` | `data/raw/classified_text_2013_01_01-2017_12_31.csv`, `data/json/batch_requests_2013_01_01-2017_12_31_batch_*.jsonl` |
| `batch_classify_images.py` | Classifies images from tweets as birth announcements using OpenAI's GPT-4 Batch API, creating JSONL batch requests, monitoring job status, and merging results back into the original dataset. | `data/raw/classified_text_GPT4_2013_01_01-2017_12_31.csv` | `data/raw/classified_images_2013_01_01-2017_12_31.csv`, `data/raw/hand_coding/to_hand_code_2013_01_01-2017_12_31.csv`, `data/json/batch_image_requests_2013_01_01-2017_12_31_batch_*.jsonl` |
| `sentiment_analysis.py` | Analyzes sentiment of tweets using the CardiffNLP Twitter-RoBERTa transformer model, classifying emotions as negative, neutral, or positive with confidence scores. | `data/raw/tweets_by_user_2018.csv` | `data/raw/tweet_sentiment_2018.csv` |
| `remove_incomplete_volume_userids.py` | Filters out incomplete user records by comparing expected versus actual observation dates in a retweet/reply volume dataset, keeping only users with complete daily data. | `data/raw/retweet_reply_volume_by_user_2013_2017.csv` | `data/raw/retweet_reply_volume_by_user_2013_2017.csv` (overwritten) |

**Key Insight:** These are the main production classification scripts. `batch_classify_text.py` → `batch_classify_images.py` form a two-stage classification pipeline for birth announcements.

---

## scripts/py/LLM_demographics/

**Purpose:** Demographics extraction scripts using multimodal LLM analysis

| Script | Description | Input Files | Output Files |
|--------|-------------|-------------|--------------|
| `get_demographics.py` | Infers user demographics (gender, race, occupation, number of children) from Twitter profile information using OpenAI's GPT-4 Batch API with multi-modal analysis of names, descriptions, profile images, and tweet text. | `data/raw/user_info_2018.csv` | `data/raw/user_info_with_demographics_2018.csv`, `data/json/batch_requests_gender_batch_*.jsonl`, `data/json/batch_requests_race_batch_*.jsonl`, `data/json/batch_requests_occupation_batch_*.jsonl`, `data/json/batch_requests_children_batch_*.jsonl` |
| `get_demographics_update.py` | Identical to get_demographics.py but updated for the current working directory (D:/TwitterBirth), with additional safeguards in the gender detection prompt regarding image handling when missing. | `data/raw/user_info_2018.csv` | `data/raw/user_info_with_demographics_2018.csv`, `data/json/batch_requests_{gender/race/occupation/children}_batch_*.jsonl` |
| `get_child_gender.py` | Predicts the gender of newborn children from birth announcement tweets using OpenAI's GPT-4 Batch API, analyzing explicit linguistic signals and gendered terms with careful sibling reference validation. | `data/raw/user_info_2018.csv` | `data/raw/user_info_with_child_gender_2018.csv`, `data/json/batch_requests_child_gender_batch_*.jsonl` |

**Key Insight:** These scripts extract demographic features using multimodal LLM analysis. `get_demographics_update.py` is the active version; `get_demographics.py` is the original with old directory paths.

---

## scripts/py/test_full_archive/

**Purpose:** Scripts for testing and running LLM classification on full archive data

| Script | Description | Input Files | Output Files |
|--------|-------------|-------------|--------------|
| `classify_tweets.py` | Classifies tweets using OpenAI's Batch API with chain-of-thought prompting to identify birth announcements. | `data/raw/query_results_{begin_date}-{end_date}.csv` | `data/classified_text_{begin_date}-{end_date}.csv`, `data/json/batch_requests_{begin_date}-{end_date}.jsonl`, `data/rate_limit_tracker.json` |
| `classify_pictures.py` | Submits images from tweets to GPT-4 Batch API for classification as birth announcement images and merges results. | `data/raw/classified_text_{begin_date}-{end_date}.csv` | `data/testing/classified_images_{begin_date}-{end_date}.csv`, `data/json/batch_image_requests_{begin_date}-{end_date}.jsonl` |
| `batch_test.py` | Creates batches of tweets, submits them to OpenAI's Batch API for birth announcement classification, and merges results back into CSV. | `data/raw/query_results_{begin_date}-{end_date}.csv` | `data/raw/test_classified_results.csv`, `data/json/test_batch_{0..1}.jsonl` |
| `get_gender.py` | Classifies user gender from profile images, names, descriptions and handles using OpenAI's Batch API in batches. | `data/raw/user_info_{YEAR}.csv` | `data/raw/user_info_with_demographics{YEAR}.csv`, `data/json/batch_requests_gender_batch_{0..n}.jsonl` |
| `get_race.py` | Classifies user race/ethnicity from profile images using OpenAI's Batch API to process demographic information. | `data/raw/user_info_{YEAR}.csv` | `data/raw/user_info_with_demographics_{YEAR}.csv`, `data/json/batch_requests_demographics_batch_{0..n}.jsonl` |
| `test_get_tweets.py` | Filters and displays tweet statistics including pre-period duration, tweet count, and applies quota filtering on user data. | `data/raw/tweet_volume_by_user_2013_2017.csv` | None (prints to stdout) |
| `get_avg_tokens.py` | Reads JSONL batch results and computes average token usage across successful API responses. | `/Users/rorylawson/Desktop/TwitterBirth/data/json/batch_67c156eae840819083a79569b71cab65_output.jsonl` | None (prints to stdout) |
| `test_batch.py` | Uploads JSONL file to OpenAI, submits batch job, creates a new batch, and monitors status (incomplete/test code). | `data/json/batch_requests_{begin_date}-{end_date}.jsonl` | None (creates placeholder batches) |

**Key Insight:** `classify_tweets.py` performs the initial LLM classification on raw query results. Demographics scripts (`get_gender.py`, `get_race.py`) process the validated user data.

---

## scripts/py/test_recent_search/

**Purpose:** Testing scripts using Twitter's recent search API (7-day window)

| Script | Description | Input Files | Output Files |
|--------|-------------|-------------|--------------|
| `get_tweets_recent.py` | Queries Twitter API for tweets matching birth announcement phrases with 10 different search patterns and saves results. | None (API source) | `data/testing/query_results_{begin_date}-{end_date}.csv`, `data/testing/query_phrases_{begin_date}-{end_date}.csv` |
| `classify_tweets_recent.py` | Classifies tweets as birth announcements with optional majority voting using chain-of-thought prompting on OpenAI API. | `data/testing/query_results_{begin_date}-{end_date}.csv` | `data/testing/classified_text_{begin_date}-{end_date}.csv` |
| `classify_pictures_recent.py` | Classifies images from tweets as birth announcements using GPT-4 API and saves results with hand-coding candidates. | `data/testing/classified_text_{begin_date}-{end_date}.csv` | `data/testing/classified_pics_{begin_date}-{end_date}.csv`, `data/testing/to_hand_code_{begin_date}-{end_date}.csv` |
| `classify_accounts_recent.py` | Analyzes and classifies user profiles using DeepFace for gender and OpenAI for occupation from profile images and descriptions. | `data/testing/query_test.csv` | `data/testing/profile_classifications.csv` |
| `get_tweets_by_user_recent.py` | Fetches recent tweets from specified users via Twitter API and saves them with engagement metrics. | `data/testing/hand_coded{begin_date}-{end_date}.csv` | `data/testing/tweet_types_{begin_date}-{end_date}.csv` (or `tweet_types_test.csv`) |
| `get_tweet_counts_by_user_recent.py` | Fetches daily tweet count statistics for users during a specific date range via Twitter counts API. | `data/testing/hand_coded_{begin_date}-{end_date}.csv` | `data/testing/tweet_counts_{begin_date}-{end_date}.csv` |
| `find_optimal_query_recent.py` | Analyzes phrase matches from search queries against hand-coded tweets to calculate hit rates for accuracy evaluation. | `data/testing/query_results_{begin_date}-{end_date}.csv`, `data/testing/hand_coded_{begin_date}-{end_date}.csv`, `data/testing/query_phrases_{begin_date}-{end_date}.csv` | `data/testing/phrase_matches_{begin_date}-{end_date}.csv` |
| `compare_classifiers.py` | Compares different text classification methods using GPT-4 with chain-of-thought reasoning for birth announcement detection. | `data/testing/query_test.csv` (if test mode), `data/testing/profile_classifications.csv` | `data/testing/profile_classifications.csv` |
| `full_archive_test.py` | (Entirely commented out) Intended to classify tweets from full Twitter archive using OpenAI Batch API. | N/A (commented) | N/A (commented) |

**Key Insight:** These scripts mirror the full archive workflow but use the recent search API for testing and development purposes. Output goes to `data/testing/` rather than `data/raw/`.

---

## Original Raw Data Location

Based on this analysis, the **original raw data** from the first Twitter pull appears to be:

- **Primary raw source:** `data/raw/query_results_2013_01_01-2017_12_31.csv`
  - Generated by: `scripts/py/twitter_scraping_code/get_tweets.py`
  - Contains: Initial tweet scrape from Twitter full archive API

- **Hand-coded validation files:** `data/raw/hand_coding/{year}/hand_coded_master_{year}.csv`
  - These are manually validated birth announcements after LLM flagging

- **User longitudinal data:** `data/raw/tweet_volume_by_user_{year}.csv`
  - Generated by: `scripts/py/twitter_scraping_code/get_tweet_volume_by_user.py`
  - Contains: Daily tweet counts 18 months pre/post birth

---

## Notes

- Scripts in `test_recent_search/` use recent search API (7-day window) and output to `data/testing/`
- Scripts in `test_full_archive/` and `twitter_scraping_code/` use full archive API and output to `data/raw/`
- The hand-coding step appears to happen between LLM classification and demographic extraction
- Multiple scripts use OpenAI's Batch API for cost-effective large-scale processing
- Some paths reference old working directories (e.g., `/Users/rorylawson/Desktop/TwitterBirth/`)
