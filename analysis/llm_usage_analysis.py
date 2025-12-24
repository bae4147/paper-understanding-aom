#!/usr/bin/env python3
"""
LLM Usage Pattern Analysis for Reading Experiment
Analyzes: with_llm and with_llm_extended conditions
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

def load_data():
    """Load all required datasets"""
    experiments = pd.read_csv(DATA_DIR / "experiments.csv")
    reading_events = pd.read_csv(DATA_DIR / "reading_events.csv")
    llm_messages = pd.read_csv(DATA_DIR / "llm_messages.csv")
    participants = pd.read_csv(DATA_DIR / "participants.csv")

    return experiments, reading_events, llm_messages, participants

def filter_llm_conditions(experiments):
    """Filter for with_llm and with_llm_extended conditions"""
    llm_conditions = experiments[experiments['condition'].isin(['with_llm', 'with_llm_extended'])]
    return llm_conditions

def calculate_media_time(reading_events, llm_experiments):
    """Calculate time spent on each media type per participant"""

    # Filter events for LLM condition participants
    participant_ids = llm_experiments['participantId'].unique()
    events = reading_events[reading_events['participantId'].isin(participant_ids)].copy()

    # Merge with condition info
    events = events.merge(
        llm_experiments[['participantId', 'condition']],
        on='participantId',
        how='left'
    )

    results = []

    for participant_id in participant_ids:
        participant_events = events[events['participantId'] == participant_id].copy()
        condition = participant_events['condition'].iloc[0] if len(participant_events) > 0 else None

        if condition is None:
            continue

        # Sort by timestamp
        participant_events = participant_events.sort_values('timestamp')

        # Initialize time counters (in milliseconds)
        time_reading = 0  # scroll_action, text_selection (while reading)
        time_llm = 0      # llm_activity
        time_video = 0    # video_play to video_pause/video_ended
        time_audio = 0    # audio_play to audio_pause/audio_ended

        # Track media play states
        video_start = None
        audio_start = None

        for _, event in participant_events.iterrows():
            event_type = event['eventType']
            timestamp = event['timestamp']

            # Video tracking
            if event_type == 'video_play':
                video_start = timestamp
            elif event_type in ['video_pause', 'video_ended'] and video_start is not None:
                time_video += timestamp - video_start
                video_start = None

            # Audio tracking
            elif event_type == 'audio_play':
                audio_start = timestamp
            elif event_type in ['audio_pause', 'audio_ended'] and audio_start is not None:
                time_audio += timestamp - audio_start
                audio_start = None

            # LLM activity time (using timeSinceLast when on LLM)
            elif event_type == 'llm_activity':
                if pd.notna(event['timeSinceLast']):
                    time_llm += event['timeSinceLast']

            # Reading time (scroll actions with reading/scanning classification)
            elif event_type == 'scroll_action':
                classification = event['classification']
                if classification in ['reading', 'scanning']:
                    if pd.notna(event['pauseDuration']):
                        time_reading += event['pauseDuration']

        results.append({
            'participantId': participant_id,
            'condition': condition,
            'reading_time_ms': time_reading,
            'llm_time_ms': time_llm,
            'video_time_ms': time_video,
            'audio_time_ms': time_audio,
            'reading_time_min': time_reading / 60000,
            'llm_time_min': time_llm / 60000,
            'video_time_min': time_video / 60000,
            'audio_time_min': time_audio / 60000,
        })

    return pd.DataFrame(results)

def analyze_llm_queries(llm_messages, llm_experiments):
    """Analyze LLM query patterns"""

    # Merge with condition
    messages = llm_messages.merge(
        llm_experiments[['participantId', 'condition']],
        on='participantId',
        how='inner'
    )

    # Count queries per participant
    query_counts = messages.groupby(['participantId', 'condition']).size().reset_index(name='query_count')

    return query_counts, messages

def create_timeline_data(reading_events, llm_experiments, llm_messages):
    """Create timeline data for each participant showing when they used LLM"""

    participant_ids = llm_experiments['participantId'].unique()
    events = reading_events[reading_events['participantId'].isin(participant_ids)].copy()

    # Merge with condition info
    events = events.merge(
        llm_experiments[['participantId', 'condition']],
        on='participantId',
        how='left'
    )

    timeline_data = []

    for participant_id in participant_ids:
        participant_events = events[events['participantId'] == participant_id].copy()
        condition = participant_events['condition'].iloc[0] if len(participant_events) > 0 else None

        if condition is None or len(participant_events) == 0:
            continue

        # Sort by timestamp
        participant_events = participant_events.sort_values('timestamp')

        # Get start and end time
        start_time = participant_events['timestamp'].min()
        end_time = participant_events['timestamp'].max()
        total_duration = end_time - start_time

        # Collect events with their relative positions
        events_list = []

        for _, event in participant_events.iterrows():
            event_type = event['eventType']
            timestamp = event['timestamp']
            relative_pos = ((timestamp - start_time) / total_duration * 100) if total_duration > 0 else 0

            if event_type in ['llm_activity', 'video_play', 'video_pause', 'video_ended',
                             'audio_play', 'audio_pause', 'audio_ended', 'focus_switch']:
                events_list.append({
                    'type': event_type,
                    'timestamp': int(timestamp),
                    'relative_pos': round(relative_pos, 2),
                    'time_offset_sec': round((timestamp - start_time) / 1000, 1)
                })

        # Get LLM messages for this participant
        participant_messages = llm_messages[llm_messages['participantId'] == participant_id]
        llm_query_count = len(participant_messages)

        timeline_data.append({
            'participantId': participant_id,
            'condition': condition,
            'start_time': int(start_time),
            'end_time': int(end_time),
            'total_duration_min': round(total_duration / 60000, 2),
            'events': events_list,
            'llm_query_count': llm_query_count
        })

    return timeline_data

def generate_html_timeline(timeline_data):
    """Generate HTML page showing participant timelines"""

    # Sort by condition then participant ID
    timeline_data.sort(key=lambda x: (x['condition'], x['participantId']))

    html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Usage Timeline - Reading Experiment</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        h1 { color: #333; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; }

        .controls {
            background: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .controls label { margin-right: 20px; cursor: pointer; }

        .legend {
            display: flex;
            gap: 20px;
            flex-wrap: wrap;
            margin-bottom: 20px;
            background: white;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .legend-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }

        .condition-section {
            margin-bottom: 40px;
        }
        .condition-header {
            background: #333;
            color: white;
            padding: 10px 15px;
            border-radius: 8px 8px 0 0;
            font-weight: bold;
        }
        .condition-content {
            background: white;
            border-radius: 0 0 8px 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .participant-row {
            display: flex;
            align-items: center;
            padding: 8px 15px;
            border-bottom: 1px solid #eee;
        }
        .participant-row:last-child { border-bottom: none; }
        .participant-row:hover { background: #f9f9f9; }

        .participant-id {
            width: 200px;
            font-size: 12px;
            color: #666;
            flex-shrink: 0;
        }
        .participant-meta {
            width: 120px;
            font-size: 11px;
            color: #999;
            flex-shrink: 0;
        }

        .timeline-container {
            flex: 1;
            height: 30px;
            background: #e9ecef;
            border-radius: 4px;
            position: relative;
            overflow: hidden;
        }

        .event-marker {
            position: absolute;
            top: 50%;
            transform: translateY(-50%);
            width: 8px;
            height: 20px;
            border-radius: 2px;
            cursor: pointer;
        }
        .event-marker:hover {
            transform: translateY(-50%) scale(1.3);
            z-index: 10;
        }

        .event-llm { background: #e74c3c; }
        .event-video-play { background: #3498db; }
        .event-video-pause, .event-video-ended { background: #2980b9; }
        .event-audio-play { background: #2ecc71; }
        .event-audio-pause, .event-audio-ended { background: #27ae60; }
        .event-focus-switch { background: #9b59b6; opacity: 0.5; }

        .tooltip {
            position: fixed;
            background: #333;
            color: white;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
            display: none;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .stat-value { font-size: 28px; font-weight: bold; color: #333; }
        .stat-label { color: #666; font-size: 14px; }
    </style>
</head>
<body>
    <h1>LLM Usage Timeline</h1>
    <p class="subtitle">Reading Experiment - with_llm & with_llm_extended conditions</p>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value" id="total-participants">0</div>
            <div class="stat-label">Total Participants</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="with-llm-count">0</div>
            <div class="stat-label">with_llm</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="with-llm-extended-count">0</div>
            <div class="stat-label">with_llm_extended</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="avg-queries">0</div>
            <div class="stat-label">Avg. LLM Queries</div>
        </div>
    </div>

    <div class="legend">
        <div class="legend-item">
            <div class="legend-color" style="background: #e74c3c;"></div>
            <span>LLM Activity</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #3498db;"></div>
            <span>Video</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #2ecc71;"></div>
            <span>Audio</span>
        </div>
        <div class="legend-item">
            <div class="legend-color" style="background: #9b59b6; opacity: 0.5;"></div>
            <span>Focus Switch</span>
        </div>
    </div>

    <div class="controls">
        <label><input type="checkbox" id="show-llm" checked> Show LLM</label>
        <label><input type="checkbox" id="show-video" checked> Show Video</label>
        <label><input type="checkbox" id="show-audio" checked> Show Audio</label>
        <label><input type="checkbox" id="show-focus" checked> Show Focus Switch</label>
    </div>

    <div id="timelines"></div>

    <div class="tooltip" id="tooltip"></div>

    <script>
    const timelineData = TIMELINE_DATA_PLACEHOLDER;

    // Calculate stats
    const withLlm = timelineData.filter(d => d.condition === 'with_llm');
    const withLlmExtended = timelineData.filter(d => d.condition === 'with_llm_extended');
    const totalQueries = timelineData.reduce((sum, d) => sum + d.llm_query_count, 0);

    document.getElementById('total-participants').textContent = timelineData.length;
    document.getElementById('with-llm-count').textContent = withLlm.length;
    document.getElementById('with-llm-extended-count').textContent = withLlmExtended.length;
    document.getElementById('avg-queries').textContent = (totalQueries / timelineData.length).toFixed(1);

    function renderTimelines() {
        const container = document.getElementById('timelines');
        const showLlm = document.getElementById('show-llm').checked;
        const showVideo = document.getElementById('show-video').checked;
        const showAudio = document.getElementById('show-audio').checked;
        const showFocus = document.getElementById('show-focus').checked;

        const conditions = ['with_llm', 'with_llm_extended'];
        let html = '';

        conditions.forEach(condition => {
            const participants = timelineData.filter(d => d.condition === condition);
            if (participants.length === 0) return;

            html += `
                <div class="condition-section">
                    <div class="condition-header">${condition} (${participants.length} participants)</div>
                    <div class="condition-content">
            `;

            participants.forEach(p => {
                html += `
                    <div class="participant-row">
                        <div class="participant-id">${p.participantId}</div>
                        <div class="participant-meta">${p.total_duration_min} min | ${p.llm_query_count} queries</div>
                        <div class="timeline-container">
                `;

                p.events.forEach(event => {
                    let show = false;
                    let cssClass = '';

                    if (event.type === 'llm_activity' && showLlm) {
                        show = true;
                        cssClass = 'event-llm';
                    } else if (event.type.startsWith('video') && showVideo) {
                        show = true;
                        cssClass = 'event-' + event.type.replace('_', '-');
                    } else if (event.type.startsWith('audio') && showAudio) {
                        show = true;
                        cssClass = 'event-' + event.type.replace('_', '-');
                    } else if (event.type === 'focus_switch' && showFocus) {
                        show = true;
                        cssClass = 'event-focus-switch';
                    }

                    if (show) {
                        html += `<div class="event-marker ${cssClass}"
                                     style="left: ${event.relative_pos}%;"
                                     data-type="${event.type}"
                                     data-time="${event.time_offset_sec}s"></div>`;
                    }
                });

                html += `
                        </div>
                    </div>
                `;
            });

            html += `
                    </div>
                </div>
            `;
        });

        container.innerHTML = html;

        // Add tooltips
        document.querySelectorAll('.event-marker').forEach(marker => {
            marker.addEventListener('mouseenter', (e) => {
                const tooltip = document.getElementById('tooltip');
                tooltip.textContent = `${e.target.dataset.type} @ ${e.target.dataset.time}`;
                tooltip.style.display = 'block';
                tooltip.style.left = e.pageX + 10 + 'px';
                tooltip.style.top = e.pageY - 30 + 'px';
            });
            marker.addEventListener('mouseleave', () => {
                document.getElementById('tooltip').style.display = 'none';
            });
        });
    }

    // Event listeners for checkboxes
    document.querySelectorAll('.controls input').forEach(input => {
        input.addEventListener('change', renderTimelines);
    });

    renderTimelines();
    </script>
</body>
</html>
"""

    # Replace placeholder with actual data
    html = html.replace('TIMELINE_DATA_PLACEHOLDER', json.dumps(timeline_data, ensure_ascii=False))

    return html

