# Inferred Relation Alternatives: Private Development Record

## Problem and scope

The frozen mixed script in `experiments/meaning-planning-v1/ice-return-mixed.md`
has four valid beats: a fictional captain, a clearly labeled NASA observation,
a fictional before/after food count, and the captain's decision. A separate
semantic reviewer marked one inferred motivation between the count and decision
UNKNOWN. Repeating the same judgment would not resolve the ambiguity.

Version `hybrid-story@0.14.0` adds two bounded alternatives for exactly that
kind of finding: treat the earlier beat as context, or state only their order.
The original narration, grouping, routes, grammars, numbers, source IDs and
quoted evidence remain byte-identical. An explicitly stated cause is ineligible.
The alternatives consume two shared planning repairs, undergo anonymous AB/BA
review by a separate model, and require one final sufficiency review. A provider
failure, disagreement, multiple findings or exhausted budget stops production.
This is pre-render meaning review, not film approval.

## Actual replay

Input: `output/ice-return-director-01/work/semantic-analysis-1.json`, with the
bound prior review and verified local NASA source catalog.

| Attempt | Observed outcome | Elapsed | Calls recorded |
| --- | --- | ---: | ---: |
| `output/ice-return-alternatives-01` | Strict schema rejected a source quote containing a control character | 3.824 s | 1 |
| `output/ice-return-alternatives-02` | Same schema validation error, now exposed with its field path | 0.943 s | 1 |
| `output/ice-return-alternatives-03` | First candidate review completed; reverse-order review failed with provider 401 `invalid_api_key` | 30.093 s | 2 |

After the repeated schema failure, strict quote options were limited to exact
contiguous substrings without control characters. The third run reached the
reverse-order request, demonstrating the schema issue was fixed. The 401 did
not supply a usable review; no comparison winner, final sufficiency review,
concept, scene plan, image, voice or mixed film was produced. No paid API
fallback or login action occurred. Authentication recovery remains external to
this private experiment.

Error handling now records only the HTTP status and structured error code for
401/403, so later receipts do not copy credential fragments from provider error
messages. This code change does not repair authentication.

## Evidence and next gate

The focused offline semantic and relation tests passed: 18 tests. These tests
exercise both candidate orders, disagreement, final review, budget exhaustion,
explicit-link exclusion and 401 stop. They do not establish that the frozen
mixed film is producible or that new scripts have equal quality. Resume the
same evidence-bound review only after the subscription provider is healthy;
then inspect selected concept, generate original cinematic stills, render and
audit the actual film. Broader held-out scripts and independent final-frame
comparisons remain required before promotion.

Status: `GOAL_NOT_MET`. No human or automatic production approval.
