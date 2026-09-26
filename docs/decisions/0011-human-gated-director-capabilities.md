# 0011. 사람 검수형 감독 기능 격리

## 상태

채택. 2026-09-21.

## 결정

다음 기능은 자동 제작 능력으로 간주하지 않는다.

- 인물 반응 연기
- 제한적 메시 변형
- `GRASP_AND_RETAIN`
- `INTERACTION_READY`
- 장면별 HyperFrames 승격
- 영화 이론·사용자 피드백의 제작 규칙 승격

이 기능은 `director_safety.py`의 명시적 capability 계약을 거친다. 기본값은 거부이며, 모델이 만든 장면 계획이나 자산 manifest 안의 승인 문구는 승인으로 인정하지 않는다. 승인 기록은 현재 자산·리그·화풍·렌더·프레임 또는 규칙 출처를 canonical SHA-256으로 묶으며, 입력이 하나라도 바뀌면 재검수가 필요하다.

`limited_mesh`, `grasp_and_retain`은 현재 `experiment_only`, `theory_rule`은 `candidate_only`다. 사람 검수 기록이 있어도 자동 제작에는 진입하지 않는다. `actor_reaction`, `interaction_ready`, `hyperframes_scene`은 사람 승인 뒤에도 현재 제작 버전에만 유효하며 전역 자산 또는 보편 규칙으로 승격되지 않는다.

## 보안 경계

- 승인자는 `human`만 허용한다.
- 승인과 증거는 모델 출력과 별도 저장한다.
- 증거 파일은 허용된 작업공간 안의 절대 경로와 SHA-256이 모두 맞아야 한다.
- 메시 변형은 목·어깨·몸통과 최대 변위 8%로 제한한다.
- HyperFrames 작업은 허용된 operation 목록만 사용한다.
- `INTERACTION_READY`는 제작 버전 범위 승인이지 영구 자산 등급이 아니다.
- 감독 지식은 `candidate`, `project_approved`, `rejected`만 저장한다. 자동 보편 규칙 상태는 두지 않는다.

## 본체 정본

이 결정 이후 감독 엔진의 정본 개발 위치는 이 저장소다. 이전 Astra 폴더는 자료와 검증 사례를 가져오는 읽기 전용 레퍼런스로 취급한다. 새 계약, Harness, 검수, 저장 구조와 사용자 기능은 `D:\SildeGenerator`에서 구현하고 검증한다.

## 남은 제한

사람 검수 입력 API와 검수 화면은 아직 제공하지 않는다. 따라서 격리된 기능은 현재 자동 제작에서 닫혀 있다. 이 상태는 누락이 아니라 의도적인 보안 기본값이다.
