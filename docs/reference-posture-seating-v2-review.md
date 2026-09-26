# Posture seating V2

## Evidence and correction

The first native frame at approximately 162 seconds shows a slouched pose; the one-second overview had hidden the opening straightening. V2 restores a short slouch-to-upright action, but its exact duration is still a hypothesis.

A matched stable frame near 163 seconds supplies a flat-background foreground bounding box. At 1920px equivalent resolution the source box is [300,48,1152,951]. V1 is [547,147,1225,910]. The uniform height/top-left fit uses scale 1.183486 and translation [-347.367,-125.972]. V2 measures [300,48,1102,951]: left/top/bottom align, but width remains 50px short. This proves a framing improvement, not correct anatomy or silhouette. A first attempt at fitting the slouched source frame against an upright candidate was rejected as a pose mismatch.

Phone removal moves earlier; desk entry moves later; the face close-up occurs before upright return, then the camera reframes toward the hand. These choices come from one-second comparison and need native-frame timing refinement. Both close-ups have stronger magnification than V1. No Core or production defaults are changed.

## Verification

900-frame endpoint, settled-foot stability, eye-line target, hand visibility and deliberate-detachment checks pass. All 21 out-of-order seek points pass. Existing local GSAP/Chrome rendering only, no paid calls, no Docker Mock E2E claim.

## Process rule candidate

Compare matched object states before fitting a camera. Measure stable anchors or silhouette bounds, apply camera correction separately, then inspect residual shape errors. Do not compensate a wrong pose or limb proportion with camera scale. This remains a reviewed experiment, not an automatically promoted directing rule.

Overall status remains REVISE: character anatomy and expression differ, event timings are incompletely measured, and audio is absent. V1 remains preserved.

Encoded comparison was inspected after rendering: 1920x1080, 30fps, 900 frames, 30 seconds, full decode PASS. Stable wide framing improves, and the face view now shows a lean before the upright eye-line demonstration. Remaining differences are visible in the A/B sheet: thin elongated neck, smiling rather than weary face, different elbow curvature and foot placement, late completion of knee folding, and excessive right-side cropping of props in some close-ups. These require pose/prop corrections rather than declaring the bounding-box fit a visual PASS.
