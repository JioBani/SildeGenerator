# Deposit sequence observation, source 141-165s

Research-only source analysis. No new render or capability approval in this step.
No paid calls; no production/Core changes. Existing whole-reference goal unchanged.

## Evidence

Source Ab9OZsDECZw SHA256 `31d041c98dfe3c0f3cb55fc8c530180d545ba15af7756f65d88a158a2e2db75b`.
576 native decoded frames with PTS: `.runtime/reference-study/blood-deposit-141/motion.json`.
Overview `blood-deposit-overview.png` is only a navigation aid, not exact event timing.
Final native frame `frame-00576.png` at164.998167s was enlarged and inspected.

Observed sequence: prior text disappears; a small lower-wall yellow mark appears; the lower wall deforms; the yellow region grows laterally and acquires outlined subdivisions; light circular elements collect above it. This is a visual description, not a verified medical or narration claim.

## Measurement

`blood-deposit-growth-v2.json` stores every frame, image hashes and source hash.
At width640, first connected yellow detection146.020875s has bounds[306,253,321,254]; final bounds[156,225,472,277]. Bounds are exclusive on right/bottom.
This is colored-region extent, not deposited volume, cell count or contact proof.

V1 used an undersized ROI and silently clipped the growing region. V2 widens the ROI and rejects any detected region touching its boundary. A second failure showed that floating particles can share colors; V2 now retains only pixels connected to the reviewed central lower-wall seed region. The seed is specific to this scene and cannot follow arbitrary moving deposits.

Four tests pass: rectangular envelope, cream-cell/top-arrow exclusion, holes versus outer extent, and clipped connected growth rejection. No test proves clinical accuracy or reference fidelity.

## Authoring contract to implement

- Keep vessel, wall defect, deposit, mobile particles and retained particles as distinct objects.
- Attach deposit to lower-wall coordinates, not to the screen or moving camera.
- Reproduce the small onset and later internal subdivision as separate states; do not merely scale one large yellow ellipse.
- Measure lower-wall deformation separately from deposit extent; avoid deriving both from the same value and falsely claiming contact accuracy.
- Particle arrival and retention need source trajectories and identity evidence. Random particles landing near a growing shape are not a successful reconstruction.
- Verify persistent contact and no teleportation at frame boundaries; compare raster A/B, not just timeline metadata.
- Use independently authored geometry; source pixels and source soundtrack are not delivery assets.

Particle tracking now has an initial evidence record in `reference-deposit-particle-tracks.md`:19 fragments,9 with at least24 native samples, not contact approval. Next: independently measure lower-wall deformation, validate relative particle/contact paths, then render the continuous141-165s segment. Native analysis coverage is increased; reconstructed and human-approved coverage is not.
