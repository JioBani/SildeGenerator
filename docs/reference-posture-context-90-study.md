# Posture context 90-106 study

Experimental independent assets, not approved reconstruction. No paid calls,
new dependencies, Core changes or production-rule promotion.

Native source evidence: `posture-alignment-90/motion.json`, source SHA
`47f6a63567ffd86e3d7cac3aeacfa5c8164f8b90ebab2b5c568af7c7f3504dfd`.
Inspected frames 88 (93.635208s), 223 (99.265833s), 328 (103.645208s)
and a sparse overview. These establish composition examples, not full motion
measurement. Hand action, intermediate transforms and easing remain hypotheses.

## Executable study

`harnesses/astra-motion/examples/posture-context-90-v1` contains the independent
SVG/GSAP study and a seven-part study contract. Four presentations cover the
missing window: transit ensemble, laptop use, three posture examples, frontal
figure. Runtime uses the existing pinned GSAP asset. It is a local render, not a
Docker Mock E2E; the last preflight found the Docker daemon unavailable.

First render exposed the final scene at time zero. Explicit initial GSAP states
fixed the zero-seek defect; all 16 sampled out-of-order seeks then matched. Keep
the rejected `posture-context-90-v1.mp4` as failure evidence. The usable technical
candidate is `posture-context-fixed.mp4`: 16s, 480 frames, 1920x1080, 30fps, silent.

PTS comparison `pts-comparison.mp4` contains 480 pairs, last-source-frame selection,
maximum sample age 0.041583s. Origin is 90.006583s, the first available native
frame; authored offsets use nominal 90s, so comparisons include a 0.006583s origin
offset rather than claiming exact cut alignment.

## Visual review

The comparison frames near source 96.97s and 101.94s show the intended single and
three-actor layouts, but the candidate has different head/leg proportions,
downward head orientation, scale and placement. The candidate's upright and bent
actors do not yet communicate the original pose contrast as precisely. Transit
composition is also only a rough independent interpretation. The third empty
tile in `review.png` is unused contact-sheet space, not a decoded black video
frame. Do not count this as design PASS.

Status: PARTIAL_STUDY_REVISE. Next: measure actor bounds/head angle and the 99s
layout transition; refine independent rigs; inspect the joined 60-120s sequence.
No human approval, full reference reproduction or completed transfer is claimed.

## V2 measured placement experiment

`measure_posture_layout.py` measures yellow-field foreground bounds after removing
components smaller than 12 pixels. Coordinates are normalized to 640x360. The
foreground includes chair, table, laptop and actor; it is NOT an anatomical mask.
Three unit tests cover known bounds with noise, non-yellow rejection and empty
field rejection. Five samples (94.5-98.5s) consistently gave source bounds
[182,36,384,293], V1 [213,41,365,279].

V2 changes the authored head angle from 46 to 20 degrees (a visual hypothesis,
not measured source rotation) and uses uniform scaling/translation. An initial
attempt [173,27,338,291] moved too far left and was rejected; its video and
measurement remain preserved. The centered candidate measures [207,36,367,293]
at all five samples: top/bottom match, horizontal center differs by 4px, but
width is still 42px too narrow. Edge absolute error sum drops 69 to 42px; this
is layout evidence only and cannot establish overall design improvement.

Output: `posture-context-90-v2/posture-context-centered.mp4`, with 480-frame
`pts-comparison.mp4`. Sixteen sampled out-of-order seeks pass. The 6.5s comparison
was visually inspected. Head silhouette, body proportions and leg/chair placement
remain visibly different. Status remains PARTIAL_STUDY_REVISE. V1 is retained;
no best-design approval is implied by this numerical improvement.

Process finding: separate placement (center/height), shape (width/proportions)
and performance (gaze/joints/timing). Nonuniformly stretching an actor to fit a
box would hide the remaining rig/design defect. Use this measurement as diagnostic
evidence, never as an automatic artistic acceptance gate.
