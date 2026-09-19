# ADR-0005: 대본 계층 분석, 필수 키컷 참조, 영상별 이미지 스타일

- 상태: 구현 승인
- 작성일: 2026-09-20
- 구현 담당: `pipeline-maintainer`
- 대상: React 웹, NestJS API, Python video runner, PostgreSQL/Redis, 관리자 분석 화면

## 1. 결정 요약

현재의 `대본 -> 45자 기준 장면 -> 장면별 이미지` 구조를 다음 구조로 확장한다.

```text
대본 원문
  -> 결정론적 source unit과 원문 offset
  -> 한 번의 Codex 구조화 분석
       전체 대본의 목적
       sequence의 전체 대본 내 역할과 목적
       scene group의 sequence 내 역할과 목적
       scene의 group 내 역할과 목적
       sequence별 keycut scene
       전체 영상의 master keycut
       선택한 스타일에 맞춘 영상별 Style Bible
  -> 결정론적 구조·원문 보존 검사
  -> 모든 음성 태스크 즉시 등록
  -> 모든 sequence keycut 이미지를 높은 우선순위로 병렬 생성
  -> 각 파생 장면은 자기 sequence의 실제 keycut 이미지를 필수 reference로 받아 생성
  -> 이미지와 음성이 준비된 구간부터 기존 렌더 파이프라인 실행
```

핵심 결정은 다음과 같다.

1. 대본 계층 분석은 별도의 연속 LLM 호출로 쪼개지 않고 기존 장면 계획 호출 하나에 프롬프트 모듈과 strict schema를 합친다.
2. 키컷은 별도 보너스 이미지가 아니라 실제 narration을 가진 기존 scene 하나다. 따라서 키컷 도입만으로 이미지 장수가 늘어나지 않는다.
3. 각 sequence에는 정확히 하나의 keycut scene이 있다. sequence에 scene이 하나뿐이면 그 scene 자체가 keycut이다.
4. keycut이 아닌 모든 scene은 같은 sequence의 keycut scene ID를 `parent_keycut_scene_id`로 가져야 한다.
5. 파생 scene 이미지는 실제 생성된 parent keycut 이미지를 첫 번째 reference로 반드시 전달한다. 프롬프트 문구만 상속하는 것으로 구현 완료로 보지 않는다.
6. whole-film master keycut은 sequence keycut 중 하나를 의미적으로 지정한다. 다른 sequence keycut이 master keycut 이미지 생성을 기다리게 하지는 않는다. 전역 2단계 이미지 병목을 피하기 위함이다.
7. 스타일은 사용자 선택값과 영상별 Style Bible로 고정하고, 에셋 연속성 ON/OFF와 분리한다.

## 2. 왜 세 기능을 함께 구현하는가

### 2.1 계층 분석 없는 키컷의 문제

키컷은 단순 대표 이미지나 가장 화려한 이미지가 아니다. 여러 문장의 의미를 응축하고, 뒤따르는 컷이 무엇을 준비하거나 확장해야 하는지를 정하는 중심 장면이다.

다음 질문에 답한 뒤에만 키컷을 고를 수 있다.

- 이 영상이 시청자에게 일으키려는 전체 변화는 무엇인가?
- 이 sequence는 전체 대본에서 어떤 역할을 하는가?
- 이 scene group은 sequence에서 무엇을 준비하거나 증명하거나 회수하는가?
- 이 scene은 group 안에서 관심 유도, 설명, 대비, 전환, 증거, 적용, 결말 중 무엇을 담당하는가?
- 여러 장면이 공유해야 할 시각적 중심은 무엇인가?

이 분석 없이 키컷을 선택하면 키컷이 파생 컷의 의미를 지배하지 못하고, 단순히 첫 장면 또는 보기 좋은 장면이 된다.

### 2.2 스타일 고정 없는 키컷 참조의 문제

키컷 이미지를 참조해도 영상 전체 스타일 계약이 없으면 sequence마다 사진, 일러스트, 3D, 회화가 섞일 수 있다. 반대로 텍스트 스타일 가이드만 공유하면 독립적인 확률 생성 결과가 흔들린다.

따라서 다음 두 층을 모두 사용한다.

