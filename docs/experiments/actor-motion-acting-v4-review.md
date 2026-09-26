# Acting V4: Arm Follow-Through Candidate

Status: rendered and technically checked; human naturalness review pending. Production registration and approval remain disabled.

## Finding and hypothesis

Inspection of V3 showed that the hand positions were constant in torso-local coordinates and that generated hand sprites were always upright. Consequently the arms inherited the torso movement without a separate trailing response. This is a specific mechanical limitation; it does not by itself prove that viewers find the shot unnatural.

V4 preserves the V3 head, eyes, facial timing, torso, pelvis, feet, stimulus, camera and design. Only the arms/hands change: the left wrist follows the old hand trajectory 0.10 seconds later and the right 0.14 seconds later. The shoulder still follows the original body. Two-bone constraints solve the elbow, and each hand rotates by the forearm's change from its neutral angle. There is no new idle oscillation, image generation, physical dynamics simulation or shoulder deformation.

The asymmetric delays are experimental authored values, not measurements extracted from TED-Ed and not a universal acting rule. The hypothesis is that a small trailing response reduces rigid attachment without distracting from noticing the image. A tie or preference for V3 is a valid rejection of V4.

## Reference boundary

The earlier TED-Ed native-frame expression evidence remains documented in `actor-motion-acting-v3-review.md`. It concerns quick expression-state changes, not arm timing. This revision does not claim to have measured arm follow-through in that reference.

Additional primary instructional source: [Animation Mentor, Follow-through and Overlapping Action](https://www.animationmentor.com/blog/follow-through-and-overlapping-action-the-12-basic-principles-of-animation/). It describes delayed responses to a primary action and cautions that secondary motion should be proportionate. Its principle motivates this experiment; it does not validate our output or provide the chosen numerical delays.

## Measured result

| Check | Result |
| --- | --- |
| Final video | 8 seconds, 240 frames, 1920x1080, 30fps, H.264, silent |
| Maximum wrist rotation from neutral | 3.5934 degrees |
| Maximum wrist rotation per frame | 0.5632 degrees |
| Maximum hand displacement from V3 | 7.1355 pixels in actor coordinates |
| Closest arm reach margin | 2.7516 pixels before full extension |
| Rendered wrist samples | 480, two wrists across 240 frames |
| Rendered wrist attachment error | 0 pixels |
| Rendered planted-foot drift | 0 pixels |
| Out-of-order screenshot matches | 11 |
| Additional image / paid API calls | 0 / 0 |

V3's MP4 hash is rechecked against its saved receipt and remains unchanged. V4's still clip is byte-identical to V3's still clip. Full-render eye direction checks still pass. None of these measurements prove natural acting or emotional clarity.

## Human comparison

Open `experiments/layered-motion/review.html` directly. It displays V3 and V4 under randomized A/B labels without revealing which is newer. Both videos keep their full scene context. The form asks what emotion/action each communicates, then asks which is more natural, allowing ties and rejection of both. It does not tell the reviewer what emotion they should perceive.

Downloads contain the chosen labels, version mapping, actual video hashes, answers and playback coverage. Seeking does not count as watching. Less than 90 percent playback coverage for either clip yields a draft. Completed viewing is not approval: `production_approval` and `automatic_promotion` remain false in all cases. A knowledgeable reviewer could inspect file URLs; this is casual presentation blinding, not a security boundary or a scientific controlled trial. The two HTML media elements are started together but are not frame-locked; use the deterministic renderer for frame-level measurements.

Synthetic browser tests exercise both playback, download, draft handling and a 390px layout. These results are stored under `output/layered-motion-acting-v4/ui-tests/` and explicitly are not human opinions. No human verdict has been collected by these tests.

## Reproduction

```powershell
node experiments/layered-motion/verify-v4.cjs
node experiments/layered-motion/capture.mjs --acting-v4
python experiments/layered-motion/verify_overlap_delivery.py
node experiments/layered-motion/test-review.mjs
```

Current assets and GSAP are reused. No production worker, Docker service or credentials are changed. Docker bootstrap read-only checks passed with occupied-port warnings; production Mock E2E was not rerun for this isolated static lab.

## Next decision

Do not automatically replace V3 with V4. Collect an actual comparison verdict before tuning another small variation. If the arms are still perceived as rigid, first examine the shoulder silhouette and body pose; adding more hand lag without a clear perceived defect is not justified. Full shoulder deformation, fingers, walking, grasping, other emotions and broad workflow promotion are not established by this experiment.
