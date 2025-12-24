#!/usr/bin/env python3
"""
Firebase Data Export Script
- Fetches experiment data from Firebase within specified time range
- Saves raw JSON data
- Converts to normalized CSV files matching reference structure

Data Collection Rules:
- Time range: 19 Dec 2025 13:30 ET ~ 23 Dec 2025 19:30 ET
- US/UK cutoff: 21 Dec 2025 18:58 ET (last US participant start time)
- Only includes experiments with createdAt within the time range

Output files:
- participants.csv: participant info, demographics, AI usage
- sessions.csv: experiment metadata with related IDs
- reading_summary.csv: focusTimes, classification summaries
- reading_events.csv: individual event logs
- quizzes.csv: quiz answers per question
- post_surveys.csv: NASA-TLX, self-efficacy, LLM trust/usefulness
- llm_interactions.csv: LLM summary (totalQueries, avgResponseTime)
- llm_messages.csv: Q&A pairs

Usage:
    python export_firebase_data.py                          # Export data within time range
    python export_firebase_data.py --all                    # Export ALL data (no time filter)
"""

import json
import csv
import os
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Eastern Time (UTC-5, standard time)
ET = timezone(timedelta(hours=-5))

# Korea Standard Time (UTC+9)
KST = timezone(timedelta(hours=9))

# === DATA COLLECTION TIME RANGE (ET) ===
# Experiment period: 19 Dec 2025 13:30 ET ~ 23 Dec 2025 19:30 ET
START_TIME = datetime(2025, 12, 19, 13, 30, 0, tzinfo=ET)
END_TIME = datetime(2025, 12, 23, 19, 30, 0, tzinfo=ET)

# US/UK cutoff: 21 Dec 2025 18:58 ET (last US participant start time)
UK_CUTOFF = datetime(2025, 12, 21, 18, 58, 0, tzinfo=ET)

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore


def init_firebase():
    """Initialize Firebase Admin SDK"""
    possible_paths = [
        'firebase-service-account.json',
        'scripts/firebase-service-account.json',
        '../firebase-service-account.json',
        os.path.expanduser('~/firebase-service-account.json'),
    ]

    cred_path = None
    for path in possible_paths:
        if os.path.exists(path):
            cred_path = path
            break

    if not cred_path:
        print("ERROR: Firebase service account key not found!")
        print("Please download it from Firebase Console:")
        print("  1. Go to Firebase Console > Project Settings > Service Accounts")
        print("  2. Click 'Generate new private key'")
        print("  3. Save as 'firebase-service-account.json' in the scripts folder")
        return None

    try:
        cred = credentials.Certificate(cred_path)
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        print(f"ERROR: Failed to initialize Firebase: {e}")
        return None


def get_experiment_datetime(exp_data, target_tz=None):
    """Extract datetime from experiment data for filtering

    Args:
        exp_data: experiment data dict
        target_tz: target timezone to convert to (default: KST)

    Returns:
        datetime in target timezone, or None if no timestamp found
    """
    if target_tz is None:
        target_tz = KST

    # Try preTask.completedAt (ISO string)
    if exp_data.get('preTask', {}).get('completedAt'):
        ts_str = exp_data['preTask']['completedAt']
        if isinstance(ts_str, str):
            try:
                dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                return dt.astimezone(target_tz)
            except:
                pass

    # Try readingStartedAt (Firestore Timestamp)
    if exp_data.get('readingStartedAt'):
        ts = exp_data['readingStartedAt']
        if hasattr(ts, 'timestamp'):
            dt = datetime.fromtimestamp(ts.timestamp(), tz=timezone.utc)
            return dt.astimezone(target_tz)

    # Try updatedAt (Firestore Timestamp)
    if exp_data.get('updatedAt'):
        ts = exp_data['updatedAt']
        if hasattr(ts, 'timestamp'):
            dt = datetime.fromtimestamp(ts.timestamp(), tz=timezone.utc)
            return dt.astimezone(target_tz)

    return None


