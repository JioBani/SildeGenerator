# Posture consequences: 60-90s

Status: reference analysis, not reconstructed or human approved.
Source: https://www.youtube.com/watch?v=OyK0oE5rwFY
Native analysis: `posture-anatomy-60/motion.json`, 720 frames at source PTS.
The folder name is historical shorthand; this window is not all anatomy.
Analysis SHA256: `e973b41a20e5cf082d8b981424ce22f06fd3e454fb98e0535986667a32142097`.
Local English caption SHA256: `f88d7e84d621483f287a149f7a253df213afd72fc5809acf1e064e9ca03ed843`.

## Sampled scene inventory

These times locate reviewed samples, not exact cut boundaries.

| Sample | Visible construction | Candidate narrative role |
| --- | --- | --- |
| 60s | Bent figure with enlarged curved internal detail | Continue local strain explanation |
| 63s | Reclined figure, bed, apparatus | Concrete consequence/context change |
| 66s | Apparatus enlarged, paired teal shapes on display | Isolate the explanatory target |
| 69s | Seated figure with controller-like object on couch | Familiar posture situation |
| 72-77s | Bent figure holding striped bar; other arm reaches back | Visible discomfort; exact prop identity unresolved |
| 78s | Battery-shaped symbol with low colored region | Abstract metaphor; do not label physical measurement |
| 81-85s | Close figure, altered eyes, bar movement, open mouth | Expressive performance; emotion needs semantic review |
| 87s | Multiple figures in transport-like interior | Return to a shared everyday setting |

Caption inspection places organ efficiency, discomfort associations, emotional
state and pain sensitivity across this window. This is a description of source
narration, not clinical verification or permission to repeat its claims as
current medical guidance. Captions contain rolling duplicates and must not be
treated as clean sentence timing without normalization.

## Semantic safeguards

- A large open mouth is not sufficient evidence for "yawning" or fatigue.
- The striped handheld bar must not be called a phone solely from its outline.
- Distinguish observed shape, candidate story function and verified identity.
- Do not copy the battery metaphor into a numerical energy or health claim.
- Preserve counterevidence and unresolved identities in the production pack.

## Prop measurement

`scripts/measure_posture_prop.py` checks 335 native frames in 72-86s.
150 have one eligible green component. That is color-region detection, NOT
150 validated prop identities. Rotation, partial occlusion and frame clipping
make many other frames unresolved. Missing detections must not hide the object
in the authored scene or bridge a contact transition automatically.

One reviewed visible fragment spans 82.83275-83.083s (7 frames). A quadratic
fit of the detected color-support center has maximum sample residual 0.819px
at the 640px analysis width. This is neither whole-object center accuracy nor
proof of physical acceleration. No extrapolation beyond the observed interval.
The detector and fragment gap/ambiguity checks pass five synthetic tests.

## Authoring requirements

Separate torso, head, eye, mouth, near arm, far arm, hand and striped prop.
Define grip anchor and release explicitly; a fitted path cannot decide release.
Maintain the same actor palette and silhouette through close framing. Make
the controller/couch, bed/apparatus, symbolic battery and transport context
separate scene programs, not interchangeable backgrounds behind one pose.

Suggested contract fields:

`observed_at`, `frame_hash`, `identity_status`, `story_function_hypothesis`,
`caption_evidence`, `pose_state`, `hand_anchor`, `prop_attachment`,
`release_evidence`, `path_valid_interval`, `camera_transform`, `review_status`.

Next substantive work: verify exact scene boundaries and release/eye/mouth
events, author the complete consequence sequence with independent artwork,
and compare actor silhouettes plus joint/prop continuity against the source.
No automatic motion/acting readiness promotion from this analysis.
