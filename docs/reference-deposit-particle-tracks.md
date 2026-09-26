# Deposit particle tracking evidence

Research only. Source Ab9OZsDECZw 141-165s; 456 frames from146s onward examined. No paid API, no production default changes, no contact/retention capability promotion.

## Measurement

`.runtime/reference-study/blood-deposit-particles-v1.json` contains source hash, per-frame hashes, detections and track samples.
19 track fragments were found;9 have at least24 native samples. These are spatial associations, not verified semantic identities.

The longest fragment has333 samples from151.151 to164.998167s, moving fromapproximately(5.05,230.47) to(314.91,216.66) at640x360 analysis resolution. Four more long fragments contain228,193,178 and174 samples.

Detection selects light circular connected components in the reviewed lumen ROI. Yellow deposit pixels are excluded. Area/aspect bounds reject many merged shapes. Adjacent frames are linked only when both sides have one possible partner within10 pixels. Missing detections and ambiguous merges break tracks rather than interpolating invented contact events.

## Limits

- Similar nearby particles can still exchange identities; unique proximity is not proof.
- Some edge-entering objects are partly visible, so first/last centers and radius estimates may be biased.
- Objects that merge or become occluded produce fragments. Do not sum fragments to obtain an object count.
- The10px displacement bound is per native frame and must not be reused with a different sample rate.
- A long visible path does not imply retained contact. Wall motion must be measured independently, then compared in relative coordinates.
- Narration/medical meaning and full reference fidelity remain unverified.

## Regression coverage

Four tests pass: light circle versus yellow symbol; unique adjacent match; ambiguous merge rejection; no identity bridge across a missing frame.

## Next authoring input

Use source PTS for object positions. Keep tracked fragments separate from authored hypotheses. Measure a lower-wall anchor for each candidate contact and inspect the relative gap/velocity over time. Only after that create arrival-to-retention transitions. Never replace missing evidence with random particle motion and call it reference reconstruction.
