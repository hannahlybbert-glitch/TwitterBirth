# Reddit Birth Project - Data Lineage

**Purpose:** Visual map of the complete Reddit data pipeline from raw submissions to final analysis datasets.

**Date Created:** 2026-04-07

---

## Data Pipeline Overview

Three parallel pipelines feed into the final stacked analysis file:
1. **22k Treatment Pipeline** — the primary treatment group (completed)
2. **2.3M Pipeline** — large-scale LLM birth detection (completed)
3. **Placebo Control Pipeline** — matched controls with assigned birth dates

```mermaid
flowchart TD

    %% ========== RAW DATA SOURCES ==========
    RAW1[Reddit/raw/<br/>reddit_data_2006_01_to_2018_12.csv]
    RAW2[Reddit/raw/<br/>reddit_parenting_submissions.csv]
    RAW3[Reddit/raw/<br/>births_22k_submissions.csv]
    RAW5[Reddit/raw/<br/>births_2_3M_submissions.csv<br/>]
    RAW_PL["Reddit/raw/<br/>matched_authors_jul2023.csv<br/>matched_placebo_treatment_posts_jul2023.csv<br/>matched_placebo_submissions_jul2023.csv"]

    %% ========== STAGE 1: CLEAN RAW ==========
    RAW1 -->|clean_2006_2018_sample.py| C1A[intermediate/cleaned_raw/<br/>reddit_cleaned_2006_to_2018.csv]
    C1A -->|sample 30k| C1B[intermediate/cleaned_raw/<br/>reddit_30k_sample.csv]

    RAW2 -->|clean_reddit_parenting_submissions.py| C2[intermediate/cleaned_raw/<br/>reddit_parenting_full_cleaned.parquet]
    C2 -->|extract 190k subset| C3[intermediate/cleaned_raw/<br/>reddit_parenting_190k_sample.parquet]
    C2 -->|extract_190k_from_full.py<br/>removes 190k rows, keeps complement| C4[intermediate/cleaned_raw/<br/>reddit_parenting_2_3M_sample.parquet]

    RAW3 -->|clean_22k_sample_post_history.py| C5[intermediate/cleaned_raw/<br/>reddit_22k_post_history_cleaned.csv]

    RAW5 -->|clean_2_3M_post_history.py| C7[intermediate/cleaned_raw/<br/>reddit_77k_post_history_cleaned.csv]

    RAW_PL -->|"clean_matched_authors.py<br/>clean_matched_author_birth_posts.py<br/>clean_matched_placebo_post_history.py"| CPL["intermediate/cleaned_raw/<br/>matched_authors_clean.csv<br/>matched_placebo_birth_posts_clean.csv<br/>matched_placebo_post_history_clean.csv"]

    %% ========== STAGE 2a: LLM BIRTH DETECTION — 190k SAMPLE ==========
    C3 -->|get_reddit_births.py<br/>GPT-4o-mini batch API| L1[LLM/<br/>birth_detection_parenting_sample.csv]

    L1 -->|extract_190k_llm_births.py<br/>filter birth_flag == 1| B1[intermediate/llm_births/<br/>births_190k_sample.csv]

    B1 -->|get_reddit_births.py<br/>GPT-4o-full batch API| L2[LLM/<br/>birth_detection_190k_births_GPT4o.csv]

    L2 -->|extract_22k_llm_births.py<br/>filter birth_flag == 1| B2[intermediate/llm_births/<br/>births_22k_sample.csv]

    %% ========== STAGE 2b: LLM BIRTH DETECTION — 2.3M PIPELINE ==========
    C4 -->|1_split_into_batches.py<br/>split into 10 even batches| P1[LLM/pipeline/batches/<br/>batch_01–10.parquet]
    P1 -->|2_run_mini_and_extract.py<br/>GPT-4o-mini, extract positives| P2[LLM/pipeline/staging/<br/>batch_NN_positives.csv]
    P2 -->|3_watcher_full_model.py<br/>GPT-4o full model, polls hourly| P3[LLM/pipeline/full_output/<br/>batch_NN_full_results.csv]
    P3 -->|4_merge_full_output.py<br/>combine all 10 batches| L3[LLM/<br/>birth_detection_2_3M_GPT4o_full.csv]
    L3 -->|extract_2_3M_births.py<br/>filter birth_flag == 1| B3[intermediate/llm_births/<br/>births_2_3M_sample.csv]

    %% ========== STAGE 3: MERGE BIRTHS + POST HISTORY ==========
    B2 & C5 -->|merge_births_and_posts.py| M1[intermediate/births_and_posts/<br/>merged_22k_births_and_posts.csv]

    B3 & C7 -->|merge_births_and_posts.py| M2[intermediate/births_and_posts/<br/>merged_77k_births_and_posts.csv]

    M1 & M2 -->|merge_births_and_posts.py<br/>combine 22k + 77k| MFULL[intermediate/births_and_posts/<br/>merged_births_and_posts_FULL.csv]

    MFULL -->|build_analysis_ready_file.py<br/>create time-relative-to-birth vars| F1[final/<br/>births_and_posts_FULL.csv]

    %% ========== STAGE 4: PLACEBO CONTROL ==========
    CPL & F1 -->|"build_matched_placebo_births_jul23.py<br/>assign treatment author's days_from to placebo"| PL1[intermediate/placebo_births/<br/>matched_placebo_births.csv]

    PL1 & CPL -->|build_placebo_post_history.py<br/>merge birth dates onto post history| PL2[intermediate/births_and_posts/<br/>matched_placebo_births_posts.csv]

    F1 & PL2 & CPL -->|stack_treatment_control.py<br/>restrict treatment to matched pairs, add treated flag| FINAL[final/<br/>treatment_control_births_posts.csv]

    %% ========== STYLING ==========
    classDef rawData fill:#e1f5ff,stroke:#0077be,stroke-width:2px
    classDef cleanedData fill:#e8f5e9,stroke:#4caf50,stroke-width:2px
    classDef llmOutput fill:#fff4e1,stroke:#ff9900,stroke-width:2px
    classDef pipelineData fill:#fce4ec,stroke:#e91e63,stroke-width:2px
    classDef birthSample fill:#fffde7,stroke:#f9a825,stroke-width:2px
    classDef finalData fill:#f3e5f5,stroke:#9c27b0,stroke-width:3px

    class RAW1,RAW2,RAW3,RAW5,RAW_PL rawData
    class C1A,C1B,C2,C3,C4,C5,C7,M1,M2,MFULL,CPL,PL1,PL2 cleanedData
    class L1 pipelineData
    class L2,L3 llmOutput
    class P1,P2,P3 pipelineData
    class B1 pipelineData
    class B2,B3 birthSample
    class F1,FINAL finalData
```

