# Frontal stance and supporting arm V13

Date: 2026-09-24. Isolated experiment, no production integration.

## Reason for revision

The user found the face/gesture natural but rejected the legs and the
unchanged-looking opposite arm. The prior feet used right-facing side-view
sprites under a frontal stance. Two-dimensional IK bent the knees sideways;
passing limb-length and planted-foot tests did not validate the drawing.

V11 is the baseline. V12's delayed gesture has no human preference verdict,
so V13 does not adopt it. Baseline video files and receipts are preserved.

## Changes

- Built-in image generation produced one transparent sheet with two
  front-view ivory shoes in the existing painted/teal-outline design.
  The original sheet is preserved. SVG clipping selects the sprites;
  uniform scaling, not shearing, places them under the trouser hems.
- Hip, ankles, torso, face, gaze, right-hand performance and camera timing
  are unchanged. The knees now bend primarily in depth. The rig retains
  two 131-unit bones per leg and projects depth with an authored factor
  of 0.22. A small outward pole factor of 0.12 avoids lateral buckling.
  These are experimental drawing parameters, not measured biomechanics.
- The supporting left arm has a new near-hanging rest pose, delayed
  shoulder following and a small change in elbow flex as weight transfers.
  It uses mirrored generated upper-sleeve/forearm parts instead of the
  old stroke-material arm. The existing left-hand sprite remains.
- No repeated idle oscillation, walking, planted-foot pivot or new emotion
  was added. This is one reaction and one small planted weight shift.

## Verification

The candidate is 8 seconds, 1920 x 1080, 30 fps, 240 frames, silent.
MP4 and lossless WebM have identical decoded YUV frames.

- Model-space leg length error: below 0.000001 units.
- Maximum knee lateral displacement from hip/ankle midpoint: 2.762 pixels.
- Maximum consecutive knee/supporting-hand position step: 1.027 pixels.
- Rendered foot drift: 0 pixels within each camera shot.
- 960 left and 960 right arm anchor samples: error below 0.001 pixels.
- Gaze direction error: below 0.001 degrees.
- Eleven reverse-order seek checks are deterministic.
- Face crops at eleven checkpoints are unchanged except one pixel with
  channel delta 1 at 2.90s and two antialiased pixels with maximum channel
  delta 8/255 at 4.50s. Monitor crops are unchanged.
- V11/V12 motion tests still pass. Desktop and mobile review playback,
  distinct version mapping, download records, seeking and codec fallbacks
  pass. Synthetic UI answers are not human approval.

Self-review of the 12-frame stance sheet shows consistent frontal shoes,
stable contact and less lateral knee kinking. It does not establish the
subjective naturalness of the new weight shift. The legs can still read as
restrained because the trousers conceal small depth bends. The supporting
arm still requires human evaluation of its silhouette and relaxation.

## Reusable lesson, not automatic promotion

Asset view must be compatible with the body's projected action. A side-view
shoe cannot be turned into a front view merely by rotating its image.
Record view, contact surface, joint anchors and intended motion together
before rendering. Test rest, maximum displacement and settled poses before
the full clip. Retain separate technical and human-acting verdicts.

The existing TED-Ed timing observations informed the preserved sequence of
perception, reaction and hold; no new TED-Ed gait or stance measurements
were made here. Do not describe these authored knee parameters as derived
from that source.

## Artifacts and review

- Comparison: http://127.0.0.1:18771/?compare=stance (randomized V11/V13).
- Candidate: output/layered-motion-acting-v13/animated.mp4.
- Evidence: technical-report.json, review-receipt.json, rendered-traces.json
  and stance-contact-sheet.png in the same candidate directory.
- Original generated artwork: output/layered-motion-stance-v13/front-shoes.png.
- Exact prompt: output/layered-motion-stance-v13/generation-prompt.txt.
- Asset origin/cost: output/layered-motion-stance-v13/asset-provenance.json.

This revision used one completed built-in image operation and zero separate
paid API calls. Candidate human review is pending. No REACTION_READY,
walking/general rig capability or production eligibility is granted.
