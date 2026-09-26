# Posture 90-120 second alignment study

Status: MEASURED_PARTIAL, NOT_RECONSTRUCTED, NOT_APPROVED.

Source: OyK0oE5rwFY, SHA256
`47f6a63567ffd86e3d7cac3aeacfa5c8164f8b90ebab2b5c568af7c7f3504dfd`.
The source window contains 720 decoded frames with original PTS, stored in
`.runtime/reference-study/posture-alignment-90/motion.json`.

## Observation and purpose

The window moves from everyday posture examples to a frontal character and then
front/side dark silhouettes with bright dotted lines. The final frame was inspected
directly. Its front marker line is nearly vertical; its side marker line is curved.
The two color fields separate viewpoints without requiring two differently styled
characters. Exact cut boundaries and narrative synchronization still require review.

The experiment hypothesis is: keep design identity stable while changing the
representation needed to explain structure. This is not yet an approved rule.
Do not use anatomical silhouettes when the scene function is an emotional reaction.

## Measurement

`scripts/measure_posture_alignment.py` measures 336 frames from source time 106s
onward. The v4 evidence is `.runtime/reference-study/posture-alignment-v4.json`.
It records source and analysis hashes and coordinates in 640x360 space.

- A teal/yellow boundary was detectable in 160 frames, first at 113.36325s.
  This is a detection threshold crossing, NOT a proven transition start.
- At 119.994875s, 31 frontal and 41 side bright components were detected.
  These are illustration markers, not vertebra counts or semantic joint IDs.
- The final overlay was visually checked: circles follow both dotted lines and
  the vertical field boundary. This checks the final frame, not every detection.
- Five synthetic tests cover known centers, split, background distractors, missing
  boundary, dense marker neighbors and resolution rejection (some in one test).

## Failures retained

v1 required an exact color boundary and detected only one split frame. v2 tolerates
antialiasing around the boundary but its all-around darkness check rejected dense
markers. v3/v4 use lateral dark support so neighboring vertical dots do not invalidate
one another. All previous evidence files remain available; do not overwrite them.

Touching markers can form a single component and remain unresolved. Missing
detections must not hide objects or imply disappearance. No interpolation across
cuts, forced marker counts or anatomical claims are permitted.

## Next production contract

Continue the existing 60-90s study into this window rather than making an unrelated
design sample. Preserve character identity through the everyday examples, frontal
view and simplified silhouette. Author independent silhouettes; source pixels remain
analysis evidence, not delivery assets. Validate split geometry and marker placement,
then inspect the full continuous transition and narration before accepting a study.
## Rendered alignment subsection

The independent `posture-alignment-v1` example now renders source 106-120s as a
14-second silent study, 1920x1080 at 30fps (420 frames). Runtime MP4 and source-left
comparison are in `.runtime/reference-study/posture-alignment-v1/`.
The earlier 90-106s portion and continuous 60-120s assembly remain unimplemented.

Hand-authored SVG silhouettes use the measured final marker coordinates and
measured split-boundary samples. Facial fade, marker reveal and side-character
entry timings are explicitly hypotheses rather than measurements. No source
bitmap artwork or audio is embedded in the independent candidate.

Harness validation passed. All 15 sampled reverse/forward seek checks were
order-independent; FFmpeg decoded the result without error. This local Chrome/
GSAP/FFmpeg study is not a Docker Mock E2E or whole-pipeline approval.

The final A/B frame was inspected. Marker lines and field division are close,
but torso, neck, face and hip outlines differ. The candidate is not approved for
design fidelity. The A/B at local 7.5s reveals a major missing representation:
the source first shows a colored bent profile holding a prop, whereas the candidate
introduces an already upright silhouette. This is a semantic/action omission, not
merely an easing mismatch. Next revision must restore bent profile -> posture
change -> silhouette before tuning timing; do not accept final-frame similarity
as evidence that the transition was reproduced. Technical
success does not imply narrative, medical, audio or human quality approval.

Status: PARTIAL_STUDY_REVISE. Whole-reference reconstruction and new-script narrated
transfer remain incomplete. No paid calls were made; Core and providers unchanged.

