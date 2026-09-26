# Astra motion 0.7.0 promotion

Date: 2026-09-25. This is a runtime promotion of the already selectable Astra
motion Harness, not a claim that actor performance or Gold design is approved.

## Promoted

- The live runner now reports `astra-motion@0.7.0` with source SHA-256
  `def5696b9466af10ebc2b7bd53a254ec3bfb47536103f65211bfef44bcce3c05`.
- The planning contract enters the director prompt before planning and is saved
  with the job. Provider-free preflight checks supported scene grammar and
  independent-object asset requirements before image and voice work.
- The creative-readiness and quality reports preserve design, story,
  performance and Gold review as separate pending axes. A declared actor need
  is not an actor approval.
- The Harness manifest and Python package both say 0.7.0. Source file hashing
  now sorts POSIX relative paths, so Windows and Linux compute the same
  snapshot hash from identical files.

## Evidence

- `scripts/bootstrap.ps1 -Check` and `scripts/harness.ps1 validate astra-motion`
  passed. The source hash agreed between Windows and the final Docker image.
- 50 focused Python tests passed in an isolated Docker test image.
- Two isolated Mock jobs completed through the API, worker and runner with
  `astra-motion`. The final candidate job ID was
  `77ec5cac-94c1-4038-a1b0-e7d4d80928e7`.
- The first Mock MP4 decoded as H.264/AAC, 1920x1080, 30 fps, 7.412 seconds.
  Its production pack was `READY_FOR_COMPILATION`, and quality was
  `TECHNICAL_PASS_HUMAN_PENDING`. The frame inspection showed placeholder Mock
  artwork; it is evidence of execution only, not design quality.
- After replacement, the live runner health endpoint reported `ok=true`,
  `busy=false`, `mode=live` and `astra-motion@0.7.0`. The runner became healthy;
  the web API health endpoint returned HTTP 200.
- No paid model, image or voice calls were made for this promotion.

## Limits and recovery

- The former runner image is preserved as
  `slidegenerator-runner:astra-motion-0.4.0-rollback`. Existing jobs pinned to
  0.4.0 cannot be retried on the 0.7.0 runner without routing them to the
  former image or restoring it.
- The image OAuth helper was restarting during promotion. A live image job and
  end-to-end paid production were not run. Do not repeat Codex login from this
  task; that login has previously disrupted the desktop session.
- The D actor's approved naturalness and collar join apply only to the reviewed
  source scene. New reach/contact trials, automatic image-to-rig, general
  `GRASP_AND_RETAIN`, and cross-script director rules remain research or
  human-review candidates. The approved director rules catalog is empty.
- Quality uplift, first-try success rate, render speed and production cost
  relative to 0.4.0 have not been measured. The new planning contract and
  safety checks are the demonstrated improvement.

## Bronze Age pilot after promotion

- The offline `astra-motion@0.7.0` pilot at
  `output/bronze-age-collapse-astra-0.7.0/bronze-age-collapse.mp4` rendered
  eight scenes in 56.633 seconds, 1920x1080, H.264/AAC, 30 fps. Integrated
  loudness was -16.2 LUFS and true peak was -0.6 dBFS. It used zero paid API
  calls; eight Microsoft Edge narration requests are recorded separately.
- Scene contracts and production passed technical checks. Independent visual
  review is `REVISE`, not Gold or human-approved: the video exposes English
  scene-function labels, clips some right-edge illustrations, and repeats a
  static-looking split composition. These are concrete director/design/render
  gaps, not reasons to claim that actor animation was promoted.
- The historical narration was corrected before rendering: Egypt survived in
  diminished form, the regional disruptions were not one synchronized event,
  and the Sea Peoples are not presented as the single proven cause. See
  `docs/bronze-age-collapse-pilot-review-2026-09-25.md`.

## Release activation: research-informed planning

The live Compose runner now defaults `DIRECTOR_RESEARCH_MODE` to `pilot` for
`astra-motion` planning. This supplies at most two hash-verified observations
as questions about possible visual failures. It does not register an approved
director rule, provide a new renderer effect, approve an actor, or waive the
existing preflight and human quality reviews. Operators can restore the prior
behavior with `DIRECTOR_RESEARCH_MODE=off` in the Compose environment and a
runner recreation; the 0.7.0 Harness itself is unchanged.

Release acceptance must distinguish three states: (1) service configuration
and a provider-free planning test passing, (2) a complete live production job
passing technical review, and (3) human design, story, and performance review.
Only the first state can be claimed while the image OAuth helper returns 401.
Do not repair this by borrowing the desktop Codex login or switching to a paid
API provider. A project-specific authentication repair requires the user's
own sign-in and a subsequent bridge health check before live E2E production.

Release activation verification: `bootstrap.ps1 -Check` passed; Compose
resolved `DIRECTOR_RESEARCH_MODE=pilot`; seven research tests and thirteen
planning/preflight/scene-contract tests passed without network access. The
idle live runner was recreated without rebuilding the Harness and then
reported `healthy=true`, `busy=false`, `mode=live`, and
`astra-motion@0.7.0`. Its effective research mode is `pilot`, and a sample
comparison script retrieved one verified case. The web API returned HTTP
200. The image OAuth helper was still restarting with HTTP 401, so no live
video E2E or paid call was attempted. Gold design and actor performance
remain unapproved.

The first-release creator had still filtered `astra-motion` out of its
selection list despite the runner publishing it. The deployed creator now
offers both `astra-motion@0.7.0` and `classic-slide@1.2.0`, selecting motion
by default while keeping slide available. Its heading and duration limit
follow the selection. The web production build and browser test passed, the
deployed API returned both Harness options, and the browser test passed
against the deployed site. The server's missing-harness default stays
`classic-slide` for existing API clients; the creator sends its explicit
motion selection. These checks did not submit a paid production job.
