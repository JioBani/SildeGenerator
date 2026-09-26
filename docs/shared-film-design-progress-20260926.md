# Shared Film Design: Executable Binding

Goal status: GOAL_NOT_MET, active. Previous continuation: progress, with a new
actual director plan, mixed film and decoded timing evidence. This continuation
addresses a visible renderer-level discontinuity, not the entire remaining goal.

## Experiment

- Private hybrid-story0.5 baseline preserved in output/hybrid-story-0.5-baseline.
- Candidate hybrid-story0.6 / hybrid-scene0.4 / film-design0.1.
- Keep script, voice, cinematic images, scene order and measured motion identical.
- Change shared palette, typography and subtitle backing only.
- No model/image/voice provider calls, paid APIs, login or deployment this turn.

## Implemented

One typed design binds concept identity, narrative intent, cinematic/diagram/source
treatments, palette, font, title/caption geometry and stroke width. Every scene must
carry an identical normalized contract. Same ID with different tokens is rejected.
The renderer records the exact design hash beside its executed program.

Text must have declared contrast4.5 against background and surface; graphic marks
and lines3 against background. Diagram marks must use the declared accents. These
checks establish nominal colors, NOT all-frame raster contrast or image adherence.

All five existing information grammars consume shared colors. Source framing and
attribution use the same surface/text, while authentic pixels remain unmodified.
Captions use an opaque shared surface to avoid depending on changing scene pixels.
The image-prompt path receives the same validated design for cinematic assets.
Local source/diagram routes cannot invoke the generated-image prompt adapter.

Core needed two opt-in changes: require the selected hybrid payload version during
planning, and include executable design in cinematic image prompts. Legacy SDK
schemas and old scene rendering remain available. No public harness was changed.
The existing planning-contract size limit stays intact; redundant instructions
were shortened instead of increasing it.

## Actual Output

- Baseline: output/meaning-film-dev-01/delivery/preview.mp4
- Candidate: output/meaning-film-design-01/delivery/preview.mp4
- Candidate SHA256: fe333aa27f7c8c7b7d1b43db9bacdf0e71b0b7521a96df4ae25c873fc68e4745
- Duration26.75s,1280x720,24fps; same Korean local SAPI voice.
- Routes: cinematic / quantitative_comparison / cinematic.
- Original script/image/audio reuse is explicit in design-experiment.json. This is
  a controlled correction, not another unseen-script success or automatic concept.

Candidate design is authored: night-route-editorial. It connects warm/cool night
lighting to the editable comparison using a dark neutral background, warm walking
and cool cycling bars, light text and shared caption surfaces. It has NOT been
selected by three blind independent concepts or adopted as generally superior.

PIXEL_CHECKS_PASS and DECODED_GEOMETRY_TIMING_PASS:366 native-rate diagram frames,
downsampled640x360 for measurement. Same widths322/121px and first appearances
6.167/8.083s as baseline; four frozen/reversed/quantity controls rejected. Subtitle
read windows unchanged. Contact sheet inspected: brightness jump is reduced;
labels and captions remain readable at sampled moments. No actual audience claim.

## Tests and Limitations

108 focused tests passed in39.635s, including the three-grammar pixel regression
and all9 film-design tests. Full repository suite
and production E2E are not claimed. Tests include strict schemas, palette drift,
contrast failures, old/new version isolation, image-prompt binding, Core MockTransport
design repair, real HyperFrames pixels for source preservation and comparison,
accumulation and procedure using the same design. Different grammar snapshots are
not held-out automatic director outputs.

Remaining: three genuinely distinct concepts with independent blind selection,
faithful automatic image generation from the selected concept, runtime font/license
manifest, all-frame typography/OCR/safe-area checks, full independent film A/B,
the five missing information grammars, broader negative controls, multiple held-out
scripts, smooth purposeful cameras and service E2E. This candidate is EXPERIMENTAL,
not AUTO_VALIDATED, HUMAN_APPROVED or ready for public promotion.

## Reproduce

Inside the existing pinned Docker runtime with /repo bound to the repository:

```sh
python scripts/restyle_director_probe.py output/meaning-film-dev-01 experiments/meaning-planning-v1/film-design-candidate.json experiments/meaning-planning-v1/assets output/NEW-DESIGN-RUN
python scripts/audit_director_probe.py output/NEW-DESIGN-RUN
```

Use a fresh output directory. The script verifies baseline movie, voice and original
image hashes before rendering. It never overwrites the baseline or calls providers.
