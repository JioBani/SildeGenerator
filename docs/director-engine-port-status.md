# 감독 엔진 포팅 상태

## 정본

감독 엔진과 제품의 정본은 `D:\SildeGenerator`다. 이전 `D:\ai영상자동화`는 검증 사례와 연구 자료를 읽어 오는 레퍼런스이며 새 기능을 개발하는 위치가 아니다.

## 이번 이식

| 레거시 자료 | 본체 위치 | 보강 내용 | 자동 제작 상태 |
|---|---|---|---|
| `nve_acting_review.py` | `video-generator/app/director_safety.py` | 현재 배우·리그·화풍·렌더·프레임 해시 결합, 사람 기준별 근거 요구 | 사람 승인 전 차단 |
| `nve_mesh_policy.py` | `video-generator/app/director_safety.py` | 명시적 opt-in, 목·어깨·몸통만 허용, 최대 변위 8%, 기준/후보 비교 | 실험 전용 |
| `nve_motion_asset_manifest.py` | `video-generator/app/motion_assets.py` | 외부 연구 저장소 의존 제거, source hash·권리·anchor·review 검증 | `MOTION_READY`까지만 자동 판정 |
| `nve_action_evidence.py` | capability별 계약 | `POINT` 전용 파일명 가정 제거, 동작·자산 쌍·접촉점·벤치마크 결합 | 일반화 금지 |

승인 기록과 감독 지식 후보는 각각 `director_capability_reviews`, `director_knowledge_candidates`에 내부 저장한다. 사용자 화면의 에피소드 구조는 유지하며 이 테이블은 노출하지 않는다.

## 현재 닫혀 있는 기능

- `limited_mesh`, `grasp_and_retain`: 사람 승인이 있어도 production에서 차단
- `theory_rule`: 후보 저장만 가능하며 자동 제작 규칙으로 사용하지 않음
- `actor_reaction`, `interaction_ready`, `hyperframes_scene`: 현재 계약에 묶인 사람 승인 없이는 차단
- `INTERACTION_READY`: 전역 자산 라벨로 자동 승격 불가
- Astra 모션 Harness: 기본값이 아니며 사용자가 `(실험)` 항목을 직접 선택해야 함

## 다음 개발 순서

1. `REACTION_01` rigid baseline과 limited mesh candidate를 같은 시간표로 제작한다.
2. 사람 검수 화면과 인증된 승인 API를 추가한다.
3. 승인 API가 증거 파일의 작업공간 경계와 SHA-256을 검증한 뒤 삽입 전용 기록을 남기게 한다.
4. Playwright keyframe diff와 neutral reassembly 이미지 검사를 연결한다.
5. 제한 메시와 `GRASP_AND_RETAIN`은 Gold 결과가 생긴 뒤에도 별도 기능 플래그로만 시험한다.
6. 충분한 서로 다른 작품·자산에서 재현성이 확인된 기능만 정책 버전을 올려 production 후보로 검토한다.

정책을 완화하는 작업은 config 값 변경만으로 할 수 없다. `director_safety.py`의 정책 버전, 회귀 테스트, 결정 문서를 함께 변경해야 한다.