- 전 영상 공통: 선택한 preset을 구체화한 Style Bible
- sequence 내부: 실제 keycut 이미지 reference

### 2.3 병렬성과의 관계

키컷 참조는 의도적으로 부분 의존성을 만든다. 그러나 영상 전체를 직렬화하지 않는다.

```text
sequence-001 keycut ─┬─ derived scene 1
                     ├─ derived scene 2
                     └─ derived scene 3

sequence-002 keycut ─┬─ derived scene 4
                     └─ derived scene 5

voice scene 1..N  ───────────────────── 전부 독립 병렬
```

- 서로 다른 sequence의 keycut은 이미지 슬롯에서 함께 생성할 수 있다.
- keycut이 완료된 sequence부터 파생 이미지가 큐에서 실행된다.
- 다른 sequence의 keycut 실패나 지연이 준비된 sequence의 파생 이미지를 막지 않는다.
- 모든 음성은 scene narration 확정 직후 이미지와 무관하게 등록한다.
- 이미지 슬롯을 소비하는 쪽은 슬롯 수를 알지 않는다. 기존 shared image broker에 priority와 dependency만 제공한다.

## 3. 원문 보존형 source unit

현재처럼 45자 조각을 곧바로 최종 scene으로 확정하지 않는다. 먼저 프로그램이 원문에서 변경 불가능한 작은 단위를 만든다.

예시:

```json
{
  "id": "unit-0007",
  "start_offset": 121,
  "end_offset": 168,
  "text": "하지만 그 작은 변화는 곧 우리의 일하는 방식을 바꾸기 시작했습니다."
}
```

규칙:

- 문단, 문장부호, 개행, 길이가 긴 경우 절 경계를 이용한다.
- 각 unit은 원문의 정확한 offset을 가진다.
- LLM은 narration을 다시 작성하지 않고 `source_unit_ids`만 그룹화한다.
- 최종 narration은 프로그램이 원문 slice로 재조립한다.
- 모든 source unit은 정확히 한 scene에 포함되어야 한다.
- unit 순서는 바뀌면 안 되고 중복·누락되면 작업을 시작하지 않는다.
- 공백과 문장부호를 포함한 원문 보존 검사를 결정론적으로 수행한다.

이 방식은 서사적으로 의미 있는 장면 묶음을 허용하면서도 기존의 원문 누락·의역 실패를 막는다.

## 4. 구조화 분석 결과

기존 `ScenePlan`을 단순히 필드 몇 개 추가하는 수준이 아니라 `NarrativeBlueprint` 개념으로 확장한다. 구현 언어에 따른 타입 이름은 달라도 의미는 같아야 한다.

### 4.1 전체 대본

```json
{
  "title": "...",
  "core_question": "이 영상이 끝까지 붙드는 질문",
  "thesis": "영상이 전달하려는 중심 주장",
  "audience_start_state": "시작 시 시청자의 이해·감정 상태",
  "audience_end_state": "종료 시 도달해야 하는 상태",
  "master_keycut_scene_id": "scene-012"
}
```

`master_keycut_scene_id`는 반드시 sequence keycut 중 하나여야 한다. 이는 분석·관리자 표시·프롬프트 의미 문맥용이며 모든 이미지의 추가 reference로 강제하지 않는다.

### 4.2 sequence

sequence는 전체 대본 안에서 하나의 질문, 주장, 감정 변화 또는 설명 단계를 완결하는 상위 단위다.

필수 필드:

```json
{
  "id": "sequence-001",
  "source_unit_ids": ["unit-001", "unit-002"],
  "role_in_story": "hook | setup | problem | development | escalation | turning_point | explanation | application | resolution | outro | other",
  "purpose": "전체 대본에서 이 sequence가 존재하는 이유",
  "viewer_state_before": "...",
  "viewer_state_after": "...",
  "scene_group_ids": ["group-001"],
  "keycut_scene_id": "scene-002"
}
```

### 4.3 scene group

scene group은 같은 국소 목적을 수행하는 인접 scene 묶음이다. 모든 scene을 별도 group으로 만드는 것을 금지한다. scene 하나뿐인 group은 실제로 독립 목적이 있을 때만 허용한다.

