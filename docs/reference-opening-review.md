# Opening reconstruction evidence

Status: partial study; no human Gold approval and no automatic production promotion.
Source time is in seconds. Source frames are observations, not reusable production artwork.

## Posture: OyK0oE5rwFY, 0-30 seconds

Native sampling: 720 frames in `.runtime/reference-study/posture-opening-0`.

| Source interval | Observed action | Function and reconstruction requirement |
|---|---|---|
| 0-approximately 5 | Publisher identity | Account for separately; do not reproduce the publisher logo as our identity |
| approximately 6-10.844 | Extreme face/mouth close-up at table | Establish everyday behavior through facial action rather than an abstract posture chart |
| 10.844-12.596 | Long table, slouching man versus upright woman | Spatial comparison; retain relative scale and eyelines |
| 12.596-14.556 | Upright woman's close-up | Reaction and interpersonal meaning; requires face poses |
| 14.556-16.642 | Return to wide table | Re-establish shared space and the comparison |
| 16.642-24 | Side-view phone user beside column | New setting, curved silhouette and balance preparation |
| 24-30 | Loss of balance and fall | Track support, center of mass, anticipation, impact and settling frame by frame |

Design observations: elongated simplified characters, purple clothing, dark teal limbs,
contrasting yellow/pink/green fields, limited facial marks. The old 24-second generic
posture-to-X-ray study is not a reconstruction of this opening. Its source alignment
remains unverified. These boundaries are preliminary manual observations, not approved cuts.

## Blood pressure: Ab9OZsDECZw, source 6-27 seconds

Native sampling: 720 frames over source 0-30 seconds in
`.runtime/reference-study/blood-opening-0`.
New composition: `harnesses/astra-motion/examples/blood-opening-study`.

| Source interval | Function | Candidate implementation |
|---|---|---|
| 6-14.2 | Reveal the scale of the internal vessel network | Clipped red/teal vessel pattern inside a human silhouette |
| 14.2-18.6 | Convert anatomical length into a familiar scale | Globe, wrapping line, observed 95,000 km label |
| 18.6-23.1 | Convert daily circulation into a visible volume | Tank fill and observed 7,500 L label |
| 23.1-27 | Explain recirculation rather than stored volume | Two tanks connected through a smaller T-pose human; 4-5 L label |

All labels above are transcriptions of this reference, not independently validated
medical claims. Globe paths are illustrative and must not be used as accurate geography.
Original graphics are authored for the candidate; source logo, soundtrack and artwork
are not embedded in it. The side-by-side comparison is an internal study only.

## Review and remaining work

- Human scale and hanging-arm geometry were incorrect in the initial network layout.
  Use an independent T-pose silhouette with a fixed SVG transform; do not combine
  hanging arms and horizontal arm stubs or infer final scale from a tween's initial state.
- The candidate circuit pattern is more repetitive than the source.
- The candidate globe is more angular, typography differs, and transitions are simplified.
- No audio reconstruction has been performed. Silent rendering cannot pass audio/rhythm review.
- The nine seek checkpoints include the final frame, but are not exhaustive frame testing.
- These two openings do not establish full-video competence or transfer to a new script.

### V2 comparison outcome

Rendered `blood-opening-v2.mp4`: 21.000 seconds, 1920x1080, 30 fps, 630 frames,
silent H.264. Full decode succeeded. All nine seek-order checkpoints passed.
Coverage bookkeeping tests: 11 passed (run the test file directly, since its imports
expect the scripts directory on the Python path).

`blood-opening-ab.mp4` places the source on the left and candidate on the right.
At candidate 19 seconds (source 25 seconds), the reference frames the left tank and
large human while the right tank is mostly outside the frame. The candidate shows
both tanks and a smaller centered human. This is a camera/information-order mismatch,
not merely a cosmetic detail. Reference eyes, heart, less repetitive vessels, rounded
hands and separated legs are also missing or materially different. Verdict: REVISE.
Next revision must recover camera framing over time and body proportions before
adding decorative effects. No human approval or complete-reference credit is granted.

### V3 revision

Closer source sampling at four samples per second over 24-26 seconds shows that the
single tank holds until approximately 24.6 seconds; the earlier 23.1-second network
boundary was wrong. The candidate now holds until local 18.6 seconds, then pans the
network by 650 pixels over 0.85 seconds. This is an initial manual fit, not a measured
optical-flow camera trajectory. The body has separated legs, rounded hands, eyes and
a heart marker. Vessel pattern and font design still require refinement.

Reverse-seek inspection found a real visibility leak: a GSAP child visibility reset
made the drip visible inside the hidden tank scene. Using opacity for the child
preserves inherited hidden visibility. First-frame and reverse-seek evidence must be
checked, not only sequential export. Composition-specific transition checkpoints are
now accepted by the seek verifier, including frames before, during and after the pan.
The experimental study contract records information order, camera hypothesis and
non-promotion conditions. It is not a production-approved director rule.

V3 export completed: 21 seconds, 630 frames, full decode success and 14 exact
seek-order checkpoints passed. The side-by-side frame at source 25 seconds shows
better sequential framing than V2, but the manual pan is not aligned exactly and
the inlet flow is visible too early. In particular, the flow-dot element needs an
explicit initial opacity rather than a future `fromTo` start state. This is a visual
timing defect despite passing determinism checks. Keep V3 as REVISE, not Gold.
Receipt: `.runtime/reference-study/blood-opening-v3-receipt.json` records source and
artifact hashes, verification results, zero paid calls and unresolved issues.

## Posture: next 30-60 seconds

719 native frames captured with original timestamps in `posture-30-60/motion.json`.
The three-second overview samples suggest the following next reconstruction tasks;
these are sampled observations, not final cut boundaries:

| Approximate sample time | Visible construction | Capability needed |
|---|---|---|
| 30 | Character obscured by a carried box | Prop occlusion and weight-bearing pose |
| 33 | Seated passengers with contrasting posture | Shared support surface and character interaction |
| 36,39 | Phone user seated against tree; small falling object | Persistent identity, seated support, secondary event |
| 42 | Phone user riding a two-wheel platform | Wheel-ground contact and balanced riding pose |
| 45 | Character body/limbs extending beyond crop | Frame-by-frame transition analysis before interpretation |
| 48 | Close-up phone user with curved torso and bent arm | Face/hand/phone target relationship |
| 51,54 | Phone lowers, torso bends further | Coordinated shoulder, elbow, head and spine states |
| 57 | Wide bent standing figure with long lowered arm | Camera scale change and foot support continuity |

This section needs articulated character assets and pose transitions. Replacing it
with generic infographic icons would not reproduce the reference's directing or tone.

## Process uptake

1. Record exact source windows before awarding any coverage to a rendered sample.
2. Separate observation, implementation, technical verification and human fidelity approval.
3. Trace visual quantities across transitions: human network -> geographic length ->
   volume -> circulation. Similar colors alone are not equivalent information design.
4. Verify image-free compositions as well as bitmap compositions. Load only actual
   image dependencies and wait for fonts; do not require unrelated fixture assets.
5. Retain the best reviewed version. Neither this note nor a successful render promotes
   a scene grammar or asset to an approved production capability.