## V2: restore the omitted performance

`posture-alignment-v2` preserves v1 and adds independently drawn face/headpiece,
neck, torso, arm, hand and striped prop. The colored bent profile enters first,
then head/neck/torso straighten as the grip lowers, followed by a short fade to
the upright silhouette and later dot reveal. Local authored action is 7.48-7.88s;
abstraction is 7.88-8.05s. These are hypotheses informed by source frames 570,
580 and 590, not a measured continuous pose track or a validated actor rig.

The source-left/candidate-right v2 comparison and transition screenshot are in
`.runtime/reference-study/posture-alignment-v2/`. The 7.5s A/B now contains the
previously missing colored bent person and prop. However candidate head/headpiece
is displaced too far right and partly cropped; neck and body proportions differ.
This remains PARTIAL_STUDY_REVISE. Restore framing and geometry before claiming
faithful acting. A contact solver, semantic object identity and interpolation
quality checks are not established by these path tweens.

420 frames rendered; 15 sampled seeks were order independent; decode passed.
No audio, paid calls, Core changes or automatic capability promotion. The research
lesson is to compare transition states, not only matching final diagrams. The
surrounding continuous sequence and different-script transfer remain outstanding.

## V3: horizontal framing regression check

Head origin changed from (106,155) at 72 degrees to (80,175) at 85 degrees in
performer space; the authored neck endpoint follows the revised position. This
is a framing correction, not a measured joint solution. The 7.5s source-left A/B
was inspected: the previously cropped headpiece is now visible. Body proportions,
eye expression, prop height and split synchronization still differ from source.

`scripts/verify_alignment_framing.mjs` checks all 19 output frames from 223 through
241 (after entry and through the abstraction fade). Horizontal head bounds and
full grip bounds pass. A deliberately displaced head fails the same check.
Intentional entrance cropping and source-like upright headpiece top cropping are
outside this specific invariant. It does not prove neck contact, gaze or acting.

The v3 420-frame MP4 and A/B are in `.runtime/reference-study/posture-alignment-v3/`.
15 sampled seek checks passed. The curriculum registers the 106-120s window as
PARTIAL_STUDY_REVISE, not approved coverage. No production rules are promoted.

## V4: separate actor and divider tracks

Evidence review showed that the frontal marker column moves before a divider is
detected. V3 incorrectly gated actor travel on divider detection, holding then
jumping the actor. V4 uses an independent narrow marker-column median track;
missing/ambiguous samples are not extrapolated. The first divider sample also
had an 81-pixel error because its tween began at, rather than reached, the sample
time. It is now an explicit first sample state followed by linear sample intervals.

`verify_alignment_tracks.mjs` checks 48 native timestamps from 112-114s; rendered
actor and detected divider coordinates agree within 0.05 analysis-space pixels.
This is agreement with detector output, not independent visual truth. Motion
before first divider detection is still unmeasured and may pop. The 19-frame
framing check and deliberately out-of-bounds negative control still pass.
V4 retains the earlier body/eye/prop discrepancies and remains a partial silent
study. This correction must not be promoted as general tracking capability.

Visual check at local 7.3s reveals another gap: the colored entrant is already
visible while its yellow field has not appeared (first divider detection is later).
V4 therefore is not the new approved best version. Next change must measure the
divider outside the detector's restricted x=60..579 range and synchronize the
entrant with that field. Do not hide the entrant simply to satisfy the old framing
gate, and do not mistake 48 matching samples for complete transition validation.

## V5: background-bound entrance

The detector now searches x=6..634 instead of 60..579. It observes 161 split
frames, first at 113.321542s. Six analyzer tests pass, including a boundary at
x=610. Earlier edge visibility remains below the detectable support width.
The performer now shares the measured field displacement instead of an unrelated
7.1s entry tween; its initial visibility begins with the first measured field.

