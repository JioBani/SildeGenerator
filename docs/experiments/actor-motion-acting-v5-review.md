# Acting V5: Posture Across the Cut

## Viewer feedback and scope

The user described the facial reaction to the screen change as natural. The original text and its limits are recorded in `actor-reaction-user-feedback-2026-09-24.md`. This version preserves the stimulus, gaze, brow, head and smile event timings. It changes the posture under the face to repair the visible reset between the two cuts.

The feedback does not establish that the weight shift, body acting or overall video is finished.

## Change

At 2.967 seconds V4's pelvis was at approximately (26, -273.5), its torso at -2.7 degrees and its head at +1.7 degrees. At 3.0 seconds V4 reset them to (0, -278), 0 and 0 as the camera reframed the same room. V5 carries the last pose across the edit. The body releases that carried lean from 1.2 to 2.2 seconds within the second cut, after the result is visible. The feet stay planted.

The look, facial artwork, generated image sprites and video length are reused. No images or audio were generated for this revision. This is a continuity correction, not a new universal acting rule or proof of full-body naturalness.

## Evidence

- V5 MP4: `output/layered-motion-acting-v5/animated.mp4`, SHA-256 `b90d4b905be20017300aeaee0b9c2d740ca9479332987c6c16da412b83eaad64`.
- The old V4 MP4 remains `a9ff007e41de4bdefc948c88216ccf4472cf7013a883cf38fa541adcc7f77243`.
- `output/layered-motion-acting-v5/cut-boundary.png` shows rendered frames 89 and 90 side by side.
- `output/layered-motion-acting-v5/technical-report.json` records zero computed cut-pose error, stable feet, valid arm lengths and rendered eye direction.
- The still-mode V5 and V4 clips are byte-identical. WebM and MP4 decode to the same 240 frames.

The mathematical continuity test is about the actor pose, not identical pixel positions: the camera intentionally changes framing at the cut. The frame image confirms that the lean survives the reframe.

## Review status

Technical verification passed. The user's positive feedback applies to the previous facial reaction; the changed body pose in V5 has not yet been judged by the user. V5 is therefore a candidate, with no production promotion. The first weight shift still lacks a clear story motivation, and broader emotional/gesture performances remain untested.

Compare V4 and V5 at `http://127.0.0.1:18771/?compare=pose`. The separate original comparison remains at the root URL.

Reproduce the candidate from the repository root with `node experiments/layered-motion/verify-v5.cjs`, `node experiments/layered-motion/capture.mjs --acting-v5`, lossless WebM conversion, and `python experiments/layered-motion/verify_continuity_delivery.py`. The loopback viewer is `node experiments/layered-motion/serve-review.mjs`.
