# Story and movable-design pilot: light-pollution scene

## Scope

This is an isolated research path for scene 005 of the light-pollution film. It
does not change the running site, authorize paid generation, or promote a
character rig to production. The baseline and candidate keep the same local
narration. The goal is to test two linked processes:

1. Reference observation -> design choice -> movable asset authoring.
2. Audience question -> human experience -> explanation -> changed state.

The layer separation principle follows the [Adobe still-image preparation
guide](https://helpx.adobe.com/after-effects/desktop/import-files/import-still-images/preparing-importing-still-images.html)
and [Character Animator artwork preparation](https://helpx.adobe.com/adobe-character-animator/desktop/creating-and-controlling-puppets/prepare-artwork.html).
Those guides inform our authoring structure; no Adobe code or reference artwork
is used in the output.

## Executable boundary

`app/creative_readiness.py` now emits an authoring route, required layers,
assembly requirements and evidence needs for each independently moving object
before image generation. This report remains advisory and cannot set
`production_ready`. In the isolated pilot, `app/creative_pilot.py` checks
scene-story fields, reference provenance and non-copy boundaries, competing
design concepts, movement-target coverage, authored asset hashes, layer order,
occlusion joins, sample-video hashes, and review axes. It separately reports
contract errors and human work still pending. The pilot always returns
`production_ready: false`; review text inside a JSON file is not an approval
credential.

Run `python scripts/audit_light_pollution_creative_pilot.py` from the repo root.
The command writes the normalized contract and audit to
`experiments/light-pollution-story-asset-v1/creative-pilot-contract.json` and
`creative-pilot-audit.json`. It makes no model, image, or voice calls.

## Current evidence and judgment

- C's exact video hash has a scoped human positive review for light direction,
  character response, and facial expression. Its overall assembly and
  comprehension were not approved.
- D changes only the neck/collar assembly and preserves the C timing. Its
  282-frame shot-specific technical check found no gap in two fixed probe
  regions and preserved the decoded audio hash. That is narrower than a full
  visual pass.
- The user reviewed the C/D comparison and judged D much more natural, then
  explicitly confirmed that the neck/clothing join also looks natural. This
  verdict is bound to D's video hash in `D/human-review-naturalness.json`.
  Direct inspection of `D/actor-check.png` had raised a possible tonal seam;
  that single-image concern does not override the user's motion review.
  Approval is scoped to naturalness relative to C and this exact join, not
  to every acting or design axis.
- Neither C nor D depicts a curtain-closing decision, so this shot cannot yet
  demonstrate the full experience -> explanation -> change arc. The earlier
  B-v2 user review found no comprehension advantage over A. No later
  comprehension or immersion comparison has been measured.
- The audit currently reports zero invalid evidence links and nine verified
  asset/video/review hashes, but keeps asset contact, overall acting, design,
  comprehension, immersion, fact claim, and viewer-change review pending.

## Next controlled comparison

1. Preserve D as the preferred version for naturalness and neck/clothing join.
   Inspect the full motion path and the hand/cheek contact separately; the
   user's scoped acceptance does not prove every pose or contact.
2. Add an independently controlled forearm/hand and curtain after the
   reaction shot's remaining contact review. Record the hand/curtain
   contact point and front/back drawing order; do not fake the action with a
   camera push.
3. Compare the unchanged narration and timing against the current baseline.
   Ask separately what caused the disturbance, what the person did, what the
   viewer understood, and whether the character experience improved
   engagement. Preserve the best reviewed cut; do not replace it merely
   because a revision is newer.
4. Test the same principle on a different script and different assets before
   considering a reusable director rule. Human design/acting approval for one
   exact file never grants general asset or grammar approval.
