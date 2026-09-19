# ADR-0004: 프런트 영상 길이 예측과 공개 서비스 직렬 작업 큐

- 상태: 구현 승인
- 작성일: 2026-09-19
- 구현 담당: `pipeline-maintainer`
- 배포 환경: MINI, Tailscale Funnel 공개 주소

## 1. 목표

친구들이 공개 웹에서 대본을 입력할 때 결과 영상 길이를 미리 가늠하고, 여러 사람이 동시에 요청해도 영상 생성은 시스템 전체에서 정확히 한 개씩만 실행되게 한다. 대기 중인 사용자는 자기 작업의 실제 대기 순서를 확인할 수 있어야 한다.

이 결정은 영상 작업 사이의 직렬 실행에 관한 것이다. 한 영상 내부의 이미지 슬롯과 음성 슬롯 병렬화는 유지한다.

```text
영상 작업 A ─ 실행 중
영상 작업 B ─ 대기 1번째
영상 작업 C ─ 대기 2번째

작업 A 내부:
이미지 슬롯 병렬 + 음성 슬롯 병렬 + 준비 구간 렌더링
```

## 2. 프런트 영상 길이 예측

### 2.1 산식

서버/API 호출이나 LLM을 사용하지 않고 React에서 즉시 계산한다.

현재 MINI의 Live ElevenLabs 기록 11개 작업을 합산한 값:

- 음성 문자 합계: 1,589자
- 음성 길이 합계: 278.967초
- 가중 평균: 약 5.696자/초
- 현재 음성 설정: Brian, Eleven Flash v2.5, speed 0.70

초기 상수는 다음처럼 둔다.

```ts
const KOREAN_NARRATION_CHARS_PER_SECOND = 5.7;
```

대본은 앞뒤 공백을 제거하고 연속 공백·개행을 공백 하나로 정규화한 뒤 길이를 센다.

```ts
const normalized = scenario.trim().replace(/\s+/g, " ");
const centerSeconds = normalized.length / 5.7;
const minSeconds = centerSeconds * 0.88;
const maxSeconds = centerSeconds * 1.12;
```

빈 입력은 예측값을 표시하지 않는다. 아주 짧은 입력은 최소 1초로 표시한다. 계산에는 네트워크 요청이 없어야 한다.

### 2.2 화면 표현

텍스트 영역의 글자 수 근처에 다음처럼 실시간 표시한다.

```text
예상 영상 길이 약 4분 52초
말하기 속도와 문장부호에 따라 약 4분 17초~5분 27초
```

표현 원칙:

- 중심값은 `약 N분 N초`로 표시한다.
- 60초 미만은 초만, 1시간 이상은 시간·분으로 표시한다.
- 범위는 과도한 정밀도를 피하고 5초 단위로 반올림한다.
- `현재 한국어 음성 설정 기준`이라는 설명을 붙인다.
- 이는 생성 소요시간이 아니라 완성 영상 재생시간임을 명확히 한다.
- 접근성 도구가 입력마다 장황하게 읽지 않도록 `aria-live`는 `polite`로 하고 중심값 영역 하나만 갱신한다.

### 2.3 한계와 유지관리

- 숫자, 영문, URL, 긴 쉼표와 문장부호는 발화시간을 바꾼다.
- 장면별 최소 길이와 실제 모델의 휴지는 오차를 만든다.
- 음성 모델, voice ID 또는 speed 기본값이 바뀌면 상수도 재측정해야 한다.
- 관리자 설정 변경을 일반 사용자가 할 수 있는 구조가 되면 향후 서버가 `narrationCharsPerSecond` 설정값만 제공하는 방향으로 확장할 수 있다. 이번 범위에서는 프런트 상수다.

## 3. 현재 큐 상태

- BullMQ `video-jobs` 큐가 이미 존재한다.
- 현재 MINI의 `WORKER_CONCURRENCY=1`이므로 단일 worker 안에서는 직렬 실행 중이다.
- 그러나 설정 코드는 최대 2까지 허용하며, worker replica가 늘면 시스템 전체 동시 실행 1을 보장하지 않는다.
- 공유 토큰을 모든 친구가 사용하므로 모두 같은 `userId`다.
- 현재 사용자 pending 기본 한도는 2여서 세 번째 요청부터 큐에 들어가지 못하고 429가 된다.
- 작업 조회 API에는 실제 대기 순번이 없다.
- 브라우저 새로고침 후 현재 작업 ID를 복구하지 않는다.

## 4. 시스템 전체 직렬 실행

영상 작업은 시스템 전체에서 동시에 정확히 하나만 `running`이 되게 한다.

- BullMQ global concurrency를 1로 설정하거나, 현재 BullMQ 버전에서 같은 의미를 보장하는 전역 Redis lease를 사용한다.
- processor의 local concurrency도 1로 유지한다.
- worker container replica도 우선 1로 고정한다.
- 향후 worker replica가 늘더라도 global concurrency 1이 깨지면 안 된다.
- 실행 중인 작업 안의 이미지/음성 provider 병렬 슬롯은 그대로 유지한다.
- 관리자 화면과 로그에 `videoJobGlobalConcurrency=1`을 노출한다.

환경변수 `WORKER_CONCURRENCY`를 2로 올려도 공개 운영 모드에서는 1을 넘지 못하게 하거나, 별도의 `VIDEO_JOB_GLOBAL_CONCURRENCY=1`을 명시한다. 조용히 다중 실행되는 설정 조합을 허용하지 않는다.

## 5. 큐 수용 한도

친구들이 같은 접근 토큰을 공유하므로 `USER_PENDING`이 전체 공개 큐 수용량보다 작으면 안 된다.

초기 운영값:

```text
VIDEO_JOB_GLOBAL_CONCURRENCY=1
USER_PENDING=20
GLOBAL_PENDING=20
DAILY_JOBS=0
```

pending에는 실행 중과 대기 중 작업을 모두 포함한다. 큐가 20개로 가득 찼을 때만 기존 한글 429 오류를 표시한다. 브라우저 하나에서는 자신의 기존 작업이 queued/running인 동안 추가 제출 버튼을 비활성화한다.

## 6. 대기 순번 정의

API에서 용어를 모호하게 만들지 않는다.

- `queuePosition`: waiting 작업 사이의 1 기반 순번. 실행 중 작업은 포함하지 않는다.
- `jobsAhead`: 현재 작업보다 먼저 완료돼야 하는 active + waiting 작업 수.
- `activeJobs`: 현재 실행 중인 영상 작업 수. 항상 0 또는 1.
- `queuedJobs`: 전체 waiting 작업 수.
- running/completed/failed 작업의 `queuePosition`은 `null`.

예시:

```text
A = running
B = 첫 번째 waiting
C = 두 번째 waiting

B: queuePosition=1, jobsAhead=1, activeJobs=1
C: queuePosition=2, jobsAhead=2, activeJobs=1
```

재시도 때문에 BullMQ delayed 상태로 이동한 작업은 실제 scheduler 순서를 기준으로 계산한다. PostgreSQL의 `queued_at`만으로 추측해서는 안 된다. BullMQ waiting/prioritized/delayed/active 상태 또는 큐가 제공하는 실제 순서 API를 source of truth로 사용한다. 큐 규모가 최대 20이므로 상태 조회 시 제한된 목록을 읽어 계산해도 된다.

레이스가 발생하면 순번은 다음 2초 polling에서 정정될 수 있다. 순번은 안내 정보이며 실행 순서는 BullMQ가 결정한다.

## 7. API 변경

`POST /api/jobs` 응답과 `GET /api/jobs/:id` 응답에 다음을 추가한다.

```json
{
  "id": "...",
  "status": "queued",
  "currentStage": "queue_wait",
  "queuePosition": 2,
  "jobsAhead": 2,
  "activeJobs": 1,
  "queuedJobs": 4
}
```

- 위치 조회는 인증된 본인 작업에만 제공한다.
- 다른 작업의 ID, 대본, 사용자 정보는 절대 노출하지 않는다.
- 큐 상태 조회 실패 시 작업 상태 조회 전체를 500으로 만들지 말고 순번 필드만 `null`로 반환하며 서버 로그에 원인을 남긴다.
- 작업이 running으로 전환될 때 DB의 status/current_stage와 BullMQ 상태가 짧게 어긋날 수 있으므로 UI는 `running`을 우선한다.

## 8. 프런트 큐 UI

기존 2초 작업 polling을 그대로 활용한다. 별도 SSE는 이번 기능에 필요 없다.

queued 상태:

```text
대기 중
대기열 2번째 · 앞에 2개 작업이 있습니다
현재 영상 1개 생성 중
```

첫 대기 작업:

