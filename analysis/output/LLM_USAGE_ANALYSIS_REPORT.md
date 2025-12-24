# LLM 사용 패턴 분석 보고서

**분석 대상**: with_llm & with_llm_extended 조건 참여자
**분석 일자**: 2025-12-23
**총 참여자 수**: 199명 (with_llm: 98명, with_llm_extended: 101명)

---

## 1. 매체별 사용 시간 비교

### 1.1 평균 사용 시간 (분)

| Condition | Reading | LLM | Video | Audio |
|-----------|---------|-----|-------|-------|
| with_llm | 20.27 | 4.59 | 0.00 | 0.00 |
| with_llm_extended | 11.64 | 4.16 | 1.14 | 0.99 |

### 1.2 주요 발견

#### Reading Time (읽기 시간)
- **with_llm** 조건에서 평균 **20.27분**, **with_llm_extended** 조건에서 평균 **11.64분**
- with_llm_extended 조건의 읽기 시간이 약 **43% 감소**
- 이는 extended 조건에서 Video, Audio 등 다른 매체를 활용하면서 순수 텍스트 읽기 시간이 줄어든 것으로 해석됨

#### LLM 사용 시간
- **with_llm**: 평균 4.59분 (표준편차: 5.94분)
- **with_llm_extended**: 평균 4.16분 (표준편차: 5.21분)
- 두 조건 간 LLM 사용 시간은 비슷함 (약 10% 차이)

#### Extended Resources (Video & Audio)
- **with_llm_extended 조건에서만 사용 가능**
- Video 사용자: **50명 (49.5%)**, 평균 사용 시간: 2.30분 (사용자 한정)
- Audio 사용자: **58명 (57.4%)**, 평균 사용 시간: 1.72분 (사용자 한정)
- 전체 평균: Video 1.14분, Audio 0.99분

---

## 2. LLM 쿼리 통계

### 2.1 조건별 쿼리 수 통계

| Condition | 평균 | 중앙값 | 최소 | 최대 | 총계 |
|-----------|------|-------|------|------|------|
| with_llm | 4.06 | 3.0 | 1 | 14 | 211 |
| with_llm_extended | 4.78 | 2.0 | 1 | 37 | 311 |

### 2.2 쿼리 수 분포

#### with_llm (52명 응답)
| 쿼리 수 | 참여자 수 |
|---------|----------|
| 1-3 | 28 |
| 4-6 | 13 |
| 7-10 | 8 |
| 10+ | 3 |

#### with_llm_extended (65명 응답)
| 쿼리 수 | 참여자 수 |
|---------|----------|
| 1-3 | 44 |
| 4-6 | 11 |
| 7-10 | 3 |
| 10+ | 7 |

### 2.3 주요 발견

- **중앙값 차이**: with_llm(3.0) vs with_llm_extended(2.0)
- with_llm_extended에서 중앙값은 낮지만 **최대값(37)이 더 높음** → 일부 참여자가 매우 적극적으로 LLM 사용
- 대부분의 참여자(65-68%)는 1-3개의 쿼리만 사용

---

## 3. 타임라인 시각화

참여자별 LLM, Video, Audio 사용 시점을 확인할 수 있는 인터랙티브 HTML 페이지가 생성되었습니다.

**파일 위치**: [llm_usage_timeline.html](./llm_usage_timeline.html)

### 타임라인 기능
- 각 참여자별 세션 전체에서 LLM 활동, Video/Audio 재생 시점을 수직선으로 시각화
- 조건별(with_llm, with_llm_extended) 그룹화
- 이벤트 타입별 필터링 가능
- 호버 시 정확한 시간 정보 표시

---

## 4. 핵심 인사이트

### 4.1 Extended Resources의 영향
1. **읽기 시간 감소**: Extended 리소스 접근 시 순수 읽기 시간이 43% 감소
2. **멀티미디어 활용**: 참여자의 약 50%가 Video, 57%가 Audio 사용
3. **LLM 사용은 유사**: Extended 리소스가 있어도 LLM 사용 패턴은 크게 변하지 않음

### 4.2 LLM 사용 패턴
1. **대다수 저사용**: 약 2/3의 참여자가 3개 이하의 쿼리만 사용
2. **파워유저 존재**: with_llm_extended에서 최대 37개 쿼리 사용자 존재
3. **평균 사용 시간**: 약 4-5분으로 전체 세션의 약 10-20%

### 4.3 권장 후속 분석
- LLM 쿼리 내용 분석 (질문 유형, 주제)
- LLM 사용 시점과 읽기 패턴의 상관관계
- Extended 리소스 사용자 vs 미사용자의 학습 성과 비교

---

## 5. 생성된 파일

| 파일명 | 설명 |
|--------|------|
| `media_time_by_participant.csv` | 참여자별 매체 사용 시간 |
| `llm_query_counts.csv` | 참여자별 LLM 쿼리 수 |
| `llm_usage_timeline.html` | 인터랙티브 타임라인 시각화 |
| `summary_stats.json` | 요약 통계 (JSON) |
| `LLM_USAGE_ANALYSIS_REPORT.md` | 본 보고서 |
