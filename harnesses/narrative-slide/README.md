# narrative-slide 0.1.0 (development candidate)

Forked from cinematic-slide 0.6.0. The director emits a typed `layout.direction`
for every shot. Character stories expose goals, stakes, competing choices and
consequences. Observational essays retain a visual subject without inventing drama.
The real planning path automatically requests up to two repairs for missing
causes, unexplained state changes or unmotivated repeated shots. Final contract
errors stop asset work. All review attempts remain in the job asset ledger.

Shot size, viewpoint, visible action and focal target reach the image provider.
Camera hold/push/pull and outgoing cuts/dissolves execute in the inherited graph.
The automatic contract gate has no human-review dependency. It does not measure
rendered acting, emotional response or aesthetic quality; those evaluation layers
and hybrid routing are still on the development plan.

Validate with `python scripts/harness.py validate narrative-slide` and
`python -m unittest discover -s video-generator/tests -p test_narrative_direction.py`
with `video-generator` on PYTHONPATH. This candidate is not yet a public option.

Inherited rendering behavior: scene layout.camera specifies hold/push/pull,
focus [x,y] normalized in the final crop, and strength 0..0.08. Default is hold.
Explicit continuity_group requires hold on every member, including across segments.
Invalid camera intent is rejected, not silently replaced. Image geometry still needs
visual review. No rig, parallax or automatic acting approval is provided.
Public release awaits full-script, visual and service testing.

Within a rendered segment, scene.transition describes the outgoing boundary:
cut, crossfade and dissolve are supported. Other explicit transitions fail preflight.
Segment assembly concatenates segments. The optional segment planner keeps outgoing
dissolves within a segment and only splits at cuts (or when fade duration is zero).
Preferred chunk size is soft; the episode's existing 10-scene/60-second limits remain.

History/documentary layouts display an evidence-status label. `asset_origin=generated`
means an AI reconstruction. Other origins remain unverified, even if a planner claims
archival status. This is disclosure, not source authentication or historical review.

## Inherited baseline

기존 Slide Generator의 ASS 자막, center crop, Ken Burns, crossfade, segment/최종 조립 동작을 보존하는 기본 Creative Harness입니다.

- 기준 문서: [`AI_AGENT_GUIDE.md`](../../docs/creative-harness/AI_AGENT_GUIDE.md)
- 변경 시작: `scripts/harness clone classic-slide <new-id>`
- 검증: `scripts/harness validate classic-slide`, `scripts/harness test classic-slide`
- 이 복제본은 비공개 연구 모듈입니다. 기존 classic-slide만 공개 기본값입니다.