---

## Pipeline Stages Explained

### **Stage 1: Clean Raw Data**

| Script | Input | Output |
|--------|-------|--------|
| `clean_2006_2018_sample.py` | `Reddit/raw/reddit_data_2006_01_to_2018_12.csv` | `reddit_cleaned_2006_to_2018.csv`, `reddit_30k_sample.csv` |
| `clean_reddit_parenting_submissions.py` | Reddit API / r/Parenting raw submissions | `reddit_parenting_full_cleaned.parquet`, `reddit_parenting_190k_sample.parquet` |
| `extract_190k_from_full.py` | `reddit_parenting_full_cleaned.parquet` + `reddit_parenting_190k_sample.parquet` | `reddit_parenting_2_3M_sample.parquet` (full minus 190k) |
| `clean_22k_sample_post_history.py` | `Reddit/raw/births_22k_submissions.csv` | `reddit_22k_post_history_cleaned.csv` |
| `clean_matched_authors.py` | `Reddit/raw/matched_authors_jul2023.csv` | `matched_authors_clean.csv` |
| `clean_matched_author_birth_posts.py` | `Reddit/raw/matched_placebo_treatment_posts_jul2023.csv` | `matched_placebo_birth_posts_clean.csv` |
| `clean_matched_placebo_post_history.py` | `Reddit/raw/matched_placebo_submissions_jul2023.csv` | `matched_placebo_post_history_clean.csv` |

The three matched placebo cleaning scripts run in parallel and apply the same cleaning steps (drop deleted authors, drop null ids, drop empty posts) with no top-5% trim (matched pairs must be preserved).

---

### **Stage 2a: LLM Birth Detection — 190k Sample**

