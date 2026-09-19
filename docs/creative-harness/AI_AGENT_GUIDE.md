# Creative Harness AI 작업자 가이드

이 문서는 Codex 또는 Claude가 영상 전문가를 도와 Slide Generator의 영상 연출을 개발할 때 따라야 하는 작업 계약이다.

이 문서의 목적은 AI 에이전트가 빠르게 코드를 바꾸는 것이 아니라, Core Engine을 오염시키지 않고 재현 가능한 영상 실험을 반복하게 하는 것이다.

## 1. 먼저 이해할 경계

```text
Core Engine
  작업 실행, provider, secret, queue, artifact, 복구, 계측

Harness SDK
  Core와 Creative Harness 사이의 안정 인터페이스

Creative Harness
  프롬프트, 연출 판단, 전환, 움직임, 합성, 후처리, 평가 fixture
```

영상 연출 변경의 기본 작업 범위는 `harnesses/<harness-id>/**`다.

다음 파일을 먼저 읽는다.

1. 루트 `README.md`의 Agent quick start
2. `harnesses/AGENTS.md`
3. 대상 Harness의 `README.md`
4. 대상 Harness의 `harness.yaml`
5. 대상 Harness의 `CHANGELOG.md`
6. 변경할 effect와 관련 tests/fixtures

## 2. 절대 규칙

- released Harness version을 직접 덮어쓰지 않는다.
- 실험은 기존 Harness를 새 ID 또는 새 version으로 clone해서 시작한다.
- `video-generator/app/engine/**`를 먼저 수정하지 않는다.
- Harness에서 engine private module을 import하지 않는다.
- secret, auth.json, API key, access token을 읽거나 출력하거나 fixture에 넣지 않는다.
- runtime에 `pip install`, `npm install`, curl pipe install을 추가하지 않는다.
- 새 dependency는 lockfile과 Docker build layer로 고정한다.
- shell=True 또는 문자열 조합 shell command를 사용하지 않는다. SDK ProcessRunner에 argument array를 전달한다.
- 작업 취소를 무시하는 background process를 만들지 않는다.
- 유료 provider 호출은 사용자가 명시적으로 승인한 경우에만 한다.
- 자동 검증은 Mock 이미지와 Mock 또는 Microsoft Edge 테스트 음성을 우선한다.
- Microsoft Edge TTS는 온라인 테스트 provider이며 ElevenLabs로 자동 fallback하지 않는다.
- 원문 narration을 의역·삭제·재배열하지 않는다.

## 3. 작업 시작 절차

에이전트는 코드를 수정하기 전에 다음 정보를 사용자 또는 작업 설명에서 확인하고 짧게 기록한다.

```text
실험 목표:
대상 Harness와 기준 version:
비교할 기존 결과:
평가용 대본/fixture:
바뀌어야 하는 시각적 현상:
바뀌면 안 되는 기능:
유료 Live 호출 승인 여부:
```

목표 예시:

```text
실험 목표: sequence 전환에서 단순 crossfade 대신 좌우 화면 이동을 시험한다.
기준: classic-slide 1.0.0
fixture: fixtures/sequence-transition-ko.md
변경 금지: narration, 자막 타이밍, 이미지 provider, 24fps
Live 호출: 승인 없음. 기존 fixture asset 재사용.
```

## 4. 변경 유형 판단

### 4.1 수치 또는 문구 변경

다음은 Harness config나 prompt만 변경한다.

- zoom 강도
- transition 시간
- 자막 크기·여백
- hold 시간
- 프롬프트 지침
- 색·구도 기본값

코드를 추가할 필요가 없으면 추가하지 않는다.

### 4.2 기존 effect 알고리즘 변경

대상 Harness의 `src/<package>/effects/`와 해당 test만 수정한다. 다른 Harness에 영향을 주지 않는다.

### 4.3 새로운 연출 기능

새 effect module과 TaskNode를 Harness에 추가한다.

