# Keycut 선택

각 sequence에서 기존 scene 하나를 1부터 시작하는 `keycut_scene_number`로 선택하고 그 장면의 `keycut_dna`를 작성한다.

- scene ID, parent keycut ID 또는 `cut_role=keycut`을 직접 만들지 않는다.
- 전체 master keycut은 1부터 시작하는 `master_keycut_sequence_number`로 sequence 하나를 선택한다.
- `keycut_scene_number`는 반드시 해당 sequence에 실제로 제안한 scene 수 안에 있어야 한다.
- 범위를 벗어난 번호의 컴파일러 보정은 감독 설계 실패로 처리된다.
- keycut은 추가 장면이 아니며 기존 scene 중 하나다.
