#!/usr/bin/env python3
"""
Verify tab time calculation from focus_switch and resource_tab_switch events.

This script:
1. Reconstructs tab time segments from focus_switch and resource_tab_switch events
2. Verifies segments don't overlap
3. Verifies segments are contiguous (no gaps)
4. Compares total segment time with session duration from Firebase
"""

import csv
import os
from collections import defaultdict


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


def main():
    # Paths
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    processed_dir = os.path.join(base_dir, 'data', 'processed')

    # Load data
    reading_events = load_csv(os.path.join(processed_dir, 'reading_events.csv'))
    reading_summary = load_csv(os.path.join(processed_dir, 'reading_summary.csv'))
    merged_all = load_csv(os.path.join(processed_dir, 'merged_all.csv'))

    # Get participant conditions from merged_all
    participant_conditions = {row['participantId']: row['condition'] for row in merged_all}

    # Get session duration and focusTimes from reading_summary
    summary_data = {}
    for row in reading_summary:
        pid = row['participantId']
        summary_data[pid] = {
            'duration': safe_float(row.get('duration')) or 0,  # Total session duration (ms)
            'focusTime_reading': safe_float(row.get('focusTime_reading')) or 0,
            'focusTime_chat': safe_float(row.get('focusTime_chat')) or 0,
        }

    # Group events by participant
    events_by_pid = defaultdict(list)
    for event in reading_events:
        events_by_pid[event['participantId']].append(event)

    # Sort events by timestamp
    for pid in events_by_pid:
        events_by_pid[pid].sort(key=lambda x: safe_float(x['timestamp']) or 0)

    # Analyze LLM conditions only
    llm_pids = [pid for pid, cond in participant_conditions.items()
                if cond in ('with_llm', 'with_llm_extended')]

    print("=" * 80)
    print("TAB TIME SEGMENT VERIFICATION")
    print("=" * 80)
    print()
    print("Checking: 1) No overlaps, 2) Contiguous, 3) Sum matches session duration")
    print()

    # Track stats
    total_checked = 0
    overlap_count = 0
    gap_count = 0
    duration_match_count = 0
    duration_mismatch_details = []

    # Process each participant
    for pid in llm_pids:
        events = events_by_pid.get(pid, [])
        condition = participant_conditions.get(pid, 'unknown')
        summary = summary_data.get(pid, {})

        if not events or not summary:
            continue

        total_checked += 1

        # Get all focus_switch and resource_tab_switch events
        switch_events = [e for e in events
                         if e['eventType'] in ('focus_switch', 'resource_tab_switch')]

        # Get first event timestamp and session duration from Firebase
        all_timestamps = [safe_float(e['timestamp']) for e in events if safe_float(e['timestamp'])]
        if not all_timestamps:
            continue

        first_event_timestamp = min(all_timestamps)
        last_event_timestamp = max(all_timestamps)
        firebase_duration = summary['duration']  # ms

        # Calculate session start time: first_event_timestamp - (time before first event)
        # The time before first event = firebase_duration - (last_event - first_event)
        event_span = last_event_timestamp - first_event_timestamp
        time_before_first_event = firebase_duration - event_span

        # Session start is when reading phase actually started
        session_start = first_event_timestamp - time_before_first_event
        session_end = session_start + firebase_duration

        # Build segments from switch events
        segments = []
        current_tab = 'reading'  # Default initial focus
        segment_start = session_start  # Start from actual session start

        for se in sorted(switch_events, key=lambda x: safe_float(x['timestamp']) or 0):
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
            if new_tab and new_tab != 'phase_complete':
                current_tab = new_tab
            segment_start = ts

        # Add final segment (from last switch to session end)
        if session_end > segment_start:
            segments.append({
                'start': segment_start,
                'end': session_end,
                'tab': current_tab,
                'duration': session_end - segment_start
            })

        # === Verification 1: Check for overlaps ===
        has_overlap = False
        for i, seg1 in enumerate(segments):
            for seg2 in segments[i+1:]:
                if seg1['end'] > seg2['start'] and seg2['end'] > seg1['start']:
                    has_overlap = True
                    break
            if has_overlap:
                break

        if has_overlap:
            overlap_count += 1

        # === Verification 2: Check for gaps ===
        gaps = []
        for i in range(len(segments) - 1):
            gap = segments[i+1]['start'] - segments[i]['end']
            if abs(gap) > 1:  # Allow 1ms tolerance
                gaps.append({
                    'after_segment': i,
                    'gap_ms': gap
                })

        if gaps:
            gap_count += 1

        # === Verification 3: Check total duration ===
        total_segment_time = sum(s['duration'] for s in segments)
        duration_diff = abs(total_segment_time - firebase_duration)

        if duration_diff < 100:  # Within 100ms tolerance
            duration_match_count += 1
        else:
            duration_mismatch_details.append({
                'pid': pid,
                'condition': condition,
                'firebase_duration': firebase_duration,
                'segment_total': total_segment_time,
                'diff': total_segment_time - firebase_duration
            })

        # Calculate time per tab
        tab_times = defaultdict(float)
        for seg in segments:
            tab_times[seg['tab']] += seg['duration']

        # Compare with Firebase focusTimes
        firebase_reading = summary['focusTime_reading']
        firebase_chat = summary['focusTime_chat']
        calc_reading = tab_times.get('reading', 0)
        calc_chat = tab_times.get('chat', 0)

    # Print summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Total participants checked: {total_checked}")
    print()
    print(f"1. Overlapping segments: {overlap_count}/{total_checked}")
    print(f"   {'✓ No overlaps found' if overlap_count == 0 else '⚠️ Some participants have overlapping segments'}")
    print()
    print(f"2. Gaps between segments: {gap_count}/{total_checked}")
    print(f"   {'✓ All segments are contiguous' if gap_count == 0 else '⚠️ Some participants have gaps'}")
    print()
    print(f"3. Duration match (within 100ms): {duration_match_count}/{total_checked}")
    if duration_mismatch_details:
        print(f"   ⚠️ {len(duration_mismatch_details)} participants have duration mismatch:")
        for d in duration_mismatch_details[:5]:
            print(f"      - {d['pid'][:20]}... ({d['condition']}): diff={d['diff']/1000:.2f}s")
        if len(duration_mismatch_details) > 5:
            print(f"      ... and {len(duration_mismatch_details) - 5} more")
    else:
        print(f"   ✓ All segment totals match Firebase duration")

    print()
    print("=" * 80)
    print("DETAILED CHECK - Sample Participants")
    print("=" * 80)
    print()

    # Show detailed info for first 5 participants
    sample_count = 0
    for pid in llm_pids:
        if sample_count >= 5:
            break

        events = events_by_pid.get(pid, [])
        condition = participant_conditions.get(pid, 'unknown')
        summary = summary_data.get(pid, {})

        if not events or not summary:
            continue

        sample_count += 1

        switch_events = [e for e in events
                         if e['eventType'] in ('focus_switch', 'resource_tab_switch')]

        all_timestamps = [safe_float(e['timestamp']) for e in events if safe_float(e['timestamp'])]
        first_event_timestamp = min(all_timestamps)
        last_event_timestamp = max(all_timestamps)
        firebase_duration = summary['duration']
        event_span = last_event_timestamp - first_event_timestamp
        time_before_first_event = firebase_duration - event_span
        session_start = first_event_timestamp - time_before_first_event
        session_end = session_start + firebase_duration

        # Build segments
        segments = []
        current_tab = 'reading'
        segment_start = session_start

        for se in sorted(switch_events, key=lambda x: safe_float(x['timestamp']) or 0):
            ts = safe_float(se['timestamp'])
            if ts is None:
                continue
            if ts > segment_start:
                segments.append({
                    'start': segment_start,
                    'end': ts,
                    'tab': current_tab,
                    'duration': ts - segment_start
                })
            new_tab = se.get('to', '')
            if new_tab and new_tab != 'phase_complete':
                current_tab = new_tab
            segment_start = ts

        if session_end > segment_start:
            segments.append({
                'start': segment_start,
                'end': session_end,
                'tab': current_tab,
                'duration': session_end - segment_start
            })

        # Calculate tab times
        tab_times = defaultdict(float)
        for seg in segments:
            tab_times[seg['tab']] += seg['duration']

        total_segment_time = sum(s['duration'] for s in segments)

        print(f"Participant: {pid} ({condition})")
        print(f"  Firebase session duration: {firebase_duration/1000:.1f}s")
        print(f"  Time before first event:   {time_before_first_event/1000:.1f}s")
        print(f"  Total segment time:        {total_segment_time/1000:.1f}s")
        print(f"  Difference:                {(total_segment_time - firebase_duration)/1000:.2f}s")
        print()
        print(f"  Tab times (calculated):")
        for tab in ['reading', 'chat', 'video', 'audio', 'infographics']:
            if tab_times.get(tab, 0) > 0:
                print(f"    {tab:15s}: {tab_times[tab]/1000:.1f}s")
        print()
        print(f"  Firebase focusTimes:")
        print(f"    reading:         {summary['focusTime_reading']/1000:.1f}s")
        print(f"    chat:            {summary['focusTime_chat']/1000:.1f}s")
        print()
        print(f"  Reading diff: {(tab_times.get('reading', 0) - summary['focusTime_reading'])/1000:.2f}s")
        print(f"  Chat diff:    {(tab_times.get('chat', 0) - summary['focusTime_chat'])/1000:.2f}s")
        print()
        print("-" * 60)
        print()


if __name__ == '__main__':
    main()
