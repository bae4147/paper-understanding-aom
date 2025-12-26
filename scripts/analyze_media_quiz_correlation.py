#!/usr/bin/env python3
"""
Media Ratio vs Quiz Score Correlation Analysis

Analyzes the relationship between media usage ratios and quiz performance:
1. Reading ratio vs quiz score correlation (all conditions)
2. Each media ratio vs quiz score (with_llm_extended only)
3. Multiple regression analysis (with_llm_extended)

Data sources: merged_all.csv, reading_summary.csv, quizzes.csv
"""

import csv
import os
import math
from collections import defaultdict
from datetime import datetime


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
        return {'n': 0, 'mean': None, 'sd': None, 'min': None, 'max': None}

    mean = sum(valid) / n
    if n > 1:
        variance = sum((x - mean) ** 2 for x in valid) / (n - 1)
        sd = math.sqrt(variance)
    else:
        variance = 0
        sd = 0

    return {
        'n': n,
        'mean': mean,
        'sd': sd,
        'min': min(valid),
        'max': max(valid)
    }


def pearson_correlation(x_values, y_values):
    """Calculate Pearson correlation coefficient and p-value"""
    # Filter pairs where both values are valid
    pairs = [(x, y) for x, y in zip(x_values, y_values)
             if x is not None and y is not None]

    n = len(pairs)
    if n < 3:
        return {'r': None, 'p': None, 'n': n}

    x = [p[0] for p in pairs]
    y = [p[1] for p in pairs]

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    # Calculate covariance and standard deviations
    cov_xy = sum((xi - mean_x) * (yi - mean_y) for xi, yi in pairs) / (n - 1)
    var_x = sum((xi - mean_x) ** 2 for xi in x) / (n - 1)
    var_y = sum((yi - mean_y) ** 2 for yi in y) / (n - 1)

    if var_x == 0 or var_y == 0:
        return {'r': None, 'p': None, 'n': n}

    sd_x = math.sqrt(var_x)
    sd_y = math.sqrt(var_y)

    r = cov_xy / (sd_x * sd_y)

    # Calculate t-statistic and p-value (two-tailed)
    if abs(r) >= 1:
        p = 0.0
    else:
        t = r * math.sqrt((n - 2) / (1 - r ** 2))
        # Approximate p-value using t-distribution
        # Using a simple approximation for large n
        df = n - 2
        p = 2 * (1 - t_cdf(abs(t), df))

    return {'r': r, 'p': p, 'n': n}


def t_cdf(t, df):
    """Approximate CDF of t-distribution using normal approximation for large df"""
    if df > 30:
        # Use normal approximation
        return normal_cdf(t)
    else:
        # Use a more accurate approximation
        x = df / (df + t ** 2)
        return 1 - 0.5 * incomplete_beta(df / 2, 0.5, x)


def normal_cdf(x):
    """Approximate CDF of standard normal distribution"""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def incomplete_beta(a, b, x):
    """Approximate incomplete beta function using continued fraction"""
    if x == 0:
        return 0
    if x == 1:
        return 1

    # Simple approximation
    if x < (a + 1) / (a + b + 2):
        return beta_cf(a, b, x) * (x ** a) * ((1 - x) ** b) / a
    else:
        return 1 - beta_cf(b, a, 1 - x) * ((1 - x) ** b) * (x ** a) / b


def beta_cf(a, b, x):
    """Continued fraction for incomplete beta function"""
    max_iter = 100
    eps = 1e-10

    qab = a + b
    qap = a + 1
    qam = a - 1
    c = 1
    d = 1 - qab * x / qap
    if abs(d) < eps:
        d = eps
    d = 1 / d
    h = d

    for m in range(1, max_iter + 1):
        m2 = 2 * m
        aa = m * (b - m) * x / ((qam + m2) * (a + m2))
        d = 1 + aa * d
        if abs(d) < eps:
            d = eps
        c = 1 + aa / c
        if abs(c) < eps:
            c = eps
        d = 1 / d
        h *= d * c

        aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
        d = 1 + aa * d
        if abs(d) < eps:
            d = eps
        c = 1 + aa / c
        if abs(c) < eps:
            c = eps
        d = 1 / d
        delta = d * c
        h *= delta

        if abs(delta - 1) < eps:
            break

    return h


