# 배우 자산 기술 흡수 연구

확인일: 2026-09-25. 목적은 새로운 영상 생성이 아니라, 오픈소스의 저작·검증 구조를 Astra의 재사용 가능한 배우 규격으로 옮기는 것이다. 코드·가중치·모션 데이터·예제 원화의 권리를 서로 구분한다. 아래 라이선스 표시는 확인한 원문의 요약이지 제품 배포 전체에 대한 법률 판단이 아니다.

## 먼저 바로잡은 현재 상태

첨부 자료의 “D/C 원본이 없다”는 진단은 구 작업 폴더 기준이다. 정본 `D:/SildeGenerator`에는 C/D 영상, D 제작 프로그램, 5개 배우 레이어, 부분 승인 기록이 있다. [후보 장부](actor-assets/d-nightlight-candidate.json), [조립 검사](../experiments/light-pollution-story-asset-v1/E-actor-rig-study/source-assembly-audit.json)가 근거다. 레거시 `.runtime`의 도형 실험을 D 승인 근거로 섞지 않았다.

D의 사람 승인 범위는 C 대비 자연스러움과 목·의상 접합이다. 얼굴 반응에 관한 이전 피드백은 해당 장면의 시각적 증거이며, 독립 눈동자 리그·시선 정확도·팔·손·커튼·다른 구도·전이 승인은 아니다. 판정 일시나 검토 프레임 범위를 모르면 추정하여 채우지 않는다.

현재 D는 몸통에 두 팔이 그려진 컷아웃과 얼굴 상태 이미지의 부분 합성이다. 팔 뻗기 통 이미지와 분리 전완 시안은 잘림·광륜 때문에 제작 투입이 차단됐다. 오픈소스 설치만으로 가려진 원화나 검수된 손이 생기지는 않는다.

## 우선순위와 채택 판단