```text
effects/cut_move.py
tests/test_cut_move.py
fixtures/cut-move-short.md
```

Harness `pipeline.py`가 새 node와 dependencies를 graph에 등록하게 한다. Core task type enum을 추가하지 않는다.

### 4.4 SDK로 표현할 수 없는 경우

engine private API를 우회하지 않는다. 다음을 문서화한다.

```text
현재 SDK로 불가능한 이유
필요한 최소 capability
기존 Harness와의 호환 영향
제안하는 SDK signature
테스트 방법
```

SDK 확장은 개발 담당자의 검토 대상이다. 승인 후 SDK와 Harness 변경을 분리된 commit으로 만든다.

## 5. 새 Harness 만들기

CLI가 구현된 뒤 다음 흐름을 정본으로 사용한다.

```sh
scripts/harness clone classic-slide experimental-cinematic
scripts/harness inspect experimental-cinematic
scripts/harness validate experimental-cinematic
```

복제 후 즉시 변경할 항목:

- `harness.yaml`의 ID/version/display name
- `README.md`의 실험 목적
- `CHANGELOG.md`의 최초 entry
- 대상 fixture

기존 output이나 generated media를 repository에 복사하지 않는다. fixture는 대본·작은 설정·기대 metadata 중심으로 유지한다.

## 6. 작업 그래프 설계

그래프는 실제 data dependency를 표현해야 한다.

예:

```text
scene image ───────┐
                   ├─ depth map ─ parallax render ─┐
scene voice ───────┘                               ├─ transition ─ segment
next scene render ─────────────────────────────────┘
```

규칙:

- task ID는 retry에서도 같아야 한다.
- 출력은 job workspace 안에 둔다.
- 임시 파일에 생성한 뒤 성공 시 atomic commit한다.
- 동일 입력과 code/config hash면 cache 재사용이 가능해야 한다.
- dependency를 file polling으로 기다리지 말고 graph edge로 선언한다.
- 임의 `asyncio.create_task`로 Core가 모르는 장기 작업을 만들지 않는다.
- CPU/FFmpeg 작업은 SDK resource request를 사용한다.
- 장면 하나 실패했을 때 어떤 task가 원인인지 오류에 남긴다.

## 7. Provider 사용

이미지, 음성, Codex를 직접 HTTP 호출하지 않는다. `HarnessContext`의 provider facade를 사용한다.

이유:

- secret 격리
- retry와 rate limit
- 비용 기록
- cancel 전파
- provider 교체
- Mock 테스트

새 provider 기능이 필요하면 private env나 credential 파일을 직접 읽지 말고 facade 확장을 제안한다.

## 8. 렌더 도구와 dependency

Harness는 필요한 렌더 기술을 자유롭게 선택할 수 있다.

- FFmpeg
- Pillow
- OpenCV
- Node/Remotion
- 기타 reviewed CLI

새 dependency를 추가할 때 기록한다.

```text
왜 필요한가
버전과 license
Docker image 증가량
MINI에서 CPU-only 동작 여부
없을 때의 오류
테스트 fixture
```

사용하지 않는 작업 경로에서 무거운 dependency를 import하지 않는다. GPU가 필수인 기능은 현재 MINI 기본 Harness에 넣지 않는다.

## 9. 프롬프트 변경

- 기능별 Markdown 분리를 유지한다.
- 하나의 거대 prompt로 합치지 않는다.
- 문서의 사용 시점·조건·역할·필수 변수를 prompt catalog에 반영한다.
- source unit, narration, keycut reference 계약을 깨지 않는다.
- 선택되지 않은 style/Harness prompt가 active snapshot에 섞이지 않게 한다.
- 변경된 prompt의 version/SHA가 작업에 기록되는지 테스트한다.

프롬프트가 연출 코드를 선택하게 할 수 있지만 raw shell command나 무검증 FFmpeg string을 model output으로 실행하지 않는다. LLM output은 Harness가 검증·변환한다.

## 10. 최소 테스트 순서

