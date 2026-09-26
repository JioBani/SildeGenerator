# New-Script Meaning Planning and Independent Evaluation

Overall: GOAL_NOT_MET. Private hybrid-story@0.4.0 only; no public deployment.
Progress classification: implementation and actual development evidence, not a
completed film, held-out validation, or human approval.

## Requirement

The same quality must transfer to different scripts. Information motion must
choose a representation appropriate to quantities, causes, processes, spatial
relationships and other information rather than repeat a polished reference shot.
Do not call three authored renderer examples an autonomous transfer benchmark.

## Actual Subscription Probe

Input: experiments/meaning-planning-v1/development-script.txt. This newly authored
development example concerns Jisu, a missed bus, a father at hospital and explicit
example journey times of walking40min and cycling15min. Not a real transport claim.
It has not been reserved as held-out data and cannot subsequently count as such.

Existing service-owned bridge returned200 for health and model listing. No login,
credential access, desktop authentication borrowing or paid API fallback occurred.

Actual gpt-6-sol/low meaning analysis completed in40.106s and selected:

| Beat | Function | Route | Grammar |
| --- | --- | --- | --- |
| 1 | Experience the missed bus and urgent goal | cinematic | none |
| 2 | Compare two example travel durations | diagram | quantitative_comparison |
| 3 | Experience the choice and departure | cinematic | none |

Exact source text coverage passed, including whitespace. That is structural
evidence, not independent truth of all relations. The following full scene-design
request did NOT finish a valid plan: it repeated prose inside motion.phases and
finally failed on a summary.json atomic-replacement PermissionError at521.440s.
The whole probe took561.746s. The bound was600s. There is no new delivery movie.
Do not attribute the observed filesystem lock to a particular process without
evidence; the output repetition and write failure are separate observed problems.

Evidence:
- output/meaning-live-dev-01/receipt.json
- output/meaning-live-dev-01/work/semantic-analysis-0.json
- output/meaning-live-dev-01/work/codex/attempt-1/output.txt

## Independent Critic

New app/semantic_review.py uses a separate request and gpt-5.6-terra/low. It receives
original spans, route/grammar, causes and source references, not generator
confidence, approval claims or rationales. A typed report covers every beat and
four distinct criteria: route fit, grammar fit, preserved meaning and causality.
Unknown/failed criteria cannot win. Quotes must occur in the corresponding span;
failed/unknown findings need a repair target and recheck scope.

This is PRE-RENDER evaluation: no video time or problem-frame evidence is invented.
Two requests compare original/control and then control/original. Candidate hashes,
not displayed letters, bind the verdict. All criterion verdicts and the winner
must agree across order; different request IDs alone do not prove independence.

The deliberate control changes beat2 from diagram to cinematic and removes its
grammar. Both orders detected the route error. However AB selected the original,
while BA rejected BOTH candidates. BA found that the urgency in beat1 did not
cause the example journey times in beat2. AB treated that same link as narrative
placement/motivation. Grammar verdicts also differed on the wrong-route control.

Result: ORDER_DISAGREEMENT. Do not report2/2 route detections as passing the full
negative suite,95% benchmark,90% evaluator agreement or candidate film superiority.
No automatic selection/promotion occurred. This was a critic-calibration probe,
not a genuine previous-engine versus improved-engine film comparison.

Evidence: output/meaning-critic-dev-01/{inputs,receipt}.json and work/{ab,ba}.json.
The CLI now exits nonzero for failed controls, not only transport errors.

## Fixes and Rechecks

1. Private semantic planning limits each motion phase to240 characters in the
   requested schema. Old nonsemantic schemas are unchanged.
2. A streaming guard rejects total output above128000 characters, a JSON string
   above8000 raw characters, or repeated long blocks within one string. It does
   not splice partial output into a usable scene or retry into another provider.
3. Guard checks delta streams and completion-only responses. Normal repeated JSON
   keys across objects are not mistaken for a repetitive prose string.
4. Transcript summaries are written at most once per250ms while streaming; append
   logs retain all events/output and terminal states flush. Brief PermissionError
   gets bounded retries; persistent storage failure remains a failure.
5. Unknown token usage for failed planning is recorded explicitly going forward.

Offline replay of the ACTUAL saved failure rejected at12647 total characters
because its current JSON string exceeded8000; the saved output had25664 characters.
This proves rejection of that recorded stream, not a successful live retry or
measured improvement in generation latency. No second generation was performed.

Focused Docker regression:86 tests passed in21.862s, including9 independent-review
tests,6 stream/transcript tests and the runaway-completion integration regression.
This retains70 previous focused tests. It is not the full repository test suite.
The metadata-only tokens_unknown addition was checked in the subsequent focused run.

Reproduction (from repository root in the existing runner environment):

```text
python -m unittest test_planning_stream_guard test_semantic_review test_semantic_planning test_semantic_diagrams test_hybrid_story test_hybrid_planner test_hybrid_render test_illustrated_transport test_planner test_engine_separation test_narrative_direction test_review_voice_cues
python scripts/audit_meaning_development.py output/meaning-live-dev-01 output/meaning-critic-dev-01 output/meaning-development-audit-NEW.json
```

Audit: output/meaning-development-audit-01.json binds reports and failed stream to
SHA256. Existing evidence is preserved, not rewritten to match the corrected code.

## Three Separate Learning Loops

- Work improvement: no scene plan/movie accepted; retain previous renderer examples.
- Reusable capability: bounded phase/output contracts and resilient transcript
  persistence are implemented and regression tested. Not a new visual grammar.
- Evaluator improvement: contextual sequence, motivation and actual event causation
  need explicit distinct semantics. Both generator and critic require the same
  relation definition and positive/negative examples, not a prompt tuned to pass
  this one script. This remains a hypothesis, not an approved director rule.

Next development experiment: define grounded relation endpoints and relation kind;
test direct physical cause, decision motivation, background context and merely
preceding events separately. Freeze definitions before fresh held-out evaluation.
Do not silently delete the questionable link and relabel the first probe a success.

## Cost and Scope

Four actual subscription-model requests: meaning1, scene design1, independent
review2. Three completed requests report7981 input and3248 output tokens in total;
the failed scene-design usage is unavailable and is NOT counted as zero.
Separate paid API calls0; image calls0; voice calls0. Review duration69.934s.
No external purchases, login, secret inspection, destructive deletion or deployment.

Still absent: valid full live plan/movie for this script, independent concept
selection, low-confidence alternate-plan orchestration, five remaining diagram
families, complete typography/camera review, held-out film comparisons and all
overall acceptance thresholds. Public engines and approved assets are unchanged.
