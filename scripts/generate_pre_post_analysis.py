#!/usr/bin/env python3
"""
Generate Pre-Post Analysis Report
Analyzes 295 participants comparing pre-task and post-task responses
"""

import csv
import os
from datetime import datetime
from collections import defaultdict
import math

def load_csv(filepath):
    """Load CSV file and return list of dictionaries"""
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

def count_strategies(row):
    """Count non-empty strategies in a row"""
    count = 0
    for i in range(1, 11):
        key = f'strategy{i}'
        if key in row and row[key] and row[key].strip():
            count += 1
    return count

def safe_float(value):
    """Safely convert value to float, return None if not possible"""
    if value is None or value == '' or value == 'None':
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None

def calculate_stats(values):
    """Calculate mean, variance, and SD for a list of values"""
    valid_values = [v for v in values if v is not None]
    n = len(valid_values)
    if n == 0:
        return {'n': 0, 'mean': None, 'variance': None, 'sd': None}

    mean = sum(valid_values) / n
    if n > 1:
        variance = sum((x - mean) ** 2 for x in valid_values) / (n - 1)
        sd = math.sqrt(variance)
    else:
        variance = 0
        sd = 0

    return {'n': n, 'mean': mean, 'variance': variance, 'sd': sd}

def main():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    output_dir = os.path.join(base_dir, 'analysis_results')
    os.makedirs(output_dir, exist_ok=True)

    # Load data
    pre_task = load_csv(os.path.join(processed_dir, 'pre-task.csv'))
    post_task = load_csv(os.path.join(processed_dir, 'post-task.csv'))
    experiments = load_csv(os.path.join(processed_dir, 'experiments.csv'))

    # Create participant to condition mapping
    pid_to_condition = {}
    for exp in experiments:
        pid = exp.get('participantId')
        condition = exp.get('condition')
        if pid and condition:
            pid_to_condition[pid] = condition

    # Create participant data mapping
    pre_by_pid = {row['participantId']: row for row in pre_task}
    post_by_pid = {row['participantId']: row for row in post_task}

    # Get all participant IDs that have both pre and post
    all_pids = set(pre_by_pid.keys()) & set(post_by_pid.keys())

    # Initialize data structures
    conditions = ['without_llm', 'with_llm', 'with_llm_extended']

    # Analysis data
    strategy_change = {'overall': [], 'by_condition': defaultdict(list)}
    confidence_change = {'overall': [], 'by_condition': defaultdict(list)}
    pre_approach_clarity = {'overall': [], 'by_condition': defaultdict(list)}
    post_implementation = {'overall': [], 'by_condition': defaultdict(list)}
    post_thinking_change = {'overall': [], 'by_condition': defaultdict(list)}

    # Collect data
    for pid in all_pids:
        pre = pre_by_pid[pid]
        post = post_by_pid[pid]
        condition = pid_to_condition.get(pid)

        if not condition:
            continue

        # 1. Strategy count change
        pre_count = count_strategies(pre)
        post_count = count_strategies(post)
        change = post_count - pre_count
        strategy_change['overall'].append(change)
        strategy_change['by_condition'][condition].append(change)

        # 2. Confidence change (post newStrategyConfidence - pre confidence)
        pre_conf = safe_float(pre.get('confidence'))
        post_conf = safe_float(post.get('newStrategyConfidence'))
        if pre_conf is not None and post_conf is not None:
            conf_change = post_conf - pre_conf
            confidence_change['overall'].append(conf_change)
            confidence_change['by_condition'][condition].append(conf_change)

        # 3. Pre approachClarity
        approach = safe_float(pre.get('approachClarity'))
        if approach is not None:
            pre_approach_clarity['overall'].append(approach)
            pre_approach_clarity['by_condition'][condition].append(approach)

        # 4. Post implementationLikelihood
        impl = safe_float(post.get('implementationLikelihood'))
        if impl is not None:
            post_implementation['overall'].append(impl)
            post_implementation['by_condition'][condition].append(impl)

        # 5. Post thinkingChange
        thinking = safe_float(post.get('thinkingChange'))
        if thinking is not None:
            post_thinking_change['overall'].append(thinking)
            post_thinking_change['by_condition'][condition].append(thinking)

    # Generate report
    report = []
    report.append("# Pre-Post Comparison Analysis Report")
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("## Overview")
    report.append("")
    report.append(f"- **Total Participants**: {len(all_pids)}")
    report.append(f"- **Participants with both pre and post data**: {len(all_pids)}")
    report.append("")
    report.append("### Condition Distribution")
    report.append("")
    report.append("| Condition | Count |")
    report.append("|-----------|-------|")
    for cond in conditions:
        count = len(strategy_change['by_condition'][cond])
        report.append(f"| {cond} | {count} |")
    report.append("")

    # Analysis 1: Strategy Count Change
    report.append("---")
    report.append("")
    report.append("## 1. Strategy Count Change (Pre → Post)")
    report.append("")
    report.append("### Overall")
    report.append("")
    overall_changes = strategy_change['overall']
    decreased = sum(1 for c in overall_changes if c < 0)
    same = sum(1 for c in overall_changes if c == 0)
    increased = sum(1 for c in overall_changes if c > 0)
    stats = calculate_stats(overall_changes)

    report.append(f"| Metric | Value |")
    report.append("|--------|-------|")
    report.append(f"| N | {stats['n']} |")
    report.append(f"| Mean Change | {stats['mean']:.3f} |")
    report.append(f"| SD | {stats['sd']:.3f} |")
    report.append(f"| Decreased | {decreased} ({decreased/len(overall_changes)*100:.1f}%) |")
    report.append(f"| Same | {same} ({same/len(overall_changes)*100:.1f}%) |")
    report.append(f"| Increased | {increased} ({increased/len(overall_changes)*100:.1f}%) |")
    report.append("")

    report.append("### By Condition")
    report.append("")
    report.append("| Condition | N | Mean | SD | Decreased | Same | Increased |")
    report.append("|-----------|---|------|----|-----------|----- |-----------|")
    for cond in conditions:
        changes = strategy_change['by_condition'][cond]
        if changes:
            stats = calculate_stats(changes)
            dec = sum(1 for c in changes if c < 0)
            sam = sum(1 for c in changes if c == 0)
            inc = sum(1 for c in changes if c > 0)
            report.append(f"| {cond} | {stats['n']} | {stats['mean']:.3f} | {stats['sd']:.3f} | {dec} ({dec/len(changes)*100:.1f}%) | {sam} ({sam/len(changes)*100:.1f}%) | {inc} ({inc/len(changes)*100:.1f}%) |")
    report.append("")

    # Analysis 2: Confidence Change
    report.append("---")
    report.append("")
    report.append("## 2. Confidence Change (newStrategyConfidence - confidence)")
    report.append("")
    report.append("### Overall")
    report.append("")
    stats = calculate_stats(confidence_change['overall'])
    report.append(f"| Metric | Value |")
    report.append("|--------|-------|")
    report.append(f"| N | {stats['n']} |")
    report.append(f"| Mean Change | {stats['mean']:.3f} |")
    report.append(f"| SD | {stats['sd']:.3f} |")
    report.append(f"| Variance | {stats['variance']:.3f} |")
    report.append("")

    report.append("### By Condition")
    report.append("")
    report.append("| Condition | N | Mean | SD | Variance |")
    report.append("|-----------|---|------|----|---------:|")
    for cond in conditions:
        stats = calculate_stats(confidence_change['by_condition'][cond])
        if stats['n'] > 0:
            report.append(f"| {cond} | {stats['n']} | {stats['mean']:.3f} | {stats['sd']:.3f} | {stats['variance']:.3f} |")
    report.append("")

    # Analysis 3: Pre approachClarity
    report.append("---")
    report.append("")
    report.append("## 3. Pre-Task: Approach Clarity")
    report.append("")
    report.append("### Overall")
    report.append("")
    stats = calculate_stats(pre_approach_clarity['overall'])
    report.append(f"| Metric | Value |")
    report.append("|--------|-------|")
    report.append(f"| N | {stats['n']} |")
    report.append(f"| Mean | {stats['mean']:.3f} |")
    report.append(f"| SD | {stats['sd']:.3f} |")
    report.append(f"| Variance | {stats['variance']:.3f} |")
    report.append("")

    report.append("### By Condition")
    report.append("")
    report.append("| Condition | N | Mean | SD | Variance |")
    report.append("|-----------|---|------|----|---------:|")
    for cond in conditions:
        stats = calculate_stats(pre_approach_clarity['by_condition'][cond])
        if stats['n'] > 0:
            report.append(f"| {cond} | {stats['n']} | {stats['mean']:.3f} | {stats['sd']:.3f} | {stats['variance']:.3f} |")
    report.append("")

    # Analysis 4: Post implementationLikelihood
    report.append("---")
    report.append("")
    report.append("## 4. Post-Task: Implementation Likelihood")
    report.append("")
    report.append("### Overall")
    report.append("")
    stats = calculate_stats(post_implementation['overall'])
    report.append(f"| Metric | Value |")
    report.append("|--------|-------|")
    report.append(f"| N | {stats['n']} |")
    report.append(f"| Mean | {stats['mean']:.3f} |")
    report.append(f"| SD | {stats['sd']:.3f} |")
    report.append(f"| Variance | {stats['variance']:.3f} |")
    report.append("")

    report.append("### By Condition")
    report.append("")
    report.append("| Condition | N | Mean | SD | Variance |")
    report.append("|-----------|---|------|----|---------:|")
    for cond in conditions:
        stats = calculate_stats(post_implementation['by_condition'][cond])
        if stats['n'] > 0:
            report.append(f"| {cond} | {stats['n']} | {stats['mean']:.3f} | {stats['sd']:.3f} | {stats['variance']:.3f} |")
    report.append("")

    # Analysis 5: Post thinkingChange
    report.append("---")
    report.append("")
    report.append("## 5. Post-Task: Thinking Change")
    report.append("")
    report.append("### Overall")
    report.append("")
    stats = calculate_stats(post_thinking_change['overall'])
    report.append(f"| Metric | Value |")
    report.append("|--------|-------|")
    report.append(f"| N | {stats['n']} |")
    report.append(f"| Mean | {stats['mean']:.3f} |")
    report.append(f"| SD | {stats['sd']:.3f} |")
    report.append(f"| Variance | {stats['variance']:.3f} |")
    report.append("")

    report.append("### By Condition")
    report.append("")
    report.append("| Condition | N | Mean | SD | Variance |")
    report.append("|-----------|---|------|----|---------:|")
    for cond in conditions:
        stats = calculate_stats(post_thinking_change['by_condition'][cond])
        if stats['n'] > 0:
            report.append(f"| {cond} | {stats['n']} | {stats['mean']:.3f} | {stats['sd']:.3f} | {stats['variance']:.3f} |")
    report.append("")

    # Write report
    output_path = os.path.join(output_dir, 'pre_post_analysis.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"Report saved to: {output_path}")
    print("\n" + "="*60)
    print('\n'.join(report))

if __name__ == '__main__':
    main()
