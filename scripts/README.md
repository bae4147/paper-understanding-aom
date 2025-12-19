# Data Export Scripts

Firebase에서 실험 데이터를 추출하고 CSV로 변환하는 스크립트입니다.

## Setup

### 1. Firebase Service Account Key 다운로드

1. [Firebase Console](https://console.firebase.google.com) 접속
2. Project Settings > Service Accounts
3. "Generate new private key" 클릭
4. 다운로드한 JSON 파일을 `firebase-service-account.json`으로 이름 변경
5. 이 `scripts/` 폴더에 저장

**주의: 이 파일은 절대 git에 커밋하지 마세요!**

### 2. Python 환경 설정

```bash
cd scripts
pip install -r requirements.txt
```

## Usage

```bash
cd scripts
python export_firebase_data.py
```

## Output Files

스크립트 실행 시 `data_exports/` 폴더에 다음 파일들이 생성됩니다:

| 파일 | 내용 |
|------|------|
| `raw_data_YYYYMMDD_HHMMSS.json` | 전체 raw 데이터 (JSON) |
| `experiments_main_YYYYMMDD_HHMMSS.csv` | 실험 요약 데이터 (참가자별 1행) |
| `quiz_answers_YYYYMMDD_HHMMSS.csv` | 퀴즈 답변 상세 (질문별 1행) |
| `llm_chat_history_YYYYMMDD_HHMMSS.csv` | LLM 대화 기록 (메시지별 1행) |
| `reading_events_YYYYMMDD_HHMMSS.csv` | 읽기 이벤트 로그 (이벤트별 1행) |

## Data Completeness Check

스크립트는 자동으로 각 참가자별로 누락된 필드를 확인하고 출력합니다:

```
--- participant123 (with_llm) - Status: completed ---
  MISSING (2):
    - postStudySurvey.attentionCheck.focus
    - postStudySurvey.attentionCheck.stronglyDisagreeCheck
```

이를 통해 데이터 수집에서 누락된 항목을 빠르게 확인할 수 있습니다.