def spearman_correlation(x_values, y_values):
    """Calculate Spearman rank correlation coefficient"""
    pairs = [(x, y) for x, y in zip(x_values, y_values)
             if x is not None and y is not None]

    n = len(pairs)
    if n < 3:
        return {'rho': None, 'p': None, 'n': n}

    # Rank the values
    x = [p[0] for p in pairs]
    y = [p[1] for p in pairs]

    def rank(values):
        sorted_indices = sorted(range(len(values)), key=lambda i: values[i])
        ranks = [0] * len(values)
        for rank_val, idx in enumerate(sorted_indices):
            ranks[idx] = rank_val + 1
        return ranks

    x_ranks = rank(x)
    y_ranks = rank(y)

    # Calculate Pearson correlation on ranks
    result = pearson_correlation(x_ranks, y_ranks)
    # Rename 'r' to 'rho' for Spearman
    return {'rho': result['r'], 'p': result['p'], 'n': result['n']}


def simple_linear_regression(x_values, y_values):
    """Perform simple linear regression"""
    pairs = [(x, y) for x, y in zip(x_values, y_values)
             if x is not None and y is not None]

    n = len(pairs)
    if n < 3:
        return None

    x = [p[0] for p in pairs]
    y = [p[1] for p in pairs]

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    # Calculate slope and intercept
    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in pairs)
    denominator = sum((xi - mean_x) ** 2 for xi in x)

    if denominator == 0:
        return None

    slope = numerator / denominator
    intercept = mean_y - slope * mean_x

    # Calculate R-squared
    y_pred = [slope * xi + intercept for xi in x]
    ss_res = sum((yi - ypi) ** 2 for yi, ypi in zip(y, y_pred))
    ss_tot = sum((yi - mean_y) ** 2 for yi in y)

    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # Calculate standard error of slope
    if n > 2:
        mse = ss_res / (n - 2)
        se_slope = math.sqrt(mse / denominator) if denominator > 0 else 0
        t_stat = slope / se_slope if se_slope > 0 else 0
        p_value = 2 * (1 - t_cdf(abs(t_stat), n - 2))
    else:
        se_slope = 0
        t_stat = 0
        p_value = 1

    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_squared,
        'se_slope': se_slope,
        't_stat': t_stat,
        'p_value': p_value,
        'n': n
    }


def multiple_regression(X, y):
    """
    Perform multiple linear regression using normal equations.
    X: list of lists (each inner list is a row of predictors)
    y: list of dependent variable values
    """
    n = len(y)
    k = len(X[0]) if X else 0

    if n < k + 2:
        return None

    # Add intercept column
    X_with_intercept = [[1] + row for row in X]
    k_full = k + 1

    # Matrix operations (simple implementation)
    # X'X
    XtX = [[sum(X_with_intercept[i][j] * X_with_intercept[i][l]
                for i in range(n))
            for l in range(k_full)]
           for j in range(k_full)]

    # X'y
    Xty = [sum(X_with_intercept[i][j] * y[i] for i in range(n))
           for j in range(k_full)]

    # Solve using Gaussian elimination
    try:
        coeffs = solve_linear_system(XtX, Xty)
    except Exception:
        return None

    if coeffs is None:
        return None

    intercept = coeffs[0]
    betas = coeffs[1:]

    # Calculate predictions and residuals
    y_pred = [intercept + sum(betas[j] * X[i][j] for j in range(k))
              for i in range(n)]
    residuals = [y[i] - y_pred[i] for i in range(n)]

    # Calculate R-squared
    mean_y = sum(y) / n
    ss_res = sum(r ** 2 for r in residuals)
    ss_tot = sum((yi - mean_y) ** 2 for yi in y)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

    # Adjusted R-squared
    adj_r_squared = 1 - (1 - r_squared) * (n - 1) / (n - k - 1) if n > k + 1 else 0

    # Calculate standard errors (simplified)
    mse = ss_res / (n - k - 1) if n > k + 1 else 0

    return {
        'intercept': intercept,
        'coefficients': betas,
        'r_squared': r_squared,
        'adj_r_squared': adj_r_squared,
        'mse': mse,
        'n': n,
        'k': k
    }


