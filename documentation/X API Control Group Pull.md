# X API Control Group Pull

**Goal:** Collect panel data for ~8,000 "average" Twitter users as a control group against parents in the treatment group. Collect a snapshot of who the users are, plus a 3-year daily posting history centered on a sampled tweet from 2013–2018 matching the distribution of births in the treatment group.

---

## Pipeline Overview

| Phase | Description |
|-------|-------------|
| **Phase 1** | Pull 20k seed tweets (2013–18) via weighted time-window sampling for a placebo birth date |
| **Phase 1b** | Manual spot check of 100 randomly sampled seed tweets |
| **Phase 2** | Pull user profiles for all 20k users + apply filters |
| **Phase 2b** | Checkpoint — confirm data similarity to treatment group |
| **Phase 3** | Pull daily post counts over 3-year windows for surviving users |

---

## Phase 1 — Seed Tweet Collection

**Endpoint:** `GET /2/tweets/search/all` ([docs](https://docs.x.com/x-api/posts/search/introduction))

**Per-tweet fields collected:** `tweet_id`, `author_id`, `created_at`

**Query filters:**
- `-is:retweet -is:reply lang:en`
- `sort_order: recency`

### Sampling Strategy

- Divide the 5-year period into **260 weekly windows**
- Query one **1-hour window per week**
- Hour drawn randomly from the day-of-week × hour-of-day distribution of the treatment sample (168 buckets, e.g., Mon 8am … Sun 11pm)
- Yearly allocation proportional to the treatment sample's yearly distribution

### Per-Week Query Logic

1. Draw a weighted random day-hour from the treatment timestamp distribution
2. `week_start` = Monday of that week (e.g., `2013-01-07 00:00:00 UTC`)
3. `start_time` = `week_start` + chosen hour
4. `end_time` = `start_time` + 1 hour
5. Pull up to `[week's target N]` tweets from that window
6. Deduplicate on `author_id` → add to candidate pool

**Cost:** ~260 API calls ≈ $1

---

## Phase 1b — Manual Spot Check

Randomly sample **100 seed tweets** from the full 20k candidate pool and manually confirm tweets appear organic (not bots or advertisements). Re-sample if needed.

---

## Phase 2 — User Profile Lookup + Filtering

**Endpoint:** `GET /2/users` (batch, 100 users/request) ([docs](https://docs.x.com/x-api/fundamentals/rate-limits))

**Fields pulled per user:** `username`, `description`, `created_at`, `public_metrics.followers_count`, `public_metrics.following_count`, `public_metrics.tweet_count`, `verified`

### Filters

| Filter | Rule | Rationale |
|--------|------|-----------|
| **Filter A** — Pre-period validity | Drop if `seed_tweet_date − account_created_date < 18 months` | Ensures a full pre-window |
| **Filter B** — High-volume filter | Drop if `lifetime_tweet_count / account_age_in_weeks > 403` | Removes bots and power users |

> **Threshold note:** 403/week derived from the winsorized max avg weekly post rate in the treatment sample (1,610.889 monthly posts ÷ 4 ≈ 402.7 → 403)

**Target:** Retain at least ~8k users

**Estimated API calls:** 200 (100 users/request × 20k users)  
**Cost:** $200 ($0.010/user × 20k users)

---

## Phase 2b — Account Stats Checkpoint

Review filtered user profile data to confirm it matches the treatment sample distributions:

- [ ] Distribution of seed tweet dates across 2013–2018
- [ ] Distribution of account creation dates
- [ ] Distribution of average weekly post rates — validate the 403/week cutoff
- [ ] Follower/following distributions
- [ ] Surviving user count ≥ ~8k (if not, return to Phase 1 and expand candidate pool)
- [ ] Spot-check a handful of user profiles manually

> Phase 3 takes the surviving list from this checkpoint. Can manually trim here if needed.

---

## Phase 3 — Daily Post Volume (3-Year Panel)

**Endpoint:** `GET /2/tweets/counts/all` ([docs](https://docs.x.com/x-api/fundamentals/rate-limits))

**Output:** Daily count time series per user — 18 months before seed tweet through 18 months after. Returns `{ date, count }` for every day, including 0s on days with no posts.

**Two calls per user to separate post types:**

| Call | Query | Output Column |
|------|-------|---------------|
| Call A | `from:{user_id} -is:retweet -is:reply` | `original_quote_count` |
| Call B | `from:{user_id} (is:retweet OR is:reply)` | `retweet_reply_count` |

**Parameters per call:**
- `granularity=day`
- `start_time` = seed tweet date − 18 months
- `end_time` = seed tweet date + 18 months

**Estimated API calls:** ~16,000 (2 calls × ~8k–20k users, depending on Phase 2b)  
**Cost:** $160–400 ($0.010/request × 2 calls × 8k–20k users)

> **Parallelization note:** Rate limit is 300 requests/15 min; 16k–40k requests ≈ 14–28 hours. Parallelize across multiple API keys or use async batching to stay within rate limits.

---

## Cost Summary

| Phase | Endpoint | Requests | Cost |
|-------|----------|----------|------|
| Seed Tweets | `tweets/search/all` | ~260 | ~$1 |
| User Profiles | `users` (batch) | 200 | $200 |
| Daily Counts/Volume | `tweets/counts/all` | 16,000–40,000 | $160–400 |
| **Total** | | | **$360–600** |