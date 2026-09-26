# Preproduction Brief, Private 0.15.0

## Why this change

Meaning analysis already separated cinematic, editable diagram and registered
source beats. The concept and scene models still had to infer how each selected
diagram grammar should look from a large general contract. This made a generic
title or decorative effect too easy to propose when a script changed. The new
brief carries the accepted information task into both planning stages without
another model call.

## Executable obligations

| Grammar | Minimum visual events |
| --- | --- |
| `cause_change_result` | Cause appears, relation arrives, affected target changes, result holds |
| `step_sequence` | Ordered steps and completion, final step holds |
| `quantitative_comparison` | Values in one unit on a common zero scale, then reading hold |
| `cumulative_change` | Separate increments, computed running totals, total holds |
| `transport_track` | Named endpoints, identifiable moving token, arrival hold |
| `before_after` | One entity and metric, first measurement retained, second on common scale |
| `map_spatial` | Fixed named places, quoted relationships, not-to-scale label |

These obligations are drawn from the existing grammar ledger and runtime; they
do not add a new animation capability. The scene schema already validates most
items. One additional Core check catches a causal diagram whose incoming edge
never changes its target's before/after state. A registered source beat also
retains its claim and catalog boundary, so a modern observation cannot silently
become footage of a fictional or historical event.

## Contract and evidence

The brief records the semantic analysis hash, grammar ledger hash, source
catalog hash and exact source-span hash per beat. It is generated after the
existing independent meaning acceptance, before concept and scene design. Both
stages receive the same object. Concept selection records its hash; scene design
checks it before making a request. A changed stored brief during repair stops
planning. This is structural provenance, not independent verification of facts.

The 0.14.0 candidate was preserved under
`output/hybrid-story-0.14.0-baseline`. Public cinematic-slide and motion
engines were not changed. No image, voice, paid API or live login call was used
for this change. Focused offline tests cover the mixed route, missing grammar
and source, causal-state defect, actual Core planning path, and tamper stop.

## Limitations and next evaluation

The independent subscription reviewer currently returns 401 on the frozen
mixed-script replay. Therefore no new film or held-out transfer result is
claimed from this version. The brief can carry an incorrect analysis faithfully;
its meaning still depends on the separate critic. Additional diagram grammars
still need real scene designs and actual-frame evidence on different scripts.

Status: `GOAL_NOT_MET` for the full mixed-film objective; preproduction contract
implemented and offline-tested only.
