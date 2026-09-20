# ADR-0009: Deterministic narrative plan compiler

- Status: accepted
- Date: 2026-09-21

## Decision

The planning model proposes only semantic choices: nested sequence/group/scene intent, the number of consecutive source units consumed by each scene, keycut positions, visual direction, and continuity appearance/reference scene numbers.

The runner is the sole owner of runtime structure. A deterministic compiler assigns and derives:

- exact source-unit slices and narration;
- continuous scene, group, and sequence IDs;
- group and sequence source-unit ranges;
- one keycut per sequence, every parent keycut link, and the master keycut ID;
- continuity asset IDs from category and stable array order;
- scene present/reference asset IDs from asset appearance/reference scene numbers;
- reference limits and continuity-disabled empty state.

Model output no longer contains runtime IDs or foreign-key lists. Invalid or out-of-range numeric hints are clamped, filtered, or dropped deterministically and recorded in usage metadata. They do not trigger a second paid planning call.

## Rationale

If an invariant can be validated without interpretation, it can generally be constructed without model reasoning. Asking a model to duplicate IDs across a large JSON document created avoidable referential failures such as declaring a character as `asset-object-001` while scenes referenced `asset-character-001`.

MCP and conversational skills are not used for this responsibility because job execution must remain available, versioned, testable, and deterministic inside the runner without an external agent session.

## Compatibility

The compiled `ScenePlan` runtime and persisted blueprint remain unchanged, so image scheduling, administration, resume artifacts, and Creative Harness consumers keep the existing public contract. Only the model-facing proposal schema changes.

## Verification

- compiler unit tests cover exact source preservation, canonical hierarchy IDs, keycut parents, and canonical continuity references;
- the historical mismatched asset-prefix case cannot be represented in the model-facing schema;
- existing plan validation remains as an assertion over compiler output;
- classic and experimental harness prompt sets explicitly forbid model-generated runtime IDs.