다음 순서를 건너뛰지 않는다.

1. `scripts/harness validate <id>`
2. Harness unit tests
3. graph cycle/dependency 검사
4. Mock provider fixture E2E
5. MP4 ffprobe와 결정론적 QC
6. 프레임 sampling 또는 screenshot 기반 시각 검사
7. 기존 classic Harness 회귀
8. 필요하고 승인된 경우에만 짧은 Live E2E

Live E2E를 할 때는 비용을 제한한다.

- 짧은 대본
- 최소 scene 수
- 사용 provider/model 명시
- 실행 전 승인
- 실행 후 실제 호출 수·비용 보고

## 11. 영상 품질 평가

코드 성공만으로 완료하지 않는다. 변경 목적에 맞는 시각 검사를 수행한다.

공통 확인:

- narration과 장면 의미 일치
- keycut과 파생 scene 관계
- transition이 이야기 흐름을 방해하지 않음
- 카메라 이동이 자막과 피사체를 잘라내지 않음
- 반복 효과가 기계적으로 보이지 않음
- 자막 안전영역
- 장면 사이 style 연속성
- 음성·자막·영상 sync
- 마지막 frame/음성 잘림 없음

정량값은 현재 관리자에 있는 전체·구간별 생성시간, 비용, 품질 점수를 사용한다. 별도 CPU/RAM 세분화는 요구되지 않는다.

## 12. 비교 실험

두 Harness를 비교할 때 가능한 한 다음을 고정한다.

- 같은 대본
- 같은 image model
- 같은 Codex model/effort
- 같은 voice provider/voice
- 같은 continuity 설정
- 같은 FPS와 resolution

이미지 생성의 확률성 때문에 한 번의 결과만으로 결론 내리지 않는다. 필요하면 같은 fixture를 여러 번 생성하고 품질 메모를 남긴다.

비교 보고 예시:

```text
기준: classic-slide 1.0.0
후보: experimental-cut-move 0.1.0
fixture: sequence-transition-ko

의도한 변화:
- sequence 경계가 더 분명해짐

관찰:
- group 내부는 기존 crossfade 유지
- sequence 경계 2곳에만 cut move 적용
- 자막 잘림 없음

회귀:
- 영상 길이 동일 범위
- 음성 sync 정상
- 기존 provider 호출 수 변화 없음

검증:
- unit tests
- Mock E2E
- frame screenshots
```

## 13. Commit과 버전

- 변경 전 새 Harness/version인지 확인한다.
- behavior가 바뀌면 version을 올린다.
- `CHANGELOG.md`에 목표, 변경, fixture, 알려진 한계를 기록한다.
- generated output, secret, `.runtime`, DB volume을 commit하지 않는다.
- dependency 변경과 creative behavior 변경을 가능하면 분리한다.
- Core/SDK 변경이 필요한 경우 Harness commit과 분리한다.

## 14. 작업 완료 보고 형식

에이전트는 사용자에게 다음을 보고한다.

```text
Harness ID/version
실험 목적
수정한 prompt/config/code
Core Engine 수정 여부와 이유
실행한 tests
Mock/Live provider 구분
생성시간·비용·품질 관찰
시각 검수 결과
남은 한계
재현 명령
```

Core를 수정하지 않았다면 명확히 적는다. SDK 부족으로 Core를 수정했다면 어떤 최소 capability를 추가했는지 설명한다.

## 15. 최종 판단 기준

좋은 Harness 변경은 다음 조건을 만족한다.

- 새로운 연출 의도가 실제 영상에서 보인다.
- Core Engine과 다른 Harness에 영향을 주지 않는다.
- 같은 version과 inputs로 재현 가능한 구조다.
- 실패·취소·재시도·artifact 기록이 기존 시스템과 연결된다.
- 비용과 복잡성 증가가 품질 개선에 비해 타당하다.
- 다음 영상 전문가 또는 AI 에이전트가 문서를 읽고 이어서 수정할 수 있다.
