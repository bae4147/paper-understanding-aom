#!/usr/bin/env python3
"""
Data Preprocessing Script
- Filters experiments to 1 per participant (completed only)
- Classifies US/UK based on Prolific file
- Outputs normalized CSV files

Data Filtering Rules:
1. If participant has 1 completed experiment -> use it
2. If participant has 2+ completed experiments -> use the latest (by createdAt), report duplicates
3. If participant has 0 completed experiments -> exclude

US/UK Classification:
- If participantId exists in Prolific US export file -> US
- Otherwise -> UK

Expected counts: US=124, UK=176
"""

import json
import csv
import os
import re
from datetime import datetime, timezone, timedelta
from collections import defaultdict

# Paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'raw', 'raw_data_20251223_143357.json')
PROLIFIC_US_PATH = os.path.join(SCRIPT_DIR, '..', 'data', 'raw', 'prolific_demographic_export_6941e12aceea30a8ba0e1f90.csv')
OUTPUT_DIR = os.path.join(SCRIPT_DIR, '..', 'data', 'processed')
REPORT_DIR = os.path.join(SCRIPT_DIR, '..', 'analysis_results')

# IDs to exclude (test data)
EXCLUDE_IDS = [
    'Q1. Please list the specific strategies you used to make this meeting more effective. * Enter one strategy per field. Click "Add Strategy" to add more.  1. Strategy 1   Add Strategy How confident are you that these strategies improved the meeting\'s effectiveness? * Not at all confident 1 2 3 4 5 6 7 Extremely confident Q2. To what extent did you have a clear, intentional approach to running this meeting effectively? * No clear approach 1 2 3 4 5 6 7 Very clear and intentional Q3. Please briefly describe any challenges or difficulties you experienced during this meeting. * Continue to Reading →',
    'C8D1FZR6'
]

# Prolific ID pattern (24 hex characters)
PROLIFIC_ID_PATTERN = re.compile(r'^[a-f0-9]{24}$')


def normalize_participant_id(pid):
    """Remove @auth.prolific.com or @email.prolific.com suffix"""
    if pid and '@auth.prolific.com' in pid:
        return pid.replace('@auth.prolific.com', '')
    if pid and '@email.prolific.com' in pid:
        return pid.replace('@email.prolific.com', '')
    return pid


def load_prolific_us_ids():
    """Load US participant IDs from Prolific export"""
    import csv
    with open(PROLIFIC_US_PATH, 'r') as f:
        reader = csv.DictReader(f)
        return set(row['Participant id'] for row in reader)


def get_created_at(exp):
    """Extract createdAt datetime from experiment"""
    ts_str = exp.get('preTask', {}).get('completedAt')
    if ts_str and isinstance(ts_str, str):
        try:
            return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        except:
            pass
    return None


def get_completed_at(exp):
    """Extract completedAt datetime from experiment"""
    ts_str = exp.get('postStudySurvey', {}).get('surveyCompletedAt')
    if ts_str and isinstance(ts_str, str):
        try:
            return datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
        except:
            pass
    return None


def filter_experiments(data):
    """
    Filter experiments to 1 per participant.
    Returns: (filtered_data, report_info)
    """
    # Group by participant
    by_participant = defaultdict(list)

    for exp in data:
        pid_raw = exp.get('participantId')

        # Skip excluded IDs
        if pid_raw in EXCLUDE_IDS:
            continue

        pid = normalize_participant_id(pid_raw)
        if not pid:
            continue

        by_participant[pid].append(exp)

    filtered = []
    report = {
        'total_participants_raw': len(by_participant),
        'excluded_no_completed': [],
        'multiple_completed': [],
        'invalid_pid_format': []
    }

    for pid, experiments in by_participant.items():
        # Check PID format
        if not PROLIFIC_ID_PATTERN.match(pid):
            report['invalid_pid_format'].append(pid)

        # Filter to completed only
        completed = [e for e in experiments if e.get('status') == 'completed']

        if len(completed) == 0:
            # Rule 3: No completed experiments -> exclude
            report['excluded_no_completed'].append({
                'pid': pid,
                'total_experiments': len(experiments),
                'statuses': [e.get('status') for e in experiments]
            })
            continue

        if len(completed) == 1:
            # Rule 1: Exactly 1 completed -> use it
            filtered.append(completed[0])
        else:
            # Rule 2: Multiple completed -> use latest, report
            # Sort by createdAt descending
            completed_sorted = sorted(
                completed,
                key=lambda e: get_created_at(e) or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True
            )
            latest = completed_sorted[0]
            filtered.append(latest)

            report['multiple_completed'].append({
                'pid': pid,
                'count': len(completed),
                'used_experiment_id': latest.get('experimentId', latest.get('_experimentDocId')),
                'all_created_at': [str(get_created_at(e)) for e in completed_sorted]
            })

    return filtered, report


