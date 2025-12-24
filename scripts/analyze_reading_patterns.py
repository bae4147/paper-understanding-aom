#!/usr/bin/env python3
"""
Reading Pattern Analysis
1. Reading Ratio analysis with ANOVA by condition
2. Reading time by section visualization (bar graph by condition)
"""

import csv
import os
import math
from collections import defaultdict
from datetime import datetime

# For visualization
try:
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    print("Warning: matplotlib not available. Skipping visualizations.")


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
        return {'n': 0, 'mean': None, 'variance': None, 'sd': None, 'se': None}

    mean = sum(valid) / n
    if n > 1:
        variance = sum((x - mean) ** 2 for x in valid) / (n - 1)
        sd = math.sqrt(variance)
        se = sd / math.sqrt(n)
    else:
        variance = 0
        sd = 0
        se = 0

    return {'n': n, 'mean': mean, 'variance': variance, 'sd': sd, 'se': se}


def log_gamma(z):
    """Stirling approximation for log(Gamma(z))"""
    if z < 0.5:
        return math.log(math.pi / math.sin(math.pi * z)) - log_gamma(1 - z)
    z -= 1
    coeffs = [76.18009172947146, -86.50532032941677, 24.01409824083091,
              -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5]
    x = 1.000000000190015
    for i, c in enumerate(coeffs):
        x += c / (z + i + 1)
    t = z + 5.5
    return 0.5 * math.log(2 * math.pi) + (z + 0.5) * math.log(t) - t + math.log(x)


def regularized_incomplete_beta(a, b, x):
    """Compute I_x(a,b) using continued fraction"""
    if x == 0: return 0.0
    if x == 1: return 1.0
    if x > (a + 1) / (a + b + 2):
        return 1.0 - regularized_incomplete_beta(b, a, 1 - x)
    
    log_beta = log_gamma(a) + log_gamma(b) - log_gamma(a + b)
    front = math.exp(a * math.log(x) + b * math.log(1 - x) - log_beta) / a
    
    tiny, eps = 1e-30, 1e-10
    f, c, d = 1.0, 1.0, 0.0
    
    for m in range(200):
        if m == 0:
            num = 1.0
        elif m % 2 == 1:
            k = (m - 1) // 2
            num = -(a + k) * (a + b + k) * x / ((a + 2*k) * (a + 2*k + 1))
        else:
            k = m // 2
            num = k * (b - k) * x / ((a + 2*k - 1) * (a + 2*k))
        
        d = 1.0 + num * d
        if abs(d) < tiny: d = tiny
        d = 1.0 / d
        c = 1.0 + num / c
        if abs(c) < tiny: c = tiny
        delta = c * d
        f *= delta
        if abs(delta - 1.0) < eps: break
    
    return front * f


def f_to_p(f_val, df1, df2):
    """Calculate p-value from F-statistic"""
    if f_val <= 0: return 1.0
    x = df1 * f_val / (df1 * f_val + df2)
    cdf = regularized_incomplete_beta(df1 / 2, df2 / 2, x)
    return 1 - cdf


def one_way_anova(*groups):
    """Perform one-way ANOVA"""
    k = len(groups)
    n_total = sum(len(g) for g in groups)
    
    all_values = [v for g in groups for v in g]
    grand_mean = sum(all_values) / len(all_values)
    
    ssb = sum(len(g) * (sum(g)/len(g) - grand_mean)**2 for g in groups)
    ssw = sum(sum((x - sum(g)/len(g))**2 for x in g) for g in groups)
    
    df_between = k - 1
    df_within = n_total - k
    
    msb = ssb / df_between
    msw = ssw / df_within
    
    f_stat = msb / msw if msw > 0 else 0
    p_value = f_to_p(f_stat, df_between, df_within)
    
    return f_stat, p_value, ssb, ssw, df_between, df_within


def calculate_eta_squared(groups):
    """Calculate eta-squared (effect size) for ANOVA"""
    all_values = [v for g in groups for v in g]
    grand_mean = sum(all_values) / len(all_values)
    sst = sum((x - grand_mean)**2 for x in all_values)
    ssb = sum(len(g) * (sum(g)/len(g) - grand_mean)**2 for g in groups)
    return ssb / sst if sst > 0 else 0


