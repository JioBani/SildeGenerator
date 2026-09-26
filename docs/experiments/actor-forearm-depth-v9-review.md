# Forearm depth V9: isolated acting experiment

The V3/V4 human review reported no meaningful difference in the perceived
computer-result reaction. V8 added a designed hand-to-chest gesture, but its
whole-arm front/back switch was visible on frames 151 and 221. V9 keeps the
V8 performance and generated bent-arm pose; only the forearm crossing the
shirt is composited in front of the torso during the transition. The original
arm stays behind the torso. This is a depth-continuity experiment, not a new
acting approval.

## Evidence

- 8 seconds, 1920 x 1080, 30 fps, 240 frames. MP4 and WebM decode to the
  same frames. No separate paid API call or new built-in image call.
- Feet, gaze, wrist position and angle stay within the V8 technical contract.
  The face and monitor are unchanged at the 11 sampled checkpoints, except
  for one face raster pixel at 2.90 seconds.
- Mean grayscale difference in the actor crop at the two former layer-switch
  frames drops from 8.32 to 6.73 (151) and 5.95 to 4.19 (221). These numbers
  measure discontinuity, not acting quality.
- V8 and V9 at 5.20 seconds both show open space between the bent arm and
  torso. It is not a newly introduced clipping line. The prior V9 rectangular
  mask did create a hard line, so it was replaced with the torso silhouette.
- Source and media hashes, frame count, codec and browser comparison are
  checked by `experiments/layered-motion/verify_depth_delivery.py` and
  `experiments/layered-motion/test-review.mjs`.

Review URL: http://127.0.0.1:18771/?compare=depth

The page randomly labels V8/V9 as A/B and records the viewer's description,
preference and any unnatural timestamp. Human naturalness/design review is
pending. V9 remains in the isolated experiment and is **not production
eligible**. Preserve the better prior candidate if the human review finds no
benefit or a worse silhouette.

Next study question: does the regional forearm compositing read as one arm in
motion, or does the transition still call attention to the layered cutout?
