# Illustrated Transport Development Evidence

## Status

GOAL_NOT_MET for the full autonomous film objective. The previous turn made
progress by inspecting the supplied reference and identifying within-shot mixing
as a missing capability. This turn implements and renders that capability in
private hybrid-story 0.2.0. No public release or human approval is recorded.

## Actual Outputs

- First candidate: `output/illustrated-transport-v1/illustrated-transport.mp4`.
- Revised candidate: `output/illustrated-transport-v2/illustrated-transport.mp4`.
- Both are silent, 8 seconds, 1280x720, 24 fps. Not a complete narrated film.
- Revised candidate displays both endpoint state changes and longer initial hold.
- Actual decoded-frame sheet: `output/illustrated-transport-v2/decoded-contact-sheet.jpg`.
- Output evidence: `output/illustrated-transport-v2/transport-observations.json`.
- Input/engine snapshot: each output's `receipt.json`. Later documentation or
  preparation validation edits may produce a new source hash; receipts retain
  the exact source snapshot used for the render, not a claim about future runs.

## Observations

The background stays fixed while a separately generated boat follows the editable
curve, rotates with its tangent, decelerates and holds at the destination. Both
endpoint labels and states are engine text, not baked into the artwork.
All 192 decoded frames passed the fixture-specific coral-roof tracker.
Three deliberately corrupted frame sequences were rejected: frozen boat with
changing bottom labels, reversed movement, and panning background. This is not a
general object tracker or the full goal's 95% negative benchmark.

## Provenance and Cost

Two original assets were generated with built-in ImageGen. Full prompts are in
`experiments/illustrated-transport-v1/generation-prompts.json`. The first is an
empty fictional coastal background; the second a transparent top-down motor boat.
No frames or sprites from the supplied reference are used in the output.
Separate paid API calls: 0. Login, image subscription bridge and ElevenLabs: untouched.
Two render candidates, one scene revision. Visual render time was about 13.4 seconds
for v1 and 11.9 seconds for v2, excluding generation, tests and snapshots.
The full task time was not instrumented; do not treat those as end-to-end timings.

## Implementation and Tests

- Public SDK: versioned optional composition; endpoint/timeline constraints.
- Core: separate trusted illustration registry, planning IDs, local asset prep.
- Harness: GSAP MotionPathPlugin + plate/SVG/alpha-sprite compositing.
- Existing public engines and narrative-slide remain unchanged.
- Harness validation passes at private version 0.2.0.
- Focused tests: illustrated transport 5, existing hybrid 9, planner 20,
  narrative direction 7, engine separation 4; 45 total. Not the full repository suite.
- The separate pytest-based Harness SDK suite could not run in the current image
  because pytest is absent. Its import failed; it is not counted as a pass.
- Official execution reference: https://gsap.com/docs/v3/Plugins/MotionPathPlugin/

## Remaining Work

1. Extend capability tests to additional paths, assets, sizes and seeking orders;
   conservative geometry does not prove semantic or aesthetic quality.
2. Move source and art availability checks through full service queue/cache/retry
   E2E; this turn's rendering runs locally through the actual compiler, not the site.
3. Add pose-change narrative shots with identity control, then join to this route
   with a common design bible. Do not replace articulated interaction with fades.
4. Implement independent concept/story/design critics, full typography/audio tests,
   unseen-script transfer and the required wider negative benchmark.
5. Only those later results can support AUTO_VALIDATED for a complete film.

## Learning Candidate

Observation: merely alternating a still with a generic graph loses the reference's
shared visual world. Hypothesis: registering an empty plate plus an independent
sprite lets explanatory motion preserve the narrative's illustration style.
Applicable to spatial transport on a clear authored surface; not arbitrary actors,
historical maps, hidden surfaces or hand/object contact. Status EXPERIMENTAL;
no generalized-rule promotion or claim of audience comprehension improvement.