def get_country(exp_data):
    """Determine country based on experiment datetime

    Returns 'UK' if after 21 Dec 2025 19:32 ET, otherwise 'US'
    """
    exp_dt = get_experiment_datetime(exp_data, target_tz=ET)
    if exp_dt is None:
        return 'unknown'

    if exp_dt >= UK_CUTOFF:
        return 'UK'
    else:
        return 'US'


def fetch_all_experiments(db, use_time_filter=True):
    """Fetch experiment data from Firebase

    Args:
        db: Firestore client
        use_time_filter: If True, only fetch experiments within START_TIME ~ END_TIME range
    """
    if use_time_filter:
        print(f"Fetching experiments within time range:")
        print(f"  Start: {START_TIME.strftime('%Y-%m-%d %H:%M')} ET")
        print(f"  End:   {END_TIME.strftime('%Y-%m-%d %H:%M')} ET")
    else:
        print("Fetching ALL experiments from Firebase (no time filter)...")

    all_data = []
    users_ref = db.collection('users')
    users = users_ref.stream()

    user_count = 0
    filtered_out_before = 0
    filtered_out_after = 0

    for user_doc in users:
        user_count += 1
        user_id = user_doc.id
        user_data = user_doc.to_dict()

        experiments_ref = users_ref.document(user_id).collection('experiments')
        experiments = experiments_ref.stream()

        for exp_doc in experiments:
            exp_data = exp_doc.to_dict()

            if use_time_filter:
                exp_dt = get_experiment_datetime(exp_data, target_tz=ET)
                if not exp_dt:
                    # No timestamp found, skip
                    filtered_out_before += 1
                    continue
                if exp_dt < START_TIME:
                    filtered_out_before += 1
                    continue
                if exp_dt > END_TIME:
                    filtered_out_after += 1
                    continue

            exp_data['_userId'] = user_id
            exp_data['_experimentDocId'] = exp_doc.id
            exp_data['_userStatus'] = user_data.get('status', 'unknown')
            all_data.append(exp_data)

    print(f"  Found {user_count} users, {len(all_data)} experiments within range")
    if use_time_filter:
        print(f"  Filtered out: {filtered_out_before} before start, {filtered_out_after} after end")
    return all_data


