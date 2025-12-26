# Media Usage Ratio vs Quiz Score Analysis

Generated: 2025-12-26 01:31:22

Data source: merged_all.csv, reading_summary.csv, quizzes.csv

---

## 1. Descriptive Statistics

### 1.1 Sample Sizes

- **without_llm**: N = 96
- **with_llm**: N = 98
- **with_llm_extended**: N = 101

### 1.2 Reading Ratio by Condition

| Condition | N | Mean | SD | Min | Max |
|-----------|---|------|----:|----:|----:|
| without_llm | 96 | 100.0% | 0.0% | 100.0% | 100.0% |
| with_llm | 98 | 71.5% | 27.9% | 1.5% | 100.0% |
| with_llm_extended | 101 | 53.7% | 30.8% | 0.9% | 100.0% |

### 1.3 Quiz Accuracy by Condition

| Condition | N | Mean | SD | Min | Max |
|-----------|---|------|----:|----:|----:|
| without_llm | 96 | 78.9% | 22.2% | 11.1% | 100.0% |
| with_llm | 98 | 81.1% | 18.8% | 22.2% | 100.0% |
| with_llm_extended | 101 | 79.9% | 19.7% | 0.0% | 100.0% |

### 1.4 Media Ratio Distribution (with_llm_extended)

| Media | N | Mean | SD | Min | Max |
|-------|---|------|----:|----:|----:|
| Reading | 101 | 53.7% | 30.8% | 0.9% | 100.0% |
| Chat | 101 | 28.2% | 28.9% | 0.0% | 96.0% |
| Video | 101 | 7.1% | 11.1% | 0.0% | 69.0% |
| Audio | 101 | 6.6% | 12.1% | 0.0% | 63.8% |
| Infographics | 101 | 4.4% | 9.9% | 0.0% | 67.5% |

---

## 2. Reading Ratio vs Quiz Score Correlation

Pearson and Spearman correlation between reading time ratio and quiz accuracy.

### 2.1 Correlation by Condition

| Condition | N | Pearson r | p-value | Spearman ρ | p-value | Interpretation |
|-----------|---|-----------|---------|------------|---------|----------------|
| without_llm | 96 | N/A | N/A | N/A | N/A | - |
| with_llm | 98 | -0.139 | 0.1689 | -0.175 | 0.0815 | weak |
| with_llm_extended | 101 | 0.026 | 0.7945 | -0.069 | 0.4920 | negligible |

*Significance: \* p<0.05, \*\* p<0.01, \*\*\* p<0.001*

### 2.2 Simple Linear Regression: Reading Ratio → Quiz Score

| Condition | N | Slope (β) | SE | t | p-value | R² |
|-----------|---|-----------|----:|---:|---------|----:|
| without_llm | 96 | N/A | N/A | N/A | N/A | N/A |
| with_llm | 98 | -0.0934 | 0.0679 | -1.38 | 0.1689 | 0.0193 |
| with_llm_extended | 101 | 0.0167 | 0.0642 | 0.26 | 0.7945 | 0.0007 |

*Interpretation: For each 1% increase in reading ratio, quiz score changes by β percentage points.*

---

## 3. Media Ratio vs Quiz Score Correlation (with_llm_extended)

Correlation between each media type's time ratio and quiz accuracy.

### 3.1 Correlation Matrix

| Media | N | Pearson r | p-value | Spearman ρ | p-value | Interpretation |
|-------|---|-----------|---------|------------|---------|----------------|
| Reading | 101 | 0.026 | 0.7945 | -0.069 | 0.4920 | negligible |
| Chat | 101 | -0.105 | 0.2920 | 0.014 | 0.8860 | weak |
| Video | 101 | -0.038 | 0.7037 | 0.109 | 0.2761 | negligible |
| Audio | 101 | 0.163 | 0.1011 | 0.089 | 0.3716 | weak |
| Infographics | 101 | 0.071 | 0.4811 | 0.164 | 0.0983 | negligible |

*Significance: \* p<0.05, \*\* p<0.01, \*\*\* p<0.001*

### 3.2 Simple Linear Regression for Each Media

| Media | N | Slope (β) | SE | t | p-value | R² |
|-------|---|-----------|----:|---:|---------|----:|
| Reading | 101 | 0.0167 | 0.0642 | 0.26 | 0.7945 | 0.0007 |
| Chat | 101 | -0.0716 | 0.0679 | -1.05 | 0.2920 | 0.0111 |
| Video | 101 | -0.0674 | 0.1772 | -0.38 | 0.7037 | 0.0015 |
| Audio | 101 | 0.2643 | 0.1612 | 1.64 | 0.1011 | 0.0264 |
| Infographics | 101 | 0.1402 | 0.1990 | 0.70 | 0.4811 | 0.0050 |

---

## 4. Multiple Regression Analysis (with_llm_extended)

Predicting quiz score from multiple media ratios.

**Note:** Since ratios sum to 100%, one variable must be excluded to avoid perfect multicollinearity. Infographics ratio is excluded as the reference category.

### 4.1 Model Summary

- **N**: 101
- **R²**: 0.0429
- **Adjusted R²**: 0.0030
- **MSE**: 385.7177

### 4.2 Coefficients

| Variable | Coefficient (β) |
|----------|----------------:|
| Intercept | 94.3778 |
| Reading Ratio | -0.1443 |
| Chat Ratio | -0.1918 |
| Video Ratio | -0.3070 |
| Audio Ratio | 0.1246 |

*Interpretation: Coefficients represent the change in quiz score for a 1% increase in that media's ratio, holding other ratios constant (relative to infographics).*

---

## 5. Summary

### Key Findings

**1. Reading Ratio vs Quiz Score:**

- **with_llm**: r = -0.139 (weak negative), p = 0.1689 (not significant)
- **with_llm_extended**: r = 0.026 (negligible positive), p = 0.7945 (not significant)

**2. Media Ratios vs Quiz Score (with_llm_extended):**

- **Reading**: r = 0.026 (negligible positive), p = 0.7945 (not significant)
- **Chat**: r = -0.105 (weak negative), p = 0.2920 (not significant)
- **Video**: r = -0.038 (negligible negative), p = 0.7037 (not significant)
- **Audio**: r = 0.163 (weak positive), p = 0.1011 (not significant)
- **Infographics**: r = 0.071 (negligible positive), p = 0.4811 (not significant)