```json
{
  "id": "group-001",
  "sequence_id": "sequence-001",
  "source_unit_ids": ["unit-001", "unit-002"],
  "role_in_sequence": "introduce | explain | evidence | example | contrast | deepen | transition | payoff | recap | other",
  "purpose": "이 sequence에서 이 묶음이 담당하는 목적",
  "setup": "이 묶음이 받아오는 정보 또는 감정",
  "payoff": "다음 묶음에 넘기는 변화",
  "scene_ids": ["scene-001", "scene-002"]
}
```

### 4.4 scene

기존 scene 필드에 다음 개념을 추가한다.

```json
{
  "id": "scene-002",
  "sequence_id": "sequence-001",
  "scene_group_id": "group-001",
  "source_unit_ids": ["unit-002"],
  "role_in_group": "이 장면이 묶음 안에서 담당하는 구체적 기능",
  "purpose": "이 장면이 없을 때 약해지는 시청자 이해 또는 감정",
  "viewer_takeaway": "이 장면 직후 시청자가 알아야 하거나 느껴야 할 것",
  "cut_role": "keycut | setup | derived | bridge | evidence | reaction | detail | transition | payoff",
  "parent_keycut_scene_id": null,
  "visual_summary": "...",
  "image_prompt": "..."
}
```

keycut이 아닌 scene은 `parent_keycut_scene_id`가 null이면 안 된다. parent는 같은 sequence의 `keycut_scene_id`와 정확히 같아야 한다. keycut scene 자신의 parent는 null이다.

## 5. 키컷 선정 원칙

프롬프트는 원본 프로젝트의 키컷 개념을 다음 원칙으로 이식한다.

- 키컷은 여러 source unit과 scene의 의미를 응축할 수 있어야 한다.
- 단지 첫 scene, 인물이 크게 나온 scene, 화려한 scene을 고르지 않는다.
- sequence의 `purpose`와 `viewer_state_after`를 가장 선명하게 시각화하는 실제 scene을 고른다.
- 파생 scene이 상속할 수 있는 색, 조명, 공간, 핵심 상징, 주 피사체 관계를 가져야 한다.
- 모든 scene을 keycut으로 만들지 않는다. sequence당 정확히 하나다.
- keycut을 위해 원문에 없는 narration이나 추가 scene을 만들지 않는다.
- whole-film master keycut은 전체 thesis와 audience_end_state를 가장 잘 대표하는 sequence keycut 하나다.

keycut에 별도의 `keycut_dna`를 둔다.

```json
{
  "story_meaning": "이 키컷이 응축하는 의미",
  "composition_anchor": "상속할 화면 구조",
  "palette_anchor": ["..."],
  "lighting_anchor": "...",
  "symbol_anchor": ["..."],
  "must_inherit": ["..."],
  "must_not_copy": ["동일 포즈", "동일 배경", "동일 프레이밍"]
}
```

## 6. 키컷 이미지 의존성과 reference 계약

### 6.1 이미지 태스크

- keycut scene은 일반 scene 이미지 장수에 포함한다.
- DB에서 분석 가능하도록 `task_type='keycut'` 또는 동등한 명시 필드를 사용한다.
- 모든 sequence keycut 태스크를 일반 파생 scene보다 높은 우선순위로 image broker에 제출한다.
- 파생 scene 태스크는 제출 시점부터 존재하지만 parent keycut task를 dependency로 가진다.
- keycut task가 완료되면 실제 파일 경로와 SHA-256을 파생 scene의 reference snapshot에 기록한다.
- 파생 scene provider 호출은 `/v1/images/edits` 계열을 사용하고 첫 reference를 parent keycut으로 보낸다.
- keycut reference가 누락되었는데 일반 generation endpoint로 조용히 전환하면 안 된다.

### 6.2 reference 예산

provider 기본 reference 상한 8개 안에서 다음처럼 사용한다.

- 파생 scene: keycut reference 1개 필수 + continuity asset reference 최대 7개 = 최대 8개
- keycut scene: continuity asset reference 최대 8개
- reference 순서와 의미를 prompt snapshot 및 task metadata에 기록한다.
- continuity 분석에서 파생 scene에 8개 asset reference를 배정했더라도 keycut 자리를 확보하기 위해 결정론적으로 최대 7개만 선택한다.

### 6.3 프롬프트 계약

