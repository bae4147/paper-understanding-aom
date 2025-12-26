#!/usr/bin/env python3
"""
Quiz Accuracy Analysis
1. Descriptive statistics (mean, variance, SD) for overall and by difficulty level
2. One-way ANOVA comparing quiz accuracy across conditions
"""

import csv
import os
import math
from collections import defaultdict
from datetime import datetime

# Try to import scipy for ANOVA, fall back to manual calculation if not available
try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def load_csv(filepath):
    """Load CSV file and return list of dictionaries"""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


def safe_float(value):
    """Safely convert value to float"""
    if value is None or value == '' or value == 'None':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def calculate_stats(values):
    """Calculate descriptive statistics"""
    valid = [v for v in values if v is not None]
    n = len(valid)
    if n == 0:
        return {'n': 0, 'mean': None, 'variance': None, 'sd': None, 'se': None, 'min': None, 'max': None}

    mean = sum(valid) / n
    if n > 1:
        variance = sum((x - mean) ** 2 for x in valid) / (n - 1)  # Sample variance
        sd = math.sqrt(variance)
        se = sd / math.sqrt(n)
    else:
        variance = 0
        sd = 0
        se = 0

    return {
        'n': n,
        'mean': mean,
        'variance': variance,
        'sd': sd,
        'se': se,
        'min': min(valid),
        'max': max(valid)
    }


def one_way_anova(*groups):
    """
    Perform one-way ANOVA
    Returns F-statistic and p-value
    """
    if HAS_SCIPY:
        # Use scipy for accurate p-value calculation
        f_stat, p_value = scipy_stats.f_oneway(*groups)
        return f_stat, p_value
    else:
        # Manual calculation (F-statistic only, approximate p-value)
        k = len(groups)  # Number of groups
        n_total = sum(len(g) for g in groups)

        # Grand mean
        all_values = [v for g in groups for v in g]
        grand_mean = sum(all_values) / len(all_values)

        # Between-group sum of squares (SSB)
        ssb = sum(len(g) * (sum(g)/len(g) - grand_mean)**2 for g in groups)

        # Within-group sum of squares (SSW)
        ssw = sum(sum((x - sum(g)/len(g))**2 for x in g) for g in groups)

        # Degrees of freedom
        df_between = k - 1
        df_within = n_total - k

        # Mean squares
        msb = ssb / df_between
        msw = ssw / df_within

        # F-statistic
        f_stat = msb / msw if msw > 0 else 0

        # Approximate p-value (requires scipy for exact calculation)
        p_value = None  # Cannot calculate without scipy

        return f_stat, p_value


def calculate_eta_squared(groups):
    """Calculate eta-squared (effect size) for ANOVA"""
    all_values = [v for g in groups for v in g]
    grand_mean = sum(all_values) / len(all_values)

    # Total sum of squares (SST)
    sst = sum((x - grand_mean)**2 for x in all_values)

    # Between-group sum of squares (SSB)
    ssb = sum(len(g) * (sum(g)/len(g) - grand_mean)**2 for g in groups)

    # Eta-squared = SSB / SST
    eta_sq = ssb / sst if sst > 0 else 0

    return eta_sq


def interpret_eta_squared(eta_sq):
    """Interpret eta-squared effect size"""
    if eta_sq < 0.01:
        return "negligible"
    elif eta_sq < 0.06:
        return "small"
    elif eta_sq < 0.14:
        return "medium"
    else:
        return "large"