def classify_country(experiments, us_ids):
    """Add country field to each experiment based on Prolific file"""
    for exp in experiments:
        pid = normalize_participant_id(exp.get('participantId'))
        if pid in us_ids:
            exp['_country'] = 'US'
        else:
            exp['_country'] = 'UK'
    return experiments


def write_csv(filepath, rows, fieldnames=None):
    """Write rows to CSV file"""
    if not rows:
        print(f"  Skipped (no data): {filepath}")
        return False

    if fieldnames is None:
        fieldnames = list(rows[0].keys())

    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Saved: {filepath} ({len(rows)} rows)")
    return True


def generate_participants_csv(experiments, output_dir):
    """Generate participants.csv"""
    rows = []
    for exp in experiments:
        pid = normalize_participant_id(exp.get('participantId'))
        rows.append({
            'participantId': pid,
            'experimentId': exp.get('experimentId', exp.get('_experimentDocId')),
            'createdAt': exp.get('preTask', {}).get('completedAt'),
            'completedAt': exp.get('postStudySurvey', {}).get('surveyCompletedAt'),
            'country': exp.get('_country')
        })

    write_csv(os.path.join(output_dir, 'participants.csv'), rows)
    return rows


def generate_experiments_csv(experiments, output_dir):
    """Generate experiments.csv"""
    rows = []
    for exp in experiments:
        pid = normalize_participant_id(exp.get('participantId'))
        exp_id = exp.get('experimentId', exp.get('_experimentDocId'))

        rows.append({
            'participantId': pid,
            'experimentId': exp_id,
            'condition': exp.get('condition'),
            'status': exp.get('status'),
            'createdAt': exp.get('preTask', {}).get('completedAt'),
            'startedAt': exp.get('reading', {}).get('startedAt') if exp.get('reading') else None,
            'completedAt': exp.get('postStudySurvey', {}).get('surveyCompletedAt'),
            'reading_id': f"{exp_id}_reading" if exp.get('reading') else '',
            'quiz_id': f"{exp_id}_quiz" if exp.get('quiz') else '',
            'review_id': '',  # No review data in current structure
            'llm_interaction_id': f"{exp_id}_llm" if exp.get('llmInteraction', {}).get('messages') else ''
        })

    write_csv(os.path.join(output_dir, 'experiments.csv'), rows)
    return rows


def generate_reading_events_csv(experiments, output_dir):
    """Generate reading_events.csv"""
    rows = []
    for exp in experiments:
        pid = normalize_participant_id(exp.get('participantId'))
        exp_id = exp.get('experimentId', exp.get('_experimentDocId'))
        events = exp.get('reading', {}).get('events', [])

        for event in events:
            rows.append({
                'participantId': pid,
                'experimentId': exp_id,
                'eventId': event.get('eventId'),
                'timestamp': event.get('timestamp'),
                'eventType': event.get('eventType'),
                'phase': event.get('phase'),
                'timeSinceLast': event.get('timeSinceLast'),
                'scrollY': event.get('scrollY'),
                'sectionBeforeScroll': event.get('sectionBeforeScroll'),
                'sectionAfterScroll': event.get('sectionAfterScroll'),
                'classification': event.get('classification'),
                'pauseDuration': event.get('pauseDuration'),
                'scrollDuration': event.get('scrollDuration'),
                'selectedText': event.get('selectedText', '')
            })

    write_csv(os.path.join(output_dir, 'reading_events.csv'), rows)
    return rows


