# Blood vessel wall observation, 111-141s

Status: measured source evidence, NOT a reconstructed or approved scene.
Experimental astra-motion 0.3.0 research only. No Core, provider or production-default changes.
Paid calls: zero. Audio semantics remain unreviewed.

## Evidence

- Source: Ab9OZsDECZw, SHA256 `31d041c98dfe3c0f3cb55fc8c530180d545ba15af7756f65d88a158a2e2db75b`.
- `.runtime/reference-study/blood-wall-111/motion.json`: 719 decoded native frames, source PTS preserved.
- `blood-wall-source.png`: overview only. FFmpeg fps contact-sheet cells are NOT exact scene-boundary evidence.
- Exact requested 129s is still branching vessels; 134s shows the ELASTIC FIBERS wall callout.
- `blood-callout-measurement-v2.json`: 264 frames at 130.004875-140.974167s.
- Arrow tip x = 312.5-313 at analysis width 640. Measured nearest orange band gap = 1-10px; unresolved band frames = 0.
- Final decoded frame at 140.974167: tip (313,70), nearest orange band y=76. The arrow follows the changing wall vertically, rather than remaining fixed on screen.

The orange-band estimator is color/ROI-specific. It measures a rendered band, not anatomical boundaries. Pixel tolerances do not prove medical correctness, motion fidelity or human approval.

## Rejected measurement

V1 included cream title/number pixels as yellow arrow pixels. This produced 61 unresolved wall frames and a false final tip (292.5,156). Preserve V1 as rejected evidence; do not compile it into motion.
V2 adds a green-to-blue color-ratio condition; regression tests include cream-text rejection, absent arrow, missing wall and wrong frame size. Five tests pass.

## Next reproduction contract

1. Keep object identity through input insert, expanding vessel, branching network and return to vessel. Exact transition boundaries still need measurement.
2. In the 130-141s wall view, author vessel layers and particles independently. Do not move a crop of the whole image.
3. Anchor the callout to a named upper-wall feature. Preserve measured tip track separately from vessel geometry so attachment error can be compared to source, not simply declared zero by construction.
4. Compare rendered tip and wall positions at all 264 source timestamps. A DOM transform match alone is not sufficient; inspect raster output and A/B video.
5. Keep source pressure text as historical transcription in this reference study only. New-script medical claims require independent current verification.
6. Do not count these 30 seconds as reconstructed coverage until an actual candidate artifact and review exist.

Full-reference reconstruction, audio reproduction and new-script transfer remain incomplete.

## Native-frame bulge analysis, 116-123s

The previously unrendered 111-132 window was re-inspected. Native frames at
113.988875 (body diagram), 116.991875 (straight band and vertical insert),
119.994875 (localized wall bulge), 125.959167 (branch network), and
129.963167 (elastic-fiber callout) establish the ordering. Sparse contact-sheet
cells must not replace these timestamps; sample midpoints can mislead.

`measure_blood_bulge.py` analyzes 168 native frames at 116.032583-122.997875s.
It tracks continuous orange-band
support in nine-pixel-wide columns every ten pixels. Color/ROI constraints are
scene-specific; these are not anatomical surfaces or validated lumen boundaries.

V1 incorrectly included separated orange particle pixels at y210 in lower-band
extrema. V2 selects the longest continuous run (minimum four rows), rejects ties,
and preserves missing observations rather than interpolating. Five synthetic
tests cover band coordinates, particle contamination, cream rejection, ambiguous
ties and invalid resolution. V1 remains rejected evidence.

At x270, V2 band support changes from upper y127-137 / lower y237-247 at
116.032583 to upper y117-126 / lower y248-258 at 120.036583. This establishes
opposing outer-band movement. It does NOT establish inner lumen width, thickness
or a clinical mechanism. The 119.994875 native image visually shows inward wall
shape changes as well; those inner boundaries still need separate measurement.

Authoring must therefore separate outer contour, inner contour, wall-layer
thickness, insert position and particles. Merely translating an entire cropped
vessel can enlarge the passage when the source instead depicts local narrowing.
Do not generate the inner contour by assuming it is a fixed offset from this
outer color-band track. No new candidate video or production promotion is
claimed by this analysis.

Evidence: `.runtime/reference-study/blood-bulge-measurement-v1.json` (rejected)
and `blood-bulge-measurement-v2.json` (color-band evidence, partial).

## Independent bulge candidate and failed raster gate

V3 adds visible bright-fluid support between the wall bands. Absolute color
thresholds missed dim side regions (only 45 of 63 columns), so the first candidate
correctly failed its minimum-geometry check before rendering. V4 uses color ratios
with lower brightness thresholds; all columns were present in the inspected
samples. Eight synthetic tests include dim bands/fluid and internal particle
occlusion. Ratios remain specific to this source palette, not general segmentation.

At x320 the observed bright-fluid support changes from [163,212] at 116.032583
to [172,202] at 120.036583. This is visible color support, not an anatomical width.
The independently authored `blood-bulge-study-v1` renders 209 frames (6.966667s)
using separate outer-band and fluid-support paths, clip-masked original particles
and an independently drawn insert. Source timing samples are held, not extrapolated.
Lines between columns are an explicit authoring approximation.

Artifacts under `.runtime/reference-study/blood-bulge-study-v1`:
`study.mp4`, `pts-comparison.mp4`, `review.png`, `raster-review.json`.
Ten sampled out-of-order seeks passed; all 209 PTS comparison frames were generated
with maximum sample age 0.041542s. The 4s A/B frame was visually inspected.

The raster gate FAILED: candidate bright-fluid support at x320 was [166,208]
initially and [175,195] after narrowing. Direction is correct, but maximum edge
error is 7px, exceeding the declared 4px tolerance. Rendered scalloped strokes
and particle occlusion can reduce visible support beyond the path coordinates.
Do not loosen the threshold or claim geometry PASS from matching DOM paths.
Next isolate stroke/particle effects with diagnostic layers, then refine wall
striations, cell shapes/density and jitter. Status: PARTIAL_STUDY_REVISE.
The complete 111-132 sequence, full references, narration and transfer remain
outstanding. No paid calls or automatic production promotion.
