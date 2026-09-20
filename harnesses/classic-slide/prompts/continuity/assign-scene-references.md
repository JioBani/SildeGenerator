# 장면별 연속성 참조 선택

각 continuity asset의 `reference_scene_numbers`에 실제 기준 이미지 참조가 필요한 전역 scene 번호만 기록한다.

- scene에 asset ID 목록을 작성하지 않는다.
- present 관계는 `appearing_scene_numbers`에서, reference 관계는 `reference_scene_numbers`에서 컴파일러가 생성한다.
- reference 번호는 반드시 appearing 번호의 부분집합으로 의도한다.
- keycut은 최대 8개, 일반 scene은 keycut 참조 자리를 제외하고 최대 7개만 컴파일러가 사용한다.
- 직전 장면 이미지는 참조하지 않는다.
