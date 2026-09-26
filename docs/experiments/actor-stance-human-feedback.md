# Stance and supporting-arm review

Date: 2026-09-24
Scope: isolated layered-motion experiment; production remains unchanged.

## Evidence and scope

The user preferred V11 over V9 in a downloaded, hash-validated A/B review
and subsequently described the face and gesture as natural. A later comment
on the V11/V12 timing comparison identifies unnatural leg motion, a spread
stance with incompatible-looking shoe direction, and an opposite arm that
still looks unchanged. The latter comment does not identify an A/B version;
do not assign it to one version or infer a V12 timing preference.

Retain the face/reaction success. Full-body acting is REVISE, and neither
production approval nor general capability promotion is granted.

## Implementation diagnosis

- actor.js fixes both foot groups at (-64, -18) and (66, -18).
  designed-skin.js substitutes the generated shoe sprites without a
  stance-specific view or orientation contract.
- performance.js solves each leg with two 131-unit bones, opposing 2D
  bend directions and fixed ankle targets. This constrains limb lengths
  but does not establish a coherent pelvis/knee/foot projection.
- The rendered 1.80-second V12 frame shows a frontal spread lower body
  with both shoes drawn in a strongly right-facing side view. Foot-contact
  checks passing is not evidence that this pose is anatomically convincing.
- V11's separated upper sleeve, forearm and hand apply only to the right
  arm. The left arm retains textured strokes and the V4 delayed-hand
  follower. It has motion numerically but no separately authored relaxed
  elbow/wrist pose, so it can still read as fixed.

Parallel feet in a wide stance are not inherently impossible. The defect
is the combination of this drawing's perspective, joint projection and
motion, not a universal ban on parallel feet.

## Next isolated revision

1. Keep the accepted face, identity and reaction timing. Use V11 as the
   comparison baseline; V12 has no human timing verdict.
2. Establish a coherent rest pose before animation: pelvis, knees, ankles
   and shoes use one consistent front/three-quarter viewpoint. Inspect
   rest, maximum weight shift and settled poses at full-body scale.
3. Author matching shoe views if required. Do not rotate or shear the
   current side-view sprite and claim that this supplies missing anatomy.
4. Model planted contact, supporting leg and a small release in the free
   knee together. Constrain knee direction as well as endpoint lengths;
   avoid a large sideways knee buckle masquerading as weight transfer.
5. Give the supporting arm a restrained shoulder/elbow/wrist response to
   the weight transfer. It need not copy the active arm or wave continually.
   Its hold should read as intentional relaxation, not a frozen asset.
6. Compare against the preserved baseline without changing face and body
   timing simultaneously. Save new candidate output separately.

## Required review evidence

- No foot sliding, sole floating, leg-length pop or camera-cut pose jump.
- Knee, ankle, shoe silhouette and pelvis agree in the chosen perspective.
- Weight shift is readable with the face cropped out and sound muted.
- The opposite arm has a plausible rest/settle, not mirrored busy motion.
- Face/reaction quality does not regress.
- Human full-body verdict remains separate from geometry tests and from
  production approval. Record failed criteria even when other parts pass.

No new video, new image or paid API call was made for this diagnosis.

Subsequent implementation: actor-frontal-stance-v13-review.md records the
new generated shoe asset and rendered V13 comparison. It does not change
the user feedback or retroactively approve the rejected lower body.
