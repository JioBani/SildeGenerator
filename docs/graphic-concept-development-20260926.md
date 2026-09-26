# Route-aware graphic concepts: development evidence

Status: EXPERIMENTAL / GOAL_NOT_MET. Private hybrid-story0.12.0 only.
No public deployment, new login, image provider or paid API call.

## Problem and hypothesis

The prior reservoir pilot (output/sufficiency-scene-plan-01) passed semantic
sufficiency but failed concept selection: all proposals invented a cinematic
still around an accepted diagram-only beat. The old critic also demanded shot,
viewpoint or lighting differences even when no cinematic beat existed.

Hypothesis: preserve accepted routes and offer genuine executable diagram-design
choices. Do not lower distinctness to names/colors or add irrelevant shots.

## Implementation

- film-design-0.2: columns, rows, dot_tracks for before_after only.
- Columns encode magnitude as height; rows as length; fixed dots as position.
- All retain two exact quoted observations, one entity/metric/unit, a common zero
  scale, ordered reveal and the earlier observation. No interpolated data or cause.
- concept-selection-0.2 fixes accepted beat routes and pins the new design schema.
- Core rejects capabilities from absent routes; a snapshot-only batch must have
  three actual distinct layouts. Independent ABC/CBA judgment remains mandatory.
- concept-review-0.5 evaluates differences within existing routes, not invented
  cinematic material. Critical winner criteria and agreement gates are unchanged.
- Legacy design0.1 serialization/hash and column markup remain identical.
- New design requires scene0.6; earlier versions fail instead of guessing.
- Numeric pixel auditing now measures horizontal lengths and fixed dot centers.

This does NOT add a new semantic grammar. Seven grammar families remain available;
whole_detail, decompose_recombine and evidence_judgment are still missing.
Other diagram-only families lack equivalent executable design alternatives.

## Actual director experiments

| Development input | Actual calls | Time | Result |
| --- | ---: | ---: | --- |
| Reservoir, 18cm then 11cm | 6 | 131.898s | One diagram, rows selected, rendered |
| Battery, 80% then 35% | 6 | 132.499s | One diagram, rows selected, rendered |
| Warehouse, 45 then 45 items | 2 | 15.571s | Critic quotation invalid; stopped |

All calls used the existing subscription bridge: Sol for generation, Terra for
independent reviews. Separate paid API calls:0. Both completed plans had 21/21
per-criterion agreement between concept review orders. Reservoir was a tie between
passing designs resolved by the documented deterministic tie-break, not measured
aesthetic superiority. Battery had a consistent preferred identity.

Warehouse failure: the critic added literal double-quote characters around its
source quotation. The strict source-substring gate correctly rejected it with
semantic_critic_quote_not_grounded. No concept, voice or video was made for that
input. Do not count it as a successful transfer or silently trim the evidence.
Next evaluator work: a versioned bounded quote-selection schema, preserving the
exact-source gate and its negative controls. No retry was made this turn.

These are DEVELOPMENT scripts, not a hidden held-out benchmark. Battery was
previously used as an authored renderer fixture; it is new to this director probe,
not an unseen domain. No full mixed-film quality claim follows from this result.

## Actual media and checks

- output/graphic-concept-film-01/delivery/preview.mp4: reservoir,20.667s.
- output/graphic-concept-battery-film-01/delivery/preview.mp4: battery,20.709s.
- output/snapshot-design-dev-01/review.html: three authored layout variants of
  the SAME battery narration,20.709s each. Not three transfer scripts.

All are1280x720,24fps,local Microsoft Heami/SAPI narration with16kHz word events,
editable SVG marks/labels and GSAP reveals. No generated artwork or source inserts
were needed by these accepted single-purpose scripts. This does not waive the
overall goal's cinematic/diagram/registered-source mixed-film requirement.

Five output videos passed numeric geometry/onset/retention checks over496 frames
each (2480 sampled-rate frames total) and15 frozen/reversed negative controls.
Five browser text-box checks passed, including injected caption collision and
left clipping. Two maximum-contract-length stress layouts also passed. Text checks
are DOM font geometry, not OCR or complete output-subtitle pixel inspection.

Actual reservoir frame13s was visually inspected: correct two bars, common origin,
18/11cm labels, separated captions. It is a functional explanatory diagram, not
evidence of reference-film aesthetic quality or emotional engagement.

No per-script code or post-selection design edit was needed for the two completed
director videos. Timings were bound to measured local narration by the existing
adapter. This is local Core/Harness rendering, not production queue/UI E2E.

## Verification and boundaries

Focused legacy/new-design suite:39 tests passed. Broader run before the final
additional numeric test:124 passed. Final regression result is recorded in the
learning record:125 passed in74.837s. Bootstrap checks passed; existing occupied ports were untouched.
The original0.11 harness remains at output/hybrid-story-0.11.0-baseline.

The goal remains unmet: third development input failed, no held-out superiority,
no complete independent rendered-film comparison, missing information grammars,
source insertion and four-style full-film tests still required. This change is
not ACTIVE, HUMAN_APPROVED or a public release.

## Reproduction

Use the pinned slidev05test-runner:working-tree Docker image and repository mount.
Run tests from video-generator with app/tests on PYTHONPATH. Director probes use
scripts/probe_meaning_planning.py with explicit --allow-subscription-director.
Render through scripts/render_director_probe.py, first --prepare-voice, then local
scripts/synthesize_timed_review_voice.ps1, then render. Use fresh output directories.
Run scripts/audit_numeric_motion.py against prepared-plan.json and the final MP4;
scripts/audit_snapshot_text.mjs measures the generated project HTML. Never reuse a
receipt after changing its plan, video or design. No paid fallback is configured.
