# Cute character continuity probe

Two GPU script excerpts, 10 seconds, 1920x1080, 30fps, silent.
This does not represent the full source script. No production readiness claim.

## Actual execution

The fixture invokes classic-slide 1.1.0's existing subtitle and render_segment
functions using a local process adapter. It does not exercise the server/queue or
providers. One built-in image edit created a neutral counterpart to the existing
pleased character. The resulting illustration preserves the room layout well enough
for a state-change test; this is not a rigged reaction.

## Finding and revision

V1 used 2% per-cut zoom and 0.3 second dissolve. At 5.15 seconds the face, window,
lamp and monitor visibly doubled. Camera restart is unsuitable for this matched
state pair: outgoing and incoming framing differ despite similar source geometry.

V2 retains the same assets/captions/timing, but locks the camera across both cuts.
The dissolve midpoint no longer visibly doubles the room geometry; screen contents
and the mouth still blend by design. This is an improvement in matched-state
continuity, not evidence of perception preceding emotional response.

## Reusable scope

For matched-state shots, preserve camera transform through the state change or hold
the camera. Do NOT globally disable cinematic moves or dissolves: a spatial reveal
or intentional change of shot scale has different requirements. A future scene
contract should identify continuity groups and enforce shared transforms inside them.
This rule is now implemented in private cinematic-slide 0.1.0 through explicit
layout.camera and continuity_group. It is not yet automatically selected by the
public production route. Human acting review, other shot scales and cross-script
transfer remain. V3 uses the new harness, with the same source illustrations.

Evidence: output/cinematic-continuity-v1 and v2 contain videos, sampled frames and
receipts with source/video hashes. No application provider calls were made.

## Local graph delivery validation

`scripts/smoke_cinematic_delivery.py` executes the registry-loaded cinematic harness
through HarnessContext and GraphExecutor, including subtitle, render, audio and video
assembly tasks. Offline Windows SAPI narration is measured before rendering.
`output/cinematic-delivery-smoke-v1/delivery/cinematic.mp4` is 10.931565 seconds,
1920x1080, 30fps, H.264/AAC. The receipt records task IDs, harness hashes, measured
duration and output hash. Paid API calls: zero. Human approval remains false.

Core now invokes optional provider-free harness plan validation before registering
asset jobs. Cinematic scene/asset budgets and measured 60-second pre-render checks
match other episode harnesses. Camera, preflight, contracts and SDK tests: 19 passed
plus 7 subtests. This is not a Docker/HTTP/queue test or arbitrary-script style proof.
