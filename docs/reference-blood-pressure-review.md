# Blood pressure explanation study V1

## Scope

Original vector 30-second study for Ab9OZsDECZw source 57-87 seconds. The preceding studied interval is source 6-57. Together they cover a continuous 81-second source interval, but are not yet approved for seamless visual continuity. No Core, provider, or production defaults changed. Paid calls 0; existing local GSAP/Chrome/FFmpeg path only. Docker Mock E2E remains unverified.

The source overview shows split heart/vessel, diastolic label, full vessel, systolic label and numerical range, diastolic range, combined reading, and transition to the body diagram. New independent SVG paths implement these roles. Timing and wave shape are hypotheses, not native-frame measurements.

## Technical checks

900 frames checked: no more than one pressure label visible, six required label states appear, wave geometry changes, slide panels remain adjacent, and the final body diagram/title are visible. Deliberately enabling a second label triggers the duplicate-label condition. This verifies event presence and layout, not physiological accuracy. All 18 out-of-order seek checkpoints pass.

## Content boundary

The displayed numerical ranges are source-study quotations, not endorsed medical advice. Current [American Heart Association guidance](https://www.heart.org/en/health-topics/high-blood-pressure/understanding-blood-pressure-readings) separates normal pressure as below 120 systolic and below 80 diastolic. A production explanation using a new script must undergo an independent fact review instead of inheriting the reference's range labels or treating 120/80 as a universal normal target.

## Reusable grammar candidate

Use a stable object to explain successive named states; show one label at a time. Preserve the visual subject across the comparison, then expand to the containing system. Transfer the structure, not the old medical numbers. Store content facts separately from visual grammar.

Review remains REVISE pending source-aligned geometry, typography, pulse timing, scene-boundary matching and audio. No human approval or automatic grammar promotion.

## Render regression and visual review

The first render exposed a heart shrinking between seek checkpoints: its initial SVG transform omitted scale while the tween target included it. Explicitly initializing scale(1) fixes the interpolation. The verifier now measures heart matrix scale on all first 150 frames, requiring at least 0.939; the fixed minimum is 0.940000057. The rejected 30-second and 81-second versions are preserved with rejected-scale filenames. Seek checkpoint success alone did not detect this defect.

The rebuilt 81-second study decodes successfully: 1920x1080, 30fps, 2430 frames. The rebuilt source/candidate comparison sheet still shows different heart geometry, smaller candidate typography, different pulse width/phase, less dense body circuitry and different body proportions. The transition is not source-aligned. These are visual REVISE findings, not solved by the technical pass. There is no audio track; rhythm and audio fidelity remain unverified. The continuous join is assembled, not approved as seamless.

Reusable safeguard: initialize all components of an animated transform explicitly and inspect extrema across rendered frames, not only selected seek checkpoints. This is a narrow implementation regression test, not automatic approval of the study's visual grammar.
