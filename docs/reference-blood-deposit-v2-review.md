# Deposit V2: visual coverage independent of identity

Research-only24s/720-frame independent vector candidate, source141-165s,1920x1080/30fps/silent. Paid calls0; no Core/provider/production default changes. Not Docker E2E or human approval.

## Implementation

V1 discarded touching circles from conservative identity tracks, causing visible particles to disappear. V2 renders per-frame fitted circles separately from temporal identity. Pool indices are explicitly unresolved, not stable actor IDs. Source-derived positions/radii/colors control independently drawn SVG circles, not copied source pixels.

Existing local OpenCV5.0.0 was used for distance-field peaks and connected components. No dependency was installed or added to the product runtime. Official API reference: https://docs.opencv.org/5.0/main_modules/imgproc_shape.html . This research script must have a reviewed dependency lock before product adoption.

Evidence: `.runtime/reference-study/blood-visible-shapes-v1.json`,456 observed frames, up to8 fitted circles. Radius/color/ROI thresholds are reviewed-scene assumptions, not general cell detection.

## Verification and limits

- Seven particle tests pass, including touching pair retention, yellow exclusion, color preservation and conservative tracking ambiguity.
- Random-order seek samples match; full MP4 decode passes.
- A/B atlocal22s/source163s now shows8 candidate circles, matching the8 visible source circles in that sample. V1 showed only5. This is a sampled correction, not proof of whole-video object counts.
- Wall wrapping and deposit-column geometry still differ; retained contact is NOT established.
- Sub-frame motion, merged-circle fits and edge entries can still jump. The render uses sampled positions, not a proven reusable interaction rig.
- Narration/audio remain absent. Visual verdict REVISE; no production promotion.

Artifacts: `blood-deposit-study-v2.mp4`, `blood-deposit-study-v2-ab.mp4` (source left), `blood-deposit-study-v2-comparison.png` under `.runtime/reference-study`.

Learning retained: uncertainty about identity must not silently remove visible geometry. Keep identity tracks, visible-shape observations and semantic contact approval as separate records.
