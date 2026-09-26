# Actor motion V1: authored layers and causal reaction

## Outcome and scope

Date: 2026-09-24. Offline experiment under `experiments/layered-motion/`.
This is an eight-second original actor study, not a completed generalized actor engine or a human-approved Gold asset.

The experiment produces a 3-second weight transfer and a 5-second stimulus/reaction shot. A still-actor baseline preserves the same camera cuts and screen stimulus. Source TED-Ed artwork is not in either deliverable.

## Source evidence

Two existing local source windows were re-inspected as contact sheets:

- Bird flu, 176-182 seconds: the agent approaches a membrane, pauses, changes facial expression, then moves again. The hold lets the small face change carry information.
- Good posture, approximately 178-184 seconds: slouch and upright poses differ in eye opening and mouth shape; the source also changes camera scale. It is not evidence that posture universally predicts emotion.

Exact source hashes and URLs are in `contract.json`. Contact sheets are at `tmp/reaction-reference-sheet.jpg` and `tmp/posture-reference-sheet.jpg`. These sparse sheets support state/order observations, not native-frame onset measurements. Existing source frame sequences remain available for finer analysis. The lab's numerical onset times are authoring hypotheses.

Official timing/spacing lesson: https://ed.ted.com/lessons/animation-basics-the-art-of-timing-and-spacing-ted-ed

## Implementation

The actor, room and monitor result were drawn as original SVG artwork. This tests the user's proposed authored-asset path without separate image API calls. The design is a new candidate, not the previously approved generated-image design.

The body uses fixed-length two-segment constraints and planted ankle endpoints. Pelvis translation, torso counter-rotation and delayed head response establish weight transfer. A small pelvis-height asymmetry keeps the support leg straighter than the relaxed leg. Contact shadows track the intended support distribution; this is an authored cue, not a physical force simulation.

The reaction uses a visible stimulus, then gaze acquisition, brows, head, mouth and torso channels. The pupil direction is calculated relative to a world-space target and compensated for head rotation. Eye opening and mouth curvature change continuously. One blink occurs during the hold; a late settle reduces the head angle and smile slightly.

GSAP 3.14.2 provides the spacing curve. All states are derived from absolute time, supporting out-of-order seek. The design renderer and performance sampler are separate files. This is a browser/FFmpeg lab renderer, not a newly registered HyperFrames Harness or an OpenToonz/Blender integration.

## Observed failure and correction

1. Initial numerical geometry passed, but the rendered neutral actor looked crouched with bent-out elbows.
2. Rounded trouser stroke ends protruded below the shoes.
3. The hip height, pelvis tilt and wrist locations were revised; a hem clip now keeps the trousers behind the shoes.

This is direct evidence that bone-length tests alone cannot establish a plausible silhouette. Preserve both a geometry gate and an actual rendered-image review.

## Evidence and limits

- All output frames are sampled for bone length, planted feet, support proxy and bounded trajectory steps.
- Browser checks measure rendered foot coordinates and compare exact image hashes after reverse-order seeking.
- Neutral actor parts export as transparent SVG and PNG layers and are recomposed for a pixel-difference check.
- A 390px-wide review screen tests scene selection, still/animated selection and horizontal overflow.
- MP4 verification checks actual duration, frame rate and dimensions separately.

Technical reports live with the output, with source hashes. These checks do not measure emotional readability, appeal, joint seam quality during motion or generalization to other designs.

Measured in this revision: both MP4s are 8.000 seconds, 1920x1080, 30fps, 240 frames, H.264, intentionally silent. Rendered foot drift is 0px across each shot. Eleven out-of-order screenshot comparisons match exactly. Fourteen neutral RGBA parts recompose with mean absolute RGB error 0.0000645 (0-255 channel range); one pixel differs by more than 8 levels. The 390px review viewport has no horizontal overflow. These are narrow technical results, not a natural-acting pass.

Human design/acting approval remains PENDING. No `ACTOR_MOTION_READY`, `REACTION_READY` or production eligibility is granted.

## Next development

1. Compare the animated and still clips without narration. Review whether gaze direction and quiet satisfaction read clearly at normal size.
2. Tune one variable at a time: pose, gaze displacement, head lag or smile magnitude. Keep the best reviewed candidate.
3. Test the same acting contract on a master-conditioned raster actor family; reject identity or neutral-reconstruction drift before animation.
4. Compare an authored OpenToonz/Blender rig where rigid layers cannot maintain the silhouette.
5. Only after naturalness is demonstrated, turn the successful preparation, asset reuse, measurement and review steps into the experimental workflow adapter.

No changes were made to the production worker, service UI, authentication, queues, database or image provider settings.
