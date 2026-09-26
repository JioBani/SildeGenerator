# Meaning Analysis Before Scene Design

Follow-up: an actual subscription probe and independent AB/BA critic now exist;
see meaning-live-evaluation-20260926.md. The original Mock-only results below are
historical to this implementation turn, not a claim that no live probe exists.

Overall status: GOAL_NOT_MET. Goal remains active.
Candidate: private hybrid-story@0.4.0, render payload hybrid-scene-0.3.
Prior goal turn classification: progress (real three-script renders and new diagram
capabilities, not a wait or a restatement). This turn adds the upstream connection.

## Problem Confirmed

Before this change, create_plan supplied punctuation-derived source units directly
to scene design. Source units were exact, but their boundaries were not semantic.
A sentence containing a person's experience and its explanation could not easily
become two purpose-specific scenes without changing the source-unit budget.

## Implemented Path

create_plan, only when the selected private harness opts in:

1. Separate semantic_beats structured request through the existing subscription bridge.
2. Validate exact character coverage, purpose/route structure, causal order,
   supported grammar and known evidence IDs.
3. Compile accepted literal spans into source units with deterministic offsets/IDs.
4. Supply the complete analysis to scene design before any image or voice work.
5. Bind one beat to one scene; reject merges, narration changes, route/grammar
   substitution and source changes. The binding is Core-owned, not model approval.
6. Persist the analysis, script/response/analysis hashes, binding and repair findings.

Fields include viewer change, story/information functions, chosen and rejected
routes, rationale, new information, emotion, causes, research/evidence needs,
grammar, transition and confidence. The source text is not whitespace-normalized.

This extends the public SDK and Core because a renderer-only prompt change cannot
replace the source partition before planning. The harness imports public SDK only.
No network call is initiated by the harness itself.

## Failure and Cost Boundary

- Missing source, unsupported grammar or low confidence stops before scene design.
  It is not retried into a conveniently different task or inflated confidence.
- Repairable analysis/design errors share at most three repair requests.
- Two consecutive equivalent structural failures stop further retries.
- Provider401, timeout, cancellation or incomplete stream never triggers API fallback.
- Request transcripts, usage records and failures are retained. Unknown failure
  token usage is explicitly unknown, not asserted to be a free successful call.
- Plain deterministic Mock mode cannot impersonate semantic analysis. Integration
  tests explicitly replace HTTP transport and do not contact any live provider.
- Old harnesses without semantic_analysis keep their existing call count/behavior.
- First supported duration contract is episode_60; long-form merge is not silently
  supported with incorrect local beat references.

## Validation

Focused regression:70 tests, including16 new meaning-contract/integration cases.
Saved console evidence: output/semantic-planning-v04-tests.txt.
Harness validation passed for private0.4.0.

Cases include a single Korean sentence split at the shift from hesitation to
explanation, exact whitespace retention, future-cause rejection, route mismatch,
missing alternatives, false source claim, unsupported grammar, low confidence,
Core-owned binding, strict JSON schema, staged request order, bounded repair,
shared repair allowance,401 failure, and no deterministic fallback.

The suite also retains the prior54 tests for the real pinned-renderer smoke,
diagram quantities, illustrated transport, old planner behavior, separate slide
mode and timed caption extraction. These are focused tests, not the entire repo.
Bootstrap checks passed; existing occupied local ports were not changed.

## What This Does Not Prove

The semantic-stage integration tests return authored Mock responses. They prove
execution order, enforcement and repair behavior, not a model's actual skill.
The purpose/route mapping checks declared intent, not truth of the interpretation.
Confidence is not an independent score. A registered source ID does not prove that
its image supports the proposed claim. No held-out accuracy percentage is claimed.

No new delivery video was generated in this turn. The previous real three-script
baseline remains output/semantic-diagrams-v03-run5/review.html. That authored
baseline must not be relabeled as output from this new automatic analysis stage.

Still required: independent route/concept evaluation including uncertain cases,
three blind concepts, actual new-script director runs, remaining five grammar
families, full mixed films, source meaning/rights checks, actual-frame typography
and camera inspection, AB/BA and held-out transfer against the requested thresholds.
No human approval, viewer emotion verification or commercial quality guarantee.

## Safety and Rollout

Real provider calls this turn:0. Paid API calls:0. Image calls:0. Voice calls:0.
No login, secret inspection, deletion or deployment. Pure-slide and public engines
are preserved. Private0.3 source snapshot is in output/hybrid-story-0.3-baseline.
The goal has not been reduced to a Mock test or this16-case contract suite.
