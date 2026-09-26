# Typed Relations to a New-Script Film

Goal status: GOAL_NOT_MET; active. Private hybrid-story@0.5.0, render payload0.3.
Previous turn classification: progress, with actual failure evidence and safety
fixes. This turn changes semantic contracts and produces a new mixed film.

## Fixed Structural Problems

The previous AB/BA critique disagreed because cause_beat_numbers could mean
physical/event cause, a person's reason, background context, or mere sequence.
semantic-beats-0.2 separates those meanings. Each link identifies an earlier beat,
kind, exact source/target quotes, and explicit/inferred grounding. Endpoint/order
validation is deterministic; whether the relationship is true still requires a
critic. A source quotation is not proof of causation.

The inherited narrative contract also forced every character story to supply a
dilemma and a later consequence. This conflicted with scripts without a dilemma.
narrative-direction-0.2 removes that forced template. Supplied choice beats must
still have coherent alternatives; no narrator text or new payoff is invented to
satisfy a generic structure. Core requires the selected direction version.

Old semantic0.1 data and its original hash order remain readable. No legacy cause
number is silently assigned a new meaning. Pure narrative-slide and public engines
retain their existing contract. Saved harness baseline: output/hybrid-story-0.4-baseline.

## Actual Development Run

Same development script as the failed first probe, not newly held-out:
experiments/meaning-planning-v1/development-script.txt.

- Meaning analysis:29.985s, no repair.
- Scene design:58.241s, no repair or source-unit adjustment.
- Whole planning probe:88.502s, DIRECTOR_CONTRACT_PASS.
- Actual plan: output/meaning-live-dev-02/scene-plan.json.
- Receipt/transcripts: output/meaning-live-dev-02/receipt.json and work/codex.

| Scene | Meaning | Execution |
| --- | --- | --- |
| 001 | Missed bus; Jisu wants to reach her father | cinematic still, hold |
| 002 | Example40min walking versus15min cycling | editable common-scale bars |
| 003 | Jisu chooses the bicycle and enters an alley | new cinematic still, hold |

The new analysis does not say urgency causes the example times. It labels the
goal-to-choice link as inferred motivation. No hospital arrival or outcome is
invented. Source inserts are absent because this fictional/example script has no
claim requiring registered archival evidence; routes are not forced into a ratio.

## Independent Pre-Render Critic

The updated critic shares the relation definitions, but receives no generator
confidence or approval statements. Its grammar criterion now explicitly asks
whether the information task needs a grammar; a wrongly chosen cinematic route
does not excuse a missing explanatory diagram.

Actual gpt-5.6-terra/low AB and BA requests both selected the original by hash and
matched every criterion, rejecting the deliberately cinematic comparison beat.
Comparison: CONSISTENT_PRE_RENDER_REVIEW in37.294s. Policy version/hash is recorded;
different policies cannot be combined into a counterbalanced review.

Evidence: output/meaning-critic-dev-02/{inputs,receipt}.json and work/{ab,ba}.json.
Scope remains ONE development control. This is not a film A/B, general critic
accuracy, a full negative-control suite, or proof of actual viewer comprehension.

## Actual Film

output/meaning-film-dev-01/delivery/preview.mp4

-26.75s,1280x720,24fps, Korean local SAPI narration and word-timed subtitles.
-Two fresh builtin ImageGen stills, with the first used as identity reference for
 the second. Original assets/prompts: experiments/meaning-planning-v1/assets.
-First image: bus-stop moment; second: same clothes/person with a bicycle at an
 alley. No reference footage, prior film or old voice is replayed.
-The middle scene uses actual director-selected nodes/values/scale, not a generated
 infographic. Only normalized event timing was bound to measured source-quote
 word events. That transformation is explicitly logged in preflight/receipt.
-Movie SHA256:32fc2f9efc8f1755f254daf5de8ca3588ef0938fb2b4281e9a92193281765369.

The image prompts were augmented by the coding agent to stabilize character
identity/framing. Images are passed through an explicit local adapter, not the
service image-provider/queue route. Do NOT call this fully autonomous service E2E.
No three-concept blind selection was performed; no overall film adoption follows.

## Decoded Output Review

PIXEL_CHECKS_PASS for picture presence, distinct scenes and declared diagram change.
366 diagram frames decoded at native24fps, spatially reduced to640x360 for geometry:

-40min bar width322px versus expected324px (compression/threshold tolerance4px).
-15min bar width121px versus expected121.5px.
-First visible times6.167s and8.083s into diagram versus measured voice anchors
 6.155s and8.066s; within0.15s.
-Monotonic growth and final read hold passed.
-Frozen-first, frozen-final, reversed, and incorrect-quantity controls rejected.
-Caption windows retain text and pass max(1.2,characters/8) measured hold checks.

Evidence: output/meaning-film-dev-01/decoded-review.json, receipt.json,
preflight.json, prepared-plan.json and decoded-contact-sheet.jpg.
Contact sheet visually inspected: person/clothes consistent, complete bicycle,
labels/subtitles legible without collisions at inspected moments. This is NOT
full-resolution all-frame defect detection, OCR, listening evaluation or emotion
measurement. No human approval is recorded.

Visible weakness: the diagram retains the renderer's fixed light background,
whereas cinematic shots use night lighting. Shared amber/cool colors help, but
the form change is still abrupt. A common design-bible binding and typography
system must replace per-renderer hard-coded styling. Do not call this the target
quality or claim superiority to the supplied reference.

## Verification and Boundaries

Harness validation passed for private0.5.0. Focused regression97 tests after final
policy check addition; includes typed-relation endpoint/order/hash tests, no-forced-
dilemma tests, actual create_plan MockTransport binding, legacy source/slide tests,
stream safety and pinned renderer tests. Not the entire repository suite.

Actual model calls4: two generator, two independent critic. Input18005 tokens,
output6231 tokens reported. Builtin image calls2, external paid API calls0,
ElevenLabs calls0. Local voice3 clips. No login, secret access, purchases, deletion
or production deployment. These counts are for this continuation, not prior turns.

## Learning and Next Work

Work loop: one valid plan and actual mixed candidate produced; no film accepted.
Engine loop: typed relations and script-grounded character structure implemented.
Evaluator loop: ambiguous relation definitions and inconsistent grammar rubric
replaced with explicit definitions; one development control now counterbalances.

These lessons remain EXPERIMENTAL. New scripts, direct-cause/motivation/context/
sequence controls, and held-out comparison are still required before general
promotion. Also outstanding: three blinded concepts, remaining five information
grammars, independent full-film review, authentic-source cases, source rights
audits, common design/typography, smooth meaningful camera and product E2E.