keycut reference에서 상속할 것:

- 선택한 이미지 스타일과 렌더링 매체
- palette, lighting, texture, contrast
- sequence의 핵심 상징과 공간 문법
- keycut DNA의 `must_inherit`

복사하면 안 되는 것:

- keycut과 동일한 포즈
- 동일한 카메라 위치와 프레이밍
- 장면 내용과 무관한 배경 및 소품
- 파생 scene의 narration과 충돌하는 인물 행동

continuity asset reference는 개체의 identity를 담당하고, keycut reference는 sequence의 시각 문법을 담당한다. 두 종류를 prompt 안에서 명확히 구분한다.

### 6.4 실패 정책

keycut reference는 사용자 결정상 필수이므로 fail-open 하지 않는다.

- keycut 이미지 생성은 기존 재시도 정책을 따른다.
- 최종 실패하면 해당 sequence의 파생 scene을 독립 생성하지 않고 영상 작업을 실패 처리한다.
- 사용자 메시지는 `시퀀스 2의 기준 키컷 이미지를 만들지 못했습니다.`처럼 원인을 표시한다.
- 관리자 상세에는 provider 오류, 재시도, 기다리던 파생 태스크 수를 표시한다.

## 7. 이미지 스타일 선택

현재 렌더러가 정지 슬라이드 기반이므로 원본의 제작 형식을 그대로 과장해 `애니메틱`이라고 부르지 않는다. 초기 선택지는 이미지 결과에 실제로 반영되는 다음 세 가지로 둔다.

| ID | 사용자 표시 | 목적 |
|---|---|---|
| `editorial_illustration` | 에디토리얼 일러스트 | 현재 기본 스타일과 가장 가까운 정돈된 설명형 일러스트 |
| `cinematic_realism` | 영화적 사실화 | 영화 스틸처럼 현실적인 인물·공간·빛과 렌즈감 |
| `graphic_explainer` | 그래픽 설명형 | 인과·비교·구조를 도형과 공간 관계로 설명, 이미지 내부 글자는 금지 |

- 기존 클라이언트가 `imageStyle`을 보내지 않으면 `editorial_illustration`을 사용한다.
- 선택값은 React -> Nest DTO -> DB -> BullMQ payload -> runner까지 명시적으로 전달한다.
- 작업 시작 후 변경되지 않으며 관리자 작업 상세와 분석 차원에 기록한다.
- `imageModel`과 `imageStyle`은 서로 다른 필드다.
- `continuityEnabled`와 `imageStyle`도 서로 독립이다.

### 7.1 preset 문서

프롬프트는 최소 다음처럼 분리한다.

```text
prompts/
  narrative/story-intent.md
  narrative/analyze-sequences.md
  narrative/analyze-scene-groups.md
  narrative/analyze-scenes.md
  keycut/select-keycuts.md
  keycut/reference-contract.md
  style/common.md
  style/presets/editorial-illustration.md
  style/presets/cinematic-realism.md
  style/presets/graphic-explainer.md
```

각 문서는 기존 관리자 프롬프트 화면에서 다음 정보를 포함해 조회·수정·버전 복원할 수 있어야 한다.

- 언제 사용되는지
- 어떤 조건에서 사용되는지
- 분석인지 이미지 생성인지
- 필수 template variable
- 현재 버전과 SHA-256

선택하지 않은 style preset은 해당 작업의 활성 prompt set fingerprint에 포함하지 않는다. 선택한 preset과 공통 스타일 문서는 포함한다.

### 7.2 영상별 Style Bible

Codex 구조화 분석 결과에 선택된 preset을 대본에 맞게 구체화한 `style_bible`을 포함한다.

필수 개념:

- `preset_id`
- `medium_and_rendering`
- `palette`
- `lighting`
- `camera_and_depth`
- `texture_and_detail`
- `character_rendering`
- `environment_rendering`
- `composition_rules`
- `forbidden_variations`

Style Bible은 장면마다 새로 만들지 않고 영상당 정확히 하나만 만든다. 그대로 모든 keycut과 scene 이미지 프롬프트에 주입하고 work artifact와 관리자 상세에 보존한다.

## 8. 한 번의 Codex 호출과 프롬프트 구성

