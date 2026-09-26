# V9 silhouette proportions - REVISE

Measured initial upstream source silhouettes (six isolated components): median bounding size23x22.5px, filled area401.5px. V8 (six components) was18x16px/217px. V9 changes ellipse radii from10/7 to12/10.5 and updates its sampled wall-clearance shape; transport and timeline stay unchanged.

Rendered V9 measurement (five fully contained components in the same crop):22x22px, area390px. Sample membership differs; these are descriptive distribution summaries, not matching cell identities. Thresholding, compression and crop rejection affect results. Source pixels were not reused in the authored artwork.

All209frames rendered. Pairwise overlap checker now reads actual ellipse radii and rejects mixed sizes/rotations rather than silently assuming10/7. V9 reports zero overlaps across131,670pair-frame checks; minimum normalized distance2.12484; maximum y step1.19333canvas pixels. Initial screenshot inspected: silhouettes are rounder and closer in scale, but internal marks, spacing and wall texture still differ. Do not treat these limited checks as whole-scene approval.

Output: .runtime/reference-study/blood-bulge-study-v9/study.mp4. Design evidence: design-measurement.json in V8/V9 directories. No paid calls, source artwork copying or automatic production promotion.

## V8 evidence retained for context

The previous constant-median speed was not an adequate reconstruction of total motion. Source per-pair median displacements sum to 179.72475814819336px across 6.965292 seconds; a constant 20.09164px/s produces only about139.94px. Do not describe V7 as proven fidelity improvement merely because its speed was measured.

V8 integrates the 167 measured displacements into 168 cumulative points and linearly interpolates at output frame times. No velocity is fabricated for missing intervals: missing observations and time gaps are rejected. This preserves the measured aggregate transport, not individual cell identity, parallax or physical fluid behavior. The measurements are still ROI optical-flow estimates with accumulated error possible.

Three integration tests pass (unequal intervals, missing data rejection, gap rejection). Output rendered 209 frames; pairwise ellipse overlap is zero over131,670 checks; maximum y step1.2158966064453125 canvas pixels. Source/candidate PTS comparison covers209frames, maximum reference sample age0.041542seconds. Interpolation between source observations is authoring, not evidence of unseen source frames.

Output: .runtime/reference-study/blood-bulge-study-v8/study.mp4. Research-only side-by-side comparison: pts-comparison.mp4 in the same folder. Source imagery in that comparison is evidence only, not an independently authored delivery. New script/engine transfer and whole-video approval remain incomplete. No paid calls or automatic rule promotion.

## V7 record retained as a superseded hypothesis

Source flow: 167 consecutive pairs from 116.032583 to 122.997875. Median upstream feature velocity: +20.09164135739853 px/s, interquartile interval 19.447058437713217..32.56056490984392. Source SHA is 31d041c98dfe3c0f3cb55fc8c530180d545ba15af7756f65d88a158a2e2db75b. The previous authored speed was 170/(209/30)=24.401913875598087 px/s.

V7 changes only the transport speed to the observed median, preserving lane placement, shape and timeline. This does not reproduce variable source velocity, cell identities, density or deformation. Flow was measured only upstream at x70..240/y174..204 with dark-cell filtering, forward/backward consistency <0.5px and at least three features. Features are re-detected for every pair. Algorithm tests cover a known translation and blank-frame rejection; these do not alone validate every source match.

Source evidence: .runtime/reference-study/blood-bulge-study-v6/source-flow.json. Local output: .runtime/reference-study/blood-bulge-study-v7/study.mp4. Human quality review and whole-reference reproduction remain incomplete.

Verification: 209 frames rendered and full decode passed. Actual SVG transforms give zero overlaps across 131,670 pair-frame checks; maximum y step is 1.3043060302734375 canvas pixels. A 4-second screenshot was inspected for intact silhouettes and channel layout. This sparse view cannot validate continuous rhythm. No paid calls or production rule promotion.

## V6 evidence retained for context

Change from V5: replace modulo-generated positions with x=-190+i*24 while retaining 36 particles, three lanes, the same authored velocity, timing, wall contours and design. This prevents modulo wrap from placing several particles almost on top of one another. Spacing is authored, not a measurement of source trajectories.

The new checker reads actual SVG transforms after seeking every output frame. For aligned equal ellipses it evaluates center displacement in ellipse coordinates. Across 209 frames and 131,670 particle-pair checks, V5 has 5,643 overlap events; V6 has zero. Counts include offscreen particles and repeated pairs in different frames, not distinct biological collisions. Minimum normalized center distance is 2.762271737161436 (overlap threshold 2). The check assumes the current identical rx10/ry7/-40-degree ellipses; it must change if the design changes.

