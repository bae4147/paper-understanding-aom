# LLM Usage Analysis Report

Generated: 2025-12-26 01:24:21

Data source: merged_all.csv, reading_events.csv, llm_messages.csv

Note: Media times (Video, Audio, Infographics) are calculated from focus_switch/resource_tab_switch events.

---

## 1. Media Usage Time Comparison

Time spent on each media type during the reading session (in seconds).

### 1.1 with_llm Condition

N = 98

| Media | N | Mean | SD | Min | Max |
|-------|---|------|----:|----:|----:|
| Reading (Paper) | 98 | 1285.3s | 2129.1s | 19.5s | 21587.6s |
| Chat/LLM | 98 | 463.0s | 554.9s | 0.0s | 3643.3s |

### 1.2 with_llm_extended Condition

N = 101

| Media | N | Mean | SD | Min | Max |
|-------|---|------|----:|----:|----:|
| Reading (Paper) | 101 | 773.9s | 436.8s | 11.6s | 1620.1s |
| Chat/LLM | 101 | 423.9s | 455.4s | 0.0s | 2042.9s |
| Video | 101 | 100.9s | 161.8s | 0.0s | 998.5s |
| Audio | 101 | 96.5s | 185.6s | 0.0s | 1217.1s |
| Infographics | 101 | 70.3s | 184.9s | 0.0s | 1254.6s |

### 1.3 Extended Media Usage (with_llm_extended)

Participants who used each extended media type:

- **Video**: 62/101 (61.4%) used it, avg 164.3s among users
- **Audio**: 61/101 (60.4%) used it, avg 159.8s among users
- **Infographics**: 71/101 (70.3%) used it, avg 100.0s among users

### 1.4 Comparison Summary

| Condition | N | Reading (Mean) | Chat/LLM (Mean) | Video | Audio | Infographics |
|-----------|---|---------------:|----------------:|------:|------:|-------------:|
| with_llm | 98 | 1285.3s | 463.0s | - | - | - |
| with_llm_extended | 101 | 773.9s | 423.9s | 100.9s | 96.5s | 70.3s |

---

## 2. LLM Query Statistics

Number of queries sent to the LLM during the reading session (from llm_messages.csv).

### 2.1 Query Count by Condition

| Condition | N | Mean | SD | Median | Min | Max |
|-----------|---|------|----:|-------:|----:|----:|
| with_llm | 98 | 2.15 | 3.08 | 1.0 | 0 | 14 |
| with_llm_extended | 101 | 3.08 | 6.30 | 1.0 | 0 | 37 |

### 2.2 Query Count Distribution

#### with_llm

| Queries | Count | Percentage |
|--------:|------:|-----------:|
| 0 | 46 | 46.9% |
| 1 | 12 | 12.2% |
| 2 | 10 | 10.2% |
| 3 | 6 | 6.1% |
| 4 | 5 | 5.1% |
| 5 | 7 | 7.1% |
| 6 | 1 | 1.0% |
| 7 | 5 | 5.1% |
| 8 | 1 | 1.0% |
| 9 | 1 | 1.0% |
| 10 | 1 | 1.0% |
| 11 | 1 | 1.0% |
| 13 | 1 | 1.0% |
| 14 | 1 | 1.0% |

#### with_llm_extended

| Queries | Count | Percentage |
|--------:|------:|-----------:|
| 0 | 36 | 35.6% |
| 1 | 21 | 20.8% |
| 2 | 17 | 16.8% |
| 3 | 6 | 5.9% |
| 4 | 5 | 5.0% |
| 5 | 2 | 2.0% |
| 6 | 4 | 4.0% |
| 7 | 1 | 1.0% |
| 9 | 1 | 1.0% |
| 10 | 1 | 1.0% |
| 11 | 1 | 1.0% |
| 13 | 2 | 2.0% |
| 22 | 1 | 1.0% |
| 26 | 1 | 1.0% |
| 36 | 1 | 1.0% |
| 37 | 1 | 1.0% |

---

## 3. Summary

### Key Findings

**1. Media Usage Time:**

- **with_llm** (N=98): Reading 1285.3s, Chat/LLM 463.0s
- **with_llm_extended** (N=101): Reading 773.9s, Chat/LLM 423.9s, Video 100.9s, Audio 96.5s, Infographics 70.3s

**with_llm_extended Time Allocation:**
- Reading: 52.8%
- Chat/LLM: 28.9%
- Video: 6.9%
- Audio: 6.6%
- Infographics: 4.8%

**2. LLM Query Count:**

- **with_llm**: Mean 2.15 queries (SD = 3.08, Median = 1.0)
- **with_llm_extended**: Mean 3.08 queries (SD = 6.30, Median = 1.0)
- with_llm_extended participants sent 43.0% more queries on average
