#!/usr/bin/env python3
"""
Survey Analysis for Reading Experiment
Likert Scale Analysis with Stacked Bar Chart Visualization
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from collections import defaultdict

# Paths
DATA_DIR = Path(__file__).parent.parent / "data" / "processed"
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

# Define survey item groups
SURVEY_GROUPS = {
    "NASA-TLX (Task Load)": {
        "items": [
            "nasaTLX_mentalDemand",
            "nasaTLX_physicalDemand",
            "nasaTLX_temporalDemand",
            "nasaTLX_performance",
            "nasaTLX_effort",
            "nasaTLX_frustration"
        ],
        "labels": [
            "Mental Demand",
            "Physical Demand",
            "Temporal Demand",
            "Performance",
            "Effort",
            "Frustration"
        ],
        "scale": 7,
        "scale_description": "1 = Very Low, 7 = Very High",
        "reverse_items": ["nasaTLX_performance"]
    },
    "Self-Efficacy": {
        "items": [
            "selfEfficacy_overallGoal",
            "selfEfficacy_authorsReasoning",
            "selfEfficacy_connectingIdeas",
            "selfEfficacy_ownIdeas",
            "selfEfficacy_alternativePerspectives",
            "selfEfficacy_verifyCredibility",
            "selfEfficacy_questionClaims",
            "selfEfficacy_broaderImplications"
        ],
        "labels": [
            "Overall Goal",
            "Author's Reasoning",
            "Connecting Ideas",
            "Own Ideas",
            "Alternative Perspectives",
            "Verify Credibility",
            "Question Claims",
            "Broader Implications"
        ],
        "scale": 7,
        "scale_description": "1 = Strongly Disagree, 7 = Strongly Agree"
    },
    "LLM Usefulness": {
        "items": [
            "llmUsefulness_overall",
            "llmUsefulness_conceptHelp",
            "llmUsefulness_findingsHelp",
            "llmUsefulness_practicalHelp",
            "llmUsefulness_timeSaving"
        ],
        "labels": [
            "Overall",
            "Concept Help",
            "Findings Help",
            "Practical Help",
            "Time Saving"
        ],
        "scale": 7,
        "scale_description": "1 = Strongly Disagree, 7 = Strongly Agree",
        "llm_only": True
    },
    "LLM Trust": {
        "items": [
            "llmTrust_competence",
            "llmTrust_accuracy",
            "llmTrust_benevolence",
            "llmTrust_reliability",
            "llmTrust_comfortActing",
            "llmTrust_comfortUsing"
        ],
        "labels": [
            "Competence",
            "Accuracy",
            "Benevolence",
            "Reliability",
            "Comfort Acting",
            "Comfort Using"
        ],
        "scale": 7,
        "scale_description": "1 = Strongly Disagree, 7 = Strongly Agree",
        "llm_only": True
    },
    "Attention Check": {
        "items": [
            "attentionCheck_focus",
            "attentionCheck_stronglyDisagreeCheck"
        ],
        "labels": [
            "Focus Level",
            "Strongly Disagree Check"
        ],
        "scale": 7,
        "scale_description": "1-5 (Focus), 1 = Strongly Disagree (Check)",
        "no_condition_split": True
    },
    "AI Usage Frequency": {
        "items": ["aiUsage_frequency"],
        "labels": ["AI Usage Frequency"],
        "scale": "categorical",
        "scale_description": "never / rarely / sometimes / often / very-often",
        "categories": ["never", "rarely", "sometimes", "often", "very-often"],
        "no_condition_split": True
    }
}

def load_data():
    """Load merged data"""
    data = pd.read_csv(DATA_DIR / "merged_all.csv")
    return data

def calculate_likert_distribution(data, item, scale=7):
    """Calculate distribution of responses for a Likert item"""
    counts = data[item].value_counts().sort_index()
    total = len(data[item].dropna())

    distribution = {}
    for i in range(1, scale + 1):
        count = counts.get(i, 0)
        distribution[i] = {
            'count': int(count),
            'percentage': round(count / total * 100, 1) if total > 0 else 0
        }

    return distribution, total

def calculate_statistics(data, items, scale='numeric'):
    """Calculate descriptive statistics for survey items"""
    stats = {}
    for item in items:
        valid_data = data[item].dropna()
        if len(valid_data) > 0:
            # Check if numeric
            if scale == 'categorical' or not pd.api.types.is_numeric_dtype(valid_data):
                stats[item] = {
                    'n': len(valid_data),
                    'mean': None,
                    'std': None,
                    'median': None,
                    'min': None,
                    'max': None
                }
            else:
                stats[item] = {
                    'n': len(valid_data),
                    'mean': round(valid_data.mean(), 2),
                    'std': round(valid_data.std(), 2),
                    'median': round(valid_data.median(), 2),
                    'min': int(valid_data.min()),
                    'max': int(valid_data.max())
                }
    return stats

def analyze_by_condition(survey, group_name, group_config):
    """Analyze survey items by experimental condition"""
    items = group_config['items']
    labels = group_config['labels']
    scale = group_config.get('scale', 7)
    scale_description = group_config.get('scale_description', '')
    llm_only = group_config.get('llm_only', False)
    no_condition_split = group_config.get('no_condition_split', False)

    results = {
        'group_name': group_name,
        'items': [],
        'by_condition': {},
        'no_condition_split': no_condition_split,
        'scale': scale if scale != 'categorical' else 'categorical',
        'scale_description': scale_description
    }

    if no_condition_split:
        # Analyze all participants together
        conditions = ['all']
        results['by_condition']['all'] = {
            'n': len(survey),
            'stats': calculate_statistics(survey, items, scale)
        }
    else:
        conditions = ['with_llm', 'with_llm_extended', 'without_llm']
        if llm_only:
            conditions = ['with_llm', 'with_llm_extended']

        for condition in conditions:
            cond_data = survey[survey['condition'] == condition]
            results['by_condition'][condition] = {
                'n': len(cond_data),
                'stats': calculate_statistics(cond_data, items, scale)
            }

    # Per-item analysis
    for item, label in zip(items, labels):
        item_result = {
            'item': item,
            'label': label,
            'distributions': {}
        }

        for condition in conditions:
            if no_condition_split:
                cond_data = survey
            else:
                cond_data = survey[survey['condition'] == condition]
            if scale != 'categorical':
                dist, total = calculate_likert_distribution(cond_data, item, scale)
                item_result['distributions'][condition] = {
                    'distribution': dist,
                    'total': total
                }
            else:
                # Categorical handling
                categories = group_config.get('categories', [])
                counts = cond_data[item].value_counts()
                total = len(cond_data[item].dropna())
                dist = {}
                for cat in categories:
                    count = counts.get(cat, 0)
                    dist[cat] = {
                        'count': int(count),
                        'percentage': round(count / total * 100, 1) if total > 0 else 0
                    }
                item_result['distributions'][condition] = {
                    'distribution': dist,
                    'total': total
                }

        results['items'].append(item_result)

    return results

def analyze_demographics(survey):
    """Analyze demographic data"""
    results = {}

    # Age
    age_data = survey['demographics_age'].dropna()
    results['age'] = {
        'n': len(age_data),
        'mean': round(age_data.mean(), 1),
        'std': round(age_data.std(), 1),
        'min': int(age_data.min()),
        'max': int(age_data.max()),
        'distribution': {}
    }
    # Age groups
    age_bins = [0, 25, 35, 45, 55, 65, 100]
    age_labels = ['18-24', '25-34', '35-44', '45-54', '55-64', '65+']
    age_groups = pd.cut(age_data, bins=age_bins, labels=age_labels)
    for label in age_labels:
        count = (age_groups == label).sum()
        results['age']['distribution'][label] = {
            'count': int(count),
            'percentage': round(count / len(age_data) * 100, 1)
        }

    # Gender
    gender_counts = survey['demographics_gender'].value_counts()
    total_gender = len(survey['demographics_gender'].dropna())
    results['gender'] = {
        'n': total_gender,
        'distribution': {}
    }
    for gender in gender_counts.index:
        results['gender']['distribution'][gender] = {
            'count': int(gender_counts[gender]),
            'percentage': round(gender_counts[gender] / total_gender * 100, 1)
        }

    # Education
    edu_counts = survey['demographics_education'].value_counts()
    total_edu = len(survey['demographics_education'].dropna())
    results['education'] = {
        'n': total_edu,
        'distribution': {}
    }
    edu_order = ['high-school', 'some-college', 'bachelor', 'master', 'doctorate', 'other']
    for edu in edu_order:
        if edu in edu_counts.index:
            results['education']['distribution'][edu] = {
                'count': int(edu_counts[edu]),
                'percentage': round(edu_counts[edu] / total_edu * 100, 1)
            }

    # English Proficiency
    eng_counts = survey['demographics_englishProficiency'].value_counts()
    total_eng = len(survey['demographics_englishProficiency'].dropna())
    results['english_proficiency'] = {
        'n': total_eng,
        'distribution': {}
    }
    eng_order = ['native', 'fluent', 'advanced', 'intermediate', 'beginner']
    for level in eng_order:
        if level in eng_counts.index:
            results['english_proficiency']['distribution'][level] = {
                'count': int(eng_counts[level]),
                'percentage': round(eng_counts[level] / total_eng * 100, 1)
            }

    return results

def generate_html_visualization(all_results, demographics):
    """Generate HTML page with stacked bar charts"""

    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Survey Analysis - Reading Experiment</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f8f9fa;
            padding: 30px;
            color: #333;
        }
        h1 { margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; }

        .section {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 30px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .section-title {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e9ecef;
        }

        .condition-tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .condition-tab {
            padding: 8px 16px;
            border: none;
            background: #e9ecef;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }
        .condition-tab.active {
            background: #333;
            color: white;
        }
        .condition-tab:hover:not(.active) {
            background: #dee2e6;
        }

        .chart-container {
            margin-bottom: 25px;
        }
        .chart-row {
            display: flex;
            align-items: center;
            margin-bottom: 12px;
        }
        .chart-label {
            width: 200px;
            font-size: 13px;
            color: #555;
            flex-shrink: 0;
            padding-right: 15px;
        }
        .chart-label .n-count {
            color: #999;
            font-size: 11px;
        }
        .chart-bar-container {
            flex: 1;
            height: 32px;
            display: flex;
            border-radius: 4px;
            overflow: hidden;
            background: #f1f3f5;
        }
        .chart-bar-segment {
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            font-weight: 500;
            color: white;
            transition: all 0.3s;
            min-width: 0;
        }
        .chart-bar-segment:hover {
            filter: brightness(1.1);
        }
        .chart-bar-segment span {
            opacity: 0;
            transition: opacity 0.2s;
        }
        .chart-bar-segment:hover span,
        .chart-bar-segment[style*="width: 1"]:not([style*="width: 10"]) span,
        .chart-bar-segment[style*="width: 2"] span,
        .chart-bar-segment[style*="width: 3"] span,
        .chart-bar-segment[style*="width: 4"] span,
        .chart-bar-segment[style*="width: 5"] span {
            opacity: 1;
        }


        /* 7-point Likert colors (diverging) */
        .likert-1 { background: #c0392b; }
        .likert-2 { background: #e74c3c; }
        .likert-3 { background: #f39c12; }
        .likert-4 { background: #95a5a6; }
        .likert-5 { background: #82c91e; }
        .likert-6 { background: #2ecc71; }
        .likert-7 { background: #27ae60; }

        .legend {
            display: flex;
            justify-content: center;
            gap: 15px;
            margin-bottom: 25px;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 6px;
            font-size: 12px;
        }
        .legend-color {
            width: 16px;
            height: 16px;
            border-radius: 3px;
        }

        /* Demographics */
        .demo-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 25px;
        }
        .demo-card {
            background: #f8f9fa;
            border-radius: 8px;
            padding: 20px;
        }
        .demo-card h4 {
            font-size: 14px;
            color: #666;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .demo-bar-row {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
        }
        .demo-bar-label {
            width: 100px;
            font-size: 12px;
            color: #555;
        }
        .demo-bar-bg {
            flex: 1;
            height: 20px;
            background: #e9ecef;
            border-radius: 3px;
            overflow: hidden;
        }
        .demo-bar-fill {
            height: 100%;
            background: #4c6ef5;
            display: flex;
            align-items: center;
            padding-left: 8px;
            font-size: 11px;
            color: white;
            font-weight: 500;
        }
        .demo-bar-value {
            width: 60px;
            text-align: right;
            font-size: 12px;
            color: #666;
            padding-left: 10px;
        }

        /* Stats table */
        .stats-table {
            width: 100%;
            border-collapse: collapse;
            font-size: 13px;
            margin-top: 15px;
        }
        .stats-table th {
            background: #f1f3f5;
            padding: 10px;
            text-align: left;
            font-weight: 600;
        }
        .stats-table td {
            padding: 10px;
            border-bottom: 1px solid #e9ecef;
        }
        .stats-table tr:hover {
            background: #f8f9fa;
        }

        .toggle-btn {
            background: none;
            border: 1px solid #dee2e6;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-left: 10px;
        }
        .toggle-btn:hover {
            background: #f1f3f5;
        }

        .hidden { display: none; }
    </style>
</head>
<body>
    <h1>Survey Analysis Results</h1>
    <p class="subtitle">Reading Experiment - Likert Scale Responses by Condition</p>

    <div class="legend">
        <div class="legend-item"><div class="legend-color likert-1"></div><span>1 (Strongly Disagree)</span></div>
        <div class="legend-item"><div class="legend-color likert-2"></div><span>2</span></div>
        <div class="legend-item"><div class="legend-color likert-3"></div><span>3</span></div>
        <div class="legend-item"><div class="legend-color likert-4"></div><span>4 (Neutral)</span></div>
        <div class="legend-item"><div class="legend-color likert-5"></div><span>5</span></div>
        <div class="legend-item"><div class="legend-color likert-6"></div><span>6</span></div>
        <div class="legend-item"><div class="legend-color likert-7"></div><span>7 (Strongly Agree)</span></div>
    </div>

    <div id="survey-sections"></div>

    <div class="section">
        <div class="section-title">Demographics</div>
        <div class="demo-grid" id="demographics"></div>
    </div>

    <script>
    const surveyData = SURVEY_DATA_PLACEHOLDER;
    const demographicsData = DEMOGRAPHICS_DATA_PLACEHOLDER;

    const conditionLabels = {
        'with_llm': 'With LLM',
        'with_llm_extended': 'With LLM Extended',
        'without_llm': 'Without LLM',
        'all': 'All Participants'
    };

    function renderSurveySections() {
        const container = document.getElementById('survey-sections');
        let html = '';

        surveyData.forEach((group, groupIndex) => {
            const conditions = Object.keys(group.by_condition);
            const noConditionSplit = group.no_condition_split;

            html += `
                <div class="section" data-group="${groupIndex}">
                    <div class="section-title">
                        ${group.group_name}
                        <button class="toggle-btn" onclick="toggleTable(${groupIndex})">Show Table</button>
                    </div>
                    <p style="color: #888; font-size: 12px; margin-bottom: 15px; font-style: italic;">
                        Scale: ${group.scale_description || (group.scale === 'categorical' ? 'Categorical' : '1-' + group.scale + ' Likert')}
                    </p>
            `;

            // Only show condition tabs if not no_condition_split
            if (!noConditionSplit) {
                html += `
                    <div class="condition-tabs">
                        ${conditions.map((cond, i) => `
                            <button class="condition-tab ${i === 0 ? 'active' : ''}"
                                    onclick="switchCondition(${groupIndex}, '${cond}')">
                                ${conditionLabels[cond]} (n=${group.by_condition[cond].n})
                            </button>
                        `).join('')}
                    </div>
                `;
            } else {
                html += `<p style="color: #666; font-size: 13px; margin-bottom: 15px;">All Participants (n=${group.by_condition['all'].n})</p>`;
            }

            html += `
                    <div class="chart-container" id="chart-${groupIndex}">
                        ${renderChart(group, conditions[0])}
                    </div>
                    <div class="stats-table-container hidden" id="table-${groupIndex}">
                        ${renderStatsTable(group)}
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;
    }

    function renderChart(group, condition) {
        let html = '';

        group.items.forEach(item => {
            const dist = item.distributions[condition];
            if (!dist) return;

            const total = dist.total;
            const distribution = dist.distribution;
            const stats = group.by_condition[condition].stats[item.item];

            // Check if categorical
            const isCategorical = typeof Object.keys(distribution)[0] === 'string' &&
                                  isNaN(parseInt(Object.keys(distribution)[0]));

            html += `
                <div class="chart-row">
                    <div class="chart-label">
                        ${item.label}
                        <span class="n-count">(n=${total})</span>
                    </div>
                    <div class="chart-bar-container">
            `;

            if (isCategorical) {
                // Categorical bar
                const catColors = ['#e74c3c', '#f39c12', '#95a5a6', '#2ecc71', '#27ae60'];
                const categories = Object.keys(distribution);
                categories.forEach((cat, i) => {
                    const pct = distribution[cat].percentage;
                    if (pct > 0) {
                        html += `
                            <div class="chart-bar-segment"
                                 style="width: ${pct}%; background: ${catColors[i % catColors.length]};"
                                 title="${cat}: ${pct}%">
                                <span>${pct >= 8 ? pct + '%' : ''}</span>
                            </div>
                        `;
                    }
                });
            } else {
                // Likert bar
                for (let i = 1; i <= 7; i++) {
                    const pct = distribution[i]?.percentage || 0;
                    if (pct > 0) {
                        html += `
                            <div class="chart-bar-segment likert-${i}"
                                 style="width: ${pct}%;"
                                 title="Score ${i}: ${pct}%">
                                <span>${pct >= 8 ? pct + '%' : ''}</span>
                            </div>
                        `;
                    }
                }
            }

            html += `
                    </div>
                </div>
            `;
        });

        return html;
    }

    function renderStatsTable(group) {
        const conditions = Object.keys(group.by_condition);

        let html = `
            <table class="stats-table">
                <thead>
                    <tr>
                        <th>Item</th>
                        ${conditions.map(c => `<th>${conditionLabels[c]}<br>(n=${group.by_condition[c].n})</th>`).join('')}
                    </tr>
                </thead>
                <tbody>
        `;

        group.items.forEach(item => {
            html += `<tr><td>${item.label}</td>`;
            conditions.forEach(cond => {
                const dist = item.distributions[cond];
                if (dist) {
                    // Show mode (most frequent response)
                    const distribution = dist.distribution;
                    let mode = '-';
                    let maxPct = 0;
                    for (const [val, data] of Object.entries(distribution)) {
                        if (data.percentage > maxPct) {
                            maxPct = data.percentage;
                            mode = val;
                        }
                    }
                    html += `<td>Mode: ${mode} (${maxPct}%)</td>`;
                } else {
                    html += `<td>-</td>`;
                }
            });
            html += `</tr>`;
        });

        html += `</tbody></table>`;
        return html;
    }

    function switchCondition(groupIndex, condition) {
        const section = document.querySelector(`[data-group="${groupIndex}"]`);
        const tabs = section.querySelectorAll('.condition-tab');
        tabs.forEach(tab => tab.classList.remove('active'));
        event.target.classList.add('active');

        const group = surveyData[groupIndex];
        document.getElementById(`chart-${groupIndex}`).innerHTML = renderChart(group, condition);
    }

    function toggleTable(groupIndex) {
        const table = document.getElementById(`table-${groupIndex}`);
        const chart = document.getElementById(`chart-${groupIndex}`);
        const btn = event.target;

        if (table.classList.contains('hidden')) {
            table.classList.remove('hidden');
            chart.classList.add('hidden');
            btn.textContent = 'Show Chart';
        } else {
            table.classList.add('hidden');
            chart.classList.remove('hidden');
            btn.textContent = 'Show Table';
        }
    }

    function renderDemographics() {
        const container = document.getElementById('demographics');

        const demoConfigs = [
            { key: 'age', title: 'Age Distribution', subtitle: `Mean: ${demographicsData.age.mean} years` },
            { key: 'gender', title: 'Gender' },
            { key: 'education', title: 'Education Level' },
            { key: 'english_proficiency', title: 'English Proficiency' }
        ];

        let html = '';

        demoConfigs.forEach(config => {
            const data = demographicsData[config.key];
            if (!data) return;

            html += `
                <div class="demo-card">
                    <h4>${config.title} ${config.subtitle ? `<span style="font-weight:normal">(${config.subtitle})</span>` : ''}</h4>
            `;

            const dist = data.distribution;
            const maxPct = Math.max(...Object.values(dist).map(d => d.percentage));

            Object.entries(dist).forEach(([label, values]) => {
                const barWidth = (values.percentage / maxPct) * 100;
                html += `
                    <div class="demo-bar-row">
                        <div class="demo-bar-label">${label}</div>
                        <div class="demo-bar-bg">
                            <div class="demo-bar-fill" style="width: ${barWidth}%">
                                ${values.percentage >= 15 ? values.percentage + '%' : ''}
                            </div>
                        </div>
                        <div class="demo-bar-value">${values.count} (${values.percentage}%)</div>
                    </div>
                `;
            });

            html += `</div>`;
        });

        container.innerHTML = html;
    }

    renderSurveySections();
    renderDemographics();
    </script>
</body>
</html>
"""

    return html

