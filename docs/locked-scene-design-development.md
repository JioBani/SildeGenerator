# Locked Scene Design: Private Development

Goal remains GOAL_NOT_MET. This candidate addresses a specific transfer bottleneck:
the scene planner was rewriting accepted meaning spans and design tokens while
repairing unrelated errors. The water-script baseline used four scene calls and
still merged/lost a beat. It remains preserved in output/concept-water-scenes-03.

## Ownership

Private hybrid-story0.8 uses locked-scene-design-0.1. The previous0.7 harness is
preserved at output/hybrid-story-0.7-baseline. Public engines are unchanged.

- Meaning analysis owns exact ordered narration spans, route, grammar, evidence
  requirements and typed relations. Those decisions still need semantic evaluation.
- Independently selected concept owns the shared design tokens.
- Scene director owns visible staging, subjects/states, camera intent on cinematic
  shots, diagram objects/quantities/timing, and sequence/group intent.
- Core owns expansion to runtime ScenePlan, source counts, references and hashes.

The director receives exactly one named design slot per accepted meaning beat.
Sequence groups reference those IDs once in source order. Duplicate, missing or
reordered references fail rather than dropping or merging narration. Fixed fields
are absent from model output, not retyped and then silently repaired. Attempts to
supply those fields fail. Diagram/source cameras are fixed because the renderer
supports only hold there. Cut is the only supported hybrid transition.

This does not replace creative shot planning with a topic template. Accumulation
amounts, comparisons, graphic nodes, reaction staging and source claims are not
filled with canned subject-specific content. The current one-beat/one-scene limit
is inherited from semantic-beats0.2, not a claim about unrestricted film editing.

## Negative Cases

Tests cover missing/extra slots, source-order reversal, duplicate IDs, source-count
override, transition override, grammar/design injection, local camera injection,
and forged semantic layout. Core source binding uses only accepted registered IDs.
The existing strict plan, semantic coverage, causality, design, quantity and asset
preflight gates still run after expansion. Contract pass is not film approval.

## Bounded Actual Comparison

The same water script, accepted four-beat analysis and garden_scale concept are
reused with their original evidence hashes. Rendering capabilities and concept
review input are unchanged; the schema/ownership boundary is the intervention.
The comparison command records the failed previous receipt and allows zero scene
repairs for this new-engine probe. It must not reset the old candidate's exhausted
budget by renaming a directory. No new concepts, external paid APIs, login changes
or public deployment are requested.

Results are recorded separately after the actual process completes. No film,
held-out superiority or viewer emotion is implied by schema/unit-test acceptance.

## Actual Development Result: 2026-09-26

- Prior scene design: four subscription calls, three repairs, failed beat coverage
  after 428.243s. Evidence: output/concept-water-scenes-03/receipt.json.
- Locked design: one subscription scene call, zero repairs, contract pass in
  124.518s. Evidence: output/concept-water-locked-01/receipt.json. This is one
  development comparison, not a statistically established first-attempt rate.
- Three original native ImageGen stills were made from the exported Core prompts.
  Images 2 and 4 referenced image 1. This agent-mediated artwork step is not the
  service image-provider path. Four local SAPI utterances provide measured timing.
- Final output: output/meaning-water-film-02/delivery/preview.mp4, 33.875s,
  1280x720, 24fps, H.264/AAC. No external paid API or ElevenLabs calls.
- Routes: cinematic empty can, cinematic resolve, editable cumulative diagram,
  cinematic watering. The fictional example does not require a source-media shot;
  no real evidence is fabricated. Narration remains unchanged.
- Numeric audit decoded 470 diagram frames. The 10/30/45-liter cumulative widths
  were 106/320/480px at audit resolution versus 106.67/320/480px expected.
  Voice-aligned starts were within tolerance. Frozen-start, frozen-end and
  reversed negative controls all failed. This is not whole-film validation.
- Focused regression: 126 tests passed in 56.227s. Harness validation passed.
  Audio was non-silent, mean -21.2dB and peak -3.8dB; these are not LUFS figures
  and do not establish speech naturalness or intelligibility.

The first render attempt stopped before video on an over-restrictive normalized
event gap. Shared-design accumulation now checks actual .6s animation separation;
legacy normalized guards remain. The same voice and assets were reused without
regeneration. The 12000-character planning guard also caught redundant contract
descriptions. Descriptions were shortened; the guard was not enlarged or bypassed.
Planning and final-render source hashes differ for those recorded fixes; both
snapshots remain in their receipts. No source receipt was overwritten.

## Actual Frame Review And Next Work

The contact sheet and full-size 18s frame were inspected. The final sheet's empty
last tile is contact-sheet padding, not evidence of a black video ending.

- The event labels redundantly repeat the cumulative values already printed by
  the renderer. Add structured event-only labels plus ownership/negative tests;
  do not strip arbitrary words from model text or patch only this one script.
- The second cinematic still varies position but weakly communicates resolve.
  First two shots share a wide view. Stronger action/shot contrast needs an
  independent actual-frame review; contract acceptance did not establish it.
- The final still shows watering, not the entire scoop/fill/pour performance.
  This limited representative-action scope is not a validated actor capability.
- Only five of ten target graphic grammar families are implemented. Comparison
  and accumulation have actual numeric pixel evidence; that does not prove all
  information types or equivalent quality on unseen scripts.

State remains GOAL_NOT_MET / development only. Public deployment, held-out film
superiority, full independent film review and audience response are not approved.
Next: resolve label ownership and actual shot differentiation, then expand and
test unsupported information structures on separately frozen held-out scripts.
