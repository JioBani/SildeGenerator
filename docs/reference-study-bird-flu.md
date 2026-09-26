# Bird flu reference study

## Scope and evidence

Reference: https://www.youtube.com/watch?v=bHB5iiDDJ-s

Title verified from source metadata: Everything you need to know about bird flu - Benjamin Anderson.
Original duration: approximately 389.734 seconds. Original frame rate is approximately 23.976 fps.
The current result is an **18-second silent representative reconstruction**, not the complete film, not a frame-identical copy, and not a human-approved Gold scene.

Evidence root: `.runtime/reference-study/bird-flu/`.
Whole-film overview: 390 one-second samples, 59 automatic boundary candidates. The older reviewed study contains 63 boundaries; these are different methods and must not be reported as matching counts.
Older observations were inspected read-only under `D:/ai영상자동화/platform_strategy/nve/research/2026-09-21/teded_bird_flu/`.

Three dynamic windows were inspected as frame sheets and retained at every decoded source frame:

| Window | Original seconds | Frames | Observation |
| --- | --- | --- | --- |
| Entry | 121.8-127.8 | 143 | Approach, contact pause, enclosure, cyan internal strands |
| Reaction | 176-182 | 144 | Stop at membrane, small facial change, held reaction, failed bounce |
| Contact | 256-262 | 144 | Approach, eyes close, arms meet, shared drift |

The third window does NOT include the full genetic exchange. Do not promote it as an exchange mechanism or general GRASP_AND_RETAIN validation.

## Manner and design interpretation

The source links a human-scale problem to an internal mechanism, then returns to real-world implications. The previous narrative map provides approximate spans: symptom mystery 0-65.6, history/classification 65.6-121.8, entry 121.8-133.5, spread 133.5-171, human receptor barrier 171-203.7, mutation 203.7-251, exchange 251-290.7, current risk 290.7-331.9, response 331.9-369.7, then credits.

The visually useful rules are hypotheses rather than universal theory:

- Stable body color and surface marker shape identify an agent across cuts.
- Warm organic surroundings separate from cool cyan agents.
- Eyes, eyebrows and mouth carry reaction while the body holds nearly still.
- Contact is an event with a pause, not merely overlapping two shapes.
- Paired movement preserves a shared contact point instead of independently tweening hands.

The reconstruction uses newly generated bitmap bodies, independently authored facial parts, constrained arm paths, and original tissue backgrounds. It does not use cropped source characters as final production assets.

## Revisions and operational lessons

1. The initial sprite generation included a background/glow. The edited result supplied an alpha image in the tool response, but its auto-saved file was empty. The returned image bytes were preserved locally, decoded unchanged, and visually inspected. A zero-byte auto-save is not a successful asset delivery.
2. The first sprite viewport exposed neighboring sprites because a general SVG overflow rule applied to nested viewports. Restrict clipping to the inner atlas viewport. Visual counting catches this when seek determinism alone does not.
3. Independent receptor movement detached markers from the membrane. Move the membrane and attached markers in the same coordinate system.
4. Translating a clipped membrane exposed its lower edge. Allow the extended membrane artwork to cover the viewport throughout its movement.
5. Scaling SVG eyes moved them incorrectly. Animate ellipse radius for closure instead of relying on ambiguous transform origins.
6. Chrome verification failed because C: was full. The retry used D: temporary storage without deleting user files.
7. HSV tracking found 130/143 and 133/144 candidates, but the opening human frame and cyan strands can be false detections. Keep missing values, confidence limitations and raw evidence. These tracks were NOT automatically converted to authoritative movement.

## Implementation and validation

Example code and contract: `harnesses/astra-motion/examples/bird-flu-study/`.
Runtime assets and assembled composition: `.runtime/reference-study/bird-flu/reproduction/`.
Renderer: pinned existing HyperFrames runtime in `slidegenerator-runner:working-tree`, GSAP, 1920x1080, 30fps, 18 seconds. Network disabled during rendering. No narration or music in this motion test.

v1-v3 rendered through HyperFrames. During final v4 output, Docker run and even Docker status stopped responding. Their local client processes were stopped; the service was not reset and user files were not deleted. v4 uses the same composition/timeline with `render_reference_local.mjs`, local Chrome frame capture and FFmpeg encoding. Do not label v4 as a completed HyperFrames render. The Docker service availability remains an operational issue outside this study.

`verify_reference_seek.mjs` now accepts a timeline ID and explicit image paths; default behavior is preserved for the prior three-reference benchmark.
`verify_bird_contact.mjs` measures shared hand endpoints for all 114 frames in the contact hold. This tests geometry only.
The reference/candidate comparison is a local review artifact. Do not distribute source excerpts as original assets or assume ownership of the source media.

## Remaining gaps and promotion criteria

- Background density, original camera tracking, organic enclosure deformation and facial proportions are approximate.
- The human-to-interior transition, full-film typography, narration, sound and later mechanism scenes remain unreconstructed.
- The final result requires human design/acting review and a second-script transfer test before promotion.
- Retain v1 for comparison; v2 fixes visual defects rather than silently overwriting the original.
- A/B inspection then found the contact pair too small. v3 increases the pair's shared scale while preserving its contact geometry. This is a framing correction, not a claim of full style equivalence.
- v3 seek review found 576 pixels differing by one color level at 12.2 seconds. Disabling GSAP automatic 3D layer promotion eliminated the mismatch; v4 passes all eight exact screenshot comparisons. Never relax an exact test silently to hide compositor differences.
- Separately paid image API calls: zero. Built-in image generation was used; this is not a guarantee about subscription limits.

Do not activate a universal automatic production rule from this single benchmark.