def save_raw_json(data, output_dir):
    """Save raw data as JSON"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"raw_data_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, default=str, ensure_ascii=False)

    print(f"  Saved raw JSON: {filepath}")
    return filepath


def write_csv(filepath, rows, fieldnames=None):
    """Helper to write CSV file"""
    if not rows:
        return False

    if fieldnames is None:
        fieldnames = list(rows[0].keys())

    with open(filepath, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  Saved: {filepath} ({len(rows)} rows)")
    return True


def normalize_participant_id(pid):
    """Normalize participant ID by removing @auth.prolific.com suffix if present"""
    if pid and '@auth.prolific.com' in pid:
        return pid.replace('@auth.prolific.com', '')
    return pid


def convert_to_csv(data, output_dir):
    """Convert experiment data to normalized CSV files matching reference structure"""

    # Filter to only completed experiments
    completed_data = [exp for exp in data if exp.get('status') == 'completed']
    excluded_count = len(data) - len(completed_data)
    if excluded_count > 0:
        print(f"  Excluding {excluded_count} non-completed sessions (abandoned/in_progress)")

    # Track unique participants for participants.csv (from completed sessions only)
    # Key: normalized participant ID, Value: experiment data
    participants = {}

    # === 1. sessions.csv (completed only) ===
    sessions_rows = []
    for exp in completed_data:
        pid_raw = exp.get('participantId')
        pid = normalize_participant_id(pid_raw)  # Normalize for matching
        session_id = exp.get('experimentId', exp.get('_experimentDocId'))

        # Store participant info (use normalized ID as key)
        # Since we're iterating over completed_data only, all sessions here are completed
        if pid and pid not in participants:
            participants[pid] = exp

        sessions_rows.append({
            'participantId': pid,
            'session_id': session_id,
            'condition': exp.get('condition'),
            'paper': exp.get('paper'),
            'status': exp.get('status'),
            'mode': exp.get('mode'),
            'createdAt': exp.get('preTask', {}).get('completedAt'),
            'completedAt': exp.get('postStudySurvey', {}).get('surveyCompletedAt'),
            'reading_id': f"{session_id}_reading" if exp.get('reading') else '',
            'quiz_id': f"{session_id}_quiz" if exp.get('quiz') else '',
            'llm_interaction_id': f"{session_id}_llm" if exp.get('llmInteraction', {}).get('messages') else '',
        })

    write_csv(os.path.join(output_dir, 'sessions.csv'), sessions_rows)

    # === 2. participants.csv ===
    participants_rows = []
    for pid, exp in participants.items():
        survey = exp.get('postStudySurvey', {})
        demographics = survey.get('demographics', {})
        ai_usage = survey.get('aiUsage', {})

        participants_rows.append({
            'participantId': pid,
            'condition': exp.get('condition'),
            'country': get_country(exp),
            # Demographics
            'demographics_age': demographics.get('age'),
            'demographics_gender': demographics.get('gender'),
            'demographics_education': demographics.get('education'),
            'demographics_workingSituation': demographics.get('workingSituation'),
            'demographics_workHoursPerWeek': demographics.get('workHoursPerWeek'),
            'demographics_yearsInOrganization': demographics.get('yearsInOrganization'),
            'demographics_yearsInJob': demographics.get('yearsInJob'),
            'demographics_jobTitle': demographics.get('jobTitle'),
            'demographics_industry': demographics.get('industry'),
            'demographics_ethnicity': json.dumps(demographics.get('ethnicity', []), ensure_ascii=False) if demographics.get('ethnicity') else '',
            'demographics_englishProficiency': demographics.get('englishProficiency'),
            # AI Usage
            'aiUsage_frequency': ai_usage.get('frequency'),
            'aiUsage_toolsUsed': ai_usage.get('toolsUsed'),
            'aiUsage_purposes': json.dumps(ai_usage.get('purposes', []), ensure_ascii=False) if ai_usage.get('purposes') else '',
        })

    write_csv(os.path.join(output_dir, 'participants.csv'), participants_rows)

    # === 3. reading_summary.csv ===
    reading_summary_rows = []
    for exp in completed_data:
        reading = exp.get('reading', {})
        if not reading:
            continue

        session_id = exp.get('experimentId', exp.get('_experimentDocId'))
        focus_times = reading.get('focusTimes', {})
        cls_summary = reading.get('classificationSummary', {})

        reading_summary_rows.append({
            'participantId': normalize_participant_id(exp.get('participantId')),
            'session_id': session_id,
            'reading_id': f"{session_id}_reading",
            'totalEvents': reading.get('totalEvents'),
            'duration': reading.get('duration'),
            # Focus times
            'focusTime_reading': focus_times.get('reading'),
            'focusTime_chat': focus_times.get('chat'),
            'focusTime_audio': focus_times.get('audio'),
            'focusTime_video': focus_times.get('video'),
            'focusTime_infographics': focus_times.get('infographics'),
            'focusTime_simplified': focus_times.get('simplified'),
            'focusTime_quiz': focus_times.get('quiz'),
            # Classification summary
            'reading_count': cls_summary.get('reading', {}).get('count'),
            'reading_totalDuration': cls_summary.get('reading', {}).get('totalDuration'),
            'scanning_count': cls_summary.get('scanning', {}).get('count'),
            'scanning_totalDuration': cls_summary.get('scanning', {}).get('totalDuration'),
            'scrolling_count': cls_summary.get('scrolling', {}).get('count'),
            'scrolling_totalDuration': cls_summary.get('scrolling', {}).get('totalDuration'),
        })

    write_csv(os.path.join(output_dir, 'reading_summary.csv'), reading_summary_rows)

    # === 4. reading_events.csv ===
    events_rows = []
    for exp in completed_data:
        events = exp.get('reading', {}).get('events', [])
        session_id = exp.get('experimentId', exp.get('_experimentDocId'))

        for event in events:
            events_rows.append({
                'participantId': normalize_participant_id(exp.get('participantId')),
                'session_id': session_id,
                'eventId': event.get('eventId'),
                'timestamp': event.get('timestamp'),
                'eventType': event.get('eventType'),
                'phase': event.get('phase'),
                'classification': event.get('classification'),
                'pauseDuration': event.get('pauseDuration'),
                'scrollDuration': event.get('scrollDuration'),
                'sectionBeforeScroll': event.get('sectionBeforeScroll'),
                'sectionAfterScroll': event.get('sectionAfterScroll'),
                'scrollDirection': event.get('scrollDirection'),
                'scrollDistance': event.get('scrollDistance'),
                'from': event.get('from'),
                'to': event.get('to'),
                'duration': event.get('duration'),
                'currentTime': event.get('currentTime'),
            })

    write_csv(os.path.join(output_dir, 'reading_events.csv'), events_rows)

    # === 5. quizzes.csv ===
    quizzes_rows = []
    for exp in completed_data:
        quiz = exp.get('quiz', {})
        if not quiz.get('answers'):
            continue

        session_id = exp.get('experimentId', exp.get('_experimentDocId'))
        answers = quiz.get('answers', {})
        grading = quiz.get('gradingDetails', {})

        # Create a row with all answers as columns
        row = {
            'participantId': normalize_participant_id(exp.get('participantId')),
            'session_id': session_id,
            'quiz_id': f"{session_id}_quiz",
            'condition': exp.get('condition'),
            'paper': exp.get('paper'),
            'duration': quiz.get('duration'),
            'total_questions': quiz.get('totalQuestions'),
            'correct_count': quiz.get('correctCount'),
            'not_sure_count': quiz.get('notSureCount'),
            'accuracy': quiz.get('accuracy'),
            'confidence': quiz.get('confidence'),
        }

        # Add individual answers
        for i in range(1, 13):  # Assuming max 12 questions
            q_key = f"q{i}"
            row[f'answer_{i}'] = answers.get(q_key, '')
            row[f'correct_{i}'] = grading.get(q_key, {}).get('isCorrect', '')

        quizzes_rows.append(row)

    write_csv(os.path.join(output_dir, 'quizzes.csv'), quizzes_rows)

    # === 6. post_surveys.csv ===
    surveys_rows = []
    for exp in completed_data:
        survey = exp.get('postStudySurvey', {})
        if not survey:
            continue

        session_id = exp.get('experimentId', exp.get('_experimentDocId'))
        nasa = survey.get('nasaTLX', {})
        self_eff = survey.get('selfEfficacy', {})
        overall_comp = self_eff.get('overallComprehension', {})
        critical = self_eff.get('criticalEngagement', {})
        llm_use = survey.get('llmUsefulness', {})
        llm_trust = survey.get('llmTrust', {})
        attention = survey.get('attentionCheck', {})

        surveys_rows.append({
            'participantId': normalize_participant_id(exp.get('participantId')),
            'session_id': session_id,
            'condition': exp.get('condition'),
            # NASA-TLX
            'nasaTLX_mentalDemand': nasa.get('mentalDemand'),
            'nasaTLX_physicalDemand': nasa.get('physicalDemand'),
            'nasaTLX_temporalDemand': nasa.get('temporalDemand'),
            'nasaTLX_performance': nasa.get('performance'),
            'nasaTLX_effort': nasa.get('effort'),
            'nasaTLX_frustration': nasa.get('frustration'),
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
            # LLM Usefulness (for with_llm conditions)
            'llmUsefulness_overall': llm_use.get('overall'),
            'llmUsefulness_conceptHelp': llm_use.get('conceptHelp'),
            'llmUsefulness_findingsHelp': llm_use.get('findingsHelp'),
            'llmUsefulness_practicalHelp': llm_use.get('practicalHelp'),
            'llmUsefulness_timeSaving': llm_use.get('timeSaving'),
            # LLM Trust (for with_llm conditions)
            'llmTrust_competence': llm_trust.get('competence'),
            'llmTrust_accuracy': llm_trust.get('accuracy'),
            'llmTrust_benevolence': llm_trust.get('benevolence'),
            'llmTrust_reliability': llm_trust.get('reliability'),
            'llmTrust_comfortActing': llm_trust.get('comfortActing'),
            'llmTrust_comfortUsing': llm_trust.get('comfortUsing'),
            # Attention Check
            'attentionCheck_focus': attention.get('focus'),
            'attentionCheck_stronglyDisagreeCheck': attention.get('stronglyDisagreeCheck'),
            # Feedback
            'studyFeedback': survey.get('studyFeedback'),
            'completedAt': survey.get('surveyCompletedAt'),
        })

    write_csv(os.path.join(output_dir, 'post_surveys.csv'), surveys_rows)

    # === 7. llm_interactions.csv ===
    llm_interactions_rows = []
    for exp in completed_data:
        llm = exp.get('llmInteraction', {})
        messages = llm.get('messages', [])
        if not messages:
            continue

        session_id = exp.get('experimentId', exp.get('_experimentDocId'))

        # Calculate average response time
        response_times = [m.get('responseTime', 0) for m in messages if m.get('responseTime')]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        llm_interactions_rows.append({
            'participantId': normalize_participant_id(exp.get('participantId')),
            'session_id': session_id,
            'llm_interaction_id': f"{session_id}_llm",
            'totalQueries': llm.get('totalQueries', len(messages)),
            'avgResponseTime': avg_response_time,
        })

    write_csv(os.path.join(output_dir, 'llm_interactions.csv'), llm_interactions_rows)

    # === 8. llm_messages.csv ===
    llm_messages_rows = []
    for exp in completed_data:
        messages = exp.get('llmInteraction', {}).get('messages', [])
        if not messages:
            continue

        session_id = exp.get('experimentId', exp.get('_experimentDocId'))

        for i, msg in enumerate(messages):
            llm_messages_rows.append({
                'participantId': normalize_participant_id(exp.get('participantId')),
                'session_id': session_id,
                'message_order': i + 1,
                'question': msg.get('question', ''),
                'answer': msg.get('answer', ''),
                'questionTime': msg.get('questionTime', msg.get('timestamp')),
                'answerTime': msg.get('answerTime'),
                'responseTime': msg.get('responseTime'),
            })

    write_csv(os.path.join(output_dir, 'llm_messages.csv'), llm_messages_rows)

    print(f"\n  Total: 8 CSV files created")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Export Firebase experiment data to JSON and CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python export_firebase_data.py                # Export data within time range (default)
  python export_firebase_data.py --all          # Export ALL data (no time filter)
  python export_firebase_data.py --raw-only     # Only save raw JSON (no CSV conversion)
        """
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Export ALL data without time range filter'
    )
    parser.add_argument(
        '--raw-only',
        action='store_true',
        help='Only save raw JSON, skip CSV conversion'
    )
    return parser.parse_args()


def main():
    args = parse_args()

    use_time_filter = not args.all

    print("="*60)
    print("FIREBASE DATA EXPORT")
    print("="*60)

    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
    os.makedirs(output_dir, exist_ok=True)

    # Initialize Firebase
    db = init_firebase()
    if not db:
        return

    # Fetch data
    data = fetch_all_experiments(db, use_time_filter=use_time_filter)

    if not data:
        print("No data found!")
        return

    # Save raw JSON
    print("\nSaving raw JSON...")
    raw_dir = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
    os.makedirs(raw_dir, exist_ok=True)
    save_raw_json(data, raw_dir)

    # Convert to CSV (unless --raw-only)
    if not args.raw_only:
        print("\nConverting to CSV...")
        convert_to_csv(data, output_dir)

    print("\n" + "="*60)
    print("EXPORT COMPLETE")
    print(f"Raw JSON saved to: {os.path.abspath(raw_dir)}")
    if not args.raw_only:
        print(f"CSV files saved to: {os.path.abspath(output_dir)}")
    print("="*60)


if __name__ == '__main__':
    main()
