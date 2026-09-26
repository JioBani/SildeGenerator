# Posture consequences: first continuous study

Example: `harnesses/astra-motion/examples/posture-consequences-study`.
Output: `.runtime/reference-study/posture-consequences-v2.mp4`.
Scope: source 60-90s, 30 seconds, 1920x1080, 30fps, silent.
Decision: PARTIAL_STUDY_REVISE. No human or acting approval.

## Authoring

Independent SVG artwork builds the bent figure/internal detail, bed/apparatus,
couch figure, discomfort pose, battery symbol, close performance and transport
context. These are distinct scene programs, not one pose over new backgrounds.
Head, eye, mouth, arms, hand and prop are independently addressable.

Five large image-change candidates were visually checked and used as source
cut times: 62.687625, 69.194125, 72.238833, 77.5775 and 79.788042 seconds.
The later transport wipe is an approximate reconstruction, not a measured cut.
Monitor zoom, recline, gaze, head/arm and mouth timing are authored hypotheses.
Only the seven-frame late prop fragment uses measured source coordinates;
the color-support center is not a certified grip or whole-object center.

## Failures and corrections

1. Initially all later scenes were visible until the timeline first evaluated.
   The first screenshot therefore showed the transport scene.
2. Merely setting parent SVG visibility hidden was insufficient: a child prop
   with explicit visible state could show after reverse seeking. Parent opacity
   now gates scene display, and every later scene has explicit initial opacity.
3. CSS head rotation with an incorrectly interpreted pivot moved the head out
   of the close frame. Explicit SVG translate/rotate/scale interpolation keeps
   the parent-space origin stable.
4. The close arm's starting point was detached from the torso; its start was
   moved into the shoulder region. This is visual correction, not IK approval.

V1 and first/repeated seek screenshots are retained as failure evidence.

## Remaining fidelity gaps

- Opening silhouette and prop pose differ from the source's deeper forward bend.
- Reclining motion incorrectly rotates much of the figure as one group; legs
  and torso need separate pivots, and the monitor close shot includes stray feet.
- The couch character uses a simplified face with insufficient eyelid acting.
- Close head proportions differ, and its open mouth can read as a smile rather
  than the source expression. No semantic emotion label is approved.
- Unmeasured early prop flight is only a hypothesis; release and contact remain
  unvalidated. The final measured fragment must not imply the whole path passed.
- Transport figures and environment are schematic and mostly still.
- No source narration/audio was reproduced or synchronized.

## Learning boundary

Retain the initial-state, reverse-seek and coordinate-space failures as technical
regression cases. Do not promote approximate acting, object identity or inferred
clinical semantics. A complete short timeline and deterministic frame capture
do not establish source fidelity or whole-reference completion.

Next: correct recline articulation and monitor framing, then match eye/mouth
states using close source comparisons before expanding actor reuse.

## V3: bed-space support constraints

`posture-consequences-v3` separates upper body, legs/feet, backrest, resting arm
and raised arm. The bed coordinate system owns support targets; camera movement
is an explicit SVG transform above those coordinates. The upper body no longer
rotates the feet with it.

`measure_posture_backrest.py` observes 87 green backrest orientations before the
camera zoom (62.687625-66.274542s), approximately 0.98-45.89 degrees. The measured
object is the backrest, not the person's anatomy. Assigning that angle to the
authored torso is a declared authoring assumption. Detector tests cover a known
slope, a horizontal rest and absence.

The resting hand target remains (317,245) in bed coordinates. Authored segment
lengths are 95 and 115 units. The raised arm has separate segment lengths and a
hypothesized target path; these are not measured source wrist trajectories.

`verify_posture_support.mjs` checks 195 frames from local 2.7s through 9.1667s,
including the camera zoom. It verifies wrist/foot/leg endpoints and resting-arm
segment lengths in bed space. A deliberately translated foot must fail. All
checked residuals must be below .01 units. This does not prove rendered contact,
source pose fidelity or acting quality.

Visual samples confirm horizontal legs during recline and removal of the old
raised-foot intrusion into the monitor shot. Part of the raised elbow/body is
still visible during the zoom; framing is not yet fully source-matched. Existing
face, silhouette, mouth-expression and later-scene deficiencies remain.
Status remains REVISE. No automatic asset readiness or production promotion.
