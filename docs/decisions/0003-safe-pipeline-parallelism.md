# ADR-0003: 안전한 1차 파이프라인 병렬화

- 상태: 구현 승인
- 작성일: 2026-09-19
- 구현 담당: `pipeline-maintainer`
- 목표: 결과 의미와 품질을 바꾸지 않고 생성시간 단축

## 1. 확정 결정

1. 최종 영상 기본 FPS를 30에서 24로 낮춘다.
2. 장면 계획이 확정되면 장면 이미지와 장면 음성을 서로 독립적으로 생성한다.
3. 음성은 전체 대본 한 번 생성 방식으로 바꾸지 않는다. 현재와 동일하게 장면별 파일을 생성하고 마지막에 장면 순서대로 연결한다.
4. 이미지 큐와 별도로 전역 공유 음성 슬롯 큐를 둔다.
5. 이미지와 음성이 모두 준비된 연속 구간은 뒤 장면을 기다리지 않고 렌더링할 수 있게 한다.
6. 이미지·음성의 결정론적 기술 검사는 각 artifact가 생성되는 즉시 수행한다.

## 2. 사용자 관점의 이유

- 장면 계획이 확정되면 그 장면의 나레이션과 이미지 프롬프트가 모두 확정된다. 실제 이미지 파일은 음성 생성 입력이 아니다.
- 현재와 똑같이 장면별 음성을 만들고 순서대로 잇기 때문에 음성 품질, 장면 길이, 자막 의미를 바꿀 필요가 없다.
- 전체 음성 타임스탬프를 다시 장면에 매핑하는 과설계를 피한다.
- 슬라이드 영상에서 30fps의 추가 프레임보다 생성시간 절감이 더 중요하며, 24fps는 느린 확대·이동과 크로스페이드를 유지할 수 있는 보수적 값이다.
- 이미지 API 대기 중 MINI CPU로 준비된 영상 구간을 렌더링하면 이미지 시간 뒤에 전체 렌더 시간을 다시 더하지 않아도 된다.

## 3. 현재 구조와 제거할 잘못된 의존성

현재 코드는 모든 이미지 작업을 먼저 등록한 뒤 장면 순서로 다음을 반복한다.

```text
await scene image
validate image
call scene TTS
measure audio duration
persist scene
```

이미지 broker는 백그라운드에서 계속 실행되지만, 첫 음성은 첫 이미지 완료 전에 시작하지 못하고 음성 요청은 한 번에 하나씩만 실행된다. 이는 품질 요구가 아니라 orchestration 편의로 생긴 실행 의존성이다.

다음 의존성은 유지한다.

- 이미지와 음성은 동일한 확정 장면 계획을 입력으로 사용한다.
- 장면 또는 렌더 구간은 필요한 이미지와 음성 길이가 모두 준비되어야 한다.
- 최종 mux와 검사는 모든 필수 구간과 전체 나레이션이 준비되어야 한다.

다음 의존성만 제거한다.

- 장면 음성이 해당 장면 이미지 완료를 기다리는 관계
- 다음 장면 음성이 앞 장면 음성 완료를 기다리는 관계

## 4. 목표 실행 그래프

```text
입력 검증·프롬프트 snapshot
              │
        Codex 장면 계획
              │
       ┌──────┴──────┐
       │             │
 이미지 태스크     음성 태스크
 전역 이미지 풀    전역 음성 풀
       │             │
 즉시 이미지 QC   즉시 음성 QC·길이 측정
       └──────┬──────┘
              │ 장면/구간 readiness
      준비된 연속 구간 렌더링
              │
     구간 concat + 전체 음성 mux
              │
            최종 QC
```

## 5. 장면별 음성 태스크

장면 계획 완료 직후 모든 장면 음성 태스크를 등록한다. 이미지 결과를 기다리지 않는다.

필수 입력:

- job ID, scene ID, scene index
- 확정된 `scene.narration`
- provider, model, voice ID
- stability, similarity, speed, style, language, seed, output format

필수 결과:

- scene ID와 index
- audio artifact path와 SHA-256
- duration ms, bytes, codec/sample rate/channels
- provider request ID와 호출 소요시간
- 문자 수, 비용, retry/오류 정보

