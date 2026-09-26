# Director learning: first production bridge

## What is evidence, and what is not

The light-pollution motion benchmark is a manually authored 59.23-second video, not an automatic director output. V1 contained two observable failures: the city silhouette crossed the split comparison boundary, and bird/turtle root transforms were overwritten by local motion. V2 changed only the clipping and transform hierarchy for these cases. The paired frames and SHA-256 digests are recorded in `docs/director-learning-ledger.json` and `docs/evidence/light-pollution-v1-v2/`. The production video and technical limits are recorded in `docs/experiments/light-pollution-motion-benchmark-2026-09-24.md`.

These observations establish a traceable failure/correction pair. They do **not** establish viewer comprehension, full-route correctness, or generalization to a new script. Both cases remain `NOT_REVIEWED` and are absent from the production catalog.

## Runtime boundary

`video-generator/app/director_learning.py` loads only `video-generator/app/knowledge/approved-director-rules.json`. The research ledger is not loaded by the production worker. Selection requires a separate approval record matching the canonical rule hash, an evidence file packaged under the catalog's `evidence/` directory with matching SHA-256, a supported harness and motion kind, and a script trigger. An invalid catalog fails planning before model or image calls. Missing/changed/escaping evidence and stale approvals cannot select a rule.

`create_plan` records `director-learning-selection.json`, passes at most three selected cases with conditions and counterexamples to the live director prompt, and records `director-learning-application.json` after planning. The latter checks only whether a matching scene function and motion kind appear in the structured plan. `STRUCTURE_PRESENT_UNREVIEWED` is not a rendered or human quality pass. The current catalog is empty, so existing prompts and video behavior remain unchanged.

This is a code-review-controlled catalog, not a cryptographic identity system for reviewers. A reviewer identity, approval receipt, and versioned promotion operation need to be added before real cases can be activated. Do not populate `human_approvals` from model output or research status alone. Existing worker containers must be rebuilt before they run this bridge; no running job was restarted for this change.

## Next transfer experiment

1. Obtain human design/meaning review of the V1/V2 light-pollution clips. Record the exact video hashes, scene timecodes, what was understood, what remained unclear, and reviewer decision.
2. Implement `clip_region` and parent/local transform as explicit versioned renderer contracts. They are not current Astra motion effects; the new selector correctly rejects them now.
3. Use a different script and different assets, keeping narration identical between baseline and learned candidate. Compare the same scene function with and without the new contract.
4. Measure boundary bleed, full-path on-screen continuity, first-attempt quality, human correction count, and viewer comprehension separately. Preserve the best candidate; do not overwrite it with the latest.
5. After a successful independent review, package the evidence, approve the exact rule hash through a human-controlled operation, rebuild the worker, then run a site-to-render E2E with selection and application logs. Only then can the rule be called transferred into automatic production.

Focused verification: 27 planner/learning/genre tests passed in the runner image with source mounts. No paid model or image calls were made for this bridge. No comprehension A/B or live site E2E was performed.