def generate_summary_stats(media_time_df, query_counts_df):
    """Generate summary statistics"""

    summary = {}

    # Overall stats
    summary['total_participants'] = len(media_time_df)
    summary['with_llm_count'] = len(media_time_df[media_time_df['condition'] == 'with_llm'])
    summary['with_llm_extended_count'] = len(media_time_df[media_time_df['condition'] == 'with_llm_extended'])

    # Media time by condition
    for condition in ['with_llm', 'with_llm_extended']:
        cond_data = media_time_df[media_time_df['condition'] == condition]
        summary[f'{condition}_reading_time_avg'] = round(cond_data['reading_time_min'].mean(), 2)
        summary[f'{condition}_llm_time_avg'] = round(cond_data['llm_time_min'].mean(), 2)
        summary[f'{condition}_video_time_avg'] = round(cond_data['video_time_min'].mean(), 2)
        summary[f'{condition}_audio_time_avg'] = round(cond_data['audio_time_min'].mean(), 2)

    # LLM query stats
    for condition in ['with_llm', 'with_llm_extended']:
        cond_queries = query_counts_df[query_counts_df['condition'] == condition]
        summary[f'{condition}_queries_avg'] = round(cond_queries['query_count'].mean(), 2)
        summary[f'{condition}_queries_median'] = round(cond_queries['query_count'].median(), 2)
        summary[f'{condition}_queries_max'] = int(cond_queries['query_count'].max())
        summary[f'{condition}_queries_min'] = int(cond_queries['query_count'].min())
        summary[f'{condition}_queries_total'] = int(cond_queries['query_count'].sum())

    return summary

