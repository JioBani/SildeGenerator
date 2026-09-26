# Transport contract integration review

## V4 controlled readability comparison

Private harness astra-transport-lab0.1.1 adds a bounded layout.token_size profile.
V4 selects readable (180x72px,36px text), versus compact (84x60px,24px) in V3.
Timing, labels, colors, centers, scene boundaries and narration remain unchanged.
Output: `.runtime/reference-study/transport-comparison-v4/narrated.mp4`.
The unchanged AAC stream hashes to
`7d08ec908a3317993cae37837f98332f094b64dcd7e028b36fd45795e3995dc8`.

Nine transport tests and harness validation pass. Browser center/text checking
passes12,350 checks with0.016042px maximum error, including reverse seek.
A960x540 decoded frame at12s shows legible six calculation labels without visible
overlap. This is a sampled design observation, not a full-frame text-fit audit or
proof of viewer comprehension. Small phone playback and the complete reference
tone/design are not validated. Previous versions remain untouched.

The bootstrap check confirms Docker daemon is unavailable; Docker Mock E2E did
not run. Local existing Chrome/GSAP/FFmpeg rendered475frames with no paid calls.
Core and the public default harness were not changed. The readability profile
remains experimental, not an automatic Gold promotion.

Learning: preserve identity/timing when testing visual hierarchy. A size change
should be independently selectable rather than requiring a new motion program.
Do not treat bigger labels as a universal rule: dense diagrams and different
aspect ratios need their own overlap and readability checks. Next evaluate the
full designed sequence and human understanding, rather than repeatedly optimizing
this small diagram and calling the reference-reproduction objective complete.

## Narrated comparison V3: pacing experiment

Candidate: `.runtime/reference-study/transport-comparison-v3/narrated.mp4`.
Baseline V2 is preserved. Both use the same private-lab palette, typography,
token shapes and disclaimer, NOT a claim of matching the earlier illustrated
Gold design. Existing narration is stream-copied unchanged: audio SHA256
`7d08ec908a3317993cae37837f98332f094b64dcd7e028b36fd45795e3995dc8`.

- Hypothesis: explain one calculation before showing multiple jobs, and allow
  fewer sequential completions to make waiting visible without rapid-fire text.
- Changed variables: scene segmentation, operation timing and completed job count.
  This is a combined staging experiment, not a single-variable causal study.
- DEMO 0-6.913197s: one expression moves through input, calculation and result;
  result holds from5s. CPU 6.913197-10.422131s: two jobs finish, four remain queued.
  GPU 10.422131-15.833333s: all six jobs process and finish together.
- Technical evidence: eight transport unit tests pass. Browser forward/reverse
  verification passes12,350 center/label checks over475frames, max error
  0.016042px. H.264/AAC,1920x1080,30fps. No paid calls or new generated assets.
- Visual observation from one-second contact sheet: input-to-result transformation
  and remaining-versus-complete contrast are more explicit. Tokens remain small
  relative to the canvas; large empty areas weaken emphasis on compact displays.
- Limitations: no viewer comprehension trial, no listening review, no full-film
  evaluation, no production integration. CPU illustration is simplified and does
  not establish actual CPU/GPU speed or the absence of CPU parallelism.
- Status: REVISE / HUMAN_REVIEW_REQUIRED. Do not replace an approved best version.
- Next experiment: keep this audio and timing fixed, test a more legible object
  scale, then ask viewers what changes between the two processing modes without
  showing them the intended answer. Compare both versions blind where feasible.

Video SHA256: `31efdc4a7c51175826d88b8205f23ae2dc0c0dc32b28bd4c6aa7086b367cd916`.
Contract review SHA256: `197143c0cc51d260dd51e7bf312d32e34945260a2cadd72c52e5ac5e61108612`.
Evidence remains a scoped experimental observation, not a universal directing rule.

Previous turn: progress. Evidence-bound learning packets and compatibility diagnostics were implemented, but there was no compiler implementation for transport_track.

This turn creates private astra-transport-lab@0.1.0, a separate fork of astra-motion@0.3.0. The existing public/default harness and Core are unchanged. The new package validates normalized token paths, then emits labeled token elements and GSAP segments through compile_scene_program and compile_project. Samples carry seconds and normalized coordinates; interpolation is linear, initial rest and final hold preserve endpoints.

Validation rejects unknown motion kinds, missing token references, duplicate tracks/IDs, invalid label lengths, nonfinite values, unsafe coordinates, non-increasing times and excessive sample/token counts. Initial/final rest is not a missing sample: no unsupported speed is inferred outside the supplied track.

