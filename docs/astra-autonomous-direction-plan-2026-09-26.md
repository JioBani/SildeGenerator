# Astra autonomous direction and hybrid production

Date: 2026-09-26. Status: active implementation; not a completed release.

## Updated unattended objective (supersedes earlier acceptance assumptions)

Authoritative user specification: goal-objective.md and pasted-text-1.txt in
`C:/Users/user/.codex/attachments/d82e8bfd-3b85-4be2-b781-fa876f9ea770/`.
Both were read in full after the goal update. Existing implementation is retained;
the new requirements are additions, not declarations that old smoke tests satisfy them.

- No routine user questions, selection requests or human-review waiting state.
- Priority: original meaning/facts, route fit, causal/emotional continuity, rights,
  coherent tone/design, readability, meaningful motion, then time/cost.
- Analyse semantic beats with original-unit coverage, purpose, new information,
  reason/rejected alternatives and evidence needs. Do not invent a dilemma.
- At least three blinded concepts, independently compared; lock a common design
  bible/typography contract across all routes. Preserve two visual anchors at cuts.
- Ten explanation grammars requested; only three are currently implemented.
- Each text role needs safe area, timing and contrast checks (4.5:1 normal, 3:1
  large). Readable duration >= max(1.2 s, effective characters / 8).
- Motivated cameras need easing plus initial/final holds, focal bounds and
  start/middle/end pixel checks; current still hold is not proof of this system.
- Independent actual-frame critic, AB and BA ordering, negative controls and
  held-out data must precede adoption. Generator self-scores never count.
- Acceptance requires all critical dimensions to pass, exact meaning/evidence/
  quantity coverage, >=95% negative detection, >=98% deliberate misrouting
  detection, >=95% held-out route accuracy, >=90% evaluator agreement and >=70%
  held-out superiority, with zero critical regressions. Unknown is not pass.
- Limits: plan repairs 3, repairs per scene 3, total candidates 5. Same cause
  twice triggers engine/input/evaluator diagnosis rather than another generation.
- Final status is AUTO_VALIDATED or GOAL_NOT_MET, never HUMAN_APPROVED. Automatic
  acceptance does not measure real audience emotion or guarantee commercial quality.
- Separate work-improvement, engine-learning and evaluator-learning loops.
  Rule promotion additionally requires >=3 development scripts, >=2 held-out
  improvements, >=95% relevant negative detection and zero critical regressions.
- No paid APIs/ElevenLabs/purchases/login changes, rights-unclear material,
  destructive cleanup, public-engine overwrite or automatic production deployment.

Immediate implementation of these stricter rules:
`app/autonomous_policy.py` rejects missing/unverified/stale evaluations, order
bias, zero-sample metrics, held-out leakage and missing benchmark categories.
It includes a scoped repeat budget. Seven synthetic unit tests exercise policy
logic; they are NOT empirical quality scores. The independent evaluator and
trusted evidence collector are not yet implemented, so this gate cannot establish
semantic validity by itself and is not an automatic service promotion mechanism.
The existing hybrid v3 delivery is explicitly GOAL_NOT_MET under this policy.
Its separate unattended checkpoint preserves technical successes and unmet checks.

## Intended result

User clarification: develop TWO INDEPENDENT ENGINES, not a combined replacement
for the slide product. `narrative-slide` strengthens pure cinematic slide films;
`hybrid-story` is a new motion+slide film engine with optional verified sources.
Their plans, rendering contracts, regression sets and release decisions stay
separate. Sharing infrastructure does not permit implicit route switching.
See [Slide plan](narrative-slide-development-plan.md) and
[Hybrid plan](hybrid-story-development-plan.md). The unattended adoption checklist
for mixed-route films is not imposed wholesale on slide-only films.

A new script produces a coherent film: cinematic still-image shots carry lived
experience and emotion, editable motion graphics explain relationships, and
verified source media supplies evidence. Four visual directions are available:
live-action cinema, 3D animation, Disney-inspired storybook animation, dystopia.
Routine production and improvement do not require a human approval queue.
The Shackleton expedition example is the user's confirmed format reference.

