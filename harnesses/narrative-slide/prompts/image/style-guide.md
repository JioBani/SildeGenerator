# 기본 스타일 가이드

- 정돈된 시네마틱 에디토리얼 일러스트레이션
- 차분한 네이비와 따뜻한 앰버 포인트 컬러
- 선명한 핵심 피사체와 절제된 배경
- 자연스러운 깊이감, 과도한 디테일과 시각적 혼잡 배제
- 장면 전환 때 색온도와 명암이 급격히 바뀌지 않게 구성
- 16:9 가로 프레임, 자막이 들어갈 하단 안전 영역 확보
# Cinematic camera contract / experimental 0.1.0

Use layout.camera={mode:hold|push|pull, focus:[x,y], strength:0..0.08}.
Focus coordinates are normalized within the final 16:9 crop. A camera move must have
a narrative target; never alternate directions just because the cut index changes.
Default to hold if a move is not motivated. For identical framing where only object
or facial state changes, assign the same nonempty layout.continuity_group to all
related cuts and use mode:hold on each. This prevents camera restart at a state change,
including when scenes render in separate segments. Protect the full face and essential
evidence at the maximum zoom; focus coordinates alone do not prove crop safety.
These are static illustration cuts, not automatic skeletal or facial animation.

The structured output schema includes camera, continuity_group and visual_labels.
Use null continuity_group when shots are not a matched-state group. Use [] for
visual_labels unless required by a renderer that actually displays those labels.
For cinematic-slide, use explicit camera objects with all three fields and select
cinematic-slide as renderer preference. Use cut/crossfade/dissolve transitions only.
Never emit match or wipe for this renderer. Camera motion does not animate the
character. Null camera means hold; missing fields in legacy stored plans stay valid.
