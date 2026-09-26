# 0012. 도구 체계와 Scene Program 개편

## 상태

채택. 2026-09-21.

## 진단

HyperFrames와 GSAP은 버전 고정, 프레임 탐색, FFmpeg 합성까지 안정적으로 연결돼 있었다. 그러나 기존 Astra renderer는 ScenePlan의 `layout`, `object_states`, `motion`, `transition`, `rhythm`을 대부분 무시하고 모든 장면에 같은 카드·원·카메라 이동을 적용했다. 병목은 렌더러의 표현력보다 감독 계약을 안전한 실행 문법으로 번역하는 계층이었다.

또한 limited mesh는 자산·렌더 해시와 최대 변위 상한은 확인했지만, 작은 변위 안에서 발생하는 늘어짐·면적 붕괴·삼각형 뒤집힘·접합부 이격을 측정하지 않았다.

## 결정

### Scene Program

ScenePlan을 직접 JavaScript로 실행하지 않는다. `scene_program.py`가 다음 allowlist로 컴파일한다.

- layout: `focus`, `split`, `comparison`, `process`, `diagram`
- transition: `cut`, `crossfade`
- effect: `camera_push`, `reveal`, `emphasize`, `progress`
- component: 역할이 검증된 `subject`, `evidence`, `highlight`, `progress`, `title`

알 수 없는 값은 실행하지 않고 안전한 기본값으로 낮춘다. 컴파일된 `scene-program.json`을 렌더 결과와 함께 남겨 어떤 연출 계약이 실행됐는지 추적한다.

### limited mesh v2

실제 rest/deformed geometry에서 다음 증거를 산출한다.

- 최대 vertex displacement ratio
- edge stretch P50/P95/min/max
- triangle area ratio min/max
- triangle flip count
- seam gap ratio
- neutral reassembly error ratio

메시 계약은 topology, rest mesh, weight map, rigidity map, reference length, boundary와 occlusion 정책의 hash를 요구한다. 기하학 검사는 파손을 차단하는 기술 게이트이며, 후보가 baseline보다 실제로 더 자연스러운지는 계속 사람이 판단한다.

## 도구 역할

| 도구 | 역할 | 자동 실행 |
|---|---|---|
| HyperFrames + GSAP | 검증된 객체·타임라인의 결정론적 런타임 | 사용자가 Astra Harness를 선택한 경우 |
| FFmpeg | 음성·영상 조립과 규격화 | 허용 |
| OpenToonz Plastic | rigidity와 stacking을 포함한 Gold deformation reference | 금지 |
| Blender Armature | bone weight와 hidden region을 저작하는 오프라인 Gold 공장 | 금지 |
| Astra mesh evidence | geometry 기술 검수 | 실험 계약에서 허용 |
| Playwright | baseline/candidate keyframe diff 검수 화면 | 도입 예정 |
| scikit-image | neutral·silhouette 이미지 회귀 보조 | 도입 예정 |
| libigl ARAP/SLIM | 자체 solver 품질 비교 | 연구 전용 |

OpenToonz는 deformable mesh, skeleton vertex, angle bounds, rigidity와 stacking order를 제공한다. Blender Armature는 vertex group weight와 Preserve Volume을 제공한다. scikit-image는 SSIM, Hausdorff, PSNR, MSE를 제공하며 Playwright는 expected/actual/diff 비교를 지원한다. libigl의 SLIM은 flip을 방지하는 locally injective mapping 비교 기준으로 사용한다.

## 지식 흡수 규칙

1. 공식 문서와 원 프로젝트를 우선한다.
2. 발견한 기능을 바로 production 규칙으로 만들지 않는다.
3. 먼저 계약 필드 또는 Gold benchmark 가설로 번역한다.
4. 동일 입력 A/B에서 자동 증거와 사람 판단을 함께 기록한다.
5. 서로 다른 자산·장면에서 반복 검증된 뒤에만 정책 승격을 검토한다.

참고 자료는 `harnesses/astra-motion/config/knowledge-sources.json`에 기계 판독 가능한 형태로 관리한다.

## 다음 우선순위

1. `REACTION_01`의 rigid head baseline과 limited mesh candidate를 같은 시간표로 렌더한다.
2. P0 geometry evidence를 자동 산출한다.
3. keyframe expected/actual/diff 검수 화면을 만든다.
4. neutral reassembly에 pixel exact와 SSIM 보조 검사를 연결한다.
5. 그 결과가 유의미할 때만 Blender background worker 또는 ARAP comparator를 검토한다.

## Safety Addendum

- Mesh geometry thresholds are engine-owned. A scene may request stricter values but cannot relax the Gold benchmark policy.
- Non-finite geometry metrics and thresholds are rejected before evaluation.
- Render containers set `HYPERFRAMES_NO_TELEMETRY=1` and `DO_NOT_TRACK=1`.
