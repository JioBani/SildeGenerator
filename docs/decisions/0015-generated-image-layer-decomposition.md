# 0015. Generated Image Layer Decomposition

## Decision

AI가 만든 한 장의 장면을 그대로 확대하거나 흔드는 대신, 감독이 움직임의 의미가 있는 객체만 고르고 다음 산출물을 만든다.

1. normalized `region_hint`
2. 객체 마스크와 전체 화면 RGBA 레이어
3. 객체가 제거된 clean plate
4. 객체별 motion contract
5. 기술 지표와 사람 검수 상태가 포함된 layer manifest

현재 로컬 기준 구현은 OpenCV GrabCut과 TELEA inpainting이다. 유료 호출이 없고 설치 크기가 작아 실패 양상과 계약을 검증하는 기준선으로 사용한다.

## Promotion Gate

- `technical_ready`: 마스크 면적, 연결 성분, 화면 경계 접촉 검사를 통과했다.
- `review_status=HUMAN_PENDING`: 경계, 정체성, 가림 관계, clean plate 흔적을 사람이 확인해야 한다.
- `production_ready=true`: 사람 승인 기록이 있을 때만 렌더러가 실제 레이어와 clean plate를 사용한다.

모델이 출력한 승인 문구는 `production_ready` 근거가 될 수 없다.

## Rendering Rules

- 분리 레이어와 clean plate는 같은 픽셀 좌표계를 유지한다.
- 공유 카메라 리그가 생기기 전에는 배경만 독립적으로 확대하거나 이동하지 않는다.
- 실제 이미지 레이어의 이동량은 도형 오버레이보다 작게 제한한다.
- 실패하거나 미승인인 분해 결과는 기존 장면 렌더로 안전하게 내려간다.

## Scope

이 계약은 배, 빙판, 인물 전체, 소품처럼 하나의 실루엣을 움직이는 단계다. 눈·입·팔·손·관절·접촉은 actor rig와 interaction gate의 책임이며 자동 승격하지 않는다.

## Upgrade Path

- text/box grounding: Grounded SAM 2
- mask refinement and video tracking: SAM 2
- large-hole clean plate: LaMa or an approved image-editing provider

새 도구는 현재 manifest와 사람 승인 게이트를 그대로 구현하는 adapter로만 도입한다.

## First Evidence

`scene-008`의 인물을 분리한 결과 마스크는 한 개 연결 성분, 화면 면적 4.14%, 프레임 비접촉으로 기술 검사를 통과했다. OpenCV clean plate에는 큰 객체 제거 흔적이 남아 사람 검수는 통과하지 못했다. 일회성 proof에서는 작은 수평 이동이 실제 RGBA 인물에 적용되는 것을 확인했으며, 자동 제작 승격은 보류했다.
