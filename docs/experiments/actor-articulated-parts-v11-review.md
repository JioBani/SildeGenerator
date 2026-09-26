# Generated articulated arm V11

V9's full-motion contact sheet exposed a translucent double arm during pose
crossfade. Reduced frame-difference spikes had not detected that defect.
V10 removed the pose image but its patterned stroke and torso clipping left
an awkward held silhouette. V10 is rejected as a visual candidate; its
stills remain evidence. Neither result qualifies as approved natural acting.

V11 uses a generated sheet containing three independent pieces: upper sleeve,
forearm sleeve and hand. The first sheet's internal ellipse lines made the
elbow look like an open tube. A built-in image edit removed those lines.
During composition the sleeve interiors are united and receive a single
outer contour, preventing duplicate joint borders. Source images remain
unaltered by the renderer. A forearm mask preserves front/back depth while
the upper sleeve joins behind the shirt.

The existing notice, gaze, smile, body and hand-to-chest timing is preserved.
The same pieces remain visible throughout the motion, with no held-pose
replacement or fractional-opacity blend. The source and edited sheet,
hashes, request descriptions and remaining approval state are recorded in
`output/layered-motion-arm-parts-v1/asset-provenance.json`.

## Evidence

- 8 seconds, 1920 x 1080, 30 fps; 240 frames; MP4/WebM decoded frames match.
- 960 rendered source-anchor measurements have a maximum error below
  0.0001 pixels. Visible sleeve group opacities stay at 1 in all frames.
- Feet, gaze and wrist placement pass the existing browser checks.
- The monitor is unchanged at 11 checkpoints. Face raster differences are
  limited to two antialiased pixels at 4.50 seconds, at most 8/255 per channel;
  this is not pixel-perfect face equality.
- The 4.7-7.8 second contact sheet has no double-arm crossfade ghost visible
  at its sampled frames. This is a scoped self-review, not human approval.
- Frame-difference values at 151/221 are slightly higher than V9 because
  the artwork changes. They are retained as evidence, not optimized as a
  substitute for visual quality.
- Two completed built-in image operations created/refined this family,
  one of them in the interrupted preceding turn. No separate paid API call.

Review: http://127.0.0.1:18771/?compare=articulated (randomized V9/V11).
Human questions: does the sleeve remain one object during the lift and return;
is the arm thickness consistent with the other arm; does the small gesture
read as satisfaction rather than a mechanical exercise?

## Lessons for the next asset request

1. Specify overlapping hidden joint regions and prohibit internal end-cap
   rings when parts must join into continuous clothing.
2. Keep object identity and geometry continuous through a motion. A dissolve
   between unmatched poses can leave ghosts even when numeric timing passes.
3. Compare rest, maximum bend and adjacent transition frames before a full
   render. Keep the human acting verdict separate from geometry checks.
4. Use a shared outer contour only when the pieces form one continuous
   material; hands, cuffs and separate garments retain their own outlines.

The TED-Ed timing/spacing and puppet sources in
`docs/teded-animation-craft-study.md` informed the separation of artwork,
performance and timing. This sheet and motion are original experiments;
no claim is made that TED-Ed's specific production rig has been reproduced.
Continuous source-video analysis is still pending in that research record.

## Human review update, 2026-09-24

Review d8c3265f-0020-4bde-91dc-0cedd155a84b is bound to the actual media
hashes in output/layered-motion-human-reviews. A is V9 and B is V11;
the reviewer preferred B and reported a sudden arm-size change in A.
In a subsequent clarification the reviewer said the face and gesture also
felt natural. This is positive evidence for this specific reaction, not
approval of the whole body or other actions.

The latest feedback on the V11/V12 timing comparison reports unnatural
legs, a mismatch between the spread stance and shoe direction, and an
unchanged-looking opposite arm. The shared lower-body construction needs
revision. Preserve the positive face evidence while withholding full-body
approval. See actor-stance-human-feedback.md for the scoped diagnosis.

V11 remains experimental. Do not promote REACTION_READY globally or optimize
the production workflow based on this single partially accepted gesture.