The expanded track verifier includes the entrance relationship. It passes all
48 checked native timestamps in v5 and rejects 11 timestamps in the old v4
negative comparison. The 15 sampled seek checks and MP4 decode also pass.
V5 is rendered at `.runtime/reference-study/posture-alignment-v5/` with an A/B.
At local 7.3s the candidate no longer exposes an entrant over a teal-only field.
However the A/B source already shows a narrow yellow strip; source-frame selection
and the first measured field instant need precise PTS-aligned comparison. The
current FFmpeg source seek is not proof of exact frame correspondence. Do not
claim timing fidelity from this side-by-side alone. Remaining proportion, prop,
and acting differences are unchanged. Status stays PARTIAL_STUDY_REVISE.

## PTS-aligned comparison audit

`scripts/render_pts_comparison.py` pairs each decoded candidate PTS with the last
native source frame presented at or before origin + candidate PTS. The 420 pairs,
filenames, PTS, target times and evidence hashes are recorded beside
`posture-alignment-v5/pts-aligned-ab.mp4`. Maximum source sample age is 0.041625s;
source frames are held, not interpolated. Four selector tests pass (no future
frames, exact boundary, no early clamping, irregular PTS). The tool requires a
CFR candidate and refuses evidence overrun.

At local 7.3s (target 113.3s, presented source 113.279833s), BOTH sides are teal-only.
The earlier narrow yellow source strip was a comparison frame-selection mismatch.
At local 7.5s an actual disparity remains: candidate performer is farther right
and its headpiece is cropped. The v5 field-displacement invariant is internally
consistent but not validated against actor motion. Do not promote it. Next measure
source landmarks to distinguish fixed-position reveal from actor translation.
Matching background displacement must not be assumed to be correct choreography.

This corrects evidence interpretation, not character design. Whole-reference and
new-script transfer requirements remain incomplete. No paid calls were used.

## V6: reveal versus translation

Source frames 560, 564 and 566 show the rightmost headpiece at approximately the
same x-position as the teal boundary sweeps left. The former field-linked actor
translation was the wrong mechanism. V6 keeps performer origin at x=440 and uses
a world-space clipping rectangle driven by the measured boundary. Frontal actor
translation remains a separate track. This is a scene-specific observation, not
a universal rule that all entrances should be wipes.

The PTS-aligned A/B at local 7.5s now reveals the profile within the yellow field
instead of pushing its head beyond the right edge. Hand/prop are still too high,
body silhouette and eye design differ, and head straightening begins 0.1s after
the other body tracks. That coordination is unverified; current framing tests do
not establish neck attachment or natural acting. Keep PARTIAL_STUDY_REVISE.

Runtime `posture-alignment-v6/` contains the 420-frame silent candidate, PTS-aligned
A/B and evidence. 48 track checks, 19 framing checks with negative control, 15
sampled seeks and full decode pass. The track checker now requires fixed actor
origin plus matching clipping boundary, superseding the incorrect v5 invariant.
No Core/provider change, paid call, human approval or automatic rule promotion.

## V7: grip height and shared straightening phase

The prop detector now accepts explicit source/fit intervals while preserving its
prior defaults. In 113.3-114.1s it resolves only 6/19 frames; the proposed fitted
fragment is UNRESOLVED because evidence is missing. Report:
`.runtime/reference-study/alignment-prop-v1.json`. The detected green centroid
is NOT a grip anchor or whole-object center; it was used with visual inspection,
not fed directly into an IK claim. Five existing prop detector tests still pass.

The authored grip origin changes from (74,240) to (105,279) in performer space,
with the forearm endpoint following it. Head, neck, torso, arm and grip now share
the 7.58s start and 0.3s straightening duration rather than inconsistent start times.
This remains an authored motion hypothesis, not a measured anatomical rig.

At the PTS-aligned 7.5s comparison, prop height is closer to source. The candidate
torso/arm are thinner, shoulders higher and eyes differ. These remain REVISE.
The 420-frame silent render and PTS-aligned comparison are in
`.runtime/reference-study/posture-alignment-v7/`. Framing (19 frames and negative
control) and track (48 timestamps) checks pass. Those do not certify acting.
No paid calls or production capability promotion; full sequence and transfer are
still incomplete.