V6 maximum frame-to-frame y change is 1.725067138671875 source-canvas pixels, higher than V5. Zero overlap does not mean smoother motion or better source fidelity. Ten order-independent seeks pass; all 209 frames render and decode successfully. A screenshot at 4 seconds was visually inspected: accidental overlapping silhouettes are removed, but regular spacing, cell details and wall texture still differ from the source. Human quality approval remains absent.

Output: .runtime/reference-study/blood-bulge-study-v6/study.mp4 (6.966667s, 1920x1080, 30fps, silent). Evidence: spacing-review.json; previous V5 spacing-review.json provides the negative control. No paid calls or Core changes. Reuse this spacing diagnostic as an experimental check, not as automatic approval of anatomy or production grammar.

## V5 evidence retained for context

Current result: 209 frames rendered at 1920x1080, 30fps, 6.966667 seconds, silent. Full decode passed; ten order-independent seek comparisons passed. Two sampled center-column raster comparisons returned 1px error each. These checks do not establish whole-scene fidelity.

V4 replaced the conservative disk with a 360-point rotated ellipse and 1px margin. It still rejected 25 placements. Source frame 00272 at 122.330542 was inspected: cells occlude the bright-fluid measurement; isolated sample x320 begins at y195 while neighboring x310/x330 begin at y171. This is evidence of a measurement outlier, not anatomical closure.

V5 uses an explicit experimental spatial prior: if an inward edge differs by more than 6px from the median of its four neighbors, reconstruct that edge from the median. The original measured data remain unchanged. 71 samples across the track were inferred. This prior may erase a genuine narrow feature and is not eligible for automatic production promotion. Per-row changes are exposed as window.__contourCorrections.

All 7,524 particle placements were computed without the previous fit rejection. Maximum per-output-frame y change is 1.4885868874481787 source-canvas pixels at cell6/frame99, source119.327542. This is measurement, not a smoothness approval. Ellipse perimeter sampling is not a continuous collision proof.

Visual inspection at 4 seconds found particle pairs overlapping because the inherited modulo placement produces near-duplicate positions. Density, cell appearance and wall texture still differ from the source. Preserve REVISE. Next: replace accidental overlap with measured/explicit spacing and review continuous motion rather than only screenshots. No source trajectory fidelity or clinical validity is claimed.

Tests: test_bulge_particle_placement.cjs (V4 geometry), test_bulge_contour.cjs (unchanged flat support, isolated intrusion, original data preservation, broad narrowing). No paid calls; no Core/default renderer changes. Output: .runtime/reference-study/blood-bulge-study-v5/study.mp4.

## Prior V3 failure retained for context

Baseline: experimental V2, same 209 frames, design and wall timing. No provider calls or Core changes.

Attempt: replace fixed-height particles with normalized channel lanes. At each output frame, select the current measured contour, interpolate across its segments, and bound a particle using a conservative radius-10 disk plus 1px clearance across its horizontal extent. Explicit GSAP attribute sets support seek-based rendering.

Result: REJECTED_INPUT_GEOMETRY, not a completed video. First reported conflict: source second 121.204417, particle x=284.88995215311, allowed center y=193.22488038277504..193. The conservative disk may itself overconstrain an ellipse; this result does not prove anatomical closure or identify the true source contour.

The input is visible bright-fluid support, not an occlusion-resolved wall boundary. It is unsuitable for guaranteed particle containment without further evidence. Do not silently shrink particles, widen the wall or call this a passing motion study. Preserve V2 as the last rendered candidate, still REVISE.

Next evidence required: distinguish particle occlusion from wall shape over time; inspect contour outliers against actual source frames; use the actual rotated ellipse support rather than a disk if testing tight clearances. Only then retry the candidate. Source particle motion remains unmeasured and this lane policy remains an authoring hypothesis.

The local renderer now surfaces initialization page errors directly, rather than waiting 30 seconds and reporting only a missing timeline. This negative case terminated in approximately 1.8 seconds with its source time and coordinate. Docker preflight still fails because its daemon is unavailable; local tests are not Docker Mock E2E.

Positive regression: the unchanged V2 scene rendered all 209 frames successfully with the modified local renderer into `baseline-renderer-check.mp4` in the V3 research output directory. That file is explicitly a V2 baseline, not a successful V3 result. Harness validation passed for astra-motion@0.3.0.
