# 장면별 연속성 할당

각 장면에서 실제 등장하는 에셋은 present_asset_ids에 기록한다. 이미지 생성 시 정체성 보존에 실제로 필요한 에셋만 reference_asset_ids에 기록한다. 등장하지만 작거나 중요하지 않은 배경 요소는 present에는 포함해도 reference에서는 제외할 수 있다.

reference_asset_ids 기본 상한은 8개이고 0개가 정상이다. 선택된 continuity_assets의 ID만 사용하며 중복 ID를 넣지 않는다. reference의 모든 ID는 같은 장면의 present에도 있어야 한다. 직전 장면 이미지는 참조하지 않는다.
