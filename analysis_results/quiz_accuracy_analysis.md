# Quiz Accuracy Analysis Report

Generated: 2025-12-23 19:17:32

---

## 1. Descriptive Statistics

### Method

Descriptive statistics (Mean, SD, Variance, SE, Min, Max) were calculated for:
- **Overall accuracy**: All 9 questions (Q1-Q9)
- **Low complexity accuracy**: Q1-Q3 (basic comprehension)
- **Medium complexity accuracy**: Q4-Q6 (application)
- **High complexity accuracy**: Q7-Q9 (synthesis/evaluation)

### 1.1 Overall Results (N=295)

| Measure | N | Mean | SD | Variance | SE | Min | Max |
|---------|---|------|----|---------:|----:|----:|----:|
| Overall Accuracy | 295 | 79.97% | 20.21 | 408.39 | 1.18 | 0.0% | 100.0% |
| Low Complexity (Q1-3) | 295 | 86.33% | 22.62 | 511.48 | 1.32 | 0.0% | 100.0% |
| Medium Complexity (Q4-6) | 295 | 83.06% | 25.18 | 633.86 | 1.47 | 0.0% | 100.0% |
| High Complexity (Q7-9) | 295 | 70.51% | 30.87 | 953.06 | 1.80 | 0.0% | 100.0% |

### 1.2 Results by Condition

#### Overall Accuracy

| Condition | N | Mean | SD | Variance | SE |
|-----------|---|------|----|---------:|----:|
| Without Llm | 96 | 78.95% | 22.25 | 495.01 | 2.27 |
| With Llm | 98 | 81.08% | 18.76 | 351.85 | 1.89 |
| With Llm Extended | 101 | 79.88% | 19.67 | 386.89 | 1.96 |

#### Low Complexity (Q1-3)

| Condition | N | Mean | SD | Variance | SE |
|-----------|---|------|----|---------:|----:|
| Without Llm | 96 | 87.85% | 21.69 | 470.57 | 2.21 |
| With Llm | 98 | 85.04% | 23.01 | 529.55 | 2.32 |
| With Llm Extended | 101 | 86.14% | 23.22 | 539.17 | 2.31 |

#### Medium Complexity (Q4-6)

| Condition | N | Mean | SD | Variance | SE |
|-----------|---|------|----|---------:|----:|
| Without Llm | 96 | 81.26% | 28.53 | 814.23 | 2.91 |
| With Llm | 98 | 85.38% | 21.97 | 482.62 | 2.22 |
| With Llm Extended | 101 | 82.51% | 24.76 | 613.19 | 2.46 |

#### High Complexity (Q7-9)

| Condition | N | Mean | SD | Variance | SE |
|-----------|---|------|----|---------:|----:|
| Without Llm | 96 | 67.71% | 32.97 | 1086.96 | 3.36 |
| With Llm | 98 | 72.79% | 28.86 | 833.10 | 2.92 |
| With Llm Extended | 101 | 70.96% | 30.80 | 948.46 | 3.06 |

---

## 2. One-way ANOVA Analysis

### Method

One-way Analysis of Variance (ANOVA) was conducted to examine whether quiz accuracy
differs significantly across the three experimental conditions:
- **without_llm**: Control group (no LLM assistance)
- **with_llm**: LLM assistance available
- **with_llm_extended**: Extended LLM assistance available

**Hypotheses:**
- H0: mu1 = mu2 = mu3 (No difference in accuracy across conditions)
- H1: At least one group mean differs

**Effect size:** Eta-squared (eta^2) was calculated to determine practical significance.
- eta^2 < 0.01: negligible
- 0.01 <= eta^2 < 0.06: small
- 0.06 <= eta^2 < 0.14: medium
- eta^2 >= 0.14: large

### 2.1 ANOVA Results

| Measure | F(2, 292) | p-value | eta^2 | Effect Size | Significant (alpha=.05) |
|---------|-----------|---------|------:|-------------|-------------------------|
| Overall Accuracy | 0.269 | .5591 | 0.0018 | negligible | No |
| Low Complexity (Q1-3) | 0.378 | .4271 | 0.0026 | negligible | No |
| Medium Complexity (Q4-6) | 0.684 | .1613 | 0.0047 | negligible | No |
| High Complexity (Q7-9) | 0.671 | .1700 | 0.0046 | negligible | No |

*Note: Significance level alpha = 0.05*

### 2.2 Detailed ANOVA Summary

#### Overall Accuracy

| Source | SS | df | MS | F | p |
|--------|----:|---:|----:|---:|---:|
| Between Groups | 221.07 | 2 | 110.53 | 0.269 | .5591 |
| Within Groups | 119844.81 | 292 | 410.43 | | |
| Total | 120065.88 | 294 | | | |

#### Low Complexity (Q1-3)

| Source | SS | df | MS | F | p |
|--------|----:|---:|----:|---:|---:|
| Between Groups | 388.49 | 2 | 194.25 | 0.378 | .4271 |
| Within Groups | 149987.83 | 292 | 513.66 | | |
| Total | 150376.32 | 294 | | | |

#### Medium Complexity (Q4-6)

| Source | SS | df | MS | F | p |
|--------|----:|---:|----:|---:|---:|
| Between Groups | 869.28 | 2 | 434.64 | 0.684 | .1613 |
| Within Groups | 185485.02 | 292 | 635.22 | | |
| Total | 186354.30 | 294 | | | |

#### High Complexity (Q7-9)

| Source | SS | df | MS | F | p |
|--------|----:|---:|----:|---:|---:|
| Between Groups | 1281.47 | 2 | 640.74 | 0.671 | .1700 |
| Within Groups | 278918.32 | 292 | 955.20 | | |
| Total | 280199.80 | 294 | | | |

---

## 3. Summary and Interpretation

### Key Findings

1. **Overall Performance**: Participants achieved an average accuracy of 80.0% (SD = 20.2) across all quiz questions.

2. **Difficulty Gradient**: As expected, accuracy decreased with question complexity:
   - Low complexity: 86.3%
   - Medium complexity: 83.1%
   - High complexity: 70.5%

3. **Condition Effects (ANOVA Results)**:

   All ANOVA tests showed **no significant differences** across conditions (all F < 1.0, p > .05).
   Effect sizes (eta^2) were negligible (< 0.01) for all measures.

   - **Overall Accuracy**: F(2, 292) = 0.269, p = .559, eta^2 = 0.002
   - **Low Complexity (Q1-3)**: F(2, 292) = 0.378, p = .427, eta^2 = 0.003
   - **Medium Complexity (Q4-6)**: F(2, 292) = 0.684, p = .161, eta^2 = 0.005
   - **High Complexity (Q7-9)**: F(2, 292) = 0.671, p = .170, eta^2 = 0.005

4. **Conclusion**: LLM condition did not significantly affect quiz accuracy at any complexity level.
   The experimental manipulation (LLM access) did not lead to meaningful differences in comprehension performance.

### Condition Comparison

| Condition | Overall | Low | Medium | High |
|-----------|---------|-----|--------|------|
| Without Llm | 78.9% | 87.9% | 81.3% | 67.7% |
| With Llm | 81.1% | 85.0% | 85.4% | 72.8% |
| With Llm Extended | 79.9% | 86.1% | 82.5% | 71.0% |
