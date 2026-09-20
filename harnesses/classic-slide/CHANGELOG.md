# Changelog

## 1.1.0

- 장면 계획에서 런타임 ID와 교차참조 생성을 제거하고 결정론적 컴파일러 계약을 사용합니다.
- 모델은 중첩된 의미 구조와 장면 번호만 제안하며 source unit, hierarchy, keycut parent, continuity 참조는 Core가 생성합니다.

## 1.0.0

- 기존 24fps Ken Burns/crossfade/ASS 자막 렌더를 Core `media.py`에서 Harness로 이전했습니다.
- 임의 DAG의 subtitle/render/audio/assembly task로 실행됩니다.
