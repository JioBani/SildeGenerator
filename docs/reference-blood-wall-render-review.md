# Blood wall study V2

Research artifact, source 132-141s, 9s / 270 frames / 1920x1080 / 30fps. Silent.
Experimental astra-motion 0.3.0 example; local seek renderer, not Docker/product E2E.
Core, provider settings and automatic production capability gates unchanged. Paid calls: 0.

## Actual work

Independently authored vector layers use 216 native source wall samples and a separate measured callout track. Particles, labels and wall strokes are separately authored objects. Source pixels are not used as output artwork.

V1 rendered successfully but failed visual inspection: the color detector included text and repeating band gaps. The resulting wall had large spikes. V1 is preserved as rejected evidence.

V2 excludes yellow/cream labels by channel ratio, widens the spatial vote and uses a three-sample median. This substantially reduces spikes, but does not eliminate them. No fidelity approval is claimed.

## Verification

- Geometry measurement unit tests: 3 pass (outer edges, absent band, yellow exclusion).
- V2 random-order seeking: 13 samples produce matching hashes.
- Full V2 MP4 decode: pass.
- Visual A/B at local 7s/source 139s: REVISE.

## Remaining differences

1. Two isolated notches remain in flat wall regions. The detector still confuses patterned wall artwork with geometric contour. Fit a reviewed continuous wall model or use a connected band mask; do not keep increasing smoothing until the discrepancy is hidden.
2. The rounded inner wall decoration is missing. Current parallel strokes and dashes are not design-equivalent.
3. Typography is heavier and the hypertension heading is visible when the source sample shows only the numeric label. Measure label event boundaries rather than guessing fades.
4. Particle velocities and disappearance are authored hypotheses, not source tracks.
5. No narration, sound or medical claim verification is included.

Artifacts in `.runtime/reference-study`: `blood-wall-study-v2.mp4`, `blood-wall-study-v2-ab.mp4` (source left), `blood-wall-study-v2-comparison.png`, `blood-wall-geometry-v2.json`.

Learning: matching sampled geometry and passing deterministic seeking cannot establish visual fidelity. Preserve a separate raster A/B gate, and reject measurement contamination before promoting motion grammar. Full-reference and new-script goals remain unfinished.
