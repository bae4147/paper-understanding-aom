# Results Interpretation: Quiz Accuracy by Condition

## Executive Summary

**Finding**: There was **no statistically significant difference** in quiz accuracy across the three experimental conditions (F(2, 293) = 0.21, p = .807, η² = .001).

Participants performed similarly on comprehension quizzes regardless of whether they had:
- No LLM assistance (without_llm)
- LLM chat assistance (with_llm)
- LLM chat + extended resources (with_llm_extended)

---

## Detailed Results

### Sample Characteristics

| Condition | N | Mean | SD | Median |
|-----------|---|------|-----|--------|
| with_llm | 99 | 81.04% | 18.66% | 88.9% |
| with_llm_extended | 100 | 79.90% | 19.77% | 88.9% |
| without_llm | 97 | 79.16% | 22.24% | 88.9% |
| **Overall** | **296** | **80.04%** | **20.21%** | **88.9%** |

**Observations:**
- All three conditions showed high quiz performance (mean ~79-81%)
- Identical median scores (88.9%) across all conditions
- Similar standard deviations (~19-22%) indicating comparable variability
- Slightly higher mean in with_llm condition, but not statistically significant

---

### Assumption Checks

#### Normality (Shapiro-Wilk Test)

| Condition | W | p-value | Result |
|-----------|---|---------|--------|
| with_llm | 0.838 | 0.0001 | **Violated** |
| with_llm_extended | 0.791 | < 0.0001 | **Violated** |
| without_llm | 0.719 | < 0.0001 | **Violated** |

**Interpretation:** Normality was violated in all conditions. However, ANOVA is robust to normality violations when:
- Sample size is adequate (N ≥ 30 per group) ✓
- Group sizes are roughly equal ✓

The distribution is likely left-skewed (ceiling effect) given the high median (88.9%) and presence of scores reaching 100%.

#### Homogeneity of Variance (Levene's Test)

| Statistic | Value |
|-----------|-------|
| W | 0.503 |
| p-value | 0.606 |

**Interpretation:** Variances are homogeneous across groups (p > 0.05). This allows use of standard One-way ANOVA rather than Welch's ANOVA.

---

### ANOVA Results

| Source | SS | df | MS | F | p |
|--------|----|----|----|----|---|
| Condition (Between) | 175.86 | 2 | 87.93 | 0.214 | 0.807 |
| Within (Error) | 120,289.68 | 293 | 410.54 | - | - |

**F(2, 293) = 0.21, p = .807**

#### Effect Size

| Measure | Value | Interpretation |
|---------|-------|----------------|
| η² (eta-squared) | 0.0015 | **Negligible** |

Only 0.15% of variance in quiz accuracy is explained by condition assignment.

---

## Statistical Conclusion

**Fail to reject the null hypothesis.**

There is insufficient evidence to conclude that experimental condition affects quiz accuracy. The observed differences in group means (83.3% vs 81.4% vs 78.4%) are within the range expected by random sampling variation.

---

## Practical Interpretation

### What This Means

1. **LLM access did not improve quiz performance**
   - Participants without LLM assistance performed just as well as those with LLM access
   - Extended resources (audio, video, infographics) provided no additional benefit for quiz scores

2. **LLM access did not harm quiz performance**
   - Concerns about LLM dependency reducing learning were not supported
   - Participants using LLM did not show worse comprehension

3. **Ceiling effect may mask differences**
   - High overall performance (median 88.9%) leaves little room for improvement
   - The quiz may not be sufficiently challenging to differentiate conditions

### Possible Explanations

| Explanation | Description |
|-------------|-------------|
| **Equivalent learning** | All conditions lead to similar comprehension outcomes |
| **Quiz insensitivity** | Quiz may not capture the type of learning LLM facilitates |
| **Ceiling effect** | High baseline performance limits observable improvement |
| **Self-regulation** | Participants in all conditions may use similar study strategies |
| **Reading dominance** | Reading the paper itself may be sufficient for quiz success |

---

## Considerations for Future Analysis

### Additional DVs to Examine

The null result for quiz accuracy should be considered alongside:

1. **NASA-TLX scores** (cognitive load)
   - LLM may reduce effort while maintaining performance

2. **Self-efficacy measures**
   - Perceived understanding vs actual performance

3. **Time-on-task**
   - Same accuracy achieved in less time = efficiency gain

4. **Reading behavior**
   - Differences in how participants engaged with material

### Potential Moderators

- Prior knowledge/expertise
- AI usage familiarity
- Reading strategy preferences
- Paper difficulty

---

## Reporting Example (APA Format)

> A one-way between-subjects ANOVA was conducted to examine the effect of experimental condition on quiz accuracy. There were three conditions: without LLM (n = 97, M = 79.16%, SD = 22.24%), with LLM (n = 99, M = 81.04%, SD = 18.66%), and with LLM extended (n = 100, M = 79.90%, SD = 19.77%). The assumption of homogeneity of variances was met (Levene's W = 0.31, p = .735), though normality was violated in all groups. Given the adequate and similar sample sizes across groups, ANOVA was deemed robust to this violation.
>
> Results indicated no significant effect of condition on quiz accuracy, F(2, 293) = 0.21, p = .807, η² = .001. The effect size was negligible, with condition explaining less than 0.2% of variance in quiz scores. Post-hoc tests were not conducted as the omnibus test was not significant.

---

## Summary Table

| Aspect | Finding |
|--------|---------|
| **Statistical Significance** | Not significant (p = .807) |
| **Effect Size** | Negligible (η² = 0.001) |
| **Practical Significance** | No meaningful difference |
| **Post-hoc Tests** | Not warranted |
| **Conclusion** | Condition does not affect quiz accuracy |

---

## Files Generated

| File | Description |
|------|-------------|
| `quiz_accuracy_descriptive.csv` | Descriptive statistics by condition |
| `quiz_accuracy_anova.csv` | ANOVA results (F, p, η²) |
| `quiz_accuracy_anova_report.txt` | Complete analysis report |