def generate_reading_section_analysis_csv(experiments, output_dir):
    """Generate reading_section_analysis.csv from sectionAnalysis data"""
    rows = []
    for exp in experiments:
        pid = normalize_participant_id(exp.get('participantId'))
        exp_id = exp.get('experimentId', exp.get('_experimentDocId'))
        section_analysis = exp.get('reading', {}).get('sectionAnalysis', {})

        for section_name, section_data in section_analysis.items():
            rows.append({
                'participantId': pid,
                'experimentId': exp_id,
                'section_name': section_name,
                'reading_time': section_data.get('reading', 0),
                'scanning_time': section_data.get('scanning', 0),
                'scrolling_time': section_data.get('scrolling', 0)
            })

    write_csv(os.path.join(output_dir, 'reading_section_analysis.csv'), rows)
    return rows


def generate_reading_summary_csv(experiments, output_dir):
    """Generate reading_summary.csv"""
    rows = []
    for exp in experiments:
        pid = normalize_participant_id(exp.get('participantId'))
        exp_id = exp.get('experimentId', exp.get('_experimentDocId'))
        reading = exp.get('reading', {})

        if not reading:
            continue

        focus_times = reading.get('focusTimes', {})
        cls_summary = reading.get('classificationSummary', {})

        rows.append({
            'participantId': pid,
            'experimentId': exp_id,
            'reading_id': f"{exp_id}_reading",
            'totalEvents': reading.get('totalEvents'),
            'duration': reading.get('duration'),
            'focusTime_reading': focus_times.get('reading'),
            'focusTime_chat': focus_times.get('chat'),
            'reading_count': cls_summary.get('reading', {}).get('count'),
            'reading_totalDuration': cls_summary.get('reading', {}).get('totalDuration'),
            'scanning_count': cls_summary.get('scanning', {}).get('count'),
            'scanning_totalDuration': cls_summary.get('scanning', {}).get('totalDuration'),
            'scrolling_count': cls_summary.get('scrolling', {}).get('count'),
            'scrolling_totalDuration': cls_summary.get('scrolling', {}).get('totalDuration')
        })

    write_csv(os.path.join(output_dir, 'reading_summary.csv'), rows)
    return rows


