# Actor Acting V3 Review

Status: technical checks passed; human design and acting review pending. Research only, not registered in the production service.

## Scope and changes

The eight-second silent comparison preserves the first three-second weight-shift shot. The five-second reaction shot changes gaze acquisition, face direction and overlapping expression/body timing. V1 and V2 are preserved.

The generated V2 head had a baked-in nose. One built-in image edit removed it; a separate authored nose now moves with the eyes, brows and mouth. The blank head has silhouette IoU 0.987272 against the previous head, which is registration evidence only, not proof of design identity. The face plane translates at most seven pixels and compresses horizontally by at most nine percent. This is a limited stylized turn, not reconstructed 3D geometry.

## Reaction hypothesis

All times below are local to the reaction shot, not the complete video.

| Channel | Interval in seconds |
| --- | --- |
| Image appears | 0.65 |
| Gaze acquires image | 0.78-0.90 |
| Notice | 0.94-1.18 |
| Head follows | 0.99-1.52 |
| Small smile | 1.15-1.65 |
| Torso follows | 1.30-1.96 |
| Settle | 3.70-4.80 |

These intervals are authored experimental values, not Gold values. The pupil step budget is explicitly four pixels per output frame for the faster eye movement; it is not the V1 two-pixel budget. Isolated head-only breathing was removed. The target is the actual illustration inside the monitor, checked in rendered coordinates.

## Reference evidence

Source: https://www.youtube.com/watch?v=bHB5iiDDJ-s

Existing local native-frame evidence: `.runtime/reference-study/bird-flu/reaction/frames`, source SHA-256 `957f4678239327abaf5d2079067d7802f178e923d3f67f10c449911d0a0029b6`.

Frames 90 and 91, approximately 179.72 and 179.76 seconds, show a rapid change from narrow/sly eyes to wide eyes with a small downturned mouth. The new expression is then held. This supports testing a quick readable state change instead of interpolating every expression slowly. It does not establish universal human reaction timings or validate this candidate's acting. Reference artwork is not included in delivery assets.

## Verification and review

The capture checks 240 rendered frames for planted feet and measures gaze against the rendered target. Eleven out-of-order screenshot comparisons match. The 390-pixel review layout has no horizontal overflow. Both delivered clips are independently checked for eight seconds, 240 frames, 1920x1080, 30fps and H.264. The receipt hashes actual files and current sources.

Human review must still establish: what attracted attention, whether looking precedes emotion, whether the smile reads as restrained satisfaction, whether face/head/torso coordination is natural, and whether the design survives the turn. A comparison against the still version tests readability; comparison against V2 tests the revision. No winner is assigned automatically.

## Reproduction and provenance

Run `node experiments/layered-motion/capture.mjs --acting-v3`, then `python experiments/layered-motion/verify_acting_delivery.py` from the repository root. Open `experiments/layered-motion/designed.html?acting=v3` for the interactive comparison.

Outputs: `output/layered-motion-acting-v3/animated.mp4`, `still.mp4`, `technical-report.json`, `rendered-traces.json`, and `review-receipt.json`.

Image edit mode: built-in reference-image edit. The source edit, exact prompt and registration result are `generated-blank-head.png`, `head-edit-prompt.txt` and `head-registration.json` in the same output folder. One built-in image call was added, two cumulatively. Separate paid image API calls: zero.

## Workflow implication

Keep design registration, performance timing, rendered geometry and human acting judgment as separate gates. Preserve the best approved version; record unsuccessful candidates without promoting them. This experiment provides a reusable measurement bench, not yet an automatically approved acting asset. General walking, grasping, finger acting, large head turns and mesh deformation remain outside scope.