def generate_markdown_report(all_results, demographics):
    """Generate markdown report with tables"""

    md = """# Survey Analysis Report

**분석 대상**: 전체 참여자 (with_llm, with_llm_extended, without_llm)
**분석 일자**: 2025-12-23

---

"""

    for group in all_results:
        md += f"## {group['group_name']}\n\n"

        # Scale info
        scale_desc = group.get('scale_description', '')
        if scale_desc:
            md += f"**Scale**: {scale_desc}\n\n"

        # Distribution table
        conditions = list(group['by_condition'].keys())
        first_cond = conditions[0]
        no_condition_split = group.get('no_condition_split', False)

        if no_condition_split:
            md += f"### 응답 분포 (전체 참여자)\n\n"
        else:
            md += f"### 응답 분포 ({first_cond})\n\n"

        # Check if categorical
        first_item_dist = group['items'][0]['distributions'].get(first_cond, {}).get('distribution', {})
        is_categorical = first_item_dist and isinstance(list(first_item_dist.keys())[0], str) and not list(first_item_dist.keys())[0].isdigit()

        if is_categorical:
            # Categorical table
            categories = list(first_item_dist.keys())
            md += "| Item |"
            for cat in categories:
                md += f" {cat} |"
            md += "\n"
            md += "|------|" + "------|" * len(categories) + "\n"

            for item in group['items']:
                dist = item['distributions'].get(first_cond, {}).get('distribution', {})
                md += f"| {item['label']} |"
                for cat in categories:
                    pct = dist.get(cat, {}).get('percentage', 0)
                    md += f" {pct}% |"
                md += "\n"
        else:
            md += "| Item | 1 | 2 | 3 | 4 | 5 | 6 | 7 |\n"
            md += "|------|---|---|---|---|---|---|---|\n"

            for item in group['items']:
                dist = item['distributions'].get(first_cond, {}).get('distribution', {})
                md += f"| {item['label']} |"
                for i in range(1, 8):
                    pct = dist.get(i, {}).get('percentage', 0)
                    md += f" {pct}% |"
                md += "\n"

        md += "\n---\n\n"

    # Demographics
    md += "## Demographics (인구통계)\n\n"

    md += f"### Age (연령)\n"
    md += f"- N = {demographics['age']['n']}\n"
    md += f"- Mean = {demographics['age']['mean']} years (SD = {demographics['age']['std']})\n"
    md += f"- Range: {demographics['age']['min']} - {demographics['age']['max']}\n\n"

    md += "| 연령대 | 인원 | 비율 |\n"
    md += "|--------|------|------|\n"
    for label, values in demographics['age']['distribution'].items():
        md += f"| {label} | {values['count']} | {values['percentage']}% |\n"
    md += "\n"

    md += f"### Gender (성별)\n\n"
    md += "| 성별 | 인원 | 비율 |\n"
    md += "|------|------|------|\n"
    for label, values in demographics['gender']['distribution'].items():
        md += f"| {label} | {values['count']} | {values['percentage']}% |\n"
    md += "\n"

    md += f"### Education (학력)\n\n"
    md += "| 학력 | 인원 | 비율 |\n"
    md += "|------|------|------|\n"
    for label, values in demographics['education']['distribution'].items():
        md += f"| {label} | {values['count']} | {values['percentage']}% |\n"
    md += "\n"

    md += f"### English Proficiency (영어 능숙도)\n\n"
    md += "| 수준 | 인원 | 비율 |\n"
    md += "|------|------|------|\n"
    for label, values in demographics['english_proficiency']['distribution'].items():
        md += f"| {label} | {values['count']} | {values['percentage']}% |\n"
    md += "\n"

    md += """---

## 인구통계 시각화 제안

1. **Age**: 히스토그램 또는 박스플롯 (조건별 비교)
2. **Gender**: 파이 차트 또는 도넛 차트
3. **Education**: 수평 막대 차트 (순서대로 정렬)
4. **English Proficiency**: 수평 막대 차트

### 추천 시각화 조합
- **조건별 비교 시**: Grouped bar chart로 각 인구통계 변수의 조건별 분포 비교
- **전체 샘플 기술 시**: 위 HTML 파일의 Demographics 섹션 참조
- **논문/보고서용**: 표 형태 (본 문서의 표 활용)

---

## 생성된 파일

| 파일명 | 설명 |
|--------|------|
| `survey_analysis.html` | 인터랙티브 시각화 (스택형 바 차트) |
| `survey_stats.json` | 전체 통계 데이터 (JSON) |
| `SURVEY_ANALYSIS_REPORT.md` | 본 보고서 |
"""

    return md

