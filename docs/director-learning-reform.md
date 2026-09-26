# Director learning reform

## Diagnosis grounded in current code

1. `scripts/reference_curriculum.py` tracks sampling, partial study coverage and human approval separately, but its generated shot tasks still initialize semantic fields to null. Coverage is not scene understanding.
2. `harnesses/astra-motion/src/astra_motion/scene_program.py` currently allows camera_push, reveal, emphasize and progress. Standalone study programs demonstrate capabilities absent from this compiler. Importing their prose into a prompt cannot supply those capabilities.
3. `server/src/database/database.service.ts` declares a director_knowledge_candidates table. This audit found no reader/consumer of that table in the searched server/Python production sources. A schema alone is not a learning loop.
4. Blood-bulge V1-V9 preserved useful failures but spent many cycles on a roughly seven-second segment. Numeric improvements were narrower than the full design/meaning/audio objective. V7's measured median speed even lost total displacement; measurement provenance alone does not prove a useful transformation.

## Implemented first bridge

`docs/director-learning-ledger.json` contains two scoped, experimental cases with conditions, counterexamples, failure, correction, required effects, evidence hashes, quality axes and a different-script experiment. Neither is approved Director Experience.

`scripts/reference_learning.py` checks evidence existence and SHA, filters retrieval by scene function, and compares required effects against the actual compiler allowlist. Invalid evidence cannot be retrieved. Every research packet is explicitly production_authorized=false, even if an input record claims otherwise. Paths cannot escape the repository.

The existing curriculum command now emits `director-learning.json` alongside its coverage/backlog output. This is an executable research advisory connection, NOT a live production planner integration or runtime safety gate. The SQL candidate table was not migrated or populated, and no production defaults changed.

Actual audit output: `.runtime/reference-study/learning-reform-audit-v1/`. Ten references, 412 generated tasks, zero complete. The parallel_processing query retrieves both valid cases but flags missing transport_track, object_path and shape_aware_spacing capabilities. It does not certify the current engine can execute them.

Tests: five learning-packet checks plus twelve curriculum regression checks pass. Docker Mock E2E was not run; this change is offline research tooling, not a production release. No paid calls.

## Revised research loop

### Iteration checkpoint implementation

The offline quality evaluator now includes an `iteration_checkpoint`. Each ordered
iteration records an ID, hypothesis, changed variables, observation, next action
and unresolved failure families. Three consecutive observations of the same
failure family request cause review, counting duplicate labels only once per
attempt. Missing history is explicitly RECORD_INCOMPLETE, not proof of learning.
Duplicate iteration IDs are rejected. This advisory does not automatically rerun,
approve, stop production or overwrite a best version. Existing histories have not
been invented or retrospectively marked reviewed. The next integration step is
persisting these records from real reviews and making the production orchestrator
consume the checkpoint with an explicit human override policy.

1. Define the viewer question and intended comprehension before measuring pixels. Specify which design, layout, motion, transition, rhythm, audio and meaning axes the experiment can actually judge.
2. Classify every record as theory, observation, experimental experience or project preference. Do not turn a project-specific palette or an occlusion heuristic into a universal rule.
3. Compare source, best reviewed candidate and new candidate. Latest is not best. Record changed variables, affected axes, remaining regressions and why the next iteration is worthwhile.
4. Validate cheap measurements and geometry before a full render. Render only the affected interval during debugging; then recheck the surrounding sequence for continuity, narration and rhythm.
5. After three revisions of the same failure family, perform a cause review rather than automatically producing another variant. Preserve the full reproduction objective; this checkpoint changes method, not success criteria.
6. Test the candidate lesson on a genuinely different script and independently designed objects. Preserve narration for A/B tests. Ask viewers what happened and why, not only which version looks nicer.
7. Only reviewed transfer evidence can support an engine implementation proposal. Implement the missing operation through a versioned public contract and test it in the real production route; a standalone HTML example is insufficient.
8. Keep human review, technical execution and transferability separate. Promoting a lesson requires its artifact/version to be identified and reviewed; a model-authored approval field is never authorization.

## Next development boundary

Highest-value next step is a reusable transport-track contract and compiler adapter for a GPU task-token transfer, not another untracked visual effect. It must validate time units, ordering, gaps, identity and interpolation; expose unsupported requests rather than silently substituting camera_push. Then verify the exact production path, publish a review packet and compare comprehension/design against the best approved reference.

Track outcome metrics per scene: human correction count, repeated failure rate, transfer review result, quality regression, paid calls, render count and elapsed time. Do not combine these into one aesthetic score. The present work establishes the evidence/compatibility bridge only; production planner consumption, reviewed transfer and quality improvement remain to be demonstrated.

## Quality decision bridge implemented

`docs/director-learning-experiments.json` now binds the GPU compiler-route fixture and its measurement report to explicit file hashes. `assess_experiment` in the learning module validates those inputs, evaluates limited numerical checks, and emits seven separate quality-review questions. It cannot promote a candidate or replace a best artifact. Known regressions require rework while retaining the best; missing/changed evidence is invalid; no measurement checks cannot pass by default.

The curriculum command emits `quality-decisions.json` as well as the learning packet. Real output in `.runtime/reference-study/learning-reform-audit-v2/` records the GPU experiment as HUMAN_QUALITY_REVIEW_REQUIRED despite technical_pass=true. Actual browser checking covered six token centers at all120frames in both directions (1,440checks), with maximum coordinate error0.015625pixels. This proves only the checked single-scene contract execution, not design quality or narrative transfer success.

Five new quality tests, five evidence/retrieval tests and twelve curriculum regressions pass (22total). Cases cover regression preservation, altered video/report hashes, missing measurement coverage, evidence-bound retrieval and refusal to turn numerical success into approval. These are offline research decisions, not a deployed production enforcement service. Docker E2E, planner ingestion, human review and full-reference/new-script deliverables remain outstanding.

The next comparison must not be another unlabeled token test: use the existing designed GPU baseline and unchanged narration; explicitly show input -> calculation -> output and test whether a viewer can explain the difference between sequential and parallel processing. Measure timing/order independently from the human comprehension response. Keep the full original reproduction goal in the coverage audit; current complete count is zero.