| 자료 | 직접 확인한 내용 | Astra에 가져올 구조 | 이번 처리와 한계 |
|---|---|---|---|
| [Inochi2D](https://github.com/Inochi2D/inochi2d) | 노드 부모 변환, 마스크 참조, 파라미터 범위·기본값. [법적 안내](https://github.com/Inochi2D/inochi2d/wiki/Legal-Info)는 BSD-2-Clause | 배우 정체성·부위·텍스처·제어값을 분리하고 참조 무결성 검사 | A: 구조 분석. 런타임/모델 원화 미도입 |
| [OpenToonz Plastic](https://github.com/opentoonz/opentoonz_docs/blob/master/source/create_animations_using_plastic_tool.rst) | 삼각 메시/골격, 각도 제한, 강성, stacking order. [본체 라이선스](https://github.com/opentoonz/opentoonz/blob/bf89db1667563fdebd5fee916cc48905956fde34/LICENSE.txt)는 3-clause BSD 형태 | 기준 자세, 관절 범위, 가림 순서 분리 | A: 제한값 검사. 메시 변형·IK 실행 미구현. 서드파티는 별도 |
| [MediaPipe Face](https://developers.google.com/edge/mediapipe/solutions/vision/face_landmarker), [Hand](https://developers.google.com/edge/mediapipe/solutions/vision/hand_landmarker) | 얼굴 52 blendshape 계수와 변환행렬, 손 21 지점 | 관측 좌표를 배우별 소수 의미 제어값으로 매핑 | A: 입력 규격 참고. 추론 실행·2D 스타일 배우 정확도 검증 안 함 |
| [SAM 2](https://github.com/facebookresearch/sam2#license) | 이미지/영상 프롬프트 기반 마스크. 공식 안내에 체크포인트·데모·학습 코드 Apache-2.0 명시, 일부 부속물 별도 | 원화의 마스크 초안과 수정 이력 | A: 분리 후보. 설치·가중치 다운로드·마스크 생성 안 함; 리깅/뒷면 복원 아님 |
| [CMU MoCap](https://mocap.cs.cmu.edu/) | 상용 제품 포함과 원자료 재판매를 구분. 손·발끝 잡음 및 손가락/엄지 미캡처 주의 | 동작 단계와 관절 순서의 측정 자료 | A: 공식 조건 확인. 데이터 시퀀스 분석은 아직 0건, 손가락 학습 근거로 사용 금지 |
| [Iki](https://github.com/zeikar/iki) | MIT, 역할 기반 자동 리거, JSON 형식·검증기·테스트 | 누락된 부위, 중복 ID, 잘못된 참조/수치 조기 거부 | B: 파일 단위 분석. 공식 호환 어댑터나 런타임 채택 아님 |
| [Godot Skeleton2D](https://docs.godotengine.org/en/stable/classes/class_skeleton2d.html) | Bone2D 계층과 rest 변환 API | 기준 자세와 실행 자세를 분리 | B: API 조사. 해당 버전의 IK 적용 스택은 별도 벤치 필요 |
| [DragonBonesJS](https://github.com/DragonBones/DragonBonesJS) | TypeScript/JavaScript 런타임 공개 | 골격·외형·슬롯·행동 재사용 비교 | B: 후속 파일 분석. 유지보수·현재 브라우저 호환성 미검증 |
| [MMPose](https://github.com/open-mmlab/mmpose) | 여러 신체 부위의 포즈 추정 도구와 모델 | 복잡한 자세 관측·좌표계 변환 | B: 모델/데이터별 권리와 스타일 그림의 오차부터 시험 |
| [PixiJS](https://github.com/pixijs/pixijs) | 2D GPU 렌더러 | 레이어·마스크·메시 재생 후보 | B: 이번에 GSAP/HyperFrames 교체하지 않음 |
| [Rive runtime](https://github.com/rive-app/rive-runtime/blob/main/LICENSE) | 런타임 MIT | 상태 전환/계층 갱신 비교 | B: 편집기·모델 원화까지 같은 권리라는 뜻 아님 |
| [Theatre.js](https://github.com/theatre-js/theatre#license) | core Apache-2.0, Studio AGPL-3.0 구분 | 저작 데이터와 실행 패키지 분리 | B: 편집기 포함은 별도 검토 |
| [Anime Segmentation](https://github.com/SkyTNT/anime-segmentation) | 캐릭터 전경 분리 도구 | 외곽 마스크 비교 | B: 관절 부품 분리와 다름. 모델/데이터 별도 확인 |
| [GRAB](https://grab.is.tue.mpg.de/) | 인체·물체 접촉 데이터, 이용 접근 절차 | 접촉점/유지 조건을 설계하는 참고 | C: 가입·약관 동의·다운로드 안 함; 실제 동작을 추출했다고 주장하지 않음 |
| [LaFAN1](https://github.com/ubisoft/ubisoft-laforge-animation-dataset) | README에 CC BY-NC-ND 4.0, 동작 보간 평가 설명 | 위치·회전·시간 오차를 따로 보는 평가 관점 | C: 데이터/코드 제품 반입 보류. 회사 내부 연구가 자동으로 비상업 이용이 되는 것은 아님 |
| [CartoonSegmentation](https://github.com/CartoonSegmentation/CartoonSegmentation) | 연구 데이터의 사용 범위 주의 문구 | 비교 연구 후보 | C: 권리가 불명확한 데이터·가중치는 제품 반입 보류. 모든 구성요소를 일괄 불법/금지라고 단정하지 않음 |

## 실제로 읽은 구현과 우리 규격의 대응

세 저장소는 아래 commit으로 고정하여 읽었다. 소개 글 확인과 코드 분석을 구분한다. 원본 코드와 예제 원화를 복사·배포하지 않았다.

| 소스 revision / 파일 | 관찰 | 이번 흡수 |
|---|---|---|
| Inochi2D `ba2b1413c68d9f7bf575fef790ba0c35715558db`, [nodes/package.d](https://github.com/Inochi2D/inochi2d/blob/ba2b1413c68d9f7bf575fef790ba0c35715558db/source/inochi2d/nodes/package.d) | 부모와 지역/전체 변환 분리 | `Part.parent`, 지역 피벗·기준 위치, 계층 순환 거부 |
| 같은 revision, [visual/mask.d](https://github.com/Inochi2D/inochi2d/blob/ba2b1413c68d9f7bf575fef790ba0c35715558db/source/inochi2d/nodes/visual/mask.d) | 마스크를 식별자로 참조하고 로드 후 해결 | `mask_part` 누락·순환 거부. 잘못된 마스크를 조용히 제거하지 않음 |
| 같은 revision, [param1d.d](https://github.com/Inochi2D/inochi2d/blob/ba2b1413c68d9f7bf575fef790ba0c35715558db/source/inochi2d/param/parameters/param1d.d) 및 [INP2](https://github.com/Inochi2D/inochi2d/blob/ba2b1413c68d9f7bf575fef790ba0c35715558db/tech-docs/inp2-puppet.md) | 범위/기본값/바인딩, Puppet·텍스처·확장 영역 분리 | `Control` 범위 검사, 원화 파일 해시와 배우 구조 분리. INP 파서 구현은 아님 |
| OpenToonz `bf89db1667563fdebd5fee916cc48905956fde34`, [plasticskeleton.h](https://github.com/opentoonz/opentoonz/blob/bf89db1667563fdebd5fee916cc48905956fde34/toonz/sources/include/ext/plasticskeleton.h), [plasticskeletondeformation.h](https://github.com/opentoonz/opentoonz/blob/bf89db1667563fdebd5fee916cc48905956fde34/toonz/sources/include/ext/plasticskeletondeformation.h) | 부모 정점/각도 범위와 변형 파라미터/stacking order 분리 | `Joint` 기준각·상하한, 별도 `draw_order`와 가림 제약 |
| Iki `19588298520a8362d7da4ee0cdd47c221585f35c`, [auto-rig.ts](https://github.com/zeikar/iki/blob/19588298520a8362d7da4ee0cdd47c221585f35c/packages/editor/src/auto-rig.ts) | 역할표와 필수 부위 검사. 해당 자동 리거는 양쪽 눈을 요구 | 요구되는 부위가 없으면 조기 거부. 측면인 D에 반대쪽 눈을 억지로 생성하지 않음 |
| 같은 revision, [types.ts](https://github.com/zeikar/iki/blob/19588298520a8362d7da4ee0cdd47c221585f35c/packages/format/src/types.ts), [validate.ts](https://github.com/zeikar/iki/blob/19588298520a8362d7da4ee0cdd47c221585f35c/packages/format/src/validate.ts), [검증 테스트](https://github.com/zeikar/iki/blob/19588298520a8362d7da4ee0cdd47c221585f35c/packages/format/__tests__/validate.test.ts) | 텍스처/제어값/부위 분리, 유한 수치 및 ID 참조 검증 | NaN/무한대, 중복 부위, 미지원 필드 거부 및 회귀 테스트 |

## 이번 연구용 규격

[ActorRig 모델](../experiments/actor-rig-research/rig_contract.py)에서 [JSON Schema](../experiments/actor-rig-research/actor-rig.schema.json)를 생성한다. 현 서비스에서는 이 모듈을 import하지 않는다.

```text
ActorRig (research-0.1)
  actor_id / style_id / allowed_shots
  canvas / coordinate_system
  parts: parent / texture hash / size / local pivot / rest transform / mask reference
  joints: associated part / min / rest / max
  controls: semantic kind / parts / range / default / DRAFT
  draw_order + occlusion pairs
  contacts: effector / local anchor / scene target / pixel tolerance
  actions: requirements / prerequisite / frame interval / retained contact / DRAFT
  provenance: file references and hashes
  production_ready: false (only allowed value)
```

- 좌표는 좌상단 원점, 오른쪽 X/아래 Y, 시계 방향 degree다. 부위 위치는 부모 지역 좌표이며 접촉 측정은 캔버스 좌표로 제출한다. 프레임 구간은 `[start,end)`다.
- 구조 검사와 파일 검사를 구분한다. 이 규격은 파일 해시의 문법만 검사하며 실제 파일 확인은 기존 `actor_assets.py` 후보 검사가 담당한다. synthetic fixture의 0 해시는 실제 증거가 아니다.
- 현재 계약에 메시를 넣으면 거부한다. 가중치·강성·IK chain·바인딩 실행·동적 draw order·리타게팅은 **후속 범위**다. 필드 선언만으로 구현됐다고 하지 않는다.
- 접촉 추적 검사는 유지 구간의 모든 프레임을 요구하며 손/목표 거리 초과와 누락을 검출한다. 제출 좌표가 실제 픽셀과 같은지는 별도 검증이며 자연스러움도 판정하지 않는다.
- `grasp`와 `pull`은 접촉 유지가 필요하고 `pull`은 같은 접촉을 가진 선행 `grasp`가 끝난 뒤여야 한다. CMU/GRAB에서 추출한 수치가 아니라 **우리가 작성한 검사 가설**이다.
- JSON 왕복과 같은 입력 해시는 검증한다. 영상 결정성·다른 운영체제 렌더 일치와는 다른 검사다.

## D에 적용하는 순서

1. 기존 D의 중립·인지·찡그림/최대 회전·정착과 목 접합을 정지 PNG로 저장한다. 같은 브라우저 세션에서 시간 재탐색 후 이미지 해시도 대조한다.
2. 승인된 목 가림 방식은 유지한다. “목 주변에 유연 메시 적용”은 바로 수용하지 않는다. 현재 문제를 다시 만들 위험이 있으며 필요성이 입증되지 않았다.
3. 몸통에 그려진 팔을 제거한 master torso, 상완, 전완, 손을 동일 원화 기준에서 저작한다. 기존 잘림/광륜 후보를 그대로 관절에 붙이지 않는다.
4. 중립 재조립, 관절 최소/최대, 접합 crop과 손 상태표를 통과시킨다. 머리 뒤/옷 아래 숨은 영역은 실제 필요한 변위만큼 저작한다.
5. 익명화한 자체 촬영 또는 권리가 확인된 동작 한 개로 준비→접근→접촉→유지 시간을 측정한다. 처음에는 손가락 상세 연기 대신 검수된 손 상태 교체를 사용한다.
6. 성숙한 2-bone IK 구현 후보를 격리 시험한다. 관절 길이, elbow 방향, 최대 도달거리, 접촉 유지 오차를 비교한 뒤 선택한다. 이번에 새 IK solver를 만들지 않는다.
7. D에 필요한 범위가 통과한 후에만 다른 대본/배우 전이를 수행한다. 다른 사람의 예제 puppet 라이선스를 확인하기 전에는 제품 배우로 넣지 않는다.

## 평가·권리·증거의 추가 보완

2x2 비교는 기존/개선 감독과 기존/새 실행의 효과를 나눈다. 대본·음성·길이·디자인 목표는 고정하되, **자산 개선 자체를 평가할 때 입력 자산까지 같다고 주장하면 모순**이다. 원화 identity를 고정하고 레이어/리그 패키지 변경을 독립 변수로 기록한다. 반복 비교는 버전명을 가리고 제시 순서를 섞는다. [NIST 실험 설계](https://www.itl.nist.gov/div898/handbook/pri/section3/pri3.htm)는 후속 평가 설계의 참고다.

VMAF/SSIM/좌표 오차는 기술 증거이며 의미·감정·행동 이해를 대신하지 않는다. 수치/사람 판정/사례 승인/자동 제작 승격을 별도 필드로 유지한다. 실제 예제 배우·모션 파일을 받을 때 작성자, 파일별 권리, 버전/해시, 허용 목적, 수정·배포 조건을 등록한다. 현재 외부 원화·가중치·모션 데이터는 반입하지 않았다.

남은 증거: D/C의 고정 대본·음성 타임코드 및 실제 렌더 환경 식별자 전체 묶음, 독립 팔·손/커튼 원화, 관절 극값 합성, 실제 픽셀 접촉 측정, 새 대본 전이, 사람 검수. 이 문서나 규격 통과는 이 항목들의 완료를 뜻하지 않는다.
