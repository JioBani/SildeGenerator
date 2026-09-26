# Changelog

## 0.1.0

- `classic-slide@1.2.0`에서 분리한 비공개 카메라 안정화 실험입니다.
- 장면 중간에 초점이 이동하던 좌우 왕복 수식을 고정 초점 수식으로 교체했습니다.
- 4배 작업 좌표계에서 `zoompan`을 계산해 1080p 정수 좌표 양자화에 따른 미세 떨림을 완화합니다.
- 대본, 이미지 생성, 음성, 자막, crossfade 계약은 변경하지 않습니다.

## 1.2.0

- 작업별 화면 비율과 자막 포함 여부를 렌더 계약으로 전달합니다.

## 1.1.0

- 장면 계획에서 런타임 ID와 교차참조 생성을 제거하고 결정론적 컴파일러 계약을 사용합니다.
- 모델은 중첩된 의미 구조와 장면 번호만 제안하며 source unit, hierarchy, keycut parent, continuity 참조는 Core가 생성합니다.

## 1.0.0

- 기존 24fps Ken Burns/crossfade/ASS 자막 렌더를 Core `media.py`에서 Harness로 이전했습니다.
- 임의 DAG의 subtitle/render/audio/assembly task로 실행됩니다.
