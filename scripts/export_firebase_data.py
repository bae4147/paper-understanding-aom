#!/usr/bin/env python3
"""
Firebase Data Export Script
- Fetches all experiment data from Firebase
- Saves raw JSON data
- Converts to CSV for analysis

Usage:
    python export_firebase_data.py                          # Export all data
    python export_firebase_data.py --after "2025-12-20 03:30"  # Export data after specific datetime
    python export_firebase_data.py --today                  # Export only today's data
"""

import json
import csv
import os
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# Korea Standard Time (UTC+9)
KST = timezone(timedelta(hours=9))

# Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Firebase
def init_firebase():
    """Initialize Firebase Admin SDK"""
    # Look for service account key in multiple locations
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


def get_experiment_datetime(exp_data):
    """Extract datetime from experiment data for filtering (returns KST aware datetime)"""
    # Try various timestamp fields

    # Try preTask.completedAt (ISO string)
    if exp_data.get('preTask', {}).get('completedAt'):
        ts_str = exp_data['preTask']['completedAt']
        if isinstance(ts_str, str):
            try:
                dt = datetime.fromisoformat(ts_str.replace('Z', '+00:00'))
                # Convert to KST
                return dt.astimezone(KST)
            except:
                pass

    # Try readingStartedAt (Firestore Timestamp)
    if exp_data.get('readingStartedAt'):
        ts = exp_data['readingStartedAt']
        if hasattr(ts, 'timestamp'):
            dt = datetime.fromtimestamp(ts.timestamp(), tz=timezone.utc)
            return dt.astimezone(KST)

    # Try updatedAt (Firestore Timestamp)
    if exp_data.get('updatedAt'):
        ts = exp_data['updatedAt']
        if hasattr(ts, 'timestamp'):
            dt = datetime.fromtimestamp(ts.timestamp(), tz=timezone.utc)
            return dt.astimezone(KST)

    return None


def fetch_all_experiments(db, after_datetime=None):
    """Fetch all experiment data from Firebase

    Args:
        db: Firestore client
        after_datetime: Optional datetime to filter experiments created after this time
    """
    if after_datetime:
        print(f"Fetching experiments after {after_datetime}...")
    else:
        print("Fetching all experiments from Firebase...")

    all_data = []
    users_ref = db.collection('users')
    users = users_ref.stream()

    user_count = 0
    filtered_count = 0

    for user_doc in users:
        user_count += 1
        user_id = user_doc.id
        user_data = user_doc.to_dict()

        # Get all experiments for this user
        experiments_ref = users_ref.document(user_id).collection('experiments')
        experiments = experiments_ref.stream()

        for exp_doc in experiments:
            exp_data = exp_doc.to_dict()

            # Apply datetime filter if specified
            if after_datetime:
                exp_dt = get_experiment_datetime(exp_data)
                if not exp_dt or exp_dt < after_datetime:
                    filtered_count += 1
                    continue

            exp_data['_userId'] = user_id
            exp_data['_experimentDocId'] = exp_doc.id
            exp_data['_userStatus'] = user_data.get('status', 'unknown')
            all_data.append(exp_data)

    if after_datetime:
        print(f"  Found {user_count} users, {len(all_data)} experiments after filter (filtered out {filtered_count})")
    else:
        print(f"  Found {user_count} users, {len(all_data)} experiments")
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


def flatten_dict(d, parent_key='', sep='_'):
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            # Convert list to string representation
            items.append((new_key, json.dumps(v, default=str)))
        else:
            items.append((new_key, v))
    return dict(items)


