# Designed reaction gesture V8

Date: 2026-09-24. Isolated study in `experiments/layered-motion` only. No production renderer or service route was changed.

## Question

Can the already-liked notice-and-smile face reaction gain a readable body action without losing the design identity or reproducing the shoulder attachment problem?

The [TED-Ed timing and spacing lesson](https://ed.ted.com/lessons/animation-basics-the-art-of-timing-and-spacing-ted-ed) supports treating frame-to-frame spacing as an animation craft choice, not using a universal easing formula. Its page does not provide measured timing for this actor; all numeric timings here are authored hypotheses. The [TED-Ed puppet lesson](https://ed.ted.com/lessons/making-a-ted-ed-lesson-animating-zombies-with-puppets) explicitly uses stiff puppet movement for zombies, which is a counterexample rather than a target for this human reaction.

## Attempt and rejection

V7 raised the existing fist with the two-bone IK arm. Bone lengths and velocity passed, but the elbow flared into a wing-like silhouette. Re-aiming the hand did not remove that failure. `output/layered-motion-acting-v7/rejected-first-pose.mp4` is retained as failed evidence, not a deliverable. This demonstrates why passing joint geometry alone cannot authorize a naturalness claim.

## V8 candidate

V8 changes only the reaction's right arm after the image has been noticed. The hand moves toward the chest, holds, then returns. It keeps V6's shoulder depth at rest, existing face and gaze tracks, feet, original monitor image, and scene timing. Near the held pose, it blends to one coherent bent-arm illustration rather than exposing the seams between two cylindrical sleeve segments.

The source is `output/layered-motion-arm-pose-v1/bent-right-arm.png`, created with the built-in image tool from the existing generated atlas and the V8 frame as references. It has a genuine alpha channel. The selected image is stored in the workspace; an unselected second trial remains outside the project and is not referenced. Two additional built-in image calls were used in this study. Separate paid image/API calls: zero.

Selected asset prompt: "Create one isolated 2D animation sprite on a genuinely transparent background. It is ONLY the bent RIGHT ARM of the same front-facing cartoon character shown in the references, from shoulder to hand. Preserve the teal sweater fabric texture, restrained dark teal ink contour thickness, and warm light-orange skin exactly in the reference art style. Pose: shoulder at upper left, upper arm down-right to outer elbow, forearm bends left across the chest, ending with a small relaxed fist at lower left. One seamless illustration, no torso, head, second arm, background, or text."

## Evidence and limits

- `output/layered-motion-acting-v8/technical-report.json`: deterministic frame checks, planted feet, gaze direction, wrist placement, source hashes, no paid API calls.
- `output/layered-motion-acting-v8/review-receipt.json`: 8 seconds, 240 frames, 1920x1080, identical MP4/WebM decoded frames; monitor unchanged at 11 checkpoints. One face-region raster pixel differs at the 6.20-second screenshot, so pixel-perfect face equality is not claimed.
- `output/layered-motion-acting-v8/entry-contact-sheet.png` and `exit-contact-sheet.png`: six adjacent frames around each arm depth switch. The switch is visible and needs human motion review.
- The generated pose sprite is a held key pose. It is not independently joint-rigged. Crossfading to it is not a general solution for walking, pointing, or contact.

Review at `http://127.0.0.1:18771/?compare=gesture` against V6. Ask whether the new action reads as a natural reaction, whether the elbow/shoulder still pops, and whether the character remains the same person. A reviewer choosing V8 for one scene would not establish general `REACTION_READY`; the result must stay experimental until verified across other scripts and poses. No workflow optimization or automatic promotion follows from these technical checks.