## Baseline and boundaries

- Source of truth: D:/SildeGenerator; existing working-tree changes are preserved.
- classic-slide 1.2.0, cinematic-slide manifest 0.6.0 (README still says 0.5.0),
  astra-motion 0.9.1. A new narrative-slide 0.1.0 candidate isolates new behavior.
- Existing plan describes purpose/takeaway but lacks a typed dilemma, shot reason,
  subject-state chain, and information-change contract.
- Existing reference atlas contains blood-pressure partitions and measured
  experiments. They are partial observations, not completed reproductions.
- Narration, source order, voice timing and prior outputs stay reproducible.
- Use local/mock resources first and the already authorized subscription route
  for generated artwork. No automatic switch to separately billed APIs.

## 1. Reference research

- [ ] Inspect Spring and Sprite Fright as full short films; register legal source,
  duration, native frame rate, hash, shots and stimulus/reaction timing.
- [ ] Record want, obstacle, options, cost, decision and consequence per sequence.
- [ ] Separate creator documentation, directly observed frames and inference.
- [ ] Analyse cut size, point of view, eyeline, withheld/revealed information,
  motivated repetition and reaction holds. Do not turn variety into random cuts.
- [ ] Use TED-Ed blood-pressure observations already in the atlas to seed
  comparison, causal chain, transport, scale reveal and cumulative-change grammar.
- [ ] Record counterexamples, required renderer abilities and transfer fixtures.
- [ ] Register Shackleton archive candidates from holding institutions; an online
  catalogue entry is not a downloaded asset or permission to redistribute it.

Primary sources located during this run:

- https://www.pixar.com/pixar-in-a-box
- https://www.khanacademy.org/computing/pixar/storytelling
- https://studio.blender.org/projects/spring/
- https://studio.blender.org/blog/glue-why-animation-needs-story/
- https://studio.blender.org/blog/sprite-fright-style-guide/
- https://studio.blender.org/blog/sprite-fright-the-illusion-of-simplicity/
- https://ed.ted.com/lessons/how-blood-pressure-works-wilfred-manzano
- https://www.rgs.org/our-collections/stories-from-our-collections/explore-our-collections/photograph-of-the-endurance-by-frank-hurley
- https://github.com/Vchitect/VBench

These sources establish research candidates and evaluation methods; full film
inspection and real viewer emotion have not yet been measured in this run.

## 2. Narrative planning and automatic repair

- [x] Add an opt-in typed shot contract to the real director schema and compiler.
- [x] Bind subject identity, goal/stakes, visible action, state before/after,
  scene purpose, information gain, shot size, camera and causal reference.
- [x] Character-story contracts require a choice with competing costs.
  Observational essays need not invent a protagonist or a historical decision.
- [x] Reject declared duplicate compositions, broken state chains, future
  causes, and empty decision consequences before image generation.
- [x] Feed exact findings into a bounded director repair loop; keep all attempts
  but judge the final candidate. Exhaustion is a visible failure, not approval.
- [x] Carry the selected shot contract into image requests and existing camera work.

## 3. Four styles

- [x] Add style definitions through UI, API, schema and snapshotted image prompts.
- [x] Live-action: physical lighting, lens/shot continuity, restrained performance.
- [x] 3D animation: consistent sculpted proportions/materials and clear silhouettes.
- [x] Disney-inspired: original expressive characters, appealing shape design,
  authored colour scripts and storybook staging, without franchise assets/logos.
- [x] Dystopia: institutional scale, isolated subject, controlled practical light;
  preserve readable faces and causes instead of indiscriminate darkness.
- [x] Generate dedicated preview images; do not reuse unrelated fantasy thumbnails.
- [ ] Render the same held-out script in all four and inspect identity/cut variety.

## 4. Hybrid execution

- [x] Add a versioned hybrid harness with per-scene routing, not whole-job fallback.
- [ ] Emotional event -> narrative slide; relational explanation -> motion;
  claim requiring authentic observation -> verified source media.