def convert_to_csv(data, output_dir):
    """Convert experiment data to multiple CSV files"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 1. Main experiment summary CSV
    main_rows = []
    for exp in data:
        row = {
            'participantId': exp.get('participantId'),
            'experimentId': exp.get('experimentId'),
            'condition': exp.get('condition'),
            'paper': exp.get('paper'),
            'status': exp.get('status'),
            'mode': exp.get('mode'),

            # Pre-task
            'preTask_strategies': json.dumps(exp.get('preTask', {}).get('strategies', []), default=str),
            'preTask_confidence': exp.get('preTask', {}).get('confidence'),
            'preTask_approachClarity': exp.get('preTask', {}).get('approachClarity'),
            'preTask_challenges': exp.get('preTask', {}).get('challenges'),
            'preTask_completedAt': exp.get('preTask', {}).get('completedAt'),

            # Reading
            'reading_duration': exp.get('reading', {}).get('duration'),
            'reading_totalEvents': exp.get('reading', {}).get('totalEvents'),
            'reading_focusTimes_reading': exp.get('reading', {}).get('focusTimes', {}).get('reading'),
            'reading_focusTimes_chat': exp.get('reading', {}).get('focusTimes', {}).get('chat'),
            'reading_focusTimes_audio': exp.get('reading', {}).get('focusTimes', {}).get('audio'),
            'reading_focusTimes_video': exp.get('reading', {}).get('focusTimes', {}).get('video'),
            'reading_focusTimes_infographics': exp.get('reading', {}).get('focusTimes', {}).get('infographics'),
            'reading_focusTimes_simplified': exp.get('reading', {}).get('focusTimes', {}).get('simplified'),
            'reading_focusTimes_quiz': exp.get('reading', {}).get('focusTimes', {}).get('quiz'),
            'reading_classification_reading_count': exp.get('reading', {}).get('classificationSummary', {}).get('reading', {}).get('count'),
            'reading_classification_reading_duration': exp.get('reading', {}).get('classificationSummary', {}).get('reading', {}).get('totalDuration'),
            'reading_classification_scanning_count': exp.get('reading', {}).get('classificationSummary', {}).get('scanning', {}).get('count'),
            'reading_classification_scanning_duration': exp.get('reading', {}).get('classificationSummary', {}).get('scanning', {}).get('totalDuration'),
            'reading_classification_scrolling_count': exp.get('reading', {}).get('classificationSummary', {}).get('scrolling', {}).get('count'),
            'reading_classification_scrolling_duration': exp.get('reading', {}).get('classificationSummary', {}).get('scrolling', {}).get('totalDuration'),

            # LLM Interaction (for with_llm conditions)
            'llmInteraction_totalQueries': exp.get('llmInteraction', {}).get('totalQueries'),

            # Extended Resources (for with_llm_extended)
            'extendedResources_audioInteractions': exp.get('extendedResources', {}).get('audioInteractions'),
            'extendedResources_videoInteractions': exp.get('extendedResources', {}).get('videoInteractions'),
            'extendedResources_tabSwitchCount': exp.get('extendedResources', {}).get('tabSwitchCount'),

            # Quiz
            'quiz_correctCount': exp.get('quiz', {}).get('correctCount'),
            'quiz_notSureCount': exp.get('quiz', {}).get('notSureCount'),
            'quiz_totalQuestions': exp.get('quiz', {}).get('totalQuestions'),
            'quiz_accuracy': exp.get('quiz', {}).get('accuracy'),
            'quiz_confidence': exp.get('quiz', {}).get('confidence'),
            'quiz_duration': exp.get('quiz', {}).get('duration'),

            # Post-task
            'postTask_strategies': json.dumps(exp.get('postTask', {}).get('strategies', []), default=str),
            'postTask_thinkingChange': exp.get('postTask', {}).get('thinkingChange'),
            'postTask_newStrategyConfidence': exp.get('postTask', {}).get('newStrategyConfidence'),
            'postTask_implementationLikelihood': exp.get('postTask', {}).get('implementationLikelihood'),
            'postTask_completedAt': exp.get('postTask', {}).get('completedAt'),

            # Post-study Survey - NASA-TLX
            'survey_nasaTLX_mentalDemand': exp.get('postStudySurvey', {}).get('nasaTLX', {}).get('mentalDemand'),
            'survey_nasaTLX_physicalDemand': exp.get('postStudySurvey', {}).get('nasaTLX', {}).get('physicalDemand'),
            'survey_nasaTLX_temporalDemand': exp.get('postStudySurvey', {}).get('nasaTLX', {}).get('temporalDemand'),
            'survey_nasaTLX_performance': exp.get('postStudySurvey', {}).get('nasaTLX', {}).get('performance'),
            'survey_nasaTLX_effort': exp.get('postStudySurvey', {}).get('nasaTLX', {}).get('effort'),
            'survey_nasaTLX_frustration': exp.get('postStudySurvey', {}).get('nasaTLX', {}).get('frustration'),

            # Post-study Survey - Self-efficacy
            'survey_selfEfficacy_overallGoal': exp.get('postStudySurvey', {}).get('selfEfficacy', {}).get('overallComprehension', {}).get('overallGoal'),
            'survey_selfEfficacy_authorsReasoning': exp.get('postStudySurvey', {}).get('selfEfficacy', {}).get('overallComprehension', {}).get('authorsReasoning'),
            'survey_selfEfficacy_connectingIdeas': exp.get('postStudySurvey', {}).get('selfEfficacy', {}).get('overallComprehension', {}).get('connectingIdeas'),
            'survey_selfEfficacy_ownIdeas': exp.get('postStudySurvey', {}).get('selfEfficacy', {}).get('criticalEngagement', {}).get('ownIdeas'),
            'survey_selfEfficacy_alternativePerspectives': exp.get('postStudySurvey', {}).get('selfEfficacy', {}).get('criticalEngagement', {}).get('alternativePerspectives'),
            'survey_selfEfficacy_verifyCredibility': exp.get('postStudySurvey', {}).get('selfEfficacy', {}).get('criticalEngagement', {}).get('verifyCredibility'),
            'survey_selfEfficacy_questionClaims': exp.get('postStudySurvey', {}).get('selfEfficacy', {}).get('criticalEngagement', {}).get('questionClaims'),
            'survey_selfEfficacy_broaderImplications': exp.get('postStudySurvey', {}).get('selfEfficacy', {}).get('criticalEngagement', {}).get('broaderImplications'),

            # Post-study Survey - LLM Usefulness (for with_llm conditions)
            'survey_llmUsefulness_overall': exp.get('postStudySurvey', {}).get('llmUsefulness', {}).get('overall'),
            'survey_llmUsefulness_conceptHelp': exp.get('postStudySurvey', {}).get('llmUsefulness', {}).get('conceptHelp'),
            'survey_llmUsefulness_findingsHelp': exp.get('postStudySurvey', {}).get('llmUsefulness', {}).get('findingsHelp'),
            'survey_llmUsefulness_practicalHelp': exp.get('postStudySurvey', {}).get('llmUsefulness', {}).get('practicalHelp'),
            'survey_llmUsefulness_timeSaving': exp.get('postStudySurvey', {}).get('llmUsefulness', {}).get('timeSaving'),

            # Post-study Survey - LLM Trust (for with_llm conditions)
            'survey_llmTrust_competence': exp.get('postStudySurvey', {}).get('llmTrust', {}).get('competence'),
            'survey_llmTrust_accuracy': exp.get('postStudySurvey', {}).get('llmTrust', {}).get('accuracy'),
            'survey_llmTrust_benevolence': exp.get('postStudySurvey', {}).get('llmTrust', {}).get('benevolence'),
            'survey_llmTrust_reliability': exp.get('postStudySurvey', {}).get('llmTrust', {}).get('reliability'),
            'survey_llmTrust_comfortActing': exp.get('postStudySurvey', {}).get('llmTrust', {}).get('comfortActing'),
            'survey_llmTrust_comfortUsing': exp.get('postStudySurvey', {}).get('llmTrust', {}).get('comfortUsing'),

            # Post-study Survey - AI Usage
            'survey_aiUsage_frequency': exp.get('postStudySurvey', {}).get('aiUsage', {}).get('frequency'),
            'survey_aiUsage_toolsUsed': exp.get('postStudySurvey', {}).get('aiUsage', {}).get('toolsUsed'),
            'survey_aiUsage_purposes': json.dumps(exp.get('postStudySurvey', {}).get('aiUsage', {}).get('purposes', []), default=str),

            # Post-study Survey - Demographics
            'survey_demographics_age': exp.get('postStudySurvey', {}).get('demographics', {}).get('age'),
            'survey_demographics_gender': exp.get('postStudySurvey', {}).get('demographics', {}).get('gender'),
            'survey_demographics_workingSituation': exp.get('postStudySurvey', {}).get('demographics', {}).get('workingSituation'),
            'survey_demographics_workHoursPerWeek': exp.get('postStudySurvey', {}).get('demographics', {}).get('workHoursPerWeek'),
            'survey_demographics_yearsInOrganization': exp.get('postStudySurvey', {}).get('demographics', {}).get('yearsInOrganization'),
            'survey_demographics_yearsInJob': exp.get('postStudySurvey', {}).get('demographics', {}).get('yearsInJob'),
            'survey_demographics_jobTitle': exp.get('postStudySurvey', {}).get('demographics', {}).get('jobTitle'),
            'survey_demographics_industry': exp.get('postStudySurvey', {}).get('demographics', {}).get('industry'),
            'survey_demographics_ethnicity': json.dumps(exp.get('postStudySurvey', {}).get('demographics', {}).get('ethnicity', []), default=str),
            'survey_demographics_education': exp.get('postStudySurvey', {}).get('demographics', {}).get('education'),
            'survey_demographics_englishProficiency': exp.get('postStudySurvey', {}).get('demographics', {}).get('englishProficiency'),

            # Post-study Survey - Attention Check
            'survey_attentionCheck_focus': exp.get('postStudySurvey', {}).get('attentionCheck', {}).get('focus'),
            'survey_attentionCheck_stronglyDisagreeCheck': exp.get('postStudySurvey', {}).get('attentionCheck', {}).get('stronglyDisagreeCheck'),

            # Post-study Survey - Feedback
            'survey_studyFeedback': exp.get('postStudySurvey', {}).get('studyFeedback'),
            'survey_completedAt': exp.get('postStudySurvey', {}).get('surveyCompletedAt'),
        }
        main_rows.append(row)

    # Save main CSV
    main_filename = f"experiments_main_{timestamp}.csv"
    main_filepath = os.path.join(output_dir, main_filename)

    if main_rows:
        with open(main_filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=main_rows[0].keys())
            writer.writeheader()
            writer.writerows(main_rows)
        print(f"  Saved main CSV: {main_filepath}")

    # 2. Quiz answers CSV
    quiz_rows = []
    for exp in data:
        if exp.get('quiz', {}).get('answers'):
            for q_id, answer in exp.get('quiz', {}).get('answers', {}).items():
                grading = exp.get('quiz', {}).get('gradingDetails', {}).get(q_id, {})
                quiz_rows.append({
                    'participantId': exp.get('participantId'),
                    'experimentId': exp.get('experimentId'),
                    'condition': exp.get('condition'),
                    'questionId': q_id,
                    'userAnswer': answer,
                    'correctAnswer': grading.get('correctAnswer'),
                    'isCorrect': grading.get('isCorrect'),
                    'isNotSure': grading.get('isNotSure'),
                })

    if quiz_rows:
        quiz_filename = f"quiz_answers_{timestamp}.csv"
        quiz_filepath = os.path.join(output_dir, quiz_filename)
        with open(quiz_filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=quiz_rows[0].keys())
            writer.writeheader()
            writer.writerows(quiz_rows)
        print(f"  Saved quiz CSV: {quiz_filepath}")

    # 3. LLM chat history CSV
    chat_rows = []
    for exp in data:
        if exp.get('llmInteraction', {}).get('messages'):
            for i, msg in enumerate(exp.get('llmInteraction', {}).get('messages', [])):
                chat_rows.append({
                    'participantId': exp.get('participantId'),
                    'experimentId': exp.get('experimentId'),
                    'condition': exp.get('condition'),
                    'messageIndex': i,
                    'role': msg.get('role'),
                    'content': msg.get('content'),
                    'timestamp': msg.get('timestamp'),
                })

    if chat_rows:
        chat_filename = f"llm_chat_history_{timestamp}.csv"
        chat_filepath = os.path.join(output_dir, chat_filename)
        with open(chat_filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=chat_rows[0].keys())
            writer.writeheader()
            writer.writerows(chat_rows)
        print(f"  Saved chat CSV: {chat_filepath}")

    # 4. Reading events CSV (optional - can be large)
    events_rows = []
    for exp in data:
        if exp.get('reading', {}).get('events'):
            for event in exp.get('reading', {}).get('events', []):
                events_rows.append({
                    'participantId': exp.get('participantId'),
                    'experimentId': exp.get('experimentId'),
                    'condition': exp.get('condition'),
                    'eventId': event.get('eventId'),
                    'eventType': event.get('eventType'),
                    'timestamp': event.get('timestamp'),
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
                })

    if events_rows:
        events_filename = f"reading_events_{timestamp}.csv"
        events_filepath = os.path.join(output_dir, events_filename)
        with open(events_filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=events_rows[0].keys())
            writer.writeheader()
            writer.writerows(events_rows)
        print(f"  Saved events CSV: {events_filepath}")

    return main_filepath


def check_data_completeness(data):
    """Check which fields are missing or incomplete"""
    print("\n" + "="*60)
    print("DATA COMPLETENESS CHECK")
    print("="*60)

    # Define expected fields by section
    expected_fields = {
        'preTask': ['strategies', 'confidence', 'approachClarity', 'challenges', 'completedAt'],
        'reading': ['duration', 'events', 'focusTimes', 'classificationSummary', 'completedAt'],
        'quiz': ['answers', 'confidence', 'duration', 'gradingDetails', 'correctCount', 'accuracy', 'submittedAt'],
        'postTask': ['strategies', 'thinkingChange', 'newStrategyConfidence', 'implementationLikelihood', 'completedAt'],
        'postStudySurvey.nasaTLX': ['mentalDemand', 'physicalDemand', 'temporalDemand', 'performance', 'effort', 'frustration'],
        'postStudySurvey.selfEfficacy.overallComprehension': ['overallGoal', 'authorsReasoning', 'connectingIdeas'],
        'postStudySurvey.selfEfficacy.criticalEngagement': ['ownIdeas', 'alternativePerspectives', 'verifyCredibility', 'questionClaims', 'broaderImplications'],
        'postStudySurvey.aiUsage': ['frequency', 'toolsUsed', 'purposes'],
        'postStudySurvey.demographics': ['age', 'gender', 'workingSituation', 'workHoursPerWeek', 'yearsInOrganization', 'yearsInJob', 'jobTitle', 'industry', 'ethnicity', 'education', 'englishProficiency'],
        'postStudySurvey.attentionCheck': ['focus', 'stronglyDisagreeCheck'],
    }

    # LLM-specific fields
    llm_fields = {
        'llmInteraction': ['messages', 'totalQueries'],
        'postStudySurvey.llmUsefulness': ['overall', 'conceptHelp', 'findingsHelp', 'practicalHelp', 'timeSaving'],
        'postStudySurvey.llmTrust': ['competence', 'accuracy', 'benevolence', 'reliability', 'comfortActing', 'comfortUsing'],
    }

    # Extended fields
    extended_fields = {
        'extendedResources': ['audioInteractions', 'videoInteractions', 'tabSwitchCount', 'inTabQuizAnswers'],
    }

    for exp in data:
        pid = exp.get('participantId', 'Unknown')
        condition = exp.get('condition', 'Unknown')
        status = exp.get('status', 'Unknown')

        print(f"\n--- {pid} ({condition}) - Status: {status} ---")

        missing = []

        # Check common fields
        for section, fields in expected_fields.items():
            parts = section.split('.')
            obj = exp
            for part in parts:
                obj = obj.get(part, {}) if obj else {}

            for field in fields:
                if obj.get(field) is None:
                    missing.append(f"{section}.{field}")

        # Check LLM fields if with_llm condition
        if condition in ['with_llm', 'with_llm_extended']:
            for section, fields in llm_fields.items():
                parts = section.split('.')
                obj = exp
                for part in parts:
                    obj = obj.get(part, {}) if obj else {}

                for field in fields:
                    if obj.get(field) is None:
                        missing.append(f"{section}.{field}")

        # Check extended fields if with_llm_extended condition
        if condition == 'with_llm_extended':
            for section, fields in extended_fields.items():
                obj = exp.get(section, {})
                for field in fields:
                    if obj.get(field) is None:
                        missing.append(f"{section}.{field}")

        if missing:
            print(f"  MISSING ({len(missing)}):")
            for m in missing:
                print(f"    - {m}")
        else:
            print("  All fields present!")

    print("\n" + "="*60)


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Export Firebase experiment data to JSON and CSV',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python export_firebase_data.py                              # Export all data
  python export_firebase_data.py --after "2025-12-20 03:30"   # Export after datetime
  python export_firebase_data.py --today                      # Export only today's data
        """
    )
    parser.add_argument(
        '--after',
        type=str,
        help='Only export data after this datetime (format: "YYYY-MM-DD HH:MM" or "YYYY-MM-DD")'
    )
    parser.add_argument(
        '--today',
        action='store_true',
        help='Only export data from today'
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Determine datetime filter
    after_datetime = None
    if args.today:
        # Today at midnight KST
        now_kst = datetime.now(KST)
        after_datetime = now_kst.replace(hour=0, minute=0, second=0, microsecond=0)
    elif args.after:
        try:
            # Try parsing with time (as KST)
            after_datetime = datetime.strptime(args.after, '%Y-%m-%d %H:%M').replace(tzinfo=KST)
        except ValueError:
            try:
                # Try parsing date only (as KST)
                after_datetime = datetime.strptime(args.after, '%Y-%m-%d').replace(tzinfo=KST)
            except ValueError:
                print(f"ERROR: Invalid datetime format '{args.after}'.")
                print("Use format: 'YYYY-MM-DD HH:MM' or 'YYYY-MM-DD'")
                return

    print("="*60)
    print("FIREBASE DATA EXPORT")
    if after_datetime:
        print(f"Filter: after {after_datetime.strftime('%Y-%m-%d %H:%M')} KST")
    print("="*60)

    # Create output directory
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'data_exports')
    os.makedirs(output_dir, exist_ok=True)

    # Initialize Firebase
    db = init_firebase()
    if not db:
        return

    # Fetch data
    data = fetch_all_experiments(db, after_datetime=after_datetime)

    if not data:
        print("No data found!")
        return

    # Save raw JSON
    print("\nSaving raw JSON...")
    save_raw_json(data, output_dir)

    # Convert to CSV
    print("\nConverting to CSV...")
    convert_to_csv(data, output_dir)

    # Check completeness
    check_data_completeness(data)

    print("\n" + "="*60)
    print("EXPORT COMPLETE")
    print(f"Files saved to: {os.path.abspath(output_dir)}")
    print("="*60)


if __name__ == '__main__':
    main()