def generate_survey_csv(experiments, output_dir):
    """Generate survey.csv (post-study survey responses)"""
    rows = []
    for exp in experiments:
        pid = normalize_participant_id(exp.get('participantId'))
        exp_id = exp.get('experimentId', exp.get('_experimentDocId'))
        survey = exp.get('postStudySurvey', {})

        if not survey:
            continue

        nasa = survey.get('nasaTLX', {})
        self_eff = survey.get('selfEfficacy', {})
        overall_comp = self_eff.get('overallComprehension', {})
        critical = self_eff.get('criticalEngagement', {})
        llm_use = survey.get('llmUsefulness', {})
        llm_trust = survey.get('llmTrust', {})
        attention = survey.get('attentionCheck', {})
        demographics = survey.get('demographics', {})
        ai_usage = survey.get('aiUsage', {})

        rows.append({
            'participantId': pid,
            'experimentId': exp_id,
            # NASA-TLX
            'nasaTLX_mentalDemand': nasa.get('mentalDemand'),
            'nasaTLX_physicalDemand': nasa.get('physicalDemand'),
            'nasaTLX_temporalDemand': nasa.get('temporalDemand'),
            'nasaTLX_effort': nasa.get('effort'),
            'nasaTLX_frustration': nasa.get('frustration'),
            # Self-efficacy - Performance
            'selfEfficacy_performance': nasa.get('performance'),
            # Self-efficacy - Overall Comprehension
            'selfEfficacy_overallGoal': overall_comp.get('overallGoal'),
            'selfEfficacy_authorsReasoning': overall_comp.get('authorsReasoning'),
            'selfEfficacy_connectingIdeas': overall_comp.get('connectingIdeas'),
            # Self-efficacy - Critical Engagement
            'selfEfficacy_ownIdeas': critical.get('ownIdeas'),
            'selfEfficacy_alternativePerspectives': critical.get('alternativePerspectives'),
            'selfEfficacy_verifyCredibility': critical.get('verifyCredibility'),
            'selfEfficacy_questionClaims': critical.get('questionClaims'),
            'selfEfficacy_broaderImplications': critical.get('broaderImplications'),
            # LLM Usefulness
            'llmUsefulness_overall': llm_use.get('overall'),
            'llmUsefulness_conceptHelp': llm_use.get('conceptHelp'),
            'llmUsefulness_findingsHelp': llm_use.get('findingsHelp'),
            'llmUsefulness_practicalHelp': llm_use.get('practicalHelp'),
            'llmUsefulness_timeSaving': llm_use.get('timeSaving'),
            # LLM Trust
            'llmTrust_competence': llm_trust.get('competence'),
            'llmTrust_accuracy': llm_trust.get('accuracy'),
            'llmTrust_benevolence': llm_trust.get('benevolence'),
            'llmTrust_reliability': llm_trust.get('reliability'),
            'llmTrust_comfortActing': llm_trust.get('comfortActing'),
            'llmTrust_comfortUsing': llm_trust.get('comfortUsing'),
            # Attention Check
            'attentionCheck_focus': attention.get('focus'),
            'attentionCheck_stronglyDisagreeCheck': attention.get('stronglyDisagreeCheck'),
            # Demographics
            'demographics_age': demographics.get('age'),
            'demographics_gender': demographics.get('gender'),
            'demographics_education': demographics.get('education'),
            'demographics_englishProficiency': demographics.get('englishProficiency'),
            'demographics_workingSituation': demographics.get('workingSituation'),
            'demographics_workHoursPerWeek': demographics.get('workHoursPerWeek'),
            'demographics_yearsInOrganization': demographics.get('yearsInOrganization'),
            'demographics_yearsInJob': demographics.get('yearsInJob'),
            'demographics_jobTitle': demographics.get('jobTitle'),
            'demographics_industry': demographics.get('industry'),
            'demographics_ethnicity': ', '.join(demographics.get('ethnicity', [])) if demographics.get('ethnicity') else '',
            # AI Usage
            'aiUsage_frequency': ai_usage.get('frequency'),
            'aiUsage_toolsUsed': ai_usage.get('toolsUsed'),
            'aiUsage_purposes': ', '.join([p.get('name', '') for p in ai_usage.get('purposes', []) if isinstance(p, dict) and p.get('name')]) if ai_usage.get('purposes') else '',
            # Feedback
            'studyFeedback': survey.get('studyFeedback'),
            'surveyCompletedAt': survey.get('surveyCompletedAt')
        })

    write_csv(os.path.join(output_dir, 'survey.csv'), rows)
    return rows


def generate_pretask_csv(experiments, output_dir):
    """Generate pre-task.csv"""
    rows = []
    for exp in experiments:
        pid = normalize_participant_id(exp.get('participantId'))
        exp_id = exp.get('experimentId', exp.get('_experimentDocId'))
        pretask = exp.get('preTask', {})

        if not pretask:
            continue

        strategies = pretask.get('strategies', [])
        # Handle both list and dict formats
        if isinstance(strategies, list):
            strategy_list = strategies
        elif isinstance(strategies, dict):
            strategy_list = [strategies.get(f'strategy{i}', '') for i in range(1, 11)]
        else:
            strategy_list = []

        row = {
            'participantId': pid,
            'experimentId': exp_id,
        }
        # Add strategy1 through strategy10
        for i in range(10):
            row[f'strategy{i+1}'] = strategy_list[i] if len(strategy_list) > i else ''
        row.update({
            'confidence': pretask.get('confidence'),
            'approachClarity': pretask.get('approachClarity'),
            'challenges': pretask.get('challenges'),
            'completedAt': pretask.get('completedAt')
        })
        rows.append(row)

    write_csv(os.path.join(output_dir, 'pre-task.csv'), rows)
    return rows


def generate_posttask_csv(experiments, output_dir):
    """Generate post-task.csv"""
    rows = []
    for exp in experiments:
        pid = normalize_participant_id(exp.get('participantId'))
        exp_id = exp.get('experimentId', exp.get('_experimentDocId'))
        posttask = exp.get('postTask', {})

        if not posttask:
            continue

        strategies = posttask.get('strategies', [])
        # Handle both list and dict formats
        if isinstance(strategies, list):
            strategy_list = strategies
        elif isinstance(strategies, dict):
            strategy_list = [strategies.get(f'strategy{i}', '') for i in range(1, 11)]
        else:
            strategy_list = []

        row = {
            'participantId': pid,
            'experimentId': exp_id,
        }
        # Add strategy1 through strategy10
        for i in range(10):
            row[f'strategy{i+1}'] = strategy_list[i] if len(strategy_list) > i else ''
        row.update({
            'newStrategyConfidence': posttask.get('newStrategyConfidence'),
            'implementationLikelihood': posttask.get('implementationLikelihood'),
            'thinkingChange': posttask.get('thinkingChange'),
            'completedAt': posttask.get('completedAt')
        })
        rows.append(row)

    write_csv(os.path.join(output_dir, 'post-task.csv'), rows)
    return rows


