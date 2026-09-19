# Keycut 선택
각 sequence에서 기존 scene 정확히 하나를 keycut으로 지정한다. 추가 scene을 만들지 않는다.
keycut에는 keycut_dna를 작성하고 parent_keycut_scene_id를 null로 둔다.
다른 모든 scene은 같은 sequence의 keycut scene ID를 parent_keycut_scene_id로 지정한다.
master_keycut_scene_id는 sequence keycut 중 thesis를 가장 잘 대표하는 하나다.
