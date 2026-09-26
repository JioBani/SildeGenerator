# Independent Motion + Slide Hybrid Engine

Status: private engine, hybrid-story@0.5.0. Separate from narrative-slide.

## Output

One film with script-conditioned cinematic still shots, editable motion graphics,
and verified source inserts when evidence is required. No fixed route ratio.
All routes share the film's concept, typography and narration timeline.

## Work

- Analyse semantic beats before selecting feel/cinematic, understand/motion or
  verify/source. Split mixed purposes into adjacent beats when necessary.
- Compare at least three blinded concepts with an independent evaluator; retain
  the chosen concept and common design-bible version across route changes.
- Expand the current five explanation grammars to the requested ten, preserving
  applicability, counterexamples, supported operations and observed evidence.
- Keep editable labels, quantities/units, paths, states and reading holds; do not
  replace explanatory animation with a generated infographic or a still zoom.
- Verify source meaning/date/rights and bind originals, prepared files and visible
  attribution. Missing evidence is SOURCE_NOT_AVAILABLE, not a generated substitute.
- Maintain at least two intentional visual anchors at route changes and inspect
  real boundary frames for continuity, typography and timing.
- Exercise the unattended acceptance policy with independent critique, reversed
  A/B order, negative controls and held-out scripts. Technical pixel checks alone
  do not qualify a film for AUTO_VALIDATED.

## Supplied Format Reference (2026-09-26)

See [the supplied Shackleton film analysis](reference-shackleton-hybrid-20260926.md).
The inspected 90-second film mixes illustrative narrative shots, limited pose
changes, illustrated maps with independently moving ships, and source-labelled
photographs. Its rights and historical claims are not verified by this analysis.

Private 0.2 now implements a first within-shot composition: an illustrated plate,
registered alpha sprite, editable cubic route and endpoint states. The 0.1 graph
transport primitive was not equivalent to this capability. Shared coordinates,
fixed-camera rendering, asset provenance and conservative sprite bounds execute.
General occlusion, moving-camera composition, portrait reauthoring and automatic
semantic matching still need implementation and evaluation.

First benchmark: an original illustrated route/moving-object shot, followed by
an identity-consistent character pose change and hold. Validate rendering before
unseen-script transfer. Source reference assets stay out of public deliveries.
The supplied 90-second reference does not change the product's 60-second limit.

## Engine Boundary

Planning contract engine_family=hybrid. Every scene needs an explicit typed route.
Own prompts/config/render package and release snapshot. May reuse tested SDK
capabilities without importing another harness's private implementation. The
slide engine remains usable without the hybrid runtime or source catalog.

## Completion

New unseen scripts produce appropriate mixed-route films with zero critical
failures and meet the authoritative unattended acceptance specification. Evidence
from a pure-slide test alone cannot pass this goal. No automatic public deployment.

## Transfer Requirement (2026-09-26)

The user's criterion is quality on a different script, not replay of one polished
reference scene. A renderer demonstration is not an automatic-director transfer.
Information motion must adapt its representation to the relationship: quantities,
increments, ordered steps, causes and transport already have separate contracts.
Whole/detail, before/after, decomposition/recombination, evidence/judgment and
general map/spatial reasoning still need dedicated capabilities and evaluation.

Private 0.3 adds cumulative_change and step_sequence and upgrades comparison
geometry. See semantic-diagrams-progress-20260926.md for actual three-script
outputs, failures, fixes and the limits of those tests. Narration is preserved;
numbers require source quotes, scale and units. The positive examples were
authored, not independently held out. Final quality remains GOAL_NOT_MET.

Private 0.4 adds a separate meaning-analysis request before scene design. Core
turns its exact spans into source units and binds purpose, route, grammar and
evidence IDs to the resulting scenes. See semantic-planning-progress-20260926.md.
This is a tested protocol connection, not measured semantic accuracy on new scripts.
Independent route alternatives, three blinded concepts and held-out quality tests
remain required; low confidence or missing capability currently fails closed.

Actual new-script development probe now exists. Meaning analysis selected three
appropriate-looking routes, but full design failed on runaway phase prose and a
transcript write error. A separate critic detected a deliberately wrong route in
both orders, yet disagreed about causality and did not approve a winner. See
meaning-live-evaluation-20260926.md. Stream limits and transcript resilience are
regression tested; no fresh film or held-out quality success is claimed. Distinguish
event causation from motivation/context before the next semantic benchmark.

Private0.5 now separates those relation kinds and removes the inherited mandatory
character dilemma. A second actual director probe completed its three-scene plan,
with consistent independent AB/BA pre-render criticism. A fresh26.75-second mixed
film is rendered from that plan, two original builtin images and local word-timed
voice.366 native-rate diagram frames passed common-scale/event-timing checks.
See semantic-relations-film-progress-20260926.md. This is one DEVELOPMENT case,
not held-out superiority or complete autonomous service production. The diagram's
fixed light design is still visually discontinuous with the night stills; shared
design/concept selection is a remaining visible bottleneck, not just documentation.

Private0.6 connects one typed executable design to all routes, rejects inconsistent
designs/low declared contrast, and preserves original image/source pixels. Actual
controlled candidate output/meaning-film-design-01 keeps the prior script, voice,
images and geometry; it is explicitly not a new-script or blind-concept success.
See shared-film-design-progress-20260926.md. Independent three-concept selection,
full-frame typography/asset adherence and broad held-out quality are still missing.

Private0.7 connects three concepts and distinct-model ABC/CBA criticism before
scene planning. The actual five-call development probe exposed an execution
false positive, not a quality success: ledger layouts, shared brackets and a
diagram zoom were approved despite missing runtime support. Exact mark limits
and new local-route camera rejection now address the concrete gap. The actual
saved plan is rejected by the new deterministic check;124 focused tests pass.
See concept-selection-progress-20260926.md. Revised critic reliability and
new-script film quality are still unproven. Public engines are unchanged.
