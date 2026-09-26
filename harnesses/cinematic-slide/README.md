# cinematic-slide 0.5.0 (private experiment)

Fork of classic-slide 1.1.0. Scene layout.camera specifies hold/push/pull,
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
