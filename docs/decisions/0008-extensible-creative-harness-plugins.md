# ADR-0008: 확장 가능한 코드형 Creative Harness Plugin

- 상태: 구현 승인
- 작성일: 2026-09-20
- 구현 담당: `pipeline-maintainer`
- 주요 사용자: 영상 전문가가 사용하는 Codex 또는 Claude 에이전트

## 1. 결정

영상 연출을 제한된 preset, enum, YAML 목록으로 규격화하지 않는다. Core Engine과 Creative Harness 사이의 실행 계약만 규격화하고, Harness는 신뢰된 Python 코드와 프롬프트·설정·asset을 함께 포함할 수 있는 Plugin package로 만든다.

```text
Core Engine
  └─ Creative Harness SDK
       └─ 설치된 Harness Plugin
            ├─ 대본·키컷·이미지 프롬프트
            ├─ 연출 계획
            ├─ 컷 전환
            ├─ 카메라 이동
            ├─ 자막·합성·후처리
            ├─ 임의의 새 작업 노드
            └─ 자체 테스트·평가 fixture
```

YAML/JSON은 자주 조정하는 값에 쓰는 편의 수단이지 표현 능력의 상한이 아니다. 새로운 기능이 설정으로 표현되지 않으면 영상 전문가는 Harness 내부에 코드를 추가한다. Core Engine을 수정하지 않는 것을 기본으로 하되, 이는 결합도를 낮추기 위한 권고이지 절대 제약이 아니다. 사용자 기능을 올바르게 제공하려면 Core 또는 Harness SDK도 공개 계약·테스트·문서를 함께 갱신하며 적절하게 수정할 수 있다.

## 2. 표준화하는 것과 하지 않는 것

### 2.1 표준화하는 것

- Harness ID, 버전, engine API 호환 범위
- Plugin entrypoint
- 작업 그래프와 dependency 표현
- 작업 취소·재시도·산출물 commit 계약
- provider 사용 방법
- 작업 디렉터리와 artifact 등록
- 로그·기존 시간/비용/품질 계측 연결
- 설치·선택·버전 고정 방법
- 테스트와 배포 방법

### 2.2 표준화하지 않는 것

- 가능한 전환 효과 목록
- 가능한 카메라 이동 목록
- 장면 렌더링 구현 방식
- FFmpeg만 사용해야 한다는 제한
- 장면당 작업 단계 개수
- 연출을 수치 설정만으로 표현해야 한다는 제한

Harness는 필요하면 FFmpeg, Pillow, OpenCV, Remotion, 별도 CLI 또는 향후 다른 렌더러를 사용할 수 있다. 다만 해당 dependency는 build 시 고정하고 job runtime에 임의 설치하지 않는다.

## 3. 성능 원칙

Plugin 구조 자체가 영상 생성시간을 의미 있게 늘리지 않도록 다음을 고정한다.

- 장면·효과마다 Docker container를 새로 만들지 않는다.
- 장시간 실행되는 runner가 선택된 Harness를 작업 시작 시 한 번 load한다.
- Harness module은 한 process에서 cache한다.
- 무거운 선택 dependency는 lazy import한다.
- 작업 그래프 구성과 manifest hash는 작업당 한 번만 수행한다.
- Core의 기존 이미지·음성·FFmpeg concurrency lease를 재사용한다.
- 선택하지 않은 Harness dependency를 기본 runner가 전부 import하지 않는다.

이번 범위에서는 CPU/RAM 세부 계측을 새로 만들지 않는다. 현재 존재하는 전체·구간별 생성시간, provider 비용, 품질 점수, 작업별 model/prompt 정보에 Harness ID·버전·hash만 추가한다. 추가 계측은 실제 필요가 확인될 때 별도 결정한다.

## 4. 소스 경계

권장 구조:

```text
video-generator/
  app/
    engine/
      job_runtime.py
      graph_executor.py
      artifact_store.py
      process_runner.py
      provider_facade.py
      validation.py

    harness_sdk/
      api.py
      context.py
      graph.py
      task.py
      artifacts.py
      services.py
      errors.py

harnesses/
  classic-slide/
    harness.yaml
    README.md
    CHANGELOG.md
    pyproject.toml
    src/classic_slide/
      plugin.py
      pipeline.py
      planning.py
      effects/
        still_motion.py
        crossfade.py
        subtitles.py
        assembly.py
    prompts/
    config/
    fixtures/
    tests/

  experimental-cinematic/
    ...
```

의존 방향:

