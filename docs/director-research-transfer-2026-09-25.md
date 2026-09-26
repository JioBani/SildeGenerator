# Reference research to director: bounded transfer trial

Date: 2026-09-25. This work does not promote any unreviewed grammar, actor
performance, or renderer effect to automatic production.

## What now connects

The motion director's planning entry point reads an evidence-checked research
brief. It looks at a short, explicitly curated set of scene-condition cues,
checks the referenced evidence file hashes, and records relevant observations
in `director-research-brief.json`, indexed in the job asset ledger. Only
`astra-motion` is eligible. The
approved-rule catalog remains separate and empty.

By default `DIRECTOR_RESEARCH_MODE=off`: the brief is recorded, not sent to
the planning model. `DIRECTOR_RESEARCH_MODE=pilot` passes at most two research
observations as **risk questions** to the live director. The prompt states
that they are unvalidated, cannot authorize an unsupported effect, and cannot
be treated as a successful transfer. Existing Harness preflight still blocks
unsupported motion before asset work.

The Docker image packages the research ledger, four source comparison frames
for two light-pollution observations, and two measurement files from the blood
pressure reference reconstruction. Their hashes are verified at selection
time. Cases whose evidence is absent or changed cannot be selected. Other
research cases remain outside this first bounded bridge.

## Comparable input

`docs/experiments/reference-transfer-brief-script.txt` is a new river-barrier
script, not the light-pollution study script. The preparation tool now writes
`baseline` and `research_pilot` director inputs from the **same source**, image
style, planning contract, and Harness. Only the research-risk context differs.
Preparation makes zero model, image, voice, or render calls. A subscription
planning run is an explicit single-variant operation and was not run here.
The final prepared comparison is in
`output/director-research-transfer-2026-09-25-v3/`. Its two receipts have
the same source hash, different prompt hashes, and zero total calls.

The relevant observations include source-timed transport in the blood
pressure reference, boundary bleed in a split comparison, and loss of a
scene-space anchor when local motion overwrote its transform. All remain
research-only. `transport_track`, `clip_region`, and `local_transform` are
reported as unsupported effects when selected; none is silently added to
the renderer.

## What must be measured before wider use

1. Run basic and pilot plans with the same unseen script and fixed model
   settings, without image or voice production at first.
2. Check whether a relevant scene was chosen, whether the plan preserved the
   whole script, and whether it asked for any unsupported action. An extra
   mention of a reference case is not a success.
3. Produce controlled A/B scenes only after the required assets and renderer
   capabilities exist. Hold narration and timing constant; review boundary
   integrity, full-path motion, viewer understanding, design, and revision
   count independently.
4. Package a human-reviewed result with video/asset/program hashes before
   considering a rule for the approved catalog. Keep the better previous
   version if a new candidate is worse.

Verification: 38 related planner/learning/preflight tests passed in an
isolated runner image; the packaged image retrieved the two relevant cases
from this cross-domain script with missing renderer effects explicitly
flagged. The candidate image was
promoted to the idle live runner with `DIRECTOR_RESEARCH_MODE=off`; the prior
image remains tagged `slidegenerator-runner:pre-director-research-rollback`.
The live runner reported `astra-motion@0.7.0` and retrieved the packaged
evidence without a network call. No paid calls occurred.

Release update: the live Compose runner now defaults to `pilot` for the bounded
risk-question context. The configuration, rather than the 0.7.0 Harness
package or approved-rule catalog, controls this behavior. The comparison and
human transfer checks above remain outstanding; pilot activation does not
constitute a successful quality evaluation.
