# Blood intervention study V1

Reference: Ab9OZsDECZw, source 201-231 seconds. Candidate: `.runtime/reference-study/blood-intervention-v1.mp4`; side-by-side evidence: `blood-intervention-v1-ab.mp4` (source left, candidate right).

## Evidence

- Original vector objects and paused GSAP timeline, 30 seconds / 900 frames.
- 900-frame fixture test: carrier-to-balloon origin gap 0; retained implant drift 0; withdrawal 1450 pixels.
- Balloon-to-deposit centerline gap at 14 seconds: 0.000275 pixels. This is not a full-surface collision test.
- Deliberately detaching the implant is detected by the test.
- All 19 seek checkpoints produce identical images after out-of-order seeking.
- No paid API calls. No audio or clinical validation.

## Visual review: REVISE

The source/candidate sheet was inspected at matched source times. The semantic sequence is recognizable: entry, inflation, deflation, second insertion, expansion, withdrawal, retained structure and resumed flow. This is not yet a faithful reconstruction.

1. Particle sizes and variety are too small and uniform in the candidate.
2. Wall lining uses smaller repeated circles rather than the source's larger scallops and rectangular outer cells.
3. The label appears too early and is too small.
4. Inflation and withdrawal timing differ; at the fourth sampled comparison the source still displays the central device while the candidate is withdrawing it.
5. The candidate balloon has a visible secondary oval highlight that makes the inflated shape read differently.
6. Deposits flatten but wall lining stays fixed. Coupled deformation is incomplete.
7. Sound and narration are absent. Human review is pending.

## Reusable finding, not automatic promotion

Separate the moving carrier from the retained object in the scene graph. Test attachment while carried and world-space stability after release. Verify intentional corruption is detected. Keep the timing hypotheses separate from measured reference events.

Next revision should measure event frames in the existing native source window, correct lining/particle proportions, and compare the same frames again. Do not generalize this fixture into GRASP_AND_RETAIN or promote INTERACTION_READY. No production defaults changed.