추가 기능 때문에 대본 분석 -> sequence 분석 -> keycut 분석 -> scene 분석을 네 번의 Codex 호출로 직렬 실행하지 않는다. 기존 scene planning 호출 한 번에 기능별 Markdown을 조립하고 하나의 strict JSON schema로 받는다.

구조:

```text
system/director
+ narrative/story-intent
+ narrative/analyze-sequences
+ narrative/analyze-scene-groups
+ narrative/analyze-scenes
+ keycut/select-keycuts
+ selected style preset
+ continuity ON 또는 OFF 문서
+ image prompt 규칙
-> NarrativeBlueprint strict JSON
```

스트리밍 transcript에는 조립된 각 문서의 버전과 request/response를 지금처럼 파일로 남긴다. 응답이 길어지므로 기존 read timeout 환경설정과 장시간 작업 cancel 전파를 유지한다.

## 9. 결정론적 검증

LLM이 출력한 다음 항목을 LLM으로 재검수하지 않는다. 프로그램으로 검증한다.

- source unit 전체가 정확히 한 번 사용됨
- 원문 순서 유지, 누락·중복·의역 없음
- sequence, group, scene 범위가 연속적이고 서로 겹치지 않음
- 모든 group이 정확히 한 sequence에 속함
- 모든 scene이 정확히 한 group과 sequence에 속함
- sequence당 keycut 정확히 하나
- master keycut이 sequence keycut 중 하나
- keycut이 아닌 scene의 parent가 같은 sequence keycut과 일치
- keycut dependency cycle 없음
- scene ID, sequence ID, group ID 연속성
- keycut 포함 reference 최대 8개
- 선택 style ID가 허용 목록에 존재
- Style Bible 필수 필드 비어 있지 않음

검증 실패 시 현재처럼 임의의 45자 scene 기준안으로 hierarchy를 소거해 복구하지 않는다. 안전한 동일-call repair를 정의하거나 명확히 실패해야 한다. 구조 분석이 사라진 채 성공한 것처럼 진행하면 안 된다.

## 10. API, DB, UI

### 10.1 생성 API

`POST /api/jobs` 요청에 추가:

```json
{
  "scenario": "...",
  "imageModel": "gpt-image-2.5-sunburst",
  "imageStyle": "editorial_illustration",
  "continuityEnabled": false
}
```

응답과 `GET /api/jobs/:id`에 `imageStyle`을 포함한다.

### 10.2 DB 및 artifacts

최소 저장 항목:

- generation job의 `image_style`
- job에 고정된 style preset 문서 버전/SHA
- `narrative-blueprint.json`
- `style-bible.json`
- sequence/group/scene hierarchy 또는 이를 안정적으로 조회할 JSONB/정규화 테이블
- keycut scene ID와 master keycut 여부
- image task의 `parent_keycut_task_id`
- reference snapshot의 kind: `keycut` 또는 `continuity_asset`
- dependency wait, keycut provider duration, derived provider duration

기존 작업은 hierarchy 없음, style은 `editorial_illustration` 또는 `legacy`로 구분해 분석 데이터에 거짓 backfill하지 않는다.

### 10.3 사용자 웹

영상 생성 화면에 세 스타일을 카드 또는 select로 표시한다. 각 항목은 이름과 결과 차이를 한 문장으로 설명한다. 초기 기본값은 `에디토리얼 일러스트`다.

현재 작업 카드와 완료 결과에 선택 스타일을 표시한다. 사용자가 style과 image model을 혼동하지 않게 별도 행으로 보여준다.

### 10.4 관리자 웹

작업 상세에 다음을 노출한다.

- 전체 대본의 core question/thesis/audience journey
- sequence 목록과 각 role/purpose
- scene group 목록과 각 role/purpose
- scene의 role/purpose/viewer takeaway
- master keycut 및 sequence keycut 표시
- keycut thumbnail과 이를 참조한 파생 scene 수
- Style Bible 및 선택 preset/버전
- keycut reference가 실제 provider 요청에 들어갔는지 확인 가능한 reference snapshot

raw JSON만 던지지 말고 hierarchy가 읽히는 접기 구조를 제공한다.

## 11. 측정과 비교 분석

기존 개선 분석에 다음 차원을 추가한다.