# Quiz correct answers (1-9)
# 1-3: Low complexity, 4-6: Medium complexity, 7-9: High complexity
QUIZ_ANSWERS = {
    '1': 'C',  # To apply scientific findings...
    '2': 'D',  # Before, During, and After
    '3': 'D',  # Their value is often questioned...
    '4': 'B',  # To share routine, nonurgent information...
    '5': 'A',  # They can stimulate positive behaviors...
    '6': 'A',  # To facilitate follow-through...
    '7': 'A',  # Carefully selecting relevant attendees...
    '8': 'C',  # The structural design before the meeting...
    '9': 'B',  # Systematically survey meeting satisfaction...
}

# Full answer text mapping for matching
QUIZ_ANSWER_TEXT = {
    '1': 'To apply scientific findings about activities before, during, and after meetings to improve their success.',
    '2': 'Before, During, and After.',
    '3': 'Their value is often questioned and they are viewed as a routine necessity.',
    '4': 'To share routine, nonurgent information without discussion.',
    '5': 'They can stimulate positive behaviors that predict team performance.',
    '6': 'To facilitate follow-through by clarifying action plans and responsibilities.',
    '7': 'Carefully selecting relevant attendees before a meeting can positively impact their long-term job satisfaction.',
    '8': 'The structural design before the meeting and active facilitation during the meeting.',
    '9': 'Systematically survey meeting satisfaction, use the feedback to re-evaluate routine meetings, and adjust their design accordingly.',
}


def is_answer_correct(question_num, user_answer):
    """Check if user's answer is correct for a given question"""
    if not user_answer or user_answer == 'Not Sure':
        return False

    q_str = str(question_num)
    correct_text = QUIZ_ANSWER_TEXT.get(q_str, '')

    # Match by checking if the correct answer text is contained in user's answer
    # or if user's answer contains the key part of correct answer
    if correct_text and correct_text.lower() in user_answer.lower():
        return True
    if correct_text and user_answer.lower() in correct_text.lower():
        return True

    # Exact match
    return user_answer.strip() == correct_text.strip()


def generate_quizzes_csv(experiments, output_dir):
    """Generate quizzes.csv with accuracy by difficulty level"""
    rows = []
    for exp in experiments:
        pid = normalize_participant_id(exp.get('participantId'))
        exp_id = exp.get('experimentId', exp.get('_experimentDocId'))
        quiz = exp.get('quiz', {})

        if not quiz.get('answers'):
            continue

        answers = quiz.get('answers', {})
        grading = quiz.get('gradingDetails', {})

        # Calculate accuracy by difficulty level
        # Low: Q1-3, Med: Q4-6, High: Q7-9
        correct_low = 0
        correct_med = 0
        correct_high = 0

        for q_num in range(1, 10):
            q_str = str(q_num)
            user_answer = answers.get(q_str, '')

            # Check correctness
            is_correct = is_answer_correct(q_num, user_answer)

            if q_num <= 3:  # Low complexity (1-3)
                if is_correct:
                    correct_low += 1
            elif q_num <= 6:  # Medium complexity (4-6)
                if is_correct:
                    correct_med += 1
            else:  # High complexity (7-9)
                if is_correct:
                    correct_high += 1

        # Calculate accuracy percentages (3 questions each)
        acc_low = round(correct_low / 3 * 100, 1)
        acc_med = round(correct_med / 3 * 100, 1)
        acc_high = round(correct_high / 3 * 100, 1)

        row = {
            'participantId': pid,
            'experimentId': exp_id,
            'condition': exp.get('condition'),
            'duration': quiz.get('duration'),
            'totalQuestions': quiz.get('totalQuestions'),
            'correctCount': quiz.get('correctCount'),
            'notSureCount': quiz.get('notSureCount'),
            'accuracy': quiz.get('accuracy'),
            'acc_low': acc_low,
            'acc_med': acc_med,
            'acc_high': acc_high,
            'confidence': quiz.get('confidence')
        }

        # Add individual answers (q1-q9)
        for i in range(1, 10):
            q_str = str(i)
            row[f'answer_{i}'] = answers.get(q_str, '')
            row[f'correct_{i}'] = grading.get(q_str, {}).get('isCorrect', '')

        rows.append(row)

    write_csv(os.path.join(output_dir, 'quizzes.csv'), rows)
    return rows


