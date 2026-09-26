# Visible Text Meaning Gate

Status: GOAL_NOT_MET. Private hybrid-story0.13.1; public engines unchanged.
Previous goal turn made progress: exact evidence binding, a real rendered stock
comparison and discovery of an incomplete generated title. No active process was
left to wait on. This turn addresses that observed failure without changing the
overall target of high-quality films on different scripts and information types.

## What Changed

The actual Core planner now invokes an opt-in independent text gate after its
structural, semantic binding, direction and diagram checks. It checks executable
diagram titles, node states/labels, edges, units, snapshot labels and spatial
labels against narration and their diagram. It does not inspect invisible prose
as though it were rendered, nor demand a sentence where a noun label suffices.

Every judgment must cover the exact ordered text IDs. Completeness, fidelity and
referent clarity are separate. FAIL needs repair evidence; UNKNOWN stops.
The critic model differs from the generator. Provider errors never fall back.
Old contracts have no added model call. Core integration is tested through
create_plan with explicit mock transport; the actual frozen-plan probe uses the
same gate with the real subscription models.

Only failed text slots may be edited. Narration, numeric values, scales, geometry,
timing and source quotes are not editable. Grounded units/referents cannot change
through this repair. The modified diagram must still pass its original contract.
One text repair consumes one remaining shared planning repair; a second failed
review stops. The report binds the reviewed pre-render packet, rubric and response.
It is not transferable pixel approval or human approval.

## Failure and Structural Correction

output/visible-text-stock-repair-01 used visible-text0.1:

- Independent critic correctly rejected the original heading ending in `알 수`.
- Direct rewrite returned a heading ending in `알 수없`, still incomplete.
- Recheck rejected it. Three subscription calls,22.293 seconds. No render.
- This exposed a repair-design issue: a strict short output slot can encourage
  continuation truncation instead of a genuinely concise reformulation.

visible-text0.2 changes the process, not just the requested suffix:

1. Generate three distinct complete alternatives without decoder maxLength.
2. Apply existing character budgets locally. Discard overlength candidates whole.
3. Choose the shortest eligible candidate for independent review, not automatic
   approval. There is no repeated sampling of the same verdict until it passes.
4. Recheck original contracts and meaning. Stop on any remaining failure.

output/visible-text-stock-repair-02 passed in20.511 seconds,three subscription
calls. Only the title changed to `중간 입출고 여부는 불명`. Original quantities45/45,
unit, labels, timings, layout and narration remained unchanged. All alternatives
and both critic verdicts are retained. This is a corrected development case, not
proof of transfer to an unseen topic.

## Actual Video

- output/visible-text-stock-film-02/delivery/preview.mp4
- 19.917 seconds,1280x720,24fps.
- SHA256:522f95474785ca746f0e1fe4db30c190209f1282e9968c505d706d4bbe3c7a09.
- Reused the exact baseline local voice and word events after narration equality
  check; no resynthesis. A new render preserves the baseline as a separate file.
-478 decoded/downsampled frames pass numeric geometry/timing checks. Three frozen
  or reversed negative manipulations are detected. Dot positions remain454px for
  both45-unit observations on a common50-unit axis; no intermediate data invented.
- Rendered font bounds pass; left-clipping and caption-collision controls detected.
- Assistant inspected frame13: complete heading, equal values and separated
  captions. Not an independent full-film A/B or actual audience measurement.

## Contrast Controls

output/visible-text-controls-01 contains six authored text variants with the same
narration and diagram. Expected answers are never sent to the critic.

- Valid noun heading:PASS.
- Complete uncertainty statement:PASS.
- Incomplete assertion:REJECT.
- Unknown intermediate movement changed into no movement:REJECT.
- Equal endpoints changed into45-unit increase:REJECT.
- Count changed into mass units:REJECT.

All6 matched expectations. One subscription call,30.537 seconds. These are four
development negatives and two positive controls, not the full-film95% negative
target or a held-out set. Do not reuse them as unseen evidence.

## Verification and Boundaries

New unit/integration tests cover exact coverage, unknown IDs, missing evidence,
input mutation, restricted edits, budget exhaustion, repeated failure, unknown,
401, legacy no-call behavior and candidate filtering without truncation.
The initial test fixture incorrectly used sentence-based rather than semantic
source units; fixed to preserve the two intended scenes. A legacy snapshot test
also inherited the new opt-in gate; pinned that test back to its explicit legacy
contract. These failures are test setup compatibility issues, not concealed passes.

Total actual calls this turn:7 subscription calls,0 separately paid API calls.
No image generation, new voice generation, authentication change or deployment.
Subscription usage is real usage. Source uncertainty, mixed-film alternative
planning and final independent rendered-film comparison remain unfinished.

Final regression:148 tests passed in79.961 seconds. Harness validation passed
for0.13.1 with snapshot SHA256
d1f6e2f92a2a8e9e044893a1435b227fcaa6b1c02f9bac5e186a89a3329315fd.
git diff --check passed (existing Windows line-ending warnings only).

Next: apply this gate to new causal, procedural and spatial scripts, preserving
the separate held-out set. Finish uncertain-relation alternatives and the actual
cinematic/diagram/source film. Do not redefine success as a correct stock chart.