def main():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    output_dir = os.path.join(base_dir, 'analysis_results')
    os.makedirs(output_dir, exist_ok=True)

    # Load quiz data
    quizzes = load_csv(os.path.join(processed_dir, 'quizzes.csv'))

    # Prepare data
    conditions = ['without_llm', 'with_llm', 'with_llm_extended']

    # Collect accuracy data
    acc_overall = {'all': [], 'by_condition': defaultdict(list)}
    acc_low = {'all': [], 'by_condition': defaultdict(list)}
    acc_med = {'all': [], 'by_condition': defaultdict(list)}
    acc_high = {'all': [], 'by_condition': defaultdict(list)}

    # Per-question accuracy (Q1-Q9)
    acc_by_question = {f'Q{i}': {'all': [], 'by_condition': defaultdict(list)} for i in range(1, 10)}

    for row in quizzes:
        cond = row.get('condition')
        overall = safe_float(row.get('accuracy'))
        low = safe_float(row.get('acc_low'))
        med = safe_float(row.get('acc_med'))
        high = safe_float(row.get('acc_high'))

        if overall is not None:
            acc_overall['all'].append(overall)
            acc_overall['by_condition'][cond].append(overall)

        if low is not None:
            acc_low['all'].append(low)
            acc_low['by_condition'][cond].append(low)

        if med is not None:
            acc_med['all'].append(med)
            acc_med['by_condition'][cond].append(med)

        if high is not None:
            acc_high['all'].append(high)
            acc_high['by_condition'][cond].append(high)

        # Per-question accuracy (correct=1, incorrect=0)
        for i in range(1, 10):
            correct_val = row.get(f'correct_{i}', '')
            if correct_val == 'True':
                acc_by_question[f'Q{i}']['all'].append(100.0)
                acc_by_question[f'Q{i}']['by_condition'][cond].append(100.0)
            elif correct_val == 'False':
                acc_by_question[f'Q{i}']['all'].append(0.0)
                acc_by_question[f'Q{i}']['by_condition'][cond].append(0.0)

    # Generate report
    report = []
    report.append("# Quiz Accuracy Analysis Report")
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("---")
    report.append("")

    # ========================================
    # Part 1: Descriptive Statistics
    # ========================================
    report.append("## 1. Descriptive Statistics")
    report.append("")
    report.append("### Method")
    report.append("")
    report.append("Descriptive statistics (Mean, SD, Variance, SE, Min, Max) were calculated for:")
    report.append("- **Overall accuracy**: All 9 questions (Q1-Q9)")
    report.append("- **Low complexity accuracy**: Q1-Q3 (basic comprehension)")
    report.append("- **Medium complexity accuracy**: Q4-Q6 (application)")
    report.append("- **High complexity accuracy**: Q7-Q9 (synthesis/evaluation)")
    report.append("")

    # Overall descriptive stats
    report.append("### 1.1 Overall Results (N=295)")
    report.append("")
    report.append("| Measure | N | Mean | SD | Variance | SE | Min | Max |")
    report.append("|---------|---|------|----|---------:|----:|----:|----:|")

    measures = [
        ("Overall Accuracy", acc_overall['all']),
        ("Low Complexity (Q1-3)", acc_low['all']),
        ("Medium Complexity (Q4-6)", acc_med['all']),
        ("High Complexity (Q7-9)", acc_high['all'])
    ]

    for name, data in measures:
        stats = calculate_stats(data)
        report.append(f"| {name} | {stats['n']} | {stats['mean']:.2f}% | {stats['sd']:.2f} | {stats['variance']:.2f} | {stats['se']:.2f} | {stats['min']:.1f}% | {stats['max']:.1f}% |")

    report.append("")

    # By condition descriptive stats
    report.append("### 1.2 Results by Condition")
    report.append("")

    measure_data_map = {
        "Overall Accuracy": acc_overall,
        "Low Complexity (Q1-3)": acc_low,
        "Medium Complexity (Q4-6)": acc_med,
        "High Complexity (Q7-9)": acc_high
    }

    for measure_name, _ in measures:
        report.append(f"#### {measure_name}")
        report.append("")
        report.append("| Condition | N | Mean | SD | Variance | SE |")
        report.append("|-----------|---|------|----|---------:|----:|")

        measure_data = measure_data_map[measure_name]

        for cond in conditions:
            data = measure_data['by_condition'][cond]
            stats = calculate_stats(data)
            cond_display = cond.replace('_', ' ').title()
            report.append(f"| {cond_display} | {stats['n']} | {stats['mean']:.2f}% | {stats['sd']:.2f} | {stats['variance']:.2f} | {stats['se']:.2f} |")

        report.append("")

    # Per-question accuracy (Q1-Q9)
    report.append("### 1.3 Per-Question Accuracy (Q1-Q9)")
    report.append("")
    report.append("#### Overall Statistics")
    report.append("")
    report.append("| Question | N | Mean | SD | Variance |")
    report.append("|----------|---|------|----|---------:|")

    for i in range(1, 10):
        q_key = f'Q{i}'
        stats = calculate_stats(acc_by_question[q_key]['all'])
        if stats['n'] > 0:
            report.append(f"| {q_key} | {stats['n']} | {stats['mean']:.2f}% | {stats['sd']:.2f} | {stats['variance']:.2f} |")
        else:
            report.append(f"| {q_key} | 0 | - | - | - |")

    report.append("")

    # Per-question by condition
    report.append("#### By Condition")
    report.append("")
    report.append("| Question | Condition | N | Mean | SD | Variance |")
    report.append("|----------|-----------|---|------|----|---------:|")

    for i in range(1, 10):
        q_key = f'Q{i}'
        for cond in conditions:
            data = acc_by_question[q_key]['by_condition'][cond]
            stats = calculate_stats(data)
            cond_display = cond.replace('_', ' ').title()
            if stats['n'] > 0:
                report.append(f"| {q_key} | {cond_display} | {stats['n']} | {stats['mean']:.2f}% | {stats['sd']:.2f} | {stats['variance']:.2f} |")
            else:
                report.append(f"| {q_key} | {cond_display} | 0 | - | - | - |")

    report.append("")

    # ========================================
    # Part 2: One-way ANOVA
    # ========================================
    report.append("---")
    report.append("")
    report.append("## 2. One-way ANOVA Analysis")
    report.append("")
    report.append("### Method")
    report.append("")
    report.append("One-way Analysis of Variance (ANOVA) was conducted to examine whether quiz accuracy")
    report.append("differs significantly across the three experimental conditions:")
    report.append("- **without_llm**: Control group (no LLM assistance)")
    report.append("- **with_llm**: LLM assistance available")
    report.append("- **with_llm_extended**: Extended LLM assistance available")
    report.append("")
    report.append("**Hypotheses:**")
    report.append("- H0: mu1 = mu2 = mu3 (No difference in accuracy across conditions)")
    report.append("- H1: At least one group mean differs")
    report.append("")
    report.append("**Effect size:** Eta-squared (eta^2) was calculated to determine practical significance.")
    report.append("- eta^2 < 0.01: negligible")
    report.append("- 0.01 <= eta^2 < 0.06: small")
    report.append("- 0.06 <= eta^2 < 0.14: medium")
    report.append("- eta^2 >= 0.14: large")
    report.append("")

    # ANOVA results
    report.append("### 2.1 ANOVA Results")
    report.append("")
    report.append("| Measure | F | p-value | eta^2 | Effect Size | Significant (alpha=.05) |")
    report.append("|---------|---|---------|------:|-------------|-------------------------|")

    anova_tests = [
        ("Overall Accuracy", acc_overall),
        ("Low Complexity (Q1-3)", acc_low),
        ("Medium Complexity (Q4-6)", acc_med),
        ("High Complexity (Q7-9)", acc_high)
    ]

    for name, data in anova_tests:
        groups = [data['by_condition'][cond] for cond in conditions]
        f_stat, p_value = one_way_anova(*groups)
        eta_sq = calculate_eta_squared(groups)
        effect_interp = interpret_eta_squared(eta_sq)

        if p_value is not None:
            p_str = f"{p_value:.4f}" if p_value >= 0.0001 else "<.0001"
            sig = "Yes*" if p_value < 0.05 else "No"
        else:
            p_str = "N/A (scipy required)"
            sig = "N/A"

        report.append(f"| {name} | {f_stat:.3f} | {p_str} | {eta_sq:.4f} | {effect_interp} | {sig} |")

    report.append("")
    report.append("*Note: Significance level alpha = 0.05*")
    report.append("")

    # Detailed ANOVA breakdown
    report.append("### 2.2 Detailed ANOVA Summary")
    report.append("")

    for name, data in anova_tests:
        groups = [data['by_condition'][cond] for cond in conditions]
        f_stat, p_value = one_way_anova(*groups)
        eta_sq = calculate_eta_squared(groups)

        k = len(groups)
        n_total = sum(len(g) for g in groups)
        df_between = k - 1
        df_within = n_total - k

        # Calculate SS values
        all_values = [v for g in groups for v in g]
        grand_mean = sum(all_values) / len(all_values)
        ssb = sum(len(g) * (sum(g)/len(g) - grand_mean)**2 for g in groups)
        ssw = sum(sum((x - sum(g)/len(g))**2 for x in g) for g in groups)
        sst = ssb + ssw
        msb = ssb / df_between
        msw = ssw / df_within

        report.append(f"#### {name}")
        report.append("")
        report.append("| Source | SS | df | MS | F | p |")
        report.append("|--------|----:|---:|----:|---:|---:|")

        if p_value is not None:
            p_str = f"{p_value:.4f}" if p_value >= 0.0001 else "<.0001"
        else:
            p_str = "N/A"

        report.append(f"| Between Groups | {ssb:.2f} | {df_between} | {msb:.2f} | {f_stat:.3f} | {p_str} |")
        report.append(f"| Within Groups | {ssw:.2f} | {df_within} | {msw:.2f} | | |")
        report.append(f"| Total | {sst:.2f} | {n_total-1} | | | |")
        report.append("")

    # ========================================
    # Interpretation and Summary
    # ========================================
    report.append("---")
    report.append("")
    report.append("## 3. Summary and Interpretation")
    report.append("")

    # Generate interpretation based on results
    report.append("### Key Findings")
    report.append("")

    # Overall pattern
    overall_stats = calculate_stats(acc_overall['all'])
    low_stats = calculate_stats(acc_low['all'])
    med_stats = calculate_stats(acc_med['all'])
    high_stats = calculate_stats(acc_high['all'])

    report.append(f"1. **Overall Performance**: Participants achieved an average accuracy of {overall_stats['mean']:.1f}% (SD = {overall_stats['sd']:.1f}) across all quiz questions.")
    report.append("")
    report.append(f"2. **Difficulty Gradient**: As expected, accuracy decreased with question complexity:")
    report.append(f"   - Low complexity: {low_stats['mean']:.1f}%")
    report.append(f"   - Medium complexity: {med_stats['mean']:.1f}%")
    report.append(f"   - High complexity: {high_stats['mean']:.1f}%")
    report.append("")

    # ANOVA interpretation
    report.append("3. **Condition Effects (ANOVA Results)**:")
    report.append("")

    for name, data in anova_tests:
        groups = [data['by_condition'][cond] for cond in conditions]
        f_stat, p_value = one_way_anova(*groups)
        eta_sq = calculate_eta_squared(groups)

        if p_value is not None and p_value < 0.05:
            report.append(f"   - **{name}**: Significant difference found (F = {f_stat:.3f}, p = {p_value:.4f}, eta^2 = {eta_sq:.4f})")
        elif p_value is not None:
            report.append(f"   - **{name}**: No significant difference (F = {f_stat:.3f}, p = {p_value:.4f}, eta^2 = {eta_sq:.4f})")
        else:
            report.append(f"   - **{name}**: F = {f_stat:.3f}, eta^2 = {eta_sq:.4f}")

    report.append("")

    # Condition comparison
    report.append("### Condition Comparison")
    report.append("")
    report.append("| Condition | Overall | Low | Medium | High |")
    report.append("|-----------|---------|-----|--------|------|")

    for cond in conditions:
        overall_m = sum(acc_overall['by_condition'][cond]) / len(acc_overall['by_condition'][cond])
        low_m = sum(acc_low['by_condition'][cond]) / len(acc_low['by_condition'][cond])
        med_m = sum(acc_med['by_condition'][cond]) / len(acc_med['by_condition'][cond])
        high_m = sum(acc_high['by_condition'][cond]) / len(acc_high['by_condition'][cond])
        cond_display = cond.replace('_', ' ').title()
        report.append(f"| {cond_display} | {overall_m:.1f}% | {low_m:.1f}% | {med_m:.1f}% | {high_m:.1f}% |")

    report.append("")

    # Write report
    output_path = os.path.join(output_dir, 'quiz_accuracy_analysis.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"Report saved to: {output_path}")
    print("\n" + "="*60)
    print('\n'.join(report))


if __name__ == '__main__':
    main()