- image style / style preset version
- sequence 수
- scene group 수
- keycut 수
- keycut reference를 사용한 파생 이미지 수
- scene당 평균 reference 수
- keycut dependency wait p50/p95
- keycut 이미지 평균 생성시간과 비용
- 파생 이미지 평균 생성시간과 비용
- style별 관리자 품질 점수
- continuity ON/OFF와 style 조합
- keycut 도입 전 legacy 작업과 도입 후 작업 구분

한 영상의 전체 시간에는 planning, keycut generation critical path, derived generation critical path를 분리해 표시한다. 병렬 작업의 누적시간과 실제 wall-clock을 혼동하지 않는다.

## 12. 테스트

### 12.1 단위 테스트

- 짧은 대본: 1 sequence, 1 group, 1 keycut
- 긴 대본: 여러 sequence/group, 모든 unit 정확히 한 번 사용
- source unit 누락·중복·순서 변경 거부
- sequence/group role 또는 purpose 누락 거부
- sequence에 keycut 0개 또는 2개 거부
- 다른 sequence keycut을 parent로 지정하면 거부
- keycut dependency cycle 거부
- 파생 scene references가 keycut 1 + asset 최대 7인지 확인
- imageStyle 누락 시 backward-compatible 기본값
- 잘못된 imageStyle 400

### 12.2 통합 테스트

- 3개 sequence keycut이 이미지 슬롯에서 병렬 시작 가능
- 각 파생 scene이 자기 keycut 완료 전 provider 호출되지 않음
- 한 sequence keycut 완료 후 다른 sequence를 기다리지 않고 그 파생 scene이 ready 상태가 됨
- 모든 파생 provider request가 실제 keycut 파일을 첫 reference로 포함
- continuity ON에서 keycut과 asset reference 역할 및 순서가 기록됨
- voice task는 keycut 이미지 완료를 기다리지 않고 전부 제출됨
- keycut 최종 실패 시 독립 이미지 fallback 없이 명확한 실패
- 세 style preset이 prompt snapshot과 provider request에 각각 반영됨

### 12.3 Live E2E와 시각 검수

같은 짧은 대본으로 세 스타일을 각각 생성하고 다음을 사람이 화면과 결과 영상으로 확인한다.

- 선택한 스타일 차이가 명확함
- 같은 영상 안에서 medium, palette, lighting, texture가 일관됨
- 각 sequence의 파생 scene이 keycut의 시각 문법을 이어받음
- keycut 배경·포즈·프레이밍을 모든 파생 scene이 복제하지 않음
- narration과 자막 원문이 완전 보존됨
- 관리자 hierarchy와 실제 이미지 태스크 dependency가 일치함
- 모바일 390px에서 스타일 선택과 hierarchy 상세에 페이지 가로 overflow 없음
- 콘솔 오류, 실패 요청, 접근성 이름 누락 없음

Live E2E는 비용을 제한하기 위해 2개 sequence, sequence당 2~3 scene인 짧은 대본으로 먼저 수행한다. mock 테스트만으로 시각 일관성 완료 판정을 하지 않는다.

## 13. 완료 조건

다음을 모두 만족해야 완료다.

1. 사용자가 세 이미지 스타일 중 하나를 선택하고 그 선택이 job 전체에 고정된다.
2. 관리자에서 선택 preset과 Style Bible, 버전을 확인할 수 있다.
3. 전체 대본 -> sequence -> scene group -> scene 역할과 목적이 명시적으로 저장·표시된다.
4. sequence마다 정확히 하나의 실제 scene keycut이 있다.
5. keycut이 아닌 모든 scene의 이미지 provider 요청에 해당 sequence의 실제 keycut 이미지가 reference로 포함된다.
6. keycut은 추가 이미지가 아니므로 scene 수와 이미지 수가 불필요하게 증가하지 않는다.
7. 서로 다른 sequence keycut과 모든 voice task는 병렬 실행 가능하다.
8. 모든 계층·원문·dependency 검사는 결정론적 프로그램으로 수행된다.
9. 프롬프트가 기능별 Markdown으로 분리되고 관리자에서 버전 관리된다.
10. 비용·시간·품질을 style과 keycut 지표별로 비교할 수 있다.