```text
Core Engine <- Harness SDK <- Harness Plugin
```

- Core는 구체 Harness package를 import하지 않는다.
- Harness는 `app.engine` 내부 구현을 import하지 않고 `harness_sdk`만 사용한다.
- Core와 Harness의 연결은 manifest entrypoint와 SDK protocol을 통해 이뤄진다.
- SDK가 부족하면 영상 전문가의 Harness에서 engine private module을 우회 import하지 않는다. 최소 SDK 확장 제안을 별도 변경으로 올린다.

## 5. Harness manifest

`harness.yaml`은 capability 목록을 제한하기 위한 문서가 아니라 설치·호환·재현성을 위한 manifest다.

```yaml
id: classic-slide
version: 1.0.0
engine_api: ">=1.0,<2.0"
entrypoint: classic_slide.plugin:ClassicSlideHarness
display_name: 기본 슬라이드 연출
description: 정지 이미지, Ken Burns, crossfade, 자막 기반 기본 Harness

prompts_dir: prompts
config_dir: config
fixtures_dir: fixtures

python:
  package: classic-slide-harness
  lockfile: requirements.lock

defaults:
  config: config/default.yaml
```

필수 검증:

- ID와 semantic version 형식
- entrypoint import 가능
- engine API 호환
- prompt/config 경로가 package root 밖으로 탈출하지 않음
- dependency lock 존재 여부
- manifest와 package 전체 hash 계산 가능

## 6. Harness API

SDK는 작고 안정적으로 유지한다. 예시 의미:

```python
class CreativeHarness(Protocol):
    manifest: HarnessManifest

    async def build_pipeline(
        self,
        context: HarnessContext,
    ) -> PipelineGraph:
        """이 작업을 완성하기 위한 임의의 DAG를 반환한다."""

    async def validate_result(
        self,
        context: HarnessContext,
        result: PipelineResult,
    ) -> HarnessValidation:
        """Harness 고유의 결정론적 검사를 반환한다."""
```

`HarnessContext`는 다음 서비스를 제공하되 secret 원문은 직접 제공하지 않는다.

- immutable job input과 narrative blueprint
- 작업별 고정 model/style/voice/Harness 설정
- job workspace와 artifact API
- Codex/image/voice provider facade
- process runner
- core logger와 cancellation token
- 기존 timing/cost tracker
- image/voice/FFmpeg resource lease 요청 API

Harness가 DB connection, Redis password, ElevenLabs key, Codex credential을 직접 열지 않게 한다. 외부 provider는 Core facade를 통해 호출해 비용·재시도·취소·보안 정책을 유지한다.

## 7. 범용 작업 그래프

Core는 영상 단계 목록이 아니라 임의의 DAG를 실행한다.

```python
graph.add(TaskNode(
    id="scene-004-depth-map",
    dependencies=["scene-004-image"],
    resource=ResourceRequest(kind="cpu", slots=1),
    run=create_depth_map,
))

graph.add(TaskNode(
    id="scene-004-parallax",
    dependencies=["scene-004-depth-map", "scene-004-voice"],
    resource=ResourceRequest(kind="ffmpeg", slots=1),
    run=render_parallax_scene,
))

graph.add(TaskNode(
    id="transition-004-005",
    dependencies=["scene-004-parallax", "scene-005-render"],
    resource=ResourceRequest(kind="ffmpeg", slots=1),
    run=render_custom_transition,
))
```

TaskNode 최소 계약:

- deterministic task ID
- dependency IDs
- async callable
- resource request
- expected output declarations
- cache/input fingerprint callback 또는 값
- retry policy 또는 `no_retry`
- cleanup callback가 필요하면 해당 hook

새 연출 기능은 새로운 TaskNode subclass나 callable을 추가하면 된다. Core의 task type enum을 추가하도록 요구하지 않는다.

### 7.1 resource request

resource kind는 연출을 제한하기 위한 allowlist가 아니라 MINI를 보호하기 위한 scheduler 힌트다.

- `image`
- `voice`
- `ffmpeg`
- `cpu`
- `io`

새 도구는 가장 가까운 공유 자원을 사용하거나 manifest에서 custom lease를 선언할 수 있다. Harness가 Core 밖에서 무제한 subprocess를 병렬 실행하지 않는다.

## 8. Process 실행과 자유도

Harness code는 신뢰된 repository code로 취급한다. arbitrary code이므로 웹에서 upload하거나 prompt editor로 수정하지 않는다.

