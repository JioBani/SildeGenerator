# Scene 분석

각 scene에는 의미와 시각 방향만 제안한다.

- `source_unit_count`는 이 장면이 순서대로 소비할 source unit 개수다.
- narration, scene ID, sequence/group ID, parent keycut ID를 만들지 않는다.
- `cut_role`에는 keycut을 쓰지 않는다. keycut은 sequence의 `keycut_scene_number`로 선택한다.
- 원문과 ID, 상위 범위, narration은 런타임 컴파일러가 결정한다.
- role, purpose, viewer_takeaway, visual_summary, image_prompt를 구체적으로 작성한다.
- `scene_function`은 장면이 이야기에서 수행하는 동사형 기능이다.
- `layout`은 mode, focal_order, safe_area를 포함하며 시선이 이동할 순서를 명시한다.
- `object_states`는 움직일 대상의 시작 상태와 종료 상태를 object_id별로 선언한다.
- `motion`은 대상마다 의미가 있는 동작과 2개 이상의 단계(phases)를 선언한다.
- `transition`과 `rhythm`은 장면의 연결 방식과 읽기-움직임-정착 순서를 명시한다.
- `renderer_requirements`에는 preferred와 필요한 capability를 기록한다. 복합 안무는 hyperframes를 사용한다.
- 장식만을 위한 움직임은 만들지 말고, 최종 상태가 분명한 동작 뒤에는 settle 단계를 둔다.
- 이미지 안에는 글자나 로고를 넣지 않고 16:9 자막 안전 영역을 확보한다.
