# Posture bending reconstruction study

## Scope

Experimental example under astra-motion 0.3.0; no Core or default production path
changes. Source: OyK0oE5rwFY, 48-60 seconds. Output: 12 seconds, 1920x1080, 30 fps,
silent original SVG artwork animated with the existing paused GSAP timeline.
No source artwork, logo or soundtrack is embedded in the standalone candidate.
Paid provider calls: zero.

## Implementation

- Source-observed palette and elongated shape language are represented in an
  independently authored figure with head, neck, torso, arms, phone and legs.
- The phone and hand share one transform. Arm endpoint and hand position use the
  same duration and easing. Head and neck endpoint interpolate together.
- The arm lowers before the torso completes its bend. Camera withdrawal follows,
  revealing the whole stance; fixed actor-space feet are unaffected by camera motion.
- This is spline deformation with fixed topology, not a validated IK skeleton or
  a production-ready full-body actor. Source timing remains an initial visual fit.

## Evidence and failure

The first geometry pass found an 8-pixel neck/head gap caused by the neutral neck
endpoint being five actor-space pixels away from the head origin. Fixing that
coordinate reduced maximum gap over all 360 frames to less than 0.001 pixels.
Hand gap and actor-space foot drift are also below 0.001 pixels. The verifier
deliberately detaches the hand after the normal pass and confirms it can detect
that failure. These measurements prove geometric attachment only, not acting quality.

Eleven first-seek/reverse-seek screenshot checkpoints pass exact hash comparison.
Harness validation passes. The general Harness SDK test command cannot collect
tests in the current Python environment because `pydantic` is missing. No SDK test
pass or Docker integration pass is claimed; no runtime dependency was installed.

## Review criteria

Compare the source and candidate at matching times for silhouette, face proportions,
arm length, torso curvature, camera scale, lowering timing and readable intention.
The legs now bend without moving the feet, but physical weight shift is not validated;
the face remains static, and no sound has
been reconstructed. Hold human approval and production promotion pending fidelity
review. Do not substitute attachment-test success for reference reproduction.

## Reuse boundary

Preserve this as a benchmark for coupled endpoints and camera-independent support.
The timings and pose paths are project-specific hypotheses, not universal acting
rules. A later transfer script must demonstrate a different action context before
this can be claimed as reusable director experience.

## V2 to V3 visual revision

The first A/B contact sheet showed that the candidate's opening figure was too
small and too central, the lowered phone stopped too high, and the rear arm missed
the source's raised elbow silhouette. V3 increases the close-up scale from 1.6 to
2.3, shifts the closing wide view rightward, enlarges the head, neutralizes the
smile, lowers the phone near foot height, raises the rear elbow and bends the leg
curves while preserving their endpoints. All 360 attachment measurements still
pass and all eleven seek checkpoints remain exact. This is a visual revision,
not proof of exact source fidelity or anatomical correctness.

Final V3 side-by-side review: opening scale and final placement are closer than V2;
the candidate still has a more angular face, different elbow/torso geometry, no
eyelid acting, and a premature rear-elbow lift. Treat the source-mapped 12 seconds
as partial study coverage, not approved fidelity. The export decoded successfully.
Source audio, whole-film coverage, and a different-script transfer remain incomplete.
