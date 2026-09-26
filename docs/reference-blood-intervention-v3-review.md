# Intervention V3: source-frame timing and occlusion

## Scope

New experimental example, not a change to Core, production defaults, or approved actor capabilities. Reference window remains Ab9OZsDECZw 201-231 seconds. V1 and V2 retained. No paid APIs or new dependencies. Docker Mock E2E remains unverified; this is the existing local Chrome/GSAP renderer.

## Evidence-driven correction

The existing 719-frame analysis contains original source PTS. `measure_reference_balloon.py` examines 72 frames from 214.5 to 217.5 seconds with a manually chosen central strip. The first detector erroneously included disconnected red wall cells. The corrected detector follows only the accepted run connected to the balloon center; a synthetic regression test verifies this distinction. Both measurement reports are preserved.

Measured balloon height at 640px analysis resolution: baseline 35px, peak 126px, hold 117px. Expansion from the last baseline at 215.506958 to peak at 215.673792 takes approximately 0.167 seconds. V3 follows the observed height samples, including overshoot and settling, rather than assuming a one-second easing. All 72 sampled source PTS match the corresponding SVG height with zero numerical error. This does NOT measure complete silhouette or perceptual fidelity.

The deposit was incorrectly clipped to the lumen and then hidden under lining cells. It now extends into the outer wall bulge and is independent of the lumen clipping group. Inner lining cells sit on its visible boundary. The 15-second screenshot was inspected: cream deposits remain visible above and below the expanded balloon.

## Verification and boundaries

- 900-frame fixture checks pass for post-acquisition attachment, support entry alignment, retention, centerline contact and deliberate detachment detection.
- Return-flow checks retain at least ten visible moving particles at all four late checkpoints.
- Source-curve comparison covers 72 source PTS samples.
- Measurement unit tests cover disconnected lining, absent object and wrong resolution.
- Out-of-order seek verification includes the short expansion and deflation events.
- Human review, audio reconstruction and whole-reference reconstruction are incomplete.

Encoded result fully decodes: 30 seconds, 1920x1080, 30fps, 900 frames. All 27 out-of-order checkpoints pass. The encoded source-left/candidate-right sheet confirms restored deposit visibility. Overall review remains REVISE: source typography is narrower, wall bulge and cell proportions differ, and the implant silhouette is still schematic. Source geometry during the brief overshoot is not fully reconstructed; the centerline check at the hold must not be read as an all-frame surface-contact guarantee.

## Reusable process

Coarse temporal sampling locates an event; native-frame measurements define its timing. Store measured values separately from inferred semantics. A color detector must not treat disconnected background objects as the target. Verify output visibility as well as object coordinates: correct coordinates do not prevent clipping or occlusion errors.

The candidate grammar is rapid expansion, overshoot, hold and release. It is stored with conditions and counterexamples in the study contract, not automatically enabled as a universal rule. A different-script transfer must independently validate meaning and safe deformation amplitude.
