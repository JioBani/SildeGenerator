# V4 Agent Visual Assessment

## Verdict

**REVISE.** The candidate is useful as a designed articulated-actor prototype, but is not yet a satisfactory natural acting example. Preserve its design and reusable rig; do not promote its performance as Gold. This is the agent's own visual judgment, not a human review or a user approval.

The previous responses relied too heavily on asking for human review after technical tests. Agent-led visual diagnosis can and should identify actionable defects before asking a person to choose a version.

## Evidence and scope

Reviewed the decoded final V4 MP4, not only its JSON contract. Extracted 0-3 seconds at 10fps for body motion, 3-8 seconds at 6fps for reaction progression, 6.0-6.5 seconds at all 30fps for blinking, and native frames 89/90 around the cut. These are temporal contact-sheet inspections, not real-time audiovisual viewing. The clip is silent, so audio integration cannot be assessed. Small fast defects outside the fully sampled blink interval may be missed.

Evidence files are in `output/layered-motion-acting-v4/self-review/`:

- `weight-10fps.png`
- `reaction-6fps.png`
- `blink-30fps.png`
- `cut-boundary.png`

V4 SHA-256: `a9ff007e41de4bdefc948c88216ccf4472cf7013a883cf38fa541adcc7f77243`.
V3 SHA-256: `3ba60cff8a87d6338a817e1632232a251287a5452e26f6da8969c03adf8850cb`.

## Findings

### 1. Body acting does not yet carry the emotional change

Across the reaction, the mouth becomes a small smile and the pupils move toward the result. That sequence is readable as looking and mild pleasure. However, the shoulder silhouette, chest and mitten-like hands remain almost the same. The body reads as a posed cutout with a changing face, rather than a person relaxing after seeing a result. Small timing offsets do not address that missing pose contrast.

This is a qualitative finding. The technical report's zero foot drift and accurate gaze angle cannot establish emotional readability or naturalness.

### 2. Pose continuity breaks at 3.0 seconds

At 2.9667 seconds the pelvis is at (26, -273.5), torso rotation is -2.7 degrees, and the head is at +1.7 degrees. At 3.0 seconds those become (0, -278), 0 and 0. The actor's body returns to its initial pose while the camera simultaneously cuts closer. The final MP4 boundary images confirm the visible posture reset.

If these are explicitly two independent rig tests, that reset is acceptable. If presented as a continuous mini-scene in the same room, it fails pose continuity. Either retain the previous pose as the reaction's initial state or explicitly separate the tests. A camera cut alone is not an explanation for a changed body state.

### 3. Weight shift is mechanically present but dramatically unspecified

The first three seconds show the pelvis moving sideways and one leg straightening while the other bends. The feet stay planted. It communicates a mild change of stance, but there is no clear reason for the change: no visible waiting behavior, adjustment to a stimulus, or task. The neutral face and symmetrical hanging hands offer little characterization. As a rig exercise it is useful; as expressive acting it remains weak.

### 4. Head direction is a limited approximation

The eyes/nose/mouth shift toward the screen while the hair/ear outline changes little. This supports a slight look, but is not convincing evidence of a larger head turn. Do not amplify that transform to imitate a substantial turn. For a stronger directional pose, author a reviewed three-quarter head view or a bounded pose set with matching anchors. A full mesh system is not automatically required.

### 5. Blinking is acceptable for this stylization

The 30fps eye sequence closes and reopens without an obvious layer detachment in these frames. It is a simple vertical eye shape change, not anatomical eyelid animation. That simplification fits a cartoon sufficiently well that it should not be the first rework target. More realism is not inherently better for this design.

### 6. V4 is a small technical refinement, not demonstrated quality growth

The arms trail the torso slightly and the wrist rotates, but the decisive poses and facial acting remain V3's. The measured maximum hand difference is about 7.14 actor-coordinate pixels. Whole-frame V3/V4 SSIM is 0.999084; the unchanged background dominates this metric, so it is not an acting score. Neither small numerical differences nor extra channels prove improvement. The agent does not choose V4 as a clear perceptual winner on the current evidence.

## What to keep

- Readable character silhouette, consistent clothing colors and recognizable identity.
- Separate body/face parts without the earlier moving-background cutout defect in the sampled frames.
- A clear visual stimulus on the monitor, then eye direction and a restrained smile.
- Stable contacts and repeatable timing as technical foundations.

The textured character and flatter room are not inherently incompatible. Their mixture should be reviewed as a project art-direction choice, not automatically rejected as a bug.

## Next revision priority

1. Establish three distinct designed key poses: focused waiting, noticing the result, and relaxed satisfaction. Judge their silhouette and face at intended playback size before adding intermediate frames.
2. Preserve the actor's state across the 3-second cut, or present independent tests explicitly.
3. Tie the small shoulder/chest/hand release to the meaning of satisfaction, not to an arbitrary idle-motion loop. Keep the feet grounded.
4. Use a separately authored directional head pose only if the desired look exceeds the current limited face-plane turn.
5. Reassess the completed silent reaction in context. A held pose is not itself a fault; the held pose must already communicate the emotion. Do not add endless breathing or swaying to conceal weak acting.

No natural-acting approval, production deployment, automated capability promotion or efficiency-stage transition follows from this assessment. No new assets, paid calls or production-code changes were made in this review.