SDK의 `ProcessRunner`는 shell string이 아니라 argument array, cwd, env allowlist, timeout, cancellation token을 받는다.

```python
await context.process.run([
    "ffmpeg", "-y", "-i", str(source),
    "-filter_complex", filter_graph,
    str(output),
])
```

영상 전문가는 복잡한 filter graph나 Python/OpenCV 로직을 자유롭게 작성할 수 있다. Core는 성공 코드, 취소, timeout, stderr tail, artifact 존재를 관리한다.

새 system package나 Node dependency가 필요하면 Harness별 Docker target/image layer에 선언한다. runtime `pip install`, `npm install`, curl pipe install은 금지한다.

## 9. Default Harness 이전

현재 `video-generator/app/media.py`에 들어 있는 창작 결정을 `classic-slide` Harness로 이동한다.

이동 대상:

- ASS 자막 theme과 줄바꿈
- 이미지 crop/framing
- Ken Burns zoom/pan
- crossfade 종류와 길이 선택
- 장면 segment render
- 영상·오디오 조립
- 해당 Harness 고유 QC

Core에 남길 것:

- 안전한 subprocess 실행
- ffprobe/Pillow 등의 범용 artifact 검사 primitive
- queue, DB, Redis, cancellation, retry
- provider broker와 resource lease
- 작업 artifact registry와 기존 계측

이전 전후 같은 fixture에서 output duration, stream, frame behavior, subtitle 위치가 회귀하지 않아야 한다.

## 10. 프롬프트와 코드 묶음

Harness는 관련 프롬프트와 코드를 한 버전으로 소유한다.

```text
classic-slide 1.3.0
  prompts/narrative/*
  prompts/keycut/*
  prompts/image/*
  prompts/direction/*
  src/classic_slide/effects/*
  config/default.yaml
```

관리자 Prompt UI에서 Markdown 수정 기능은 유지한다. 다만 저장된 문서 버전은 어떤 Harness base 문서에서 갈라졌는지 기록한다.

새 작업에는 다음을 고정한다.

- Harness ID/version
- manifest SHA-256
- Harness source tree SHA-256
- container image digest 또는 Git commit
- 선택 config SHA-256
- 실제 prompt set version

이미 완료된 작업이 참조한 released Harness version은 덮어쓰지 않는다. 동작을 바꾸면 version을 올린다.

## 11. 개발과 운영 loading

### 11.1 개발

- `harnesses/`를 runner에 bind mount할 수 있다.
- 한 작업 시작 시 version/hash를 snapshot한다.
- Python code 변경은 안전한 runner restart 또는 dev reload 후 적용한다.
- 실행 중 작업의 module을 hot swap하지 않는다.
- 새 dependency가 없으면 전체 인프라 image를 다시 build하지 않아도 된다.

### 11.2 운영

- 설치할 Harness와 dependency를 image build 때 고정한다.
- manifest에 등록된 Harness만 load한다.
- job은 접수 당시 설치된 정확한 version을 선택한다.
- 운영 컨테이너에서 arbitrary source edit 또는 package install을 하지 않는다.

## 12. API와 관리자 UI

관리자에 최소 기능을 추가한다.

- 설치된 Harness 목록과 호환 상태
- 새 작업 기본 Harness 선택
- Harness README/manifest/version/hash 보기
- Harness config schema가 제공되면 기본값 편집
- 작업 상세에서 사용 Harness 표시
- 기존 개선 분석에서 Harness version별 시간·비용·품질 비교

일반 사용자가 Python Plugin을 선택·업로드하지 못하게 한다. 공개 생성 화면에는 필요하다면 관리자가 공개 허용한 Harness의 표시 이름만 선택지로 제공한다.

## 13. CLI

에이전트와 영상 전문가를 위한 명령을 제공한다.

```text
scripts/harness list
scripts/harness inspect classic-slide
scripts/harness clone classic-slide experimental-cinematic
scripts/harness validate experimental-cinematic
scripts/harness hash experimental-cinematic
scripts/harness test experimental-cinematic
scripts/harness dev experimental-cinematic
```

Windows PowerShell wrapper와 Linux shell wrapper가 같은 기능을 호출한다. 실제 로직은 한 언어로 구현해 중복을 줄인다.

`clone`은 released version을 직접 수정하지 않고 새 ID/version으로 복제한다. `validate`는 network와 유료 provider 없이 manifest/import/graph/fixture를 검사한다.

## 14. 복구와 안전