def generate_llm_timeline_html(raw_by_pid, pid_to_condition, with_llm_pids, with_llm_extended_pids):
    """Generate HTML visualization for LLM usage timeline"""

    html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Usage Timeline</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; }
        h1 { margin-bottom: 10px; color: #333; }
        h2 { margin: 20px 0 10px; color: #555; font-size: 1.2em; }
        .description { color: #666; margin-bottom: 20px; }
        .legend { display: flex; gap: 20px; margin-bottom: 20px; flex-wrap: wrap; }
        .legend-item { display: flex; align-items: center; gap: 5px; font-size: 14px; }
        .legend-color { width: 20px; height: 20px; border-radius: 3px; }
        .condition-section { background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .participant-row { display: flex; align-items: center; margin: 4px 0; height: 24px; }
        .participant-id { width: 120px; font-size: 11px; color: #666; overflow: hidden; text-overflow: ellipsis; flex-shrink: 0; }
        .timeline-container { flex: 1; height: 20px; background: #e0e0e0; border-radius: 3px; position: relative; overflow: hidden; }
        .timeline-bar { height: 100%; position: absolute; top: 0; }
        .reading-bar { background: #4CAF50; }
        .llm-marker { position: absolute; top: 0; width: 3px; height: 100%; background: #2196F3; }
        .stats { font-size: 12px; color: #888; margin-top: 10px; }
        .scroll-container { max-height: 600px; overflow-y: auto; }
        .time-axis { display: flex; justify-content: space-between; font-size: 10px; color: #999; margin-top: 5px; padding-left: 120px; }
    </style>
</head>
<body>
    <h1>LLM Usage Timeline</h1>
    <p class="description">Each row represents one participant. The green bar shows total session duration, and blue vertical lines indicate when LLM queries were made.</p>

    <div class="legend">
        <div class="legend-item"><div class="legend-color" style="background: #4CAF50;"></div> Reading Session</div>
        <div class="legend-item"><div class="legend-color" style="background: #2196F3;"></div> LLM Query</div>
    </div>
'''

    # Process each condition
    for condition, pids, label in [
        ('with_llm', with_llm_pids, 'With LLM'),
        ('with_llm_extended', with_llm_extended_pids, 'With LLM Extended')
    ]:
        html += f'<div class="condition-section">\n'
        html += f'<h2>{label} (N={len(pids)})</h2>\n'
        html += '<div class="scroll-container">\n'

        participants_data = []

        for pid in pids:
            if pid not in raw_by_pid:
                continue

            exp = raw_by_pid[pid]
            reading = exp.get('reading', {})
            llm_interaction = exp.get('llmInteraction', {})

            # Get session duration
            duration = reading.get('duration', 0)  # in ms
            if duration == 0:
                continue

            # Get LLM query times
            messages = llm_interaction.get('messages', [])
            query_times = []

            # Get reading start time
            reading_started = exp.get('readingStartedAt')
            if reading_started and messages:
                # Parse start time
                try:
                    from datetime import datetime
                    if isinstance(reading_started, str):
                        start_ts = datetime.fromisoformat(reading_started.replace('Z', '+00:00')).timestamp() * 1000
                    else:
                        start_ts = reading_started

                    for msg in messages:
                        q_time = msg.get('questionTime')
                        if q_time:
                            # Calculate relative time from session start
                            relative_time = q_time - start_ts
                            if 0 <= relative_time <= duration:
                                query_times.append(relative_time / duration * 100)  # as percentage
                except:
                    pass

            participants_data.append({
                'pid': pid[:12] + '...' if len(pid) > 12 else pid,
                'duration': duration,
                'query_times': query_times,
                'query_count': len(messages)
            })

        # Sort by duration
        participants_data.sort(key=lambda x: x['duration'], reverse=True)

        # Find max duration for scaling
        max_duration = max((p['duration'] for p in participants_data), default=1)

        for p in participants_data:
            width_pct = (p['duration'] / max_duration) * 100
            html += f'<div class="participant-row">\n'
            html += f'  <div class="participant-id" title="{p["pid"]}">{p["pid"]}</div>\n'
            html += f'  <div class="timeline-container">\n'
            html += f'    <div class="timeline-bar reading-bar" style="width: {width_pct}%;"></div>\n'

            for qt in p['query_times']:
                # Scale to the bar width
                marker_pos = qt * (width_pct / 100)
                html += f'    <div class="llm-marker" style="left: {marker_pos}%;"></div>\n'

            html += f'  </div>\n'
            html += f'</div>\n'

        # Time axis
        max_min = max_duration / 1000 / 60
        html += f'<div class="time-axis"><span>0 min</span><span>{max_min/2:.0f} min</span><span>{max_min:.0f} min</span></div>\n'

        # Stats
        total_queries = sum(p['query_count'] for p in participants_data)
        avg_queries = total_queries / len(participants_data) if participants_data else 0
        html += f'<div class="stats">Total queries: {total_queries} | Average: {avg_queries:.1f} per participant</div>\n'

        html += '</div>\n</div>\n'

    html += '''
</body>
</html>
'''
    return html


def main():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    output_dir = os.path.join(base_dir, 'analysis_results')
    viz_dir = os.path.join(base_dir, 'visualization')
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(viz_dir, exist_ok=True)

    # Load data
    reading_summary = load_csv(os.path.join(processed_dir, 'reading_summary.csv'))
    reading_events = load_csv(os.path.join(processed_dir, 'reading_events.csv'))
    experiments = load_csv(os.path.join(processed_dir, 'experiments.csv'))

    # Create participant to condition mapping
    pid_to_condition = {}
    for exp in experiments:
        pid = exp.get('participantId')
        condition = exp.get('condition')
        if pid and condition:
            pid_to_condition[pid] = condition

    conditions = ['without_llm', 'with_llm', 'with_llm_extended']
    condition_labels = ['Without LLM', 'With LLM', 'With LLM Extended']

    # ========================================
    # Part 1: Reading Ratio Analysis
    # ========================================
    
    # Calculate reading ratio for each participant
    # Reading Ratio = reading_time / (reading_time + scanning_time + scrolling_time)
    reading_ratios = {'all': [], 'by_condition': defaultdict(list)}
    
    for row in reading_summary:
        pid = row.get('participantId')
        condition = pid_to_condition.get(pid)
        
        if not condition:
            continue
        
        reading_time = safe_float(row.get('reading_totalDuration')) or 0
        scanning_time = safe_float(row.get('scanning_totalDuration')) or 0
        scrolling_time = safe_float(row.get('scrolling_totalDuration')) or 0
        
        total_time = reading_time + scanning_time + scrolling_time
        
        if total_time > 0:
            ratio = reading_time / total_time
            reading_ratios['all'].append(ratio)
            reading_ratios['by_condition'][condition].append(ratio)

    # ========================================
    # Part 2: Reading Time by Section
    # ========================================
    
    # Define sections in order (actual section names from data)
    sections = ['Abstract', 'Introduction', 'The Science of Meetings',
                'Applying Meeting Science', 'The Future of Meeting Science', 'References']
    
    # Calculate time spent per section by condition
    # pauseDuration represents time spent on that section before scrolling
    section_times = {cond: defaultdict(list) for cond in conditions}
    
    for event in reading_events:
        pid = event.get('participantId')
        condition = pid_to_condition.get(pid)
        
        if not condition:
            continue
        
        section = event.get('sectionBeforeScroll', '')
        pause_duration = safe_float(event.get('pauseDuration')) or 0
        
        if section in sections and pause_duration > 0:
            # Convert ms to seconds
            section_times[condition][section].append(pause_duration / 1000)

    # Calculate mean time per section per condition
    section_means = {cond: {} for cond in conditions}
    section_sds = {cond: {} for cond in conditions}
    
    for cond in conditions:
        for section in sections:
            times = section_times[cond][section]
            if times:
                section_means[cond][section] = sum(times) / len(times)
                if len(times) > 1:
                    mean = section_means[cond][section]
                    section_sds[cond][section] = math.sqrt(sum((x - mean)**2 for x in times) / (len(times) - 1))
                else:
                    section_sds[cond][section] = 0
            else:
                section_means[cond][section] = 0
                section_sds[cond][section] = 0

    # ========================================
    # Generate Report
    # ========================================
    
    report = []
    report.append("# Reading Pattern Analysis Report")
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("---")
    report.append("")

    # Part 1: Reading Ratio
    report.append("## 1. Reading Ratio Analysis")
    report.append("")
    report.append("### Definition")
    report.append("")
    report.append("**Reading Ratio** = Reading Time / (Reading Time + Scanning Time + Scrolling Time)")
    report.append("")
    report.append("This metric represents the proportion of active reading time relative to total document interaction time.")
    report.append("A higher ratio indicates more focused, deliberate reading behavior.")
    report.append("")

    # Descriptive stats for reading ratio
    report.append("### 1.1 Descriptive Statistics")
    report.append("")
    report.append("#### Overall")
    report.append("")
    overall_stats = calculate_stats(reading_ratios['all'])
    report.append(f"| Metric | Value |")
    report.append(f"|--------|-------|")
    report.append(f"| N | {overall_stats['n']} |")
    report.append(f"| Mean | {overall_stats['mean']:.4f} ({overall_stats['mean']*100:.1f}%) |")
    report.append(f"| SD | {overall_stats['sd']:.4f} |")
    report.append(f"| SE | {overall_stats['se']:.4f} |")
    report.append("")

    report.append("#### By Condition")
    report.append("")
    report.append("| Condition | N | Mean | SD | SE |")
    report.append("|-----------|---|------|----|----|")
    
    for cond, label in zip(conditions, condition_labels):
        stats = calculate_stats(reading_ratios['by_condition'][cond])
        report.append(f"| {label} | {stats['n']} | {stats['mean']:.4f} ({stats['mean']*100:.1f}%) | {stats['sd']:.4f} | {stats['se']:.4f} |")
    report.append("")

    # ANOVA for reading ratio
    report.append("### 1.2 One-way ANOVA")
    report.append("")
    report.append("**Hypothesis:**")
    report.append("- H0: Reading ratio is equal across all conditions")
    report.append("- H1: At least one condition differs in reading ratio")
    report.append("")

    groups = [reading_ratios['by_condition'][cond] for cond in conditions]
    f_stat, p_value, ssb, ssw, df_b, df_w = one_way_anova(*groups)
    eta_sq = calculate_eta_squared(groups)
    
    report.append("#### ANOVA Table")
    report.append("")
    report.append("| Source | SS | df | MS | F | p |")
    report.append("|--------|----:|---:|----:|---:|---:|")
    report.append(f"| Between Groups | {ssb:.6f} | {df_b} | {ssb/df_b:.6f} | {f_stat:.3f} | {p_value:.4f} |")
    report.append(f"| Within Groups | {ssw:.6f} | {df_w} | {ssw/df_w:.6f} | | |")
    report.append(f"| Total | {ssb+ssw:.6f} | {df_b+df_w} | | | |")
    report.append("")
    
    effect_size = "negligible" if eta_sq < 0.01 else "small" if eta_sq < 0.06 else "medium" if eta_sq < 0.14 else "large"
    sig_text = "significant" if p_value < 0.05 else "not significant"
    
    report.append(f"**Results:** F({df_b}, {df_w}) = {f_stat:.3f}, p = {p_value:.4f}, η² = {eta_sq:.4f} ({effect_size})")
    report.append("")
    report.append(f"The effect of condition on reading ratio is **{sig_text}** at α = .05.")
    report.append("")

    # Part 2: Reading Time by Section
    report.append("---")
    report.append("")
    report.append("## 2. Reading Time by Section")
    report.append("")
    report.append("### Definition")
    report.append("")
    report.append("Mean pause duration (seconds) spent on each section before scrolling, aggregated across all participants per condition.")
    report.append("")

    report.append("### 2.1 Mean Time by Section and Condition")
    report.append("")
    
    # Create table header
    header = "| Section |"
    separator = "|---------|"
    for label in condition_labels:
        header += f" {label} |"
        separator += "------|"
    report.append(header)
    report.append(separator)
    
    for section in sections:
        row = f"| {section} |"
        for cond in conditions:
            mean = section_means[cond].get(section, 0)
            sd = section_sds[cond].get(section, 0)
            row += f" {mean:.2f}s (±{sd:.2f}) |"
        report.append(row)
    report.append("")

    # Calculate section-wise time by classification per condition (total)
    section_class_times = {cond: {section: {'reading': 0, 'scanning': 0, 'scrolling': 0}
                                  for section in sections} for cond in conditions}

    # Count participants per condition
    participants_per_condition = {cond: len(reading_ratios['by_condition'][cond]) for cond in conditions}

    for event in reading_events:
        pid = event.get('participantId')
        condition = pid_to_condition.get(pid)

        if not condition:
            continue

        section = event.get('sectionBeforeScroll', '')
        classification = event.get('classification', '')
        pause_duration = safe_float(event.get('pauseDuration')) or 0
        scroll_duration = safe_float(event.get('scrollDuration')) or 0

        if section in sections:
            # Add pause duration to reading or scanning
            if classification in ['reading', 'scanning']:
                section_class_times[condition][section][classification] += pause_duration / 1000
            # Add scroll duration to scrolling
            section_class_times[condition][section]['scrolling'] += scroll_duration / 1000

    # Convert to mean (divide by number of participants)
    section_class_means = {cond: {section: {'reading': 0, 'scanning': 0, 'scrolling': 0}
                                  for section in sections} for cond in conditions}
    for cond in conditions:
        n = participants_per_condition[cond]
        for section in sections:
            section_class_means[cond][section]['reading'] = section_class_times[cond][section]['reading'] / n
            section_class_means[cond][section]['scanning'] = section_class_times[cond][section]['scanning'] / n
            section_class_means[cond][section]['scrolling'] = section_class_times[cond][section]['scrolling'] / n

    # Create visualization - one stacked bar chart per condition (mean values)
    if HAS_MATPLOTLIB:
        report.append("### 2.2 Visualization")
        report.append("")

        colors_stack = {
            'reading': '#3d9970',    # Dark green
            'scanning': '#5cb85c',   # Medium green
            'scrolling': '#a8e6cf'   # Light green
        }

        for cond, label in zip(conditions, condition_labels):
            filename = f'reading_time_by_section_{cond}.png'
            n = participants_per_condition[cond]
            report.append(f"#### {label} (N={n})")
            report.append("")
            report.append(f"![Reading Time by Section - {label}](./{filename})")
            report.append("")

            fig, ax = plt.subplots(figsize=(14, 6))

            x = range(len(sections))
            width = 0.6

            reading_vals = [section_class_means[cond][s]['reading'] for s in sections]
            scanning_vals = [section_class_means[cond][s]['scanning'] for s in sections]
            scrolling_vals = [section_class_means[cond][s]['scrolling'] for s in sections]

            # Stacked bars
            ax.bar(x, reading_vals, width, label='Reading', color=colors_stack['reading'], alpha=0.9)
            ax.bar(x, scanning_vals, width, bottom=reading_vals,
                   label='Scanning', color=colors_stack['scanning'], alpha=0.9)
            ax.bar(x, scrolling_vals, width,
                   bottom=[r + s for r, s in zip(reading_vals, scanning_vals)],
                   label='Scrolling', color=colors_stack['scrolling'], alpha=0.9)

            ax.set_xlabel('Section', fontsize=12)
            ax.set_ylabel('Mean Time (seconds)', fontsize=12)
            ax.set_title(f'Mean Reading Time by Section - {label} (N={n})', fontsize=14)
            ax.set_xticks(x)
            ax.set_xticklabels(sections, rotation=30, ha='right', fontsize=10)
            ax.legend(loc='upper right')
            ax.grid(axis='y', alpha=0.3)

            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, filename), dpi=150)
            plt.close()

            print(f"Saved: {filename} to analysis_results/")

    # Summary
    report.append("---")
    report.append("")
    report.append("## 3. Summary")
    report.append("")
    
    # Reading ratio summary
    mean_ratios = [(cond, calculate_stats(reading_ratios['by_condition'][cond])['mean']) 
                   for cond in conditions]
    max_cond = max(mean_ratios, key=lambda x: x[1])
    min_cond = min(mean_ratios, key=lambda x: x[1])
    
    report.append("### Key Findings")
    report.append("")
    report.append(f"1. **Reading Ratio:**")
    report.append(f"   - Overall mean: {overall_stats['mean']*100:.1f}% of interaction time spent reading")
    report.append(f"   - Highest: {max_cond[0].replace('_', ' ').title()} ({max_cond[1]*100:.1f}%)")
    report.append(f"   - Lowest: {min_cond[0].replace('_', ' ').title()} ({min_cond[1]*100:.1f}%)")
    report.append(f"   - ANOVA: F({df_b}, {df_w}) = {f_stat:.3f}, p = {p_value:.4f}")
    report.append("")
    
    report.append(f"2. **Section Reading Patterns:**")
    # Find which section had most time overall
    total_by_section = {}
    for section in sections:
        total = sum(section_means[cond].get(section, 0) for cond in conditions) / 3
        total_by_section[section] = total

    sorted_sections = sorted(total_by_section.items(), key=lambda x: x[1], reverse=True)
    report.append(f"   - Most time spent on: {sorted_sections[0][0]} ({sorted_sections[0][1]:.2f}s avg)")
    report.append(f"   - Least time spent on: {sorted_sections[-1][0]} ({sorted_sections[-1][1]:.2f}s avg)")
    report.append("")

    # ========================================
    # Part 4: LLM Usage Analysis (with_llm and with_llm_extended only)
    # ========================================
    report.append("---")
    report.append("")
    report.append("## 4. LLM and Extended Resources Usage Analysis")
    report.append("")
    report.append("This section analyzes LLM usage patterns for the `with_llm` and `with_llm_extended` conditions.")
    report.append("")

    # Load raw data for extended resources
    import json
    raw_data_path = os.path.join(base_dir, 'data', 'raw', 'raw_data_20251223_143357.json')
    with open(raw_data_path, 'r') as f:
        raw_data = json.load(f)

    # Build lookup by participantId - only include preprocessed participants
    preprocessed_pids = set(pid_to_condition.keys())
    raw_by_pid = {exp['participantId']: exp for exp in raw_data
                  if exp['participantId'] in preprocessed_pids}

    # Analyze focus time ratios
    report.append("### 4.1 Media Usage Time Ratio")
    report.append("")

    # With LLM: Reading vs LLM
    with_llm_pids = [pid for pid, cond in pid_to_condition.items() if cond == 'with_llm']
    with_llm_extended_pids = [pid for pid, cond in pid_to_condition.items() if cond == 'with_llm_extended']

    # With LLM condition - use raw data focusTimes
    report.append("#### With LLM (N={})".format(len(with_llm_pids)))
    report.append("")
    report.append("| Media | Mean Time | SD | % of Total |")
    report.append("|-------|-----------|-----|------------|")

    wl_reading = []
    wl_chat = []

    for pid in with_llm_pids:
        if pid in raw_by_pid:
            focus_times = raw_by_pid[pid].get('reading', {}).get('focusTimes', {})
            wl_reading.append(focus_times.get('reading', 0) / 1000 / 60)  # ms to min
            wl_chat.append(focus_times.get('chat', 0) / 1000 / 60)

    wl_reading_stats = calculate_stats(wl_reading)
    wl_chat_stats = calculate_stats(wl_chat)
    wl_total = (wl_reading_stats['mean'] or 0) + (wl_chat_stats['mean'] or 0)

    if wl_total > 0:
        report.append(f"| Reading | {wl_reading_stats['mean']:.2f} min | {wl_reading_stats['sd']:.2f} | {wl_reading_stats['mean']/wl_total*100:.1f}% |")
        report.append(f"| LLM Chat | {wl_chat_stats['mean']:.2f} min | {wl_chat_stats['sd']:.2f} | {wl_chat_stats['mean']/wl_total*100:.1f}% |")
    report.append(f"| **Total** | **{wl_total:.2f} min** | | |")
    report.append("")

    # With LLM Extended condition - all media types from raw focusTimes
    report.append("#### With LLM Extended (N={})".format(len(with_llm_extended_pids)))
    report.append("")
    report.append("| Media | Mean Time | SD | % of Total |")
    report.append("|-------|-----------|-----|------------|")

    media_types = ['reading', 'chat', 'video', 'audio', 'infographics']
    media_labels = {
        'reading': 'Reading',
        'chat': 'LLM Chat',
        'video': 'Video',
        'audio': 'Audio',
        'infographics': 'Infographics'
    }
    wle_times = {media: [] for media in media_types}

    for pid in with_llm_extended_pids:
        if pid in raw_by_pid:
            focus_times = raw_by_pid[pid].get('reading', {}).get('focusTimes', {})
            for media in media_types:
                wle_times[media].append(focus_times.get(media, 0) / 1000 / 60)

    wle_stats = {media: calculate_stats(times) for media, times in wle_times.items()}
    wle_total = sum(wle_stats[media]['mean'] or 0 for media in media_types)

    for media in media_types:
        stats = wle_stats[media]
        pct = (stats['mean'] / wle_total * 100) if wle_total > 0 and stats['mean'] else 0
        report.append(f"| {media_labels[media]} | {stats['mean']:.2f} min | {stats['sd']:.2f} | {pct:.1f}% |")

    report.append(f"| **Total** | **{wle_total:.2f} min** | | |")
    report.append("")

    # LLM Query Analysis
    report.append("### 4.2 LLM Query Statistics")
    report.append("")

    llm_messages = load_csv(os.path.join(processed_dir, 'llm_messages.csv'))

    # Count queries per participant
    queries_by_pid = defaultdict(int)
    for msg in llm_messages:
        pid = msg.get('participantId')
        queries_by_pid[pid] += 1

    # With LLM
    wl_queries = [queries_by_pid.get(pid, 0) for pid in with_llm_pids]
    wl_query_stats = calculate_stats(wl_queries)

    # With LLM Extended
    wle_queries = [queries_by_pid.get(pid, 0) for pid in with_llm_extended_pids]
    wle_query_stats = calculate_stats(wle_queries)

    report.append("| Condition | N | Mean Queries | SD | Min | Max |")
    report.append("|-----------|---|--------------|-----|-----|-----|")
    report.append(f"| With LLM | {len(with_llm_pids)} | {wl_query_stats['mean']:.2f} | {wl_query_stats['sd']:.2f} | {min(wl_queries)} | {max(wl_queries)} |")
    report.append(f"| With LLM Extended | {len(with_llm_extended_pids)} | {wle_query_stats['mean']:.2f} | {wle_query_stats['sd']:.2f} | {min(wle_queries)} | {max(wle_queries)} |")
    report.append("")

    # LLM Usage Timeline Visualization (HTML)
    report.append("### 4.3 LLM Usage Timeline")
    report.append("")
    report.append("Interactive visualization showing when each participant used the LLM during their reading session.")
    report.append("")
    report.append("[View LLM Usage Timeline (HTML)](./llm_usage_timeline.html)")
    report.append("")

    # Generate HTML timeline visualization
    html_content = generate_llm_timeline_html(raw_by_pid, pid_to_condition, with_llm_pids, with_llm_extended_pids)
    html_path = os.path.join(output_dir, 'llm_usage_timeline.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"Saved: llm_usage_timeline.html to analysis_results/")

    # Write report
    output_path = os.path.join(output_dir, 'reading_pattern_analysis.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"Report saved to: {output_path}")
    print("\n" + "="*60)
    print('\n'.join(report))


if __name__ == '__main__':
    main()
