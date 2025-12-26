# Data Preprocessing Report

Generated: 2025-12-26 01:08:00

## Summary

| Metric | Value |
|--------|-------|
| **Total Participants** | 295 |
| **US Participants** | 119 |
| **UK Participants** | 176 |
| **Average Experiment Duration** | 37.7 minutes |

### Expected vs Actual

| Country | Expected | Actual | Match |
|---------|----------|--------|-------|
| US | 124 | 119 | ✗ |
| UK | 176 | 176 | ✓ |
| **Total** | **300** | **295** | ✗ |

## Condition Distribution

| Condition | Count |
|-----------|-------|
| with_llm | 98 |
| with_llm_extended | 101 |
| without_llm | 96 |

## Data Filtering Results

### Excluded Participants (No Completed Experiments): 21

- `5a8ff02e4fcb2f0001d8bb9b`: 1 experiments, statuses: ['in_progress']
- `6148bbcd519a30b146897026`: 1 experiments, statuses: ['in_progress']
- `62dc4a5fef307ee53c61afcc`: 1 experiments, statuses: ['in_progress']
- `64136034f020e6b765d0bc4c`: 1 experiments, statuses: ['in_progress']
- `6630fd6fc70f45525e94c657`: 1 experiments, statuses: ['in_progress']
- `664d8066db4407ac502a5979`: 1 experiments, statuses: ['in_progress']
- `6654847971e9e4d8aa4321eb`: 1 experiments, statuses: ['in_progress']
- `6658b831ee74fc67e629e041`: 1 experiments, statuses: ['in_progress']
- `6658ccce522b5c7e8975311e`: 1 experiments, statuses: ['in_progress']
- `668524a1a970340348138c93`: 1 experiments, statuses: ['in_progress']
- ... and 11 more

### Participants with Multiple Completed Experiments: 0

None

### Invalid Participant ID Format: 0

None

### Missing US Participants (Prolific completed but not in Firebase): 5

- `674aa67b13fcbfeda28a00ef`
- `67de01d3d44c6326661a7d33`
- `67df453bc406da9f288f9656`
- `67ed4f4554b89f3a5b5c13a7`
- `69433c650c16615381b1a0f8`

## Output Files

| File | Description |
|------|-------------|
| participants.csv | Participant info with country |
| experiments.csv | Experiment metadata |
| reading_events.csv | Individual reading events |
| reading_section_analysis.csv | Section-level reading analysis |
| reading_summary.csv | Reading summary statistics (includes focusTime for all tabs) |
| tab_segments.csv | Detailed tab segments with start/end times |
| survey.csv | Post-study survey responses |
| pre-task.csv | Pre-task responses |
| post-task.csv | Post-task responses |
| quizzes.csv | Quiz answers and accuracy |
| llm_messages.csv | LLM chat messages |