- [x] Motion plans specify nodes, edges, quantities/units, before/after states,
  labels, object paths, reveal order and reading holds.
- [ ] Select grammar by semantic relations and requirements, not keyword theme.
- [ ] Source registry binds file hash, origin, subject/date, license, attribution,
  claim and crop. Generated reconstructions never become historical photographs.
- [ ] Preserve object/colour identity at route changes and assemble to one measured
  narration timeline, subtitle track and downloadable video.

## 5. Automatic evaluation and improvement

- [ ] Deterministic checks: source coverage, temporal order, repeated frame hashes,
  OCR bounds, subtitle sync, contact/occlusion where measurable, stream/duration.
- [ ] Separate visual critic: receives actual sampled frames and transition clips,
  script and task, not generator self-scores. Findings cite frame/time evidence.
- [ ] Compare baseline and candidate in both A/B orders; disagreement or insufficient
  evidence triggers another bounded evaluation or retains the baseline.
- [ ] Keep dimensions separate: facts, causality, identity, repetition, readability,
  timing, design, performance. An average cannot hide a factual or identity failure.
- [ ] Re-render only affected assets/shots; check neighbouring transitions again.
- [ ] Persist before -> finding -> edit -> after with hashes and evaluator version.
- [ ] Auto-adopt within the tested capability only after held-out-script regression
  and no critical regression. Record AUTO_ACCEPTED, not HUMAN_APPROVED.
- [ ] Prevent score gaming: include deliberately bad cuts, random ordering, repeated
  shots, plausible wrong diagrams and source substitution as negative controls.
- [ ] Keep automatic thresholds provisional until measured against external
  evaluation data. Automated acceptance is not proof of human emotional response.

## 6. Verification and product delivery

- [ ] Freeze baseline fixtures and select unseen scripts (Shackleton, a personal
  choice story, a scientific explanation); separate development from test cases.
- [x] Run focused schema/compiler/harness tests and provider-free graph render first.
- [ ] Run real script -> designed images -> actual hybrid film with bounded calls.
- [ ] Exercise site selection, progress, error recovery, playback and download.
- [ ] Track first-pass failure rate, edits, repeated-shot rate, critic disagreement,
  time, calls, and script-conditioned visual differences.
- [ ] Ship a versioned candidate with rollback and capability reports, then activate
  only the measured path. No routine human review dependency is introduced.

## Completion evidence

The goal is complete only when all four styles render, the hybrid film contains
real routed scenes and attributable source media, unseen scripts obtain distinct
appropriate shots, and the automatic compare/repair/adoption loop runs end to end.
Contracts and unit tests alone do not establish those results.

## Implemented checkpoint: 2026-09-26

- narrative-slide@0.1.0 stays private. Existing public harness defaults unchanged.
- The real director request accepts the opt-in typed shot contract, writes each
  direction review, feeds failures back, and stops after two repair attempts.
  MockTransport exercises the actual request/compiler path; no live model call
  was needed for those tests. It verifies declared intent, not semantic truth.
- Four styles reach the UI, API enum/database constraint, RenderRequest,
  StyleBible/schema, selected prompts and image requests. Local illustration
  remains limited to its two supported styles; new styles cannot silently use it.
- Builtin ImageGen generated four fictional polar-rescue previews. See
  narrative-style-preview-manifest.json for exact prompts and saved paths.
  They are not Shackleton historical evidence. No separately billed API calls.
- Four ~10-second single-shot videos use those images, identical local Korean
  SAPI voice and the real harness graph. Version 2 output is retained; version 3
  increases subtitle size/margin after rendered-frame inspection. This is not
  an unseen-script multi-shot film or production API/queue E2E.
- rendered_review.py samples actual output frames, checks stream/timing/size,
  near-uniform pictures and near-duplicate scene pictures, and binds observations
  to video/plan hashes. It explicitly does NOT score emotion, factual accuracy,
  semantic alignment, OCR or acting. It is used by the smoke runner, not yet
  the service's final delivery gate.
