# Keycut 선택

각 sequence에서 기존 scene 하나를 1부터 시작하는 `keycut_scene_number`로 선택하고 그 장면의 `keycut_dna`를 작성한다.

- scene ID, parent keycut ID 또는 `cut_role=keycut`을 직접 만들지 않는다.
- 전체 master keycut은 1부터 시작하는 `master_keycut_sequence_number`로 sequence 하나를 선택한다.
- 번호가 실제 범위를 벗어나더라도 컴파일러가 안전하게 범위 안으로 정규화한다.
- keycut은 추가 장면이 아니며 기존 scene 중 하나다.
