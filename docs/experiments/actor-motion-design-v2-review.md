# Designed actor V2: generated art on the existing performance

Date: 2026-09-24. Lab-only review candidate, not production or Gold approval.

## Question

Can an image-generated design family retain independently controlled body motion and facial expression without moving the whole original picture or duplicating painted faces?

## Actual experiment

1. Draw a 4x4 atlas layout from the existing actor contract. Fourteen occupied slots describe the head base, torso, upper sleeves, forearms, hands, thighs, calves and shoes.
2. Use the built-in image tool once to apply a restrained painted texture. The input fixes layout, colors and silhouettes and deliberately omits eyes, brows and mouth.
3. Keep the untouched generated atlas and exact prompt in `output/layered-motion-design-v2/`.
4. Check real alpha, slot boundaries, scale drift and silhouette overlap. Register each generated part's bounds to the authored local coordinates. This is explicit scale/placement registration, not evidence that the generator respected exact geometry.
5. Render head, torso, hands and feet as registered bitmap parts. Keep eyes, brows and mouth independently animated as authored vector features.
6. Extract generated cloth interior for the arms and legs. Attach it to each bone inside continuous authored limb contours. Using complete outlined capsules at every joint would introduce double outlines. This is a hybrid design/rig path, not a general mesh-deformation solution.
7. Keep all performance timings and trajectories identical to V1. Produce animated/still clips at 1080p, 30fps, 8 seconds.

## Failures that changed implementation

- The generator widened several parts. Minimum raw silhouette IoU was about 0.771. Directly using atlas coordinates would have altered limb thickness and joint placement.
- Bounds registration raised minimum silhouette IoU to about 0.969. The accepted registration-scale interval is explicitly inclusive [0.8, 1.2]; one thigh is at 0.8. A future asset outside it is rejected rather than silently expanding the limit.
- Initial cloth tiling produced rectangular repetition seams. The failed frame is retained as `rejected-texture-repeat.png`. Centered, oversized texture tiles removed those visible repetitions in the inspected frame.
- An intermediate pattern-origin change exposed half the dark limb outline. Giving the pattern an explicit viewBox fixed the coordinate mismatch. Image review caught this; endpoint tests did not.

## What the result proves

Generated art can be bound to this specific actor's fixed geometry and motion channels. Face animation remains editable because the generated base excludes the animated facial features. Changing the design does not require regenerating every frame.

It does not prove natural acting, a universal emotion model, exact identity preservation across arbitrary generated actors, or general cloth/mesh simulation. The room and monitor illustration remain authored vectors. Human design/acting review is pending.

## Evidence and costs

- `sprite-manifest.json`: parts, bounds registration, source hash, review state.
- `registration-evidence.json`: raw and registered mask overlap for each part.
- `technical-report.json`: browser seek, rendered feet, mobile controls and source hashes.
- `review-receipt.json`: actual MP4 metadata/hashes and equal-performance A/B check.
- `generation-prompt.txt`: exact image-edit specification.

One built-in image-generation call; zero separate paid image API calls. The tool may use the account's included limits; this is not a claim of unlimited free generation.

## Workflow implications, pending acting acceptance

The useful unit to reuse is a versioned actor family: silhouette/anchors, designed sprites, facial parts and semantic performance tracks. Neutral reconstruction and moving-joint inspection belong between generation and rendering. Atlas registration and texture binding can be replayed locally. No automatic production integration or efficiency-driven skipping of acting review is enabled.

Next acting work remains the gaze/head relationship and emotional readability at normal viewing size, then a second emotional intention with the same design. OpenToonz/Blender comparisons remain pending.