Two-pass GPT-4o detection on the 190k parenting sample, yielding ~22k confirmed births.

| Script | Input | Output |
|--------|-------|--------|
| `get_reddit_births.py` | `reddit_parenting_190k_sample.parquet` | `birth_detection_parenting_sample.csv` |
| `extract_190k_llm_births.py` | `birth_detection_parenting_sample.csv` + `reddit_parenting_190k_sample.csv` | `births_190k_sample.csv` |
| `get_reddit_births.py` (2nd pass) | `births_190k_sample.csv` | `birth_detection_190k_births_GPT4o.csv` |
| `extract_22k_llm_births.py` | `birth_detection_190k_births_GPT4o.csv` + `births_190k_sample.csv` | `births_22k_sample.csv` |

---

### **Stage 2b: LLM Birth Detection — 2.3M Pipeline**

Mini → full model two-stage pipeline with continuous watcher. Runs in parallel with Stage 2a.

| Script | Input | Output |
|--------|-------|--------|
| `1_split_into_batches.py` | `reddit_parenting_2_3M_sample.parquet` | `batch_01.parquet` – `batch_10.parquet` |
| `2_run_mini_and_extract.py` | `batch_NN.parquet` | `batch_NN_positives.csv` (mini positives only) |
| `3_watcher_full_model.py` | `batch_NN_positives.csv` (polls hourly) | `batch_NN_full_results.csv` |
| `4_merge_full_output.py` | All `batch_*_full_results.csv` | `birth_detection_2_3M_GPT4o_full.csv` |
| `extract_2_3M_births.py` | `birth_detection_2_3M_GPT4o_full.csv` + `reddit_parenting_2_3M_sample.parquet` | `births_2_3M_sample.csv` |

---

### **Stage 3: Merge & Build Analysis File**

| Script | Input | Output |
|--------|-------|--------|
| `merge_births_and_posts.py` | `births_22k_sample.csv` + `reddit_22k_post_history_cleaned.csv` | `merged_22k_births_and_posts.csv` |
| `build_analysis_ready_file.py` | `merged_22k_births_and_posts.csv` | `births_and_posts_22k.csv` (adds `days_from_birth`, `months_from_birth`, etc.) |

---

### **Stage 4: Placebo Control**

| Script | Input | Output |
|--------|-------|--------|
| `build_matched_placebo_births_jul23.py` | `matched_authors_clean.csv` + `matched_placebo_birth_posts_clean.csv` + `births_and_posts_FULL.csv` | `matched_placebo_births.csv` |
| `build_placebo_post_history.py` | `matched_placebo_births.csv` + `matched_placebo_post_history_clean.csv` | `matched_placebo_births_posts.csv` |
| `stack_treatment_control.py` | `births_and_posts_FULL.csv` + `matched_placebo_births_posts.csv` + `matched_authors_clean.csv` | `treatment_control_births_posts.csv` |

`build_matched_placebo_births_jul23.py` assigns each placebo author the same `days_from` as their matched treatment author (looked up from `births_and_posts_FULL.csv`), then computes `date_birth` from the placebo birth post's `created_utc` minus that `days_from`. `stack_treatment_control.py` restricts the treatment group to authors who have a matched placebo pair before stacking.

---

## Final Analysis-Ready Datasets

### `final/births_and_posts_FULL.csv` — Treatment Group
**Structure:** One row per post, with time-relative-to-birth variables
**Key variables:** `date_birth`, `days_from_birth`, `months_from_birth`, `full_18_pre`, `one_year_pre`, `full_18_post`, `female`, `treated`

### `final/treatment_control_births_posts.csv` — Combined Treatment + Control ⭐ PRIMARY
**Structure:** Treatment group stacked with matched placebo controls (one treatment author per placebo author)
**Key variable:** `treated` (1 = confirmed Reddit birth poster, 0 = matched control)

---

## Color Key (Diagram)

| Color | Meaning |
|-------|---------|
| Blue | Raw input files |
| Green | Cleaned / intermediate data |
| Orange | LLM detection outputs |
| Pink | LLM pipeline batch files |
| Yellow | Extracted birth samples |
| Purple | Final analysis-ready files |

---

**Last Updated:** 2026-04-13
**Project Directory:** `D:/TwitterBirth/Reddit/`