- Task output은 임시 경로에 만들고 성공 후 atomic rename한다.
- Task cache key는 inputs, Harness hash, config, code version을 포함한다.
- 동일 job retry 시 성공한 compatible node를 재사용할 수 있다.
- Harness exception은 job failure로 변환하고 task ID와 Harness version을 기록한다.
- 취소 시 child process까지 종료한다.
- Plugin이 Core secret을 읽거나 host filesystem을 벗어나지 않도록 기존 runner container 경계를 유지한다.
- 이번 구조는 악의적인 Plugin을 sandbox하는 보안 기능이 아니다. 신뢰된 영상 전문가의 reviewed code만 설치한다.

## 15. AI 작업자 문서

저장소에 다음 문서를 둔다.

- `docs/creative-harness/AI_AGENT_GUIDE.md`: Codex/Claude용 전체 개발 절차
- `harnesses/AGENTS.md`: `harnesses/**` 작업 시 반드시 따를 짧은 scoped instruction
- 각 Harness의 `README.md`, `CHANGELOG.md`

루트 `AGENTS.md`는 Harness 관련 작업을 시작할 때 위 두 문서를 먼저 읽도록 연결한다. Harness template에도 같은 링크를 둔다.

AI 에이전트가 문서를 읽지 않은 채 Core Engine부터 수정하는 경로를 정상 흐름으로 취급하지 않는다. 다만 문서를 검토한 뒤 사용자 기능에 Core 변경이 필요하다고 판단했다면 영향 범위와 호환성을 명시하고 수정할 수 있다.

## 16. 테스트

### 16.1 SDK/Core

- manifest validation과 API version mismatch
- Plugin discovery/import failure
- arbitrary DAG topological execution
- cycle/unknown dependency 거부
- cancellation과 child process 정리
- atomic output, retry, cache fingerprint
- resource lease 공유
- Harness exception의 사용자 오류 변환

### 16.2 Default Harness 회귀

- 기존 짧은 fixture의 narration/audio/video duration
- 1920x1080, 24fps, H.264/AAC
- 자막 위치·줄바꿈
- Ken Burns와 crossfade가 기존 수준으로 동작
- queue, 비용, prompt snapshot, 관리자 상세 회귀

### 16.3 확장성 증명 Harness

단순 수치 변경이 아닌 작은 실험 Harness 하나를 만들어 Plugin 경계가 실제로 충분함을 증명한다.

예:

- `experimental-cut-move`
- classic Harness를 상속하거나 복제
- crossfade 대신 한 transition에서 좌우 화면 이동 구현
- Core 파일 수정 없이 새로운 task/effect 추가
- 별도 version/hash로 관리자에 표시

확장성 완료 판정은 이 실험 Harness가 Core 수정 없이 생성·렌더·복구·분석까지 통과하는 것이다.

## 17. 구현 순서

1. Harness SDK와 manifest/loader/validator
2. 범용 PipelineGraph executor 또는 현재 executor를 일반화
3. `media.py` 창작 로직을 `classic-slide` Harness로 이전
4. 기존 파이프라인이 Harness graph를 실행하도록 배선
5. version/hash/job snapshot과 관리자 선택
6. CLI와 Agent 문서
7. Default Harness 회귀
8. `experimental-cut-move`로 Core 무수정 확장 E2E
9. MINI 배포와 사용자 관점 회귀

## 18. 완료 조건

1. 현재 기본 영상이 `classic-slide` Harness Plugin으로 동일하게 생성된다.
2. 영상 전문가가 `harnesses/**`만 변경해 프롬프트·전환·카메라 이동·새 작업 단계를 추가할 수 있다.
3. 새로운 효과는 기본적으로 Core task enum 또는 `media.py` 수정 없이 추가할 수 있다. 다만 사용자 기능 구현에 Core/SDK 변경이 필요한 경우에는 공개 계약·테스트·문서를 함께 갱신한다.
4. Harness는 제한된 효과 allowlist가 아니라 임의의 DAG와 신뢰된 코드를 구성할 수 있다.
5. 작업마다 Harness version/hash가 고정되고 기존 비용·시간·품질 분석에 연결된다.
6. 별도 컨테이너-per-scene 구조를 만들지 않아 구조적 성능 저하가 없다.
7. Codex/Claude 작업자가 읽을 문서와 scoped `AGENTS.md`가 실제 개발 절차를 안내한다.
8. `experimental-cut-move`가 Core 수정 없이 확장 가능성을 증명한다.
9. 이번 범위에서 세부 CPU/RAM 계측은 추가하지 않는다.