def solve_linear_system(A, b):
    """Solve Ax = b using Gaussian elimination with partial pivoting"""
    n = len(b)
    # Create augmented matrix
    M = [row[:] + [b[i]] for i, row in enumerate(A)]

    # Forward elimination
    for col in range(n):
        # Find pivot
        max_row = col
        for row in range(col + 1, n):
            if abs(M[row][col]) > abs(M[max_row][col]):
                max_row = row
        M[col], M[max_row] = M[max_row], M[col]

        if abs(M[col][col]) < 1e-10:
            return None

        # Eliminate
        for row in range(col + 1, n):
            factor = M[row][col] / M[col][col]
            for j in range(col, n + 1):
                M[row][j] -= factor * M[col][j]

    # Back substitution
    x = [0] * n
    for i in range(n - 1, -1, -1):
        x[i] = M[i][n]
        for j in range(i + 1, n):
            x[i] -= M[i][j] * x[j]
        x[i] /= M[i][i]

    return x


def interpret_correlation(r):
    """Interpret correlation coefficient strength"""
    if r is None:
        return "N/A"
    abs_r = abs(r)
    if abs_r < 0.1:
        return "negligible"
    elif abs_r < 0.3:
        return "weak"
    elif abs_r < 0.5:
        return "moderate"
    elif abs_r < 0.7:
        return "strong"
    else:
        return "very strong"


def significance_marker(p):
    """Return significance marker based on p-value"""
    if p is None:
        return ""
    if p < 0.001:
        return "***"
    elif p < 0.01:
        return "**"
    elif p < 0.05:
        return "*"
    else:
        return ""


