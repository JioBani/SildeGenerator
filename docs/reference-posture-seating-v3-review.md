# Posture seating V3: separate facial state from body pose

## Experiment

Experimental astra-motion@0.3.0 example. Preserve V2 camera, world geometry, contacts, props, narrative order and duration. Replace the permanently smiling face with independent upper-lid coverage and mouth curvature. No Core, provider or production-default changes. Paid calls 0. Local GSAP/Chrome rendering, not a verified Docker Mock E2E.

Source 178-184s was inspected at half-second intervals. The bent actor has a half-closed eye and nearly level mouth; the upright actor has an open eye and smile. The sampled evidence supports the state distinction, not exact native-frame onset. The V3 timing is a hypothesis: body return starts at local 18s, eyelid opens at 18.15s, mouth changes at 18.35s. Do not call these Gold timings.

## Implementation

The original independent vector actor is retained. An eye-circle-clipped skin-colored lid changes height continuously; the mouth keeps its path command topology while curvature changes. The opening slouch and later desk slouch use the tired state, and upright holds use engaged. The face is not swapped as a bitmap and does not alter the head pivot or gaze endpoint.

## Technical evidence

900-frame state scan; five expected face states; bounded eyelid step under 7 actor pixels per output frame; eyelid starts before mouth. Separate endpoint test retains arm-hand and leg-foot attachment, settled foot stability, screen gaze target and hand visibility. 21 out-of-order seek checkpoints pass. These tests prove deterministic state operation, not natural acting or emotion recognition.

## Visual review

At 17.5s the candidate's lowered eyelid and level mouth distinguish the slouched hold from the open eye and smile at 19s. Existing exaggerated neck length, face proportions, arm curvature, prop cropping and gaze-dash weight remain different from the source. The source shows a more compact figure. Visual status remains REVISE. Audio absent; no human approval, no REACTION_READY or INTERACTION_READY promotion.

## Conditional grammar candidate

When an explanation explicitly contrasts an uncomfortable posture with an attentive upright state, facial state can reinforce the body change. Keep identity and contact geometry stable; stagger the face channels only when the reference or intended action supports it. Counterexamples: a neutral technical demonstration may need no emotion change, and upright posture must not universally imply happiness. Store this as a reviewed-fixture hypothesis, not a universal psychology rule.
