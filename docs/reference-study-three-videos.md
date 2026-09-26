# Three reference studies

## Delivered scope

The local source videos were acquired for analysis. Whole-video automated sampling:
365 frames (extreme heat), 869 (NVIDIA), 727 (questions), at one sample per second.
This is an overview, not a claim of complete manual shot-by-shot review.
Native-frame motion windows: 15-19s at 24fps (96 frames), 17-21s at 30fps (120),
18-22s at 24fps (96). `motion.json` preserves decoded source timestamps.
Global image difference and palette metrics do not recover object trajectories.
Observed trajectory/pose design remains manually interpreted in this experiment.

The candidate is an 18-second silent, 1920x1080/30fps study of three representative
mechanisms, using original generated art, not a recreation of all 33 minutes.
Experimental source: `harnesses/astra-motion/examples/three-reference-study/`.
Local evidence: `.runtime/reference-study/batch-three/`.

## Sources and extracted rules

1. https://www.youtube.com/watch?v=fLu080UX25o
   Hand-drawn irregular contours, quiet paper background, restrained field of
   action. A stationary exhausted adult contrasts with active children. Layer
   ordering changes when a child crosses behind/around the sofa. Source has
   multiple expressive poses; our generated runner poses still need improvement.
2. https://www.youtube.com/watch?v=1GowFTjbUnk
   Flat outlined characters and explanatory symbols. In the selected window,
   a chip shrinks to leave visual room, then brain/controller enter in sequence.
   Full boardroom acting and lead-in are not included in the candidate.
3. https://www.youtube.com/watch?v=7SWvDHvWXok
   Dark negative space, varied illustration, matched circular silhouette: sun
   dissolves to clock with continuing motion. Surface turbulence and motion blur
   remain unmatched. Center alignment is more important than adding a transition.

## Revisions and reusable findings

- Four built-in image tool calls: initial heat atlas, simplified atlas, technology
  atlas, alpha cutout edit. No separate paid image API requests. These calls still
  use the signed-in product's available allowance; no claim of unlimited free use.
- V1 failed visual compositing: multiply blend made the sofa show through skin;
  the off-white sprite background left rectangular edges. A transparency prompt
  alone was insufficient evidence. V2 uses RGBA cutouts with inspected alpha.
- V2 added geographically grounded Natural Earth land data. Public domain terms:
  https://www.naturalearthdata.com/about/terms-of-use/
  Data: https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_land.geojson
- Sequential rendering hid a seek-order problem in the character timeline.
  V3 explicitly initializes actor state and uses ordered keyframes. Eight
  sampled times are pixel-identical after forward/backward seeks.
- Playwright wait predicates must return a boolean, not a paused GSAP timeline.
  GSAP timelines are thenable, so returning one can await completion forever.
- Keep independent asset layers and align pose registration before animating.
  Never repair opaque background artifacts by making the actor itself translucent.

## Verification and promotion

HyperFrames strict render, rendered contact-sheet inspection, alpha inspection,
and Playwright seek-order checks provide technical evidence. The study contract
records per-scene remaining gaps. No automatic style or acting approval.
V3 emitted a nonblocking overlapping-GSAP-tweens warning for generated adult
background-position pose changes. Strict mode is not strict-all; this warning
must not be reported as an entirely clean lint run. The eight actual seek-order
checks passed, but broader frame coverage is still required.

Next completeness criteria: annotated object tracks throughout selected windows,
more source-faithful heat acting poses, independently timed A/B comparisons,
additional representative sections of each source, then transfer to another script.
Do not call the whole-reference reproduction complete before those checks.

## Reuse commands

`python scripts/analyze_motion_window.py INPUT.mp4 OUTPUT --start 15 --duration 4`

`node scripts/verify_reference_seek.mjs .runtime/reference-study/batch-three/reproduction`

The experimental profile is opt-in. No production renderer defaults were changed.