def main():
    print("Loading data...")
    experiments, reading_events, llm_messages, participants = load_data()

    print("Filtering LLM conditions...")
    llm_experiments = filter_llm_conditions(experiments)
    print(f"  with_llm: {len(llm_experiments[llm_experiments['condition'] == 'with_llm'])} participants")
    print(f"  with_llm_extended: {len(llm_experiments[llm_experiments['condition'] == 'with_llm_extended'])} participants")

    print("\nCalculating media time...")
    media_time_df = calculate_media_time(reading_events, llm_experiments)
    media_time_df.to_csv(OUTPUT_DIR / "media_time_by_participant.csv", index=False)
    print(f"  Saved to {OUTPUT_DIR / 'media_time_by_participant.csv'}")

    print("\nAnalyzing LLM queries...")
    query_counts_df, messages_with_condition = analyze_llm_queries(llm_messages, llm_experiments)
    query_counts_df.to_csv(OUTPUT_DIR / "llm_query_counts.csv", index=False)
    print(f"  Saved to {OUTPUT_DIR / 'llm_query_counts.csv'}")

    print("\nCreating timeline data...")
    timeline_data = create_timeline_data(reading_events, llm_experiments, llm_messages)

    print("\nGenerating HTML timeline...")
    html = generate_html_timeline(timeline_data)
    html_path = OUTPUT_DIR / "llm_usage_timeline.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  Saved to {html_path}")

    print("\nGenerating summary statistics...")
    summary = generate_summary_stats(media_time_df, query_counts_df)

    # Save summary as JSON
    with open(OUTPUT_DIR / "summary_stats.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)
    print(f"\nTotal LLM condition participants: {summary['total_participants']}")
    print(f"  - with_llm: {summary['with_llm_count']}")
    print(f"  - with_llm_extended: {summary['with_llm_extended_count']}")

    print("\n--- Media Time (minutes, average) ---")
    print(f"{'Condition':<20} {'Reading':<10} {'LLM':<10} {'Video':<10} {'Audio':<10}")
    print("-"*60)
    for condition in ['with_llm', 'with_llm_extended']:
        print(f"{condition:<20} {summary[f'{condition}_reading_time_avg']:<10} {summary[f'{condition}_llm_time_avg']:<10} {summary[f'{condition}_video_time_avg']:<10} {summary[f'{condition}_audio_time_avg']:<10}")

    print("\n--- LLM Query Statistics ---")
    print(f"{'Condition':<20} {'Avg':<8} {'Median':<8} {'Min':<8} {'Max':<8} {'Total':<8}")
    print("-"*60)
    for condition in ['with_llm', 'with_llm_extended']:
        print(f"{condition:<20} {summary[f'{condition}_queries_avg']:<8} {summary[f'{condition}_queries_median']:<8} {summary[f'{condition}_queries_min']:<8} {summary[f'{condition}_queries_max']:<8} {summary[f'{condition}_queries_total']:<8}")

    return summary, media_time_df, query_counts_df

if __name__ == "__main__":
    main()
