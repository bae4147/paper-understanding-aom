# Statistical Methodology: Quiz Accuracy Analysis

## Research Question

**RQ**: Is there a significant difference in quiz accuracy across experimental conditions (without_llm, with_llm, with_llm_extended)?

---

## Analysis Design

### Variables

| Variable | Type | Description |
|----------|------|-------------|
| **IV (Independent Variable)** | Categorical, 3 levels | Condition (without_llm, with_llm, with_llm_extended) |
| **DV (Dependent Variable)** | Continuous (0-1 scale) | Quiz Accuracy (correct answers / total questions) |

### Design Type

- **Between-subjects design**: Each participant is assigned to only one condition
- **One-way ANOVA**: Comparing means across 3 independent groups

---

## Statistical Method: One-way ANOVA

### Why One-way ANOVA?

One-way ANOVA (Analysis of Variance) was chosen for the following reasons:

1. **Three or more groups**: We have 3 experimental conditions to compare. While a t-test works for 2 groups, ANOVA is the appropriate extension for 3+ groups.

2. **Single independent variable**: We have one IV (condition) with multiple levels, making one-way ANOVA the correct choice over factorial ANOVA.

3. **Continuous dependent variable**: Quiz accuracy is measured on a continuous scale (0-1), satisfying ANOVA's requirement for a quantitative DV.

4. **Between-subjects comparison**: Different participants in each condition, not repeated measures from the same participants.

5. **Controls Type I error**: Using multiple t-tests would inflate Type I error rate. With 3 groups, we'd need 3 comparisons, increasing the chance of false positives. ANOVA performs an omnibus test first.

### Assumptions

ANOVA requires three key assumptions:

| Assumption | Test Used | Rationale |
|------------|-----------|-----------|
| **Independence** | Study design | Participants are independently assigned to conditions |
| **Normality** | Shapiro-Wilk test | Distribution of DV within each group should be approximately normal |
| **Homogeneity of Variance** | Levene's test | Variances should be equal across groups |

---

## Assumption Testing

### 1. Normality (Shapiro-Wilk Test)

**Why Shapiro-Wilk?**
- Most powerful test for normality with sample sizes < 50 per group
- Tests the null hypothesis that data comes from a normal distribution
- Significance (p < 0.05) indicates deviation from normality

**Interpretation:**
- If normality is violated, ANOVA is still robust with:
  - Sufficient sample size (n > 30 per group)
  - Approximately equal group sizes
- Alternative: Kruskal-Wallis H test (non-parametric equivalent)

### 2. Homogeneity of Variance (Levene's Test)

**Why Levene's Test?**
- Tests equality of variances across groups
- More robust than Bartlett's test when normality is violated
- Uses median (more robust) or mean to calculate deviations

**Interpretation:**
- If homogeneity is violated (p < 0.05): Use Welch's ANOVA
- Welch's ANOVA does not assume equal variances and is more robust

---

## ANOVA Procedure

### Standard One-way ANOVA (if assumptions met)

Partitions total variance into:
- **Between-group variance (SSB)**: Variance due to condition differences
- **Within-group variance (SSW)**: Variance within each condition (error)

**F-statistic** = MSB / MSW = (SSB/dfB) / (SSW/dfW)

### Welch's ANOVA (if homogeneity violated)

- Does not assume equal variances
- Uses weighted approach based on group sizes and variances
- More accurate Type I error rate when variances differ

---

## Effect Size: Eta-squared (η²)

**Why Eta-squared?**
- Measures proportion of total variance explained by condition
- Intuitive interpretation: percentage of DV variance attributable to IV
- Standard effect size measure for ANOVA

**Interpretation Guidelines (Cohen, 1988):**

| η² Value | Interpretation |
|----------|----------------|
| ≈ 0.01 | Small effect |
| ≈ 0.06 | Medium effect |
| ≈ 0.14 | Large effect |

**Calculation:**
η² = SSbetween / SStotal

---

## Post-hoc Analysis: Tukey's HSD

### When to Use

Post-hoc tests are performed **only if ANOVA is significant** (p < 0.05), indicating at least one group mean differs.

### Why Tukey's HSD?

1. **Controls familywise error rate**: Adjusts for multiple comparisons
2. **All pairwise comparisons**: Tests all possible pairs simultaneously
3. **Equal sample sizes**: Works well with balanced or slightly unbalanced designs
4. **Widely accepted**: Standard in psychological research

**Alternatives considered:**
- Bonferroni: More conservative, good for few comparisons
- Games-Howell: For unequal variances (if Welch ANOVA used)
- Scheffé: More conservative, allows complex contrasts

---

## Interpretation Guidelines

### Significance Level

- α = 0.05 (standard in psychological research)
- p < 0.05: Reject null hypothesis, significant difference exists
- p ≥ 0.05: Fail to reject null, no significant difference detected

### Reporting Standards (APA 7th Edition)

**ANOVA result:**
> F(df_between, df_within) = F-value, p = p-value, η² = effect-size

**Example:**
> F(2, 117) = 0.50, p = .609, η² = .008

---

## Limitations

1. **ANOVA tells us IF groups differ, not WHICH ones** → Need post-hoc tests
2. **Effect size is descriptive, not inferential** → Report both p and η²
3. **Non-significant result ≠ no effect** → Could be low power
4. **Assumes linear relationship** → May miss non-linear patterns

---

## Software and Packages Used

- **Python 3.x**
- **pandas**: Data manipulation
- **scipy.stats**: Shapiro-Wilk, Levene's test, basic ANOVA
- **pingouin**: Detailed ANOVA, Welch ANOVA, post-hoc tests, effect sizes

---

## References

- Cohen, J. (1988). *Statistical power analysis for the behavioral sciences* (2nd ed.). Lawrence Erlbaum Associates.
- Field, A. (2013). *Discovering statistics using IBM SPSS statistics* (4th ed.). Sage.
- Vallat, R. (2018). Pingouin: statistics in Python. *Journal of Open Source Software*, 3(31), 1026.