def main():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    output_dir = os.path.join(base_dir, 'analysis_results')
    os.makedirs(output_dir, exist_ok=True)

    # Load data
    merged_all = load_csv(os.path.join(processed_dir, 'merged_all.csv'))
    reading_summary = load_csv(os.path.join(processed_dir, 'reading_summary.csv'))
    quizzes = load_csv(os.path.join(processed_dir, 'quizzes.csv'))

    # Create lookup tables
    reading_by_pid = {row['participantId']: row for row in reading_summary}

    # Calculate quiz accuracy per participant (Q1-Q9)
    # quizzes.csv has 'accuracy' column directly, or we can use correct_1, correct_2, etc.
    quiz_accuracy = {}
    for row in quizzes:
        pid = row['participantId']
        # Try using the accuracy column directly
        acc = safe_float(row.get('accuracy'))
        if acc is not None:
            quiz_accuracy[pid] = acc
        else:
            # Fallback: calculate from correct_1, correct_2, etc.
            correct = 0
            total = 0
            for i in range(1, 10):
                is_correct = row.get(f'correct_{i}')
                if is_correct is not None and is_correct != '':
                    total += 1
                    if is_correct.lower() == 'true':
                        correct += 1
            if total > 0:
                quiz_accuracy[pid] = (correct / total) * 100

    # Process each participant and calculate ratios
    participant_data = []
    for p in merged_all:
        pid = p['participantId']
        condition = p['condition']

        if pid not in quiz_accuracy:
            continue

        reading_info = reading_by_pid.get(pid, {})
        if not reading_info:
            continue

        # Get focus times
        reading_time = safe_float(reading_info.get('focusTime_reading')) or 0
        chat_time = safe_float(reading_info.get('focusTime_chat')) or 0
        video_time = safe_float(reading_info.get('focusTime_video')) or 0
        audio_time = safe_float(reading_info.get('focusTime_audio')) or 0
        infographics_time = safe_float(reading_info.get('focusTime_infographics')) or 0

        # Calculate total time
        if condition == 'without_llm':
            total_time = reading_time  # Only reading available
        elif condition == 'with_llm':
            total_time = reading_time + chat_time
        else:  # with_llm_extended
            total_time = reading_time + chat_time + video_time + audio_time + infographics_time

        if total_time <= 0:
            continue

        # Calculate ratios
        reading_ratio = (reading_time / total_time) * 100
        chat_ratio = (chat_time / total_time) * 100 if total_time > 0 else 0
        video_ratio = (video_time / total_time) * 100 if total_time > 0 else 0
        audio_ratio = (audio_time / total_time) * 100 if total_time > 0 else 0
        infographics_ratio = (infographics_time / total_time) * 100 if total_time > 0 else 0

        participant_data.append({
            'pid': pid,
            'condition': condition,
            'quiz_accuracy': quiz_accuracy[pid],
            'reading_ratio': reading_ratio,
            'chat_ratio': chat_ratio,
            'video_ratio': video_ratio,
            'audio_ratio': audio_ratio,
            'infographics_ratio': infographics_ratio,
            'reading_time': reading_time / 1000,  # Convert to seconds
            'chat_time': chat_time / 1000,
            'video_time': video_time / 1000,
            'audio_time': audio_time / 1000,
            'infographics_time': infographics_time / 1000,
            'total_time': total_time / 1000
        })

    # Separate by condition
    without_llm = [p for p in participant_data if p['condition'] == 'without_llm']
    with_llm = [p for p in participant_data if p['condition'] == 'with_llm']
    with_llm_extended = [p for p in participant_data if p['condition'] == 'with_llm_extended']

    # Generate report
    report = []
    report.append("# Media Usage Ratio vs Quiz Score Analysis")
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("Data source: merged_all.csv, reading_summary.csv, quizzes.csv")
    report.append("")
    report.append("---")
    report.append("")

    # ========================================
    # Part 1: Descriptive Statistics
    # ========================================
    report.append("## 1. Descriptive Statistics")
    report.append("")

    report.append("### 1.1 Sample Sizes")
    report.append("")
    report.append(f"- **without_llm**: N = {len(without_llm)}")
    report.append(f"- **with_llm**: N = {len(with_llm)}")
    report.append(f"- **with_llm_extended**: N = {len(with_llm_extended)}")
    report.append("")

    report.append("### 1.2 Reading Ratio by Condition")
    report.append("")
    report.append("| Condition | N | Mean | SD | Min | Max |")
    report.append("|-----------|---|------|----:|----:|----:|")

    for name, data in [('without_llm', without_llm), ('with_llm', with_llm), ('with_llm_extended', with_llm_extended)]:
        ratios = [p['reading_ratio'] for p in data]
        stats = calculate_stats(ratios)
        if stats['n'] > 0:
            report.append(f"| {name} | {stats['n']} | {stats['mean']:.1f}% | {stats['sd']:.1f}% | {stats['min']:.1f}% | {stats['max']:.1f}% |")

    report.append("")

    report.append("### 1.3 Quiz Accuracy by Condition")
    report.append("")
    report.append("| Condition | N | Mean | SD | Min | Max |")
    report.append("|-----------|---|------|----:|----:|----:|")

    for name, data in [('without_llm', without_llm), ('with_llm', with_llm), ('with_llm_extended', with_llm_extended)]:
        scores = [p['quiz_accuracy'] for p in data]
        stats = calculate_stats(scores)
        if stats['n'] > 0:
            report.append(f"| {name} | {stats['n']} | {stats['mean']:.1f}% | {stats['sd']:.1f}% | {stats['min']:.1f}% | {stats['max']:.1f}% |")

    report.append("")

    # Media ratio distribution for with_llm_extended
    report.append("### 1.4 Media Ratio Distribution (with_llm_extended)")
    report.append("")
    report.append("| Media | N | Mean | SD | Min | Max |")
    report.append("|-------|---|------|----:|----:|----:|")

    for media in ['reading', 'chat', 'video', 'audio', 'infographics']:
        ratios = [p[f'{media}_ratio'] for p in with_llm_extended]
        stats = calculate_stats(ratios)
        if stats['n'] > 0:
            report.append(f"| {media.title()} | {stats['n']} | {stats['mean']:.1f}% | {stats['sd']:.1f}% | {stats['min']:.1f}% | {stats['max']:.1f}% |")

    report.append("")

    # ========================================
    # Part 2: Reading Ratio vs Quiz Score Correlation
    # ========================================
    report.append("---")
    report.append("")
    report.append("## 2. Reading Ratio vs Quiz Score Correlation")
    report.append("")
    report.append("Pearson and Spearman correlation between reading time ratio and quiz accuracy.")
    report.append("")

    report.append("### 2.1 Correlation by Condition")
    report.append("")
    report.append("| Condition | N | Pearson r | p-value | Spearman ρ | p-value | Interpretation |")
    report.append("|-----------|---|-----------|---------|------------|---------|----------------|")

    for name, data in [('without_llm', without_llm), ('with_llm', with_llm), ('with_llm_extended', with_llm_extended)]:
        x = [p['reading_ratio'] for p in data]
        y = [p['quiz_accuracy'] for p in data]

        pearson = pearson_correlation(x, y)
        spearman = spearman_correlation(x, y)

        if pearson['r'] is not None:
            interp = interpret_correlation(pearson['r'])
            p_sig = significance_marker(pearson['p'])
            s_sig = significance_marker(spearman['p'])
            report.append(f"| {name} | {pearson['n']} | {pearson['r']:.3f}{p_sig} | {pearson['p']:.4f} | {spearman['rho']:.3f}{s_sig} | {spearman['p']:.4f} | {interp} |")
        else:
            report.append(f"| {name} | {len(data)} | N/A | N/A | N/A | N/A | - |")

    report.append("")
    report.append("*Significance: \\* p<0.05, \\*\\* p<0.01, \\*\\*\\* p<0.001*")
    report.append("")

    # Simple linear regression for each condition
    report.append("### 2.2 Simple Linear Regression: Reading Ratio → Quiz Score")
    report.append("")
    report.append("| Condition | N | Slope (β) | SE | t | p-value | R² |")
    report.append("|-----------|---|-----------|----:|---:|---------|----:|")

    for name, data in [('without_llm', without_llm), ('with_llm', with_llm), ('with_llm_extended', with_llm_extended)]:
        x = [p['reading_ratio'] for p in data]
        y = [p['quiz_accuracy'] for p in data]

        reg = simple_linear_regression(x, y)
        if reg:
            sig = significance_marker(reg['p_value'])
            report.append(f"| {name} | {reg['n']} | {reg['slope']:.4f}{sig} | {reg['se_slope']:.4f} | {reg['t_stat']:.2f} | {reg['p_value']:.4f} | {reg['r_squared']:.4f} |")
        else:
            report.append(f"| {name} | {len(data)} | N/A | N/A | N/A | N/A | N/A |")

    report.append("")
    report.append("*Interpretation: For each 1% increase in reading ratio, quiz score changes by β percentage points.*")
    report.append("")

    # ========================================
    # Part 3: All Media Ratios vs Quiz Score (with_llm_extended)
    # ========================================
    report.append("---")
    report.append("")
    report.append("## 3. Media Ratio vs Quiz Score Correlation (with_llm_extended)")
    report.append("")
    report.append("Correlation between each media type's time ratio and quiz accuracy.")
    report.append("")

    report.append("### 3.1 Correlation Matrix")
    report.append("")
    report.append("| Media | N | Pearson r | p-value | Spearman ρ | p-value | Interpretation |")
    report.append("|-------|---|-----------|---------|------------|---------|----------------|")

    media_types = ['reading', 'chat', 'video', 'audio', 'infographics']
    for media in media_types:
        x = [p[f'{media}_ratio'] for p in with_llm_extended]
        y = [p['quiz_accuracy'] for p in with_llm_extended]

        pearson = pearson_correlation(x, y)
        spearman = spearman_correlation(x, y)

        if pearson['r'] is not None:
            interp = interpret_correlation(pearson['r'])
            p_sig = significance_marker(pearson['p'])
            s_sig = significance_marker(spearman['p'])
            report.append(f"| {media.title()} | {pearson['n']} | {pearson['r']:.3f}{p_sig} | {pearson['p']:.4f} | {spearman['rho']:.3f}{s_sig} | {spearman['p']:.4f} | {interp} |")

    report.append("")
    report.append("*Significance: \\* p<0.05, \\*\\* p<0.01, \\*\\*\\* p<0.001*")
    report.append("")

    # Simple regression for each media type
    report.append("### 3.2 Simple Linear Regression for Each Media")
    report.append("")
    report.append("| Media | N | Slope (β) | SE | t | p-value | R² |")
    report.append("|-------|---|-----------|----:|---:|---------|----:|")

    for media in media_types:
        x = [p[f'{media}_ratio'] for p in with_llm_extended]
        y = [p['quiz_accuracy'] for p in with_llm_extended]

        reg = simple_linear_regression(x, y)
        if reg:
            sig = significance_marker(reg['p_value'])
            report.append(f"| {media.title()} | {reg['n']} | {reg['slope']:.4f}{sig} | {reg['se_slope']:.4f} | {reg['t_stat']:.2f} | {reg['p_value']:.4f} | {reg['r_squared']:.4f} |")

    report.append("")

    # ========================================
    # Part 4: Multiple Regression (with_llm_extended)
    # ========================================
    report.append("---")
    report.append("")
    report.append("## 4. Multiple Regression Analysis (with_llm_extended)")
    report.append("")
    report.append("Predicting quiz score from multiple media ratios.")
    report.append("")
    report.append("**Note:** Since ratios sum to 100%, one variable must be excluded to avoid perfect multicollinearity. Infographics ratio is excluded as the reference category.")
    report.append("")

    # Prepare data for multiple regression
    # Exclude infographics to avoid multicollinearity
    X = []
    y = []
    for p in with_llm_extended:
        X.append([
            p['reading_ratio'],
            p['chat_ratio'],
            p['video_ratio'],
            p['audio_ratio']
        ])
        y.append(p['quiz_accuracy'])

    reg = multiple_regression(X, y)

    if reg:
        report.append("### 4.1 Model Summary")
        report.append("")
        report.append(f"- **N**: {reg['n']}")
        report.append(f"- **R²**: {reg['r_squared']:.4f}")
        report.append(f"- **Adjusted R²**: {reg['adj_r_squared']:.4f}")
        report.append(f"- **MSE**: {reg['mse']:.4f}")
        report.append("")

        report.append("### 4.2 Coefficients")
        report.append("")
        report.append("| Variable | Coefficient (β) |")
        report.append("|----------|----------------:|")
        report.append(f"| Intercept | {reg['intercept']:.4f} |")

        predictors = ['Reading', 'Chat', 'Video', 'Audio']
        for i, pred in enumerate(predictors):
            report.append(f"| {pred} Ratio | {reg['coefficients'][i]:.4f} |")

        report.append("")
        report.append("*Interpretation: Coefficients represent the change in quiz score for a 1% increase in that media's ratio, holding other ratios constant (relative to infographics).*")
    else:
        report.append("*Multiple regression could not be computed.*")

    report.append("")

    # ========================================
    # Part 5: Summary and Interpretation
    # ========================================
    report.append("---")
    report.append("")
    report.append("## 5. Summary")
    report.append("")

    report.append("### Key Findings")
    report.append("")

    # Reading ratio correlation findings
    report.append("**1. Reading Ratio vs Quiz Score:**")
    report.append("")

    for name, data in [('without_llm', without_llm), ('with_llm', with_llm), ('with_llm_extended', with_llm_extended)]:
        x = [p['reading_ratio'] for p in data]
        y = [p['quiz_accuracy'] for p in data]
        pearson = pearson_correlation(x, y)

        if pearson['r'] is not None:
            direction = "positive" if pearson['r'] > 0 else "negative"
            strength = interpret_correlation(pearson['r'])
            sig = "significant" if pearson['p'] < 0.05 else "not significant"
            report.append(f"- **{name}**: r = {pearson['r']:.3f} ({strength} {direction}), p = {pearson['p']:.4f} ({sig})")

    report.append("")

    # with_llm_extended media findings
    report.append("**2. Media Ratios vs Quiz Score (with_llm_extended):**")
    report.append("")

    for media in media_types:
        x = [p[f'{media}_ratio'] for p in with_llm_extended]
        y = [p['quiz_accuracy'] for p in with_llm_extended]
        pearson = pearson_correlation(x, y)

        if pearson['r'] is not None:
            direction = "positive" if pearson['r'] > 0 else "negative"
            strength = interpret_correlation(pearson['r'])
            sig = "significant" if pearson['p'] < 0.05 else "not significant"
            report.append(f"- **{media.title()}**: r = {pearson['r']:.3f} ({strength} {direction}), p = {pearson['p']:.4f} ({sig})")

    report.append("")

    # Write report
    output_path = os.path.join(output_dir, 'media_quiz_correlation.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"Report saved to: {output_path}")
    print("\n" + "=" * 60)
    print('\n'.join(report))


if __name__ == '__main__':
    main()