```text
대기열 1번째 · 현재 작업이 끝나면 시작합니다
```

running 상태:

```text
생성 중 · 현재 작업을 처리하고 있습니다
```

queue position이 일시적으로 null이면 `대기 순서를 확인하는 중`이라고 표시한다. 순번이 감소할 때 자연스럽게 갱신하고, 순번 증가도 실제 retry/requeue 결과라면 숨기지 않는다.

## 9. 새로고침 복구

긴 대기열에서는 브라우저 새로고침이나 탭 종료 후에도 자기 작업을 다시 찾아야 한다.

- 작업 생성 성공 시 현재 origin의 localStorage에 최근 작업 ID를 저장한다.
- 앱 시작 시 토큰이 존재하고 최근 작업 ID가 있으면 `GET /api/jobs/:id`로 복구한다.
- 401/404/410이면 저장한 ID를 제거한다.
- completed 작업은 다운로드 버튼과 함께 복구한다.
- failed 작업은 오류를 보여주고 새 작업 제출을 허용한다.
- 토큰 평문은 현재 정책대로 localStorage에 이미 저장되고 있으나, 작업 ID와 대본 전체를 추가 저장하지 않는다.

공유 토큰 때문에 서버에서 `내 최근 작업` 목록을 제공하면 친구끼리 작업이 섞인다. 이번 범위에서는 브라우저별 최근 작업 ID만 저장한다.

## 10. 관리자 관측성

관리자 화면에 다음을 추가한다.

- 실행 중 영상 작업: 0/1
- 대기 작업 수
- 가장 오래 기다린 작업의 대기시간
- 최근 작업 표의 대기 순번 또는 시작 당시 대기시간
- 실제 global concurrency 설정값
- queue wait p50/p95

개별 작업 이벤트에는 생성 당시 순번, 실행 시작 당시 실제 queue wait ms를 남긴다. 순번 변화 전체를 DB에 매 polling마다 저장하지는 않는다.

## 11. 테스트

### 프런트 길이 예측

- 빈 문자열은 미표시
- 공백·개행 정규화
- 57자 입력 중심값 약 10초
- 342자 입력 중심값 약 1분
- 1,710자 입력 중심값 약 5분
- 입력마다 네트워크 요청이 발생하지 않음
- 모바일 390px에서 범위 문구가 넘치지 않음

### 큐 단위/통합

- 동시에 5개 제출해도 running은 항상 1개
- 나머지 queuePosition은 1,2,3,4
- 첫 작업 완료 후 기존 1번이 running, 나머지는 1,2,3으로 감소
- 여러 worker 인스턴스 상황을 흉내 내도 전역 running은 1
- retry/delayed, failed, cancelled 상태에서 순번이 실제 BullMQ 순서와 일치
- 큐 20개까지 수용하고 21번째는 한글 429
- 큐 위치 조회 실패가 기본 작업 상태 조회를 깨뜨리지 않음
- 다른 토큰으로 작업 상세나 영상에 접근할 수 없음
- 새로고침 후 최근 작업과 순번 복구

### MINI E2E

1. mock 모드에서 서로 다른 브라우저 context로 3개 요청
2. 두 번째·세 번째 화면에 대기 1·2번째 표시
3. 첫 작업 종료 후 순번 자동 감소
4. Live 작업은 비용 절약을 위해 짧은 작업 1개만 사용하고 그 뒤 mock 또는 지연 fixture로 큐 화면 검증
5. Tailscale Funnel 공개 주소에서 제출·polling·완료·다운로드 확인
6. 콘솔 오류, 4xx/5xx 의도치 않은 요청, 모바일 overflow 확인

## 12. 완료 기준

- 대본 입력만으로 예상 완성 영상 길이와 오차 범위가 즉시 표시된다.
- 계산 과정에서 API/LLM 호출이 없다.
- 시스템 전체 영상 job running 수는 항상 1 이하이다.
- 한 영상 내부 이미지·음성 병렬화는 유지된다.
- 공유 토큰으로 20개의 pending 작업을 받을 수 있다.
- queued 사용자는 실제 대기 순번과 앞선 작업 수를 2초 이내 갱신으로 확인한다.
- 새로고침 후 자기 브라우저의 최근 작업을 복구한다.
- 친구에게 다른 사용자의 대본이나 작업 식별 정보를 노출하지 않는다.
- Funnel 공개 주소의 사용자 관점 E2E를 통과한다.
