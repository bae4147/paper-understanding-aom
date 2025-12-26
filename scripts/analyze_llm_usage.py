#!/usr/bin/env python3
"""
LLM Usage Analysis
1. Media usage time comparison by condition (Reading vs. LLM vs. Video vs. Audio vs. Infographics)
2. Average LLM query count by condition

Data sources: merged_all.csv, reading_events.csv, llm_messages.csv
Note: Video, Audio, Infographics times are calculated from focus_switch/resource_tab_switch events
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
        return {'n': 0, 'mean': None, 'sd': None, 'variance': None, 'min': None, 'max': None, 'median': None}

    mean = sum(valid) / n
    if n > 1:
        variance = sum((x - mean) ** 2 for x in valid) / (n - 1)
        sd = math.sqrt(variance)
    else:
        variance = 0
        sd = 0

    # Calculate median
    sorted_valid = sorted(valid)
    if n % 2 == 0:
        median = (sorted_valid[n // 2 - 1] + sorted_valid[n // 2]) / 2
    else:
        median = sorted_valid[n // 2]

    return {
        'n': n,
        'mean': mean,
        'sd': sd,
        'variance': variance,
        'min': min(valid),
        'max': max(valid),
        'median': median
    }


def calculate_tab_times_from_events(events):
    """
    Calculate time spent on each tab from focus_switch and resource_tab_switch events.

    Logic:
    - Start with 'reading' as default initial focus
    - Each focus_switch/resource_tab_switch marks the end of the previous segment
    - The duration is from segment_start to event timestamp
    """
    switch_events = [e for e in events
                     if e['eventType'] in ('focus_switch', 'resource_tab_switch')]

    all_timestamps = [safe_float(e['timestamp']) for e in events if safe_float(e['timestamp'])]
    if not all_timestamps:
        return {}

    first_timestamp = min(all_timestamps)
    last_timestamp = max(all_timestamps)

    # Build segments
    segments = []
    current_tab = 'reading'  # Default initial focus
    segment_start = first_timestamp

    for se in switch_events:
        ts = safe_float(se['timestamp'])
        if ts is None:
            continue

        # End current segment
        if ts > segment_start:
            segments.append({
                'start': segment_start,
                'end': ts,
                'tab': current_tab,
                'duration': ts - segment_start
            })

        # Start new segment
        new_tab = se.get('to', '')
        if new_tab:
            current_tab = new_tab
        segment_start = ts

    # Add final segment
    if last_timestamp > segment_start:
        segments.append({
            'start': segment_start,
            'end': last_timestamp,
            'tab': current_tab,
            'duration': last_timestamp - segment_start
        })

    # Sum up times per tab (in milliseconds)
    tab_times = defaultdict(float)
    for seg in segments:
        tab_times[seg['tab']] += seg['duration']

    return dict(tab_times)


def main():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    processed_dir = os.path.join(base_dir, 'data', 'processed')
    output_dir = os.path.join(base_dir, 'analysis_results')
    os.makedirs(output_dir, exist_ok=True)

    # Load data from processed CSV files
    merged_all = load_csv(os.path.join(processed_dir, 'merged_all.csv'))
    llm_messages = load_csv(os.path.join(processed_dir, 'llm_messages.csv'))
    reading_events = load_csv(os.path.join(processed_dir, 'reading_events.csv'))

    # Get condition mapping from merged_all
    participant_conditions = {row['participantId']: row['condition'] for row in merged_all}

    # Group events by participant
    events_by_pid = defaultdict(list)
    for event in reading_events:
        events_by_pid[event['participantId']].append(event)

    # Sort events by timestamp
    for pid in events_by_pid:
        events_by_pid[pid].sort(key=lambda x: safe_float(x['timestamp']) or 0)

    # Count LLM queries per participant
    query_counts = defaultdict(int)
    for msg in llm_messages:
        pid = msg['participantId']
        if pid in participant_conditions:
            query_counts[pid] += 1

    # Filter LLM conditions only from merged_all
    with_llm = [p for p in merged_all if p['condition'] == 'with_llm']
    with_llm_extended = [p for p in merged_all if p['condition'] == 'with_llm_extended']

    # Calculate media times for each participant
    # - Reading/Chat: use Firebase-calculated values from merged_all (accurate session timing)
    # - Video/Audio/Infographics: calculate from focus_switch/resource_tab_switch events
    def get_media_times(participant):
        pid = participant['participantId']
        events = events_by_pid.get(pid, [])

        # Reading and Chat from Firebase (accurate)
        reading_time = (safe_float(participant.get('reading_focusTime_reading')) or 0) / 1000
        chat_time = (safe_float(participant.get('reading_focusTime_chat')) or 0) / 1000

        # Video/Audio/Infographics from events (only available in events)
        video_time = 0
        audio_time = 0
        infographics_time = 0

        if events:
            tab_times_ms = calculate_tab_times_from_events(events)
            video_time = tab_times_ms.get('video', 0) / 1000
            audio_time = tab_times_ms.get('audio', 0) / 1000
            infographics_time = tab_times_ms.get('infographics', 0) / 1000

        return {
            'reading': reading_time,
            'chat': chat_time,
            'video': video_time,
            'audio': audio_time,
            'infographics': infographics_time,
        }

    # Process with_llm
    with_llm_media = [get_media_times(p) for p in with_llm]
    with_llm_queries = [query_counts.get(p['participantId'], 0) for p in with_llm]

    # Process with_llm_extended
    with_llm_extended_media = [get_media_times(p) for p in with_llm_extended]
    with_llm_extended_queries = [query_counts.get(p['participantId'], 0) for p in with_llm_extended]

    # Calculate stats
    def calc_media_stats(media_list, keys):
        return {key: calculate_stats([m[key] for m in media_list]) for key in keys}

    media_keys = ['reading', 'chat', 'video', 'audio', 'infographics']
    with_llm_media_stats = calc_media_stats(with_llm_media, media_keys)
    with_llm_extended_media_stats = calc_media_stats(with_llm_extended_media, media_keys)

    with_llm_query_stats = calculate_stats(with_llm_queries)
    with_llm_extended_query_stats = calculate_stats(with_llm_extended_queries)

    # Generate report
    report = []
    report.append("# LLM Usage Analysis Report")
    report.append("")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    report.append("Data source: merged_all.csv, reading_events.csv, llm_messages.csv")
    report.append("")
    report.append("Note: Media times (Video, Audio, Infographics) are calculated from focus_switch/resource_tab_switch events.")
    report.append("")
    report.append("---")
    report.append("")

    # ========================================
    # Part 1: Media Usage Time Comparison
    # ========================================
    report.append("## 1. Media Usage Time Comparison")
    report.append("")
    report.append("Time spent on each media type during the reading session (in seconds).")
    report.append("")

    # with_llm
    report.append("### 1.1 with_llm Condition")
    report.append("")
    report.append(f"N = {len(with_llm)}")
    report.append("")
    report.append("| Media | N | Mean | SD | Min | Max |")
    report.append("|-------|---|------|----:|----:|----:|")

    for media in ['reading', 'chat']:
        stats = with_llm_media_stats[media]
        label = {'reading': 'Reading (Paper)', 'chat': 'Chat/LLM'}.get(media, media.title())
        if stats['n'] > 0 and stats['mean'] is not None:
            report.append(f"| {label} | {stats['n']} | {stats['mean']:.1f}s | {stats['sd']:.1f}s | {stats['min']:.1f}s | {stats['max']:.1f}s |")
        else:
            report.append(f"| {label} | 0 | - | - | - | - |")

    report.append("")

    # with_llm_extended
    report.append("### 1.2 with_llm_extended Condition")
    report.append("")
    report.append(f"N = {len(with_llm_extended)}")
    report.append("")
    report.append("| Media | N | Mean | SD | Min | Max |")
    report.append("|-------|---|------|----:|----:|----:|")

    for media in ['reading', 'chat', 'video', 'audio', 'infographics']:
        stats = with_llm_extended_media_stats[media]
        labels = {
            'reading': 'Reading (Paper)',
            'chat': 'Chat/LLM',
            'video': 'Video',
            'audio': 'Audio',
            'infographics': 'Infographics'
        }
        label = labels.get(media, media.title())
        if stats['n'] > 0 and stats['mean'] is not None:
            report.append(f"| {label} | {stats['n']} | {stats['mean']:.1f}s | {stats['sd']:.1f}s | {stats['min']:.1f}s | {stats['max']:.1f}s |")
        else:
            report.append(f"| {label} | 0 | - | - | - | - |")

    report.append("")

    # Extended media usage (non-zero participants)
    report.append("### 1.3 Extended Media Usage (with_llm_extended)")
    report.append("")
    report.append("Participants who used each extended media type:")
    report.append("")

    for media in ['video', 'audio', 'infographics']:
        non_zero = [m[media] for m in with_llm_extended_media if m[media] > 0]
        pct = (len(non_zero) / len(with_llm_extended_media)) * 100 if with_llm_extended_media else 0
        if non_zero:
            avg = sum(non_zero) / len(non_zero)
            report.append(f"- **{media.title()}**: {len(non_zero)}/{len(with_llm_extended_media)} ({pct:.1f}%) used it, avg {avg:.1f}s among users")
        else:
            report.append(f"- **{media.title()}**: No usage")

    report.append("")

    # Comparison summary
    report.append("### 1.4 Comparison Summary")
    report.append("")
    report.append("| Condition | N | Reading (Mean) | Chat/LLM (Mean) | Video | Audio | Infographics |")
    report.append("|-----------|---|---------------:|----------------:|------:|------:|-------------:|")

    # with_llm row
    wl_reading = with_llm_media_stats['reading']['mean'] or 0
    wl_chat = with_llm_media_stats['chat']['mean'] or 0
    report.append(f"| with_llm | {len(with_llm)} | {wl_reading:.1f}s | {wl_chat:.1f}s | - | - | - |")

    # with_llm_extended row
    wle_reading = with_llm_extended_media_stats['reading']['mean'] or 0
    wle_chat = with_llm_extended_media_stats['chat']['mean'] or 0
    wle_video = with_llm_extended_media_stats['video']['mean'] or 0
    wle_audio = with_llm_extended_media_stats['audio']['mean'] or 0
    wle_infographics = with_llm_extended_media_stats['infographics']['mean'] or 0
    report.append(f"| with_llm_extended | {len(with_llm_extended)} | {wle_reading:.1f}s | {wle_chat:.1f}s | {wle_video:.1f}s | {wle_audio:.1f}s | {wle_infographics:.1f}s |")

    report.append("")

    # ========================================
    # Part 2: LLM Query Statistics
    # ========================================
    report.append("---")
    report.append("")
    report.append("## 2. LLM Query Statistics")
    report.append("")
    report.append("Number of queries sent to the LLM during the reading session (from llm_messages.csv).")
    report.append("")

    report.append("### 2.1 Query Count by Condition")
    report.append("")
    report.append("| Condition | N | Mean | SD | Median | Min | Max |")
    report.append("|-----------|---|------|----:|-------:|----:|----:|")

    # with_llm
    stats = with_llm_query_stats
    if stats['n'] > 0:
        report.append(f"| with_llm | {stats['n']} | {stats['mean']:.2f} | {stats['sd']:.2f} | {stats['median']:.1f} | {stats['min']:.0f} | {stats['max']:.0f} |")
    else:
        report.append(f"| with_llm | 0 | - | - | - | - | - |")

    # with_llm_extended
    stats = with_llm_extended_query_stats
    if stats['n'] > 0:
        report.append(f"| with_llm_extended | {stats['n']} | {stats['mean']:.2f} | {stats['sd']:.2f} | {stats['median']:.1f} | {stats['min']:.0f} | {stats['max']:.0f} |")
    else:
        report.append(f"| with_llm_extended | 0 | - | - | - | - | - |")

    report.append("")

    # Query distribution
    report.append("### 2.2 Query Count Distribution")
    report.append("")

    # with_llm distribution
    report.append("#### with_llm")
    report.append("")
    query_dist = defaultdict(int)
    for q in with_llm_queries:
        query_dist[q] += 1

    report.append("| Queries | Count | Percentage |")
    report.append("|--------:|------:|-----------:|")
    for q in sorted(query_dist.keys()):
        count = query_dist[q]
        pct = (count / len(with_llm_queries)) * 100 if with_llm_queries else 0
        report.append(f"| {q} | {count} | {pct:.1f}% |")

    report.append("")

    # with_llm_extended distribution
    report.append("#### with_llm_extended")
    report.append("")
    query_dist = defaultdict(int)
    for q in with_llm_extended_queries:
        query_dist[q] += 1

    report.append("| Queries | Count | Percentage |")
    report.append("|--------:|------:|-----------:|")
    for q in sorted(query_dist.keys()):
        count = query_dist[q]
        pct = (count / len(with_llm_extended_queries)) * 100 if with_llm_extended_queries else 0
        report.append(f"| {q} | {count} | {pct:.1f}% |")

    report.append("")

    # ========================================
    # Summary
    # ========================================
    report.append("---")
    report.append("")
    report.append("## 3. Summary")
    report.append("")

    # Key findings
    report.append("### Key Findings")
    report.append("")

    report.append("**1. Media Usage Time:**")
    report.append("")
    report.append(f"- **with_llm** (N={len(with_llm)}): Reading {wl_reading:.1f}s, Chat/LLM {wl_chat:.1f}s")
    report.append(f"- **with_llm_extended** (N={len(with_llm_extended)}): Reading {wle_reading:.1f}s, Chat/LLM {wle_chat:.1f}s, Video {wle_video:.1f}s, Audio {wle_audio:.1f}s, Infographics {wle_infographics:.1f}s")

    # Calculate time allocation percentages for extended
    total_extended = wle_reading + wle_chat + wle_video + wle_audio + wle_infographics
    if total_extended > 0:
        report.append("")
        report.append("**with_llm_extended Time Allocation:**")
        report.append(f"- Reading: {(wle_reading/total_extended)*100:.1f}%")
        report.append(f"- Chat/LLM: {(wle_chat/total_extended)*100:.1f}%")
        report.append(f"- Video: {(wle_video/total_extended)*100:.1f}%")
        report.append(f"- Audio: {(wle_audio/total_extended)*100:.1f}%")
        report.append(f"- Infographics: {(wle_infographics/total_extended)*100:.1f}%")

    report.append("")

    # Query comparison
    wl_q = with_llm_query_stats['mean'] or 0
    wle_q = with_llm_extended_query_stats['mean'] or 0

    report.append("**2. LLM Query Count:**")
    report.append("")
    report.append(f"- **with_llm**: Mean {wl_q:.2f} queries (SD = {with_llm_query_stats['sd']:.2f}, Median = {with_llm_query_stats['median']:.1f})")
    report.append(f"- **with_llm_extended**: Mean {wle_q:.2f} queries (SD = {with_llm_extended_query_stats['sd']:.2f}, Median = {with_llm_extended_query_stats['median']:.1f})")

    if wl_q > wle_q and wle_q > 0:
        diff_pct = ((wl_q - wle_q) / wle_q) * 100
        report.append(f"- with_llm participants sent {diff_pct:.1f}% more queries on average")
    elif wle_q > wl_q and wl_q > 0:
        diff_pct = ((wle_q - wl_q) / wl_q) * 100
        report.append(f"- with_llm_extended participants sent {diff_pct:.1f}% more queries on average")

    report.append("")

    # Write report
    output_path = os.path.join(output_dir, 'llm_usage_analysis.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report))

    print(f"Report saved to: {output_path}")
    print("\n" + "=" * 60)
    print('\n'.join(report))


if __name__ == '__main__':
    main()