파일은 현재처럼 장면별 `scene-XXX.mp3`로 유지한다. 모든 결과는 완료 순서가 아니라 scene index 순서로 concat한다. 전체 대본 단일 TTS나 문자 타임스탬프 기반 재분할을 이번 범위에 넣지 않는다. 현재 timestamp 응답을 유지해도 되지만 실행에 필수 의존성으로 사용하지 않는다.

## 6. 전역 음성 작업 풀

이미지 슬롯과 같은 소비자 모델을 사용하되 서로 다른 공급자 자원이므로 이미지 슬롯을 공유하지 않는다.

- 설정 키 예: `VOICE_TASK_CONCURRENCY`
- 초기 전역 동시성: 2
- 시스템 전체 동시성이다. 영상 작업마다 2개를 따로 만드는 것이 아니다.
- 여러 job 사이 fair-share를 적용한다.
- 음성 소비자는 슬롯 수, 429, 재시도 로직을 몰라야 한다.
- 향후 실제 측정 후 1→2→4 비교가 가능하게 관리자 설정 또는 환경변수로 조정한다.
- Redis global lease 또는 동일한 다중 runner 안전 장치를 사용해 runner 인스턴스가 늘어도 상한이 곱해지지 않게 한다.

음성 태스크 상태와 시도 기록은 이미지 태스크와 동등하게 추적한다. 구현 중복을 줄이기 위해 generic external-task broker를 추출하거나 별도 `VoiceTaskBroker`를 둘 수 있으나 이미지와 음성의 동시성 budget은 분리한다.

## 7. 재시도·캐시·취소

- 최초 + 최대 2회 재시도. 네트워크, 429, retryable 5xx만 자동 재시도한다.
- validation 및 일반 4xx는 같은 입력으로 반복하지 않는다.
- 성공 파일은 다음 hash 입력으로 재사용 여부를 판단한다.

```text
narration text
voice ID
model ID
stability
similarity
speed
style
language
seed
output format
```

- 단순히 파일 존재 여부만으로 재사용하지 않는다. 설정이나 대본이 바뀌었으면 새로 생성한다.
- 이미지가 실패해도 성공한 음성은 해당 job retry에서 재사용한다.
- 취소된 job의 queued 음성은 취소하고, 이미 외부 호출 중인 결과는 안전하게 폐기 또는 cancelled 처리한다.
- 파일은 attempt 임시 경로에 쓰고 검증 성공 후 최종 경로로 원자적 promote한다.

## 8. 즉시 기술 검사

음성 생성 직후 LLM 없이 다음을 검사한다.

- 디코딩 가능 여부
- duration > 0
- sample rate/channel/codec
- 파일 크기
- 평균/최대 음량
- clipping
- 비정상 전체 무음

이미지도 provider worker가 결과를 받는 즉시 기존 결정론적 검사를 완료한 뒤 succeeded로 처리한다. 최종 단계에서는 개별 artifact 검사를 반복하지 않고 존재·hash와 집계 정합성을 확인한다.

## 9. 선행 구간 렌더링

이미지와 음성 길이가 준비된 연속 장면 묶음부터 FFmpeg 렌더를 시작한다.

- 시작 구간 크기: 기존 `RENDER_SEGMENT_SCENES=8`을 우선 유지
- 구간은 장면 순서를 보존하며, 중간에 준비되지 않은 장면을 건너뛰어 잘못된 순서로 합치지 않는다.
- 구간별 자막 시간은 구간 내부 0부터 계산한다.
- 렌더된 모든 구간은 동일 codec/profile/pixel format/time base를 사용해 최종 concat을 stream copy로 수행한다.
- 전체 narration은 현재처럼 장면 음성을 순서대로 concat한 뒤 최종 mux한다.
- 재시도 시 입력 이미지 hash, 음성 hash, 렌더 설정 hash가 같은 성공 구간은 재사용할 수 있다.

MINI CPU 보호를 위해 FFmpeg 전역 동시성은 이번 1차에서 1로 유지한다. 이미지 API는 외부 연산이므로 이미지 생성과 FFmpeg 1개는 병행한다. FFmpeg 2개 이상은 2차 벤치마크 전까지 허용하지 않는다.

