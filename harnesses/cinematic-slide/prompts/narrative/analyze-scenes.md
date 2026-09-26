# Scene 분석

각 scene에는 의미와 시각 방향만 제안한다.

- `source_unit_count`는 이 장면이 순서대로 소비할 source unit 개수다.
- 모든 scene의 `source_unit_count` 합계는 story-intent에 제시된 source unit 총수와 정확히 같아야 한다.
- 장소, 시점, 화면 안/밖, 샷 크기 또는 이야기 기능이 바뀌는 unit은 한 장면에 억지로 합치지 않는다.
- 입력 unit이 남거나 초과하면 감독 설계 실패이므로 컴파일러 보정을 기대하지 않는다.
- narration, scene ID, sequence/group ID, parent keycut ID를 만들지 않는다.
- `cut_role`에는 keycut을 쓰지 않는다. keycut은 sequence의 `keycut_scene_number`로 선택한다.
- 원문과 ID, 상위 범위, narration은 런타임 컴파일러가 결정한다.
- role, purpose, viewer_takeaway, visual_summary, image_prompt를 구체적으로 작성한다.
- 이미지 안에는 글자나 로고를 넣지 않고 16:9 자막 안전 영역을 확보한다.
