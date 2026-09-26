# Wall study V4: measured geometry versus artwork

Source Ab9OZsDECZw 132-141s. Independent vector study, 9 seconds, 270 frames, 1920x1080, 30fps, silent. Paid calls zero. Experimental local renderer only; no product/Docker E2E claim, Core or production defaults unchanged.

## Changes and failures preserved

- V3 closed short horizontal texture gaps. It removed small notches but also joined antialiased label pixels into a false wall bulge. V3 is rejected, not a better default.
- V4 retains only the mask connected to an image edge after horizontal closing. Floating text is removed; the broad traveling bulge remains in the sampled comparison. This is specific to these edge-to-edge vessel views, not a generic segmenter.
- Added rounded interior wall marks separately from outer bands and dashes.
- Split numeric and heading reveals. Reviewed ink detector reports numeric onset 136.678208s and heading onset 139.180708s. Threshold uncertainty remains; these are not authored keyframe times.
- Label detector V1 falsely detected particles as letters. V2 starts after the reviewed particle fade. Do not use this detector on arbitrary scenes.

## Evidence

- 216 geometry samples, `.runtime/reference-study/blood-wall-geometry-v4.json`.
- `blood-pressure-labels-v2.json`; V1 retained as rejected evidence.
- Four synthetic geometry tests pass, including patterned gaps, preserved broad bulge and disconnected orange marks.
- V4 random-order seek: 13 sample hashes match. Full MP4 decode passes.
- `blood-wall-study-v4-comparison.png`, local 7s/source139s: previously observed spikes absent; numeric-only state now agrees with source at this sample.
- `blood-wall-study-v4-ab.mp4`: source left, independent rendering right.

## Verdict

REVISE, human approval pending. Typeface weight/width, wall-band thickness and exact waveform profile still differ. Particle movement is hypothetical and source audio has not been reproduced. Single-frame improvement is not whole-video fidelity proof.

## Transferable research finding

Color threshold alone is insufficient for patterned geometry with overlaid labels. Require reviewed object topology, preserve the rejected track, and compare the rendered output. Edge connectivity is invalid for isolated objects or cropped vessel ends and must not be generalized automatically.

Example code is `harnesses/astra-motion/examples/blood-wall-study-v3/`; V4 uses its same artwork with the corrected V4 measurement track. No automatic capability promotion.