## 10. 24fps 변경 범위

- runtime 기본값과 `.env.example`을 24로 통일한다.
- 렌더 명령, metadata, 검증, 관리자 상세에서 30으로 가정한 값이 있으면 제거한다.
- 기존 작업 artifact를 재사용할 때 fps가 cache key에 포함되어야 한다.
- 24fps 변경 후 Ken Burns와 crossfade가 시각적으로 끊기지 않는지 검증한다.
- 오디오 duration이 기준이며 프레임 반올림으로 발생하는 A/V 차이는 한 프레임 이내여야 한다.

## 11. 관측성

영상 작업마다 다음을 구분해 기록한다.

- 음성 dependency wait, queue wait, provider duration, validation duration, total duration
- 설정/유효 음성 동시성, slot ID, queue depth, active calls
- scene별 문자 수, 음성 길이, 비용, retry waste
- 이미지·음성이 동시에 실행된 시간 구간
- 각 렌더 segment의 readiness 시각, 렌더 시작/종료, 입력 hash
- 마지막 이미지 완료, 마지막 음성 완료, 첫 렌더 시작, 마지막 렌더 완료 시각
- 30→24fps 전후 영상 1분당 렌더 시간

관리자에서는 이미지와 마찬가지로 음성 큐 요약과 slot timeline을 확인할 수 있어야 한다. 비교 분석에는 voice concurrency와 FPS 차원을 추가한다.

## 12. 테스트

### 단위/통합

- 장면 계획 완료 후 이미지 완료 전 음성 provider 호출이 시작되는지 확인
- 음성 concurrency가 여러 job을 합쳐 설정값을 넘지 않는지 확인
- 완료 순서가 뒤섞여도 scene index 순서로 concat되는지 확인
- 한 장면 음성 실패가 성공한 다른 장면 음성을 재생성하지 않는지 확인
- 설정 hash 변경 시 캐시 무효화, 동일 설정 retry 시 재사용
- cancellation, 429/5xx retry, 일반 4xx no-retry
- 구간은 이미지+음성 모두 준비된 경우에만 렌더
- 구간 concat 결과 순서, 자막, A/V sync
- 실제 출력 fps 24, 1920x1080, H.264/AAC 유지

### MINI Live E2E

1. 3장면 짧은 한국어 영상으로 이미지와 음성 호출 겹침 확인
2. 음성 완료 순서를 의도적으로 섞은 mock에서 최종 나레이션 순서 확인
3. 10초 Live 영상 청취·시각 검수
4. 30fps 기준 기록과 24fps 렌더 시간·파일 크기·시각 품질 비교
5. 장면별 음성 길이 합, narration 길이, 최종 MP4 길이의 허용 오차 확인
6. 실패 후 retry에서 성공 음성과 렌더 구간이 재사용되는지 확인

## 13. 완료 기준

- 장면 계획 완료 후 모든 이미지와 음성 태스크가 독립적으로 등록된다.
- 어떤 음성 태스크도 이미지 성공을 시작 조건으로 삼지 않는다.
- 전역 음성 in-flight가 설정값을 넘지 않으며 초기값은 2다.
- 음성은 계속 장면별로 생성되고 원래 장면 순서대로 결합된다.
- 전체 대본 단일 TTS와 timestamp 재매핑은 도입하지 않는다.
- 성공 음성은 내용·설정 hash가 같으면 retry에서 재사용된다.
- 준비된 연속 구간 렌더가 남은 이미지·음성 생성과 겹쳐 실행된다.
- FFmpeg 동시성은 1이며 실제 출력은 24fps다.
- 시각 품질, 음성 품질, 자막 순서, A/V sync의 회귀가 없다.

## 14. 2차로 미루는 항목

- 전체 대본 단일 TTS 및 문자/단어 timestamp 매핑
- 문단/문장 TTS 동시성 4 이상
- FFmpeg 2개 이상 병렬 실행
- Codex 분석 분할 병렬화
- Codex 스트림에서 부분 장면을 조기 실행
- 이미지 동시성 4 초과 상향
