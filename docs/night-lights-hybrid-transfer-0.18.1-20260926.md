# Night-lights new-script hybrid transfer, private 0.18.1

Status: `GOAL_NOT_MET`. This is an authored development film and a technical
transfer probe, not an autonomous director or public-engine promotion.

## New material and scene decisions

The development script and scene brief are in
`experiments/night-lights-transfer-v1/scene-brief.json`. Its routes are:
rooftop experience (cinematic), three ordered satellite-compositing steps
(editable diagram), NASA 2016 Black Marble map (registered source), and a
different side-profile rooftop shot (cinematic return). Two built-in image
generations produced distinct stills for the same observer. Windows offline
speech produced measured Korean narration. Paid API calls: zero.

The source catalog contains the NASA page, rights guidance, original-file
SHA-256, date label and meaning limit. The map is a 2016 nighttime composite,
not a one-night photograph or proof of star visibility or health effects.
Source frame pixels are format-padded only. Cinematic frames carry an AI
recreation label and are not presented as documentary footage.

## Output comparison and typography finding

`output/night-lights-hybrid-transfer-v2/delivery/night-lights.mp4` is the
first complete film. Actual-frame review found one subtitle per entire scene,
with 2-3 dense lines occupying too much of the picture. The original stays
preserved as the comparison baseline.

`output/night-lights-hybrid-transfer-v4/delivery/night-lights.mp4` uses
separately synthesized sentences and their measured WAV durations for ten
short subtitle cues. Private `hybrid-story@0.18.1` now rejects overlapping,
out-of-scene, empty or above-two-line explicit subtitle cues before render.
Default subtitle behavior and public slide engines were not changed.

The final MP4 decodes at 1280x720, 24fps, 43.875 seconds with audio and video.
`receipt.json` records the four routes, scene/voice/image hashes, source
metadata and `PIXEL_CHECKS_PASS`. The later render is byte-identical to the
sentence-cue candidate made immediately before the 0.18.1 validation change.
Three new cue tests and 23 focused regression tests pass. Manual frame review
found the shorter captions, source attribution and three diagram states
readable at sampled times, but this is not a viewer comprehension study.

## Remaining limits

- Film scenes are generated stills with a measured camera move, not actor
  articulation, gaze or performance.
- The diagram is an accurate but simple ordered-node treatment. More varied
  visual metaphors and attention choreography remain unproven.
- The script, source selection and scene program were authored for this test;
  the autonomous planner did not choose and execute them on a held-out script.
- Pixel inspection does not judge factual accuracy, audience understanding,
  emotional effect, OCR across every frame or human design quality.
- The live service is not running this build and the private harness is not
  public. No 8080 authenticated-job E2E or long-form slide release is claimed.

Next proof: with the same sources and cost boundary, test whether the actual
planner selects the appropriate three routes on an unseen script, then compare
the resulting film to a baseline with blinded understanding questions. Preserve
the previous best result if it performs worse.