def generate_llm_messages_csv(experiments, output_dir):
    """Generate llm_messages.csv"""
    rows = []
    for exp in experiments:
        pid = normalize_participant_id(exp.get('participantId'))
        exp_id = exp.get('experimentId', exp.get('_experimentDocId'))
        messages = exp.get('llmInteraction', {}).get('messages', [])

        for i, msg in enumerate(messages):
            rows.append({
                'participantId': pid,
                'experimentId': exp_id,
                'message_order': i + 1,
                'question': msg.get('question', ''),
                'answer': msg.get('answer', ''),
                'questionTime': msg.get('questionTime', msg.get('timestamp')),
                'answerTime': msg.get('answerTime'),
                'responseTime': msg.get('responseTime')
            })

    write_csv(os.path.join(output_dir, 'llm_messages.csv'), rows)
    return rows


def generate_report(experiments, filter_report, output_dir, us_ids=None):
    """Generate preprocessing report in markdown"""
    from collections import Counter

    # Calculate statistics
    total = len(experiments)
    countries = Counter(exp.get('_country') for exp in experiments)
    conditions = Counter(exp.get('condition') for exp in experiments)

    # Find missing US participants (in Prolific but not in filtered data)
    missing_us = []
    if us_ids:
        filtered_pids = set(normalize_participant_id(exp.get('participantId')) for exp in experiments)
        # Load awaiting review from prolific file
        import csv
        with open(PROLIFIC_US_PATH, 'r') as f:
            reader = csv.DictReader(f)
            awaiting_ids = set(row['Participant id'] for row in reader if row['Status'] == 'AWAITING REVIEW')
        missing_us = awaiting_ids - filtered_pids

    # Calculate average experiment duration
    durations = []
    for exp in experiments:
        created = get_created_at(exp)
        completed = get_completed_at(exp)
        if created and completed:
            duration_minutes = (completed - created).total_seconds() / 60
            durations.append(duration_minutes)

    avg_duration = sum(durations) / len(durations) if durations else 0

    report = f"""# Data Preprocessing Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary

| Metric | Value |
|--------|-------|
| **Total Participants** | {total} |
| **US Participants** | {countries.get('US', 0)} |
| **UK Participants** | {countries.get('UK', 0)} |
| **Average Experiment Duration** | {avg_duration:.1f} minutes |

### Expected vs Actual

| Country | Expected | Actual | Match |
|---------|----------|--------|-------|
| US | 124 | {countries.get('US', 0)} | {'✓' if countries.get('US', 0) == 124 else '✗'} |
| UK | 176 | {countries.get('UK', 0)} | {'✓' if countries.get('UK', 0) == 176 else '✗'} |
| **Total** | **300** | **{total}** | {'✓' if total == 300 else '✗'} |

## Condition Distribution

| Condition | Count |
|-----------|-------|
"""
    for cond, count in sorted(conditions.items()):
        report += f"| {cond} | {count} |\n"

    report += f"""
## Data Filtering Results

### Excluded Participants (No Completed Experiments): {len(filter_report['excluded_no_completed'])}

"""
    if filter_report['excluded_no_completed']:
        for item in filter_report['excluded_no_completed'][:10]:  # Show first 10
            report += f"- `{item['pid']}`: {item['total_experiments']} experiments, statuses: {item['statuses']}\n"
        if len(filter_report['excluded_no_completed']) > 10:
            report += f"- ... and {len(filter_report['excluded_no_completed']) - 10} more\n"
    else:
        report += "None\n"

    report += f"""
### Participants with Multiple Completed Experiments: {len(filter_report['multiple_completed'])}

"""
    if filter_report['multiple_completed']:
        for item in filter_report['multiple_completed']:
            report += f"- `{item['pid']}`: {item['count']} completed experiments\n"
            report += f"  - Used: `{item['used_experiment_id']}`\n"
            report += f"  - All createdAt: {item['all_created_at']}\n"
    else:
        report += "None\n"

    report += f"""
### Invalid Participant ID Format: {len(filter_report['invalid_pid_format'])}

"""
    if filter_report['invalid_pid_format']:
        for pid in filter_report['invalid_pid_format']:
            report += f"- `{pid[:50]}{'...' if len(pid) > 50 else ''}`\n"
    else:
        report += "None\n"

    report += f"""
### Missing US Participants (Prolific completed but not in Firebase): {len(missing_us)}

"""
    if missing_us:
        for pid in sorted(missing_us):
            report += f"- `{pid}`\n"
    else:
        report += "None\n"

    report += """
## Output Files

| File | Description |
|------|-------------|
| participants.csv | Participant info with country |
| experiments.csv | Experiment metadata |
| reading_events.csv | Individual reading events |
| reading_section_analysis.csv | Section-level reading analysis |
| reading_summary.csv | Reading summary statistics |
| survey.csv | Post-study survey responses |
| pre-task.csv | Pre-task responses |
| post-task.csv | Post-task responses |
| quizzes.csv | Quiz answers and accuracy |
| llm_messages.csv | LLM chat messages |
"""

    os.makedirs(output_dir, exist_ok=True)
    report_path = os.path.join(output_dir, 'preprocessing_report.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\nReport saved to: {report_path}")
    return report


def main():
    print("=" * 60)
    print("DATA PREPROCESSING")
    print("=" * 60)

    # Load raw data
    print("\n1. Loading raw data...")
    with open(RAW_DATA_PATH, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    print(f"   Loaded {len(raw_data)} experiments")

    # Load Prolific US IDs
    print("\n2. Loading Prolific US IDs...")
    us_ids = load_prolific_us_ids()
    print(f"   Loaded {len(us_ids)} US participant IDs")

    # Filter experiments (1 per participant, completed only)
    print("\n3. Filtering experiments...")
    filtered_data, filter_report = filter_experiments(raw_data)
    print(f"   Filtered to {len(filtered_data)} experiments")
    print(f"   - Excluded (no completed): {len(filter_report['excluded_no_completed'])}")
    print(f"   - Multiple completed (used latest): {len(filter_report['multiple_completed'])}")
    print(f"   - Invalid PID format: {len(filter_report['invalid_pid_format'])}")

    # Classify US/UK
    print("\n4. Classifying US/UK...")
    filtered_data = classify_country(filtered_data, us_ids)
    us_count = sum(1 for exp in filtered_data if exp.get('_country') == 'US')
    uk_count = sum(1 for exp in filtered_data if exp.get('_country') == 'UK')
    print(f"   US: {us_count}, UK: {uk_count}")

    # Generate CSV files
    print("\n5. Generating CSV files...")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    generate_participants_csv(filtered_data, OUTPUT_DIR)
    generate_experiments_csv(filtered_data, OUTPUT_DIR)
    generate_reading_events_csv(filtered_data, OUTPUT_DIR)
    generate_reading_section_analysis_csv(filtered_data, OUTPUT_DIR)
    generate_reading_summary_csv(filtered_data, OUTPUT_DIR)
    generate_survey_csv(filtered_data, OUTPUT_DIR)
    generate_pretask_csv(filtered_data, OUTPUT_DIR)
    generate_posttask_csv(filtered_data, OUTPUT_DIR)
    generate_quizzes_csv(filtered_data, OUTPUT_DIR)
    generate_llm_messages_csv(filtered_data, OUTPUT_DIR)

    # Generate report
    print("\n6. Generating report...")
    generate_report(filtered_data, filter_report, REPORT_DIR, us_ids=us_ids)

    print("\n" + "=" * 60)
    print("PREPROCESSING COMPLETE")
    print(f"CSV files saved to: {os.path.abspath(OUTPUT_DIR)}")
    print("=" * 60)


if __name__ == '__main__':
    main()