def main():
    print("Loading survey data...")
    survey = load_data()
    print(f"  Total responses: {len(survey)}")

    # Analyze each group
    all_results = []
    for group_name, group_config in SURVEY_GROUPS.items():
        print(f"\nAnalyzing: {group_name}")
        result = analyze_by_condition(survey, group_name, group_config)
        all_results.append(result)

    # Demographics
    print("\nAnalyzing demographics...")
    demographics = analyze_demographics(survey)

    # Save JSON
    print("\nSaving results...")
    with open(OUTPUT_DIR / "survey_stats.json", 'w', encoding='utf-8') as f:
        json.dump({
            'survey_groups': all_results,
            'demographics': demographics
        }, f, indent=2, ensure_ascii=False)

    # Generate HTML
    html = generate_html_visualization(all_results, demographics)
    html = html.replace('SURVEY_DATA_PLACEHOLDER', json.dumps(all_results, ensure_ascii=False))
    html = html.replace('DEMOGRAPHICS_DATA_PLACEHOLDER', json.dumps(demographics, ensure_ascii=False))

    with open(OUTPUT_DIR / "survey_analysis.html", 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  Saved: {OUTPUT_DIR / 'survey_analysis.html'}")

    # Generate Markdown
    md = generate_markdown_report(all_results, demographics)
    with open(OUTPUT_DIR / "SURVEY_ANALYSIS_REPORT.md", 'w', encoding='utf-8') as f:
        f.write(md)
    print(f"  Saved: {OUTPUT_DIR / 'SURVEY_ANALYSIS_REPORT.md'}")

    # Print summary
    print("\n" + "="*60)
    print("SURVEY ANALYSIS SUMMARY")
    print("="*60)

    for group in all_results:
        print(f"\n{group['group_name']}")
        print("-" * 40)
        for cond, data in group['by_condition'].items():
            print(f"  {cond}: n={data['n']}")

if __name__ == "__main__":
    main()