Verification: harness manifest validation passed; two unit tests (including six invalid-input subcases) passed; two existing scene-program regression tests passed. A four-second, six-token independent GPU fixture rendered120frames via the actual experimental compiler output and the local seek renderer. The 2s screenshot places six distinct numbered tokens at the expected midpoint region. This is a compiler-route transfer smoke, NOT a completed GPU narration or Gold design. The inherited template has an empty caption band, decorative progress and plain tokens; human design/meaning review remains unpassed.

Local output: `.runtime/reference-study/transport-lab-gpu-v1/study.mp4`. No paid calls. An image extraction attempted before the encoder completed failed with missing moov; the same live process was awaited and extraction then succeeded, without restarting the render.

Not verified: Docker HyperFrames CLI execution, queue/cancellation behavior for this harness, full production planner consumption, multi-scene seek continuity, comprehension improvement and human approval. The local runtime used the existing GSAP asset without dependency installation. This harness is private and not a production release.

Next: verify exact positions and reverse seeks in browser against contract samples; add source/target labels and computation events to turn motion into explanation; compare with the best designed GPU version using the same narration. Do not treat a supported effect name as evidence of narrative quality.

Position/reverse-seek follow-up completed: `scripts/verify_transport_contract.mjs` reads actual bounding-box centers at each of120frames in forward and reverse order, comparing against independent interpolation of the compiled contract. All1,440token checks passed with maximum0.015625px deviation and no order dependence. This verifier deliberately refuses multi-scene inputs rather than pretending that single-scene evidence covers their boundaries. Result: `.runtime/reference-study/transport-lab-gpu-v1/contract-review.json`. Meaning, design, transitions and audio remain unapproved.

## Semantic state fixture V2

Private lab token contracts now optionally carry ordered queued/processing/complete state events with bounded text and scene-local seconds. These compile to actual text and color changes, rather than static numbered boxes. State labels are HTML-escaped in markup and script-safe JSON-encoded in inline timeline code. Four unit tests pass, including invalid state kinds/times and closing-script text rejection.

V2 fixture shows six independent multiplication expressions entering a central processing position, holding for one second, becoming results3/6/9/12/15/18 and moving to the result column. Values are authored fixture content, not calculations inferred or verified by the general renderer. The inherited empty caption band and decorative progress are absent for token scenes. This dedicated layout currently has GPU-specific column headings; it must become a declared layout contract before use for arbitrary transport subjects.

Rendered V2: `.runtime/reference-study/transport-lab-gpu-v2/study.mp4`, four seconds,120frames, silent. Browser contract verification now also checks state text at every forward/reverse frame. 1,440checks pass with maximum position error0.015625px. Final screenshot inspected for readable results and distinct columns. Full narration, CPU comparison, comprehension testing and approved art-direction matching are still missing; status remains REVISE / HUMAN_REVIEW_REQUIRED. No source artwork or paid generation used.

## Narrated comparison through compiler

Column labels/positions are now explicit validated layout.columns fields, not hardcoded GPU text. The existing renderer still owns a restricted three-stage-style presentation; declaring labels does not make it a general design system.

`scripts/build_transport_comparison.py` compiles a two-scene15.833333s excerpt. CPU illustration schedules six nonoverlapping calculation intervals after6.913197s. GPU begins at10.422131s and processes all six together. Both use matching expressions/results. This is an intentionally simplified contrast, not a claim that real CPUs have no parallelism or a hardware speed benchmark. The first six seconds are visually static and CPU operations are fast; pacing still needs review.

The existing three-sentence user-script excerpt's audio is stream-copied from context-reveal-gpu-narrated-v4. Both encoded audio streams hash to7d08ec908a3317993cae37837f98332f094b64dcd7e028b36fd45795e3995dc8. No new TTS or paid calls. Candidate `.runtime/reference-study/transport-comparison-v2/narrated.mp4` has475frames. V1's insufficient caption contrast was corrected in V2 and V1 preserved.

Verifier now supports explicit scene durations and checks every token in forward/reverse order, including hidden tokens:11,400checks passed, max coordinate error0.0158386px. A12s screenshot confirms GPU calculation labels and readable disclaimer. Scene visibility, actual viewer comprehension, full narration, Gold design matching and Docker E2E are not proven by these checks. This remains a partial new-script transfer, not completion of the two-reference objective.
