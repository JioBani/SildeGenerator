# V3 containment experiment - rejected initialization

Baseline: experimental V2, same 209 frames, design and wall timing. No provider calls or Core changes.

Attempt: replace fixed-height particles with normalized channel lanes. At each output frame, select the current measured contour, interpolate across its segments, and bound a particle using a conservative radius-10 disk plus 1px clearance across its horizontal extent. Explicit GSAP attribute sets support seek-based rendering.

Result: REJECTED_INPUT_GEOMETRY, not a completed video. First reported conflict: source second 121.204417, particle x=284.88995215311, allowed center y=193.22488038277504..193. The conservative disk may itself overconstrain an ellipse; this result does not prove anatomical closure or identify the true source contour.

The input is visible bright-fluid support, not an occlusion-resolved wall boundary. It is unsuitable for guaranteed particle containment without further evidence. Do not silently shrink particles, widen the wall or call this a passing motion study. Preserve V2 as the last rendered candidate, still REVISE.

Next evidence required: distinguish particle occlusion from wall shape over time; inspect contour outliers against actual source frames; use the actual rotated ellipse support rather than a disk if testing tight clearances. Only then retry the candidate. Source particle motion remains unmeasured and this lane policy remains an authoring hypothesis.

The local renderer now surfaces initialization page errors directly, rather than waiting 30 seconds and reporting only a missing timeline. This negative case terminated in approximately 1.8 seconds with its source time and coordinate. Docker preflight still fails because its daemon is unavailable; local tests are not Docker Mock E2E.

Positive regression: the unchanged V2 scene rendered all 209 frames successfully with the modified local renderer into `baseline-renderer-check.mp4` in the V3 research output directory. That file is explicitly a V2 baseline, not a successful V3 result. Harness validation passed for astra-motion@0.3.0.