- Focused verification: 20 planner tests, 7 direction tests, 2 style tests,
  3 real-FFmpeg observation tests, 1 server style test, 4 Playwright UI tests.
  Web/server builds and narrative harness validation pass. This is not the
  full repository suite. Browser checks cover desktop/mobile preview loading,
  option submission, local-fallback exclusion and preserved motion UI.
- Candidate UI preview: http://127.0.0.1:18808/. The API/container release has
  not been upgraded with these changes; this is not a production activation.
- Next: mixed scene execution + source registry, then independent frame-based
  critic and bounded comparison/adoption. No routine human approval queue is
  being added. Research/full-film/transfer milestones remain open.

## Hybrid execution checkpoint: 2026-09-26

- Previous goal turn made implementation progress; continuation reaped the exact
  existing render session rather than starting a duplicate. The completed v2
  movie was subtitle-only and was rejected by actual-picture comparison.
- hybrid-story@0.1.0 remains private. Its scene routes are cinematic still,
  editable GSAP diagram, and registered source. Only cinematic routes submit
  generated-image tasks. Source/diagram preparation is in Core and does not
  silently call a provider. Full runner/queue/UI E2E for this path remains open.
- `output/hybrid-story-smoke-v3/delivery/hybrid.mp4`: 33.792 s, 1280x720, 24fps,
  Korean offline SAPI voice, real pinned HyperFrames/GSAP + FFmpeg output. It is
  an authored integration demonstration, not a live director's new-script film.
  A fictional AI expedition picture, editable causal graph and NASA modern
  observation are visibly distinct. The final picture is an intentional callback.
- v2 retained as a negative control. Preserving the timeline registry and naming/
  sizing the composition root restored mounted output. A pinned HyperFrames
  snapshot regression now checks cinematic pixels and late diagram state changes.
- The blank-frame detector originally confused channel colour differences with
  spatial variation. v0.2 measures channels independently and detects tinted
  blanks. It also tests declared diagram changes against output pixels above the
  subtitle region. These are technical observations, not semantic judgments.
- New hybrid jobs opt into the actual Core final-picture gate. A failed check is
  saved before final_video/success and stops delivery without paid retries.
  Legacy harnesses do not opt in. The public SDK guide documents both additions.
- Source registry checks original hash/path/image readability before planning and
  again during preparation; renderer verifies the prepared hash. The fixture is
  a NASA SVS 2016 Antarctic sea-ice data visualization, NOT a 1915 Shackleton
  photograph. The official page caption and filename contain inconsistent day
  details; only the year and subject are used. No archival-accuracy claim.
- `harnesses/hybrid-story/knowledge/visual-grammar.json` binds three recipes to
  the existing partial blood-pressure observation atlas: causal response, common
  scale comparison and endpoint transport. Applicability, counterexamples,
  limitations, pending transfer status and hashes reach actual planner requests
  and per-attempt hybrid reviews. This is not full reference reconstruction.
- Unknown source IDs enter the real planner's bounded repair loop. Two MockTransport
  tests prove successful correction and exhaustion without changing narration or
  silently changing route. Source metadata is not proof of factual correctness.
- Focused verification this continuation: hybrid 9 (including real snapshot test),
  planner 20, narrative direction 7, rendered observations 5, render cache 2,
  segment planning 3: 46 tests passed. Separate Playwright audit verifies actual
  MP4 loading/seeking, nonblank route pixels, diagram changes and desktop/mobile
  review layout. Not the entire repository suite.
- `output/hybrid-story-smoke-v3/review.html` is the local review artifact. The
  original receipt is unchanged; a separately hashed observation report records
  the current observer's findings. Source+video dates are disclosed in the review.
- No new image generation, no paid APIs, no login changes, no production rollout.
- Still required: full short-film observation, richer topic-specific diagrams,
  independent factual/visual critic, held-out multi-shot four-style films,
  blinded-order comparison and bounded automatic adoption, actual service E2E.
  The complete goal remains active; no human-review queue was added.
