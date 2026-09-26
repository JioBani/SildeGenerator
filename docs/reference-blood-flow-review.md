# Blood flow continuation study

Source: Ab9OZsDECZw, 27-57 seconds. Native frame evidence: 719 frames in
`.runtime/reference-study/blood-27-57/motion.json`. Source sampling retains original
timestamps; output uses 30 fps. No human approval or production promotion.

## Observed sequence and implementation

1. Continue the previous two-tank illustration for the first 0.7 seconds using the
   previous candidate's final frame, not an extracted source frame.
2. Enlarge oxygen, then reveal a field of transported constituents.
3. Change to a vessel cross-section with moving constituent symbols.
4. Remove constituents while introducing outward pressure arrows.
5. Add the blood-pressure label, then reveal a heart panel from the left.
6. Show contraction followed by the systolic-pressure label.

Timings are initial manually fitted observations from one-second and three-second
contact sheets, not exact frame-level boundary approval. Independent code-native
artwork uses the observed red/burgundy, pale lining and yellow-vector design roles.
Shapes are schematic; neither chemical structures nor heart anatomy are certified.

## Corrections and evidence

- Relative motion replaces an absolute x target which could reverse some particles.
- Four equal-topology wall keyframes move a periodic wave through the vessel instead
  of only oscillating between two stationary shapes. This is not a physical simulation.
- 55 particle transforms were inspected for 77 successive frame steps while visible;
  every horizontal delta is positive. Checks also confirm particle removal, pressure
  reveal and caption states at selected times.
- V1: all 19 first-seek/reverse-seek screenshot checkpoints pass exact hash comparison.
- Harness validation passes. These tests do not establish reference fidelity.
- Renderer and GSAP dependencies are reused locally. No provider calls or installs.

## Remaining differences

Constituent variety and placement, heart anatomy, typography, contraction-vector
details, precise wave timing and transitions need A/B refinement. Source audio has
not been recreated. The opening bridge is a held candidate frame, not a live
continuation of the earlier flow. This makes the 51-second combined study a review
artifact, not a finished continuous reconstruction. No universal director rule is
promoted from this experiment.

## Export and comparative review

Combined candidate `blood-continuous-51-v1.mp4` is 51.000 seconds, 1530 frames at
1920x1080/30 fps, and fully decodes. Source mapping is 6-57 seconds. Coverage is
unioned with earlier samples, never counted twice. The A/B sheet confirms correct
broad sequence but materially smaller constituent symbols, less shape variety,
a narrower heart panel, thinner lining, different wave amplitude and missing
cardiac contraction vectors. Verdict remains REVISE. The receipt preserves source
and candidate hashes and all technical evidence; no fidelity score is fabricated.

## V2 design refinement and regression

The gallery now has deliberately varied symbol sizes and asymmetric placement,
including additional dimer and branching shapes instead of repeated uniform cells.
The heart panel occupies half the screen. Vessel walls have a rounded lining and
a larger traveling-wave amplitude. Two yellow heart-to-vessel arrows appear during
the pressure explanation. These changes address specific V1/source A/B differences.

The flow-direction/state verifier still passes, but exact seek comparison regressed:
16 of 19 checkpoints pass; 26.5, 28 and the final frame differ. At time 28, the
comparison differs in 124 pixels around the heart edge. A DOM-state comparison
with the actual final-frame excursion reports no differences. Switching heart
scaling to explicit SVG transforms did not resolve it. The cause is not proven;
do not dismiss it as harmless or replace exact tests with a tolerance to get PASS.
Keep V1 available, V2 experimental and the determinism issue open. Source audio,
precise timing and full-film fidelity remain incomplete.
