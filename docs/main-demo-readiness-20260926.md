# Main-service demo readiness, 2026-09-26

Status: **LIVE PREFLIGHT PASSES; FULL REQUIREMENTS DEMO NOT YET VERIFIED**.
Readiness is separate from private research-film success. The runner-only
repair below was made after confirming that no generation job was active.

## Observed today

- `http://127.0.0.1:8080/` and `/api/health` returned 200.
- Before repair, public harness options reported `classic-slide@1.2.0` and
  `astra-motion@0.9.1` compatible. The live `hybrid-story` entry failed with
  `No module named 'app.harness_sdk.direction'`: the runner image predated the
  mounted harness code. Its `public` flag remains false.
- The public production-options endpoint reported OAuth images, local motion
  graphics and Microsoft Edge voice. This does not prove that an image can
  actually be generated under the current subscription quota.
- A separate, undeployed `slidegenerator-runner:demo-candidate` image was built
  from current source. Inside it, `hybrid-story@0.18.1` loaded successfully.
  No running 8080 container or provider login was changed.
- Current source: server build and 38 tests pass; web build and 12 tests pass;
  23 focused hybrid/subtitle regressions pass. These are not a queue-to-MP4
  product E2E or a 10/30-minute reliability result.

## Live runner repair

- Before the change, the production database had zero queued/running/waiting
  jobs. A custom-format database backup is retained at
  `.runtime/backups/slidegen-pre-runner-20260926.dump`.
- The old runner image is retained as `slidegenerator-runner:pre-20260926`
  (`sha256:1b9173453524189cdfe46bce9e85663eac60d4a369159d330507b369cfb0feec`).
  Only the live runner container was replaced. The tested image is tagged
  `slidegenerator-runner:release-20260926` and `:working-tree`
  (`sha256:42439d889bc340ed7dd51b7dc579c98df20edf7b42d86107286936350053c2dd`),
  so a routine no-build Compose restart does not select the stale tag.
- After repair, the live preflight reports `classic-slide@1.2.0`,
  `astra-motion@0.9.1`, and private `hybrid-story@0.18.1` all loadable.
  The latest completed MP4 remains on the shared job-data volume. The
  `image-oauth` bridge resolves from the new runner and `/health` returns 200.
- The earlier slide failure contained `[Errno -2] Name or service not known`.
  Connectivity is currently healthy, but the failed job was not replayed and
  OAuth entitlement was not retested. Do not interpret bridge health as a
  successful paid/usage-consuming image generation.
- `scripts/bootstrap.ps1 -Check` passed. `scripts/doctor.ps1 -SkipSmoke`
  initially saw a bridge model-discovery failure immediately after the runner
  restart; the identical read-only probe then succeeded, and two subsequent
  doctor runs passed (Compose, API, web, and bridge: 4/4). This transient does
  not prove a sustained outage is fixed. No live render was submitted.
- Rollback, if a runner-only regression appears and no job is active: retag
  `slidegenerator-runner:pre-20260926` as `:working-tree`, then recreate only
  the runner with `docker compose up -d --no-build runner`. Preserve the backup
  and avoid stopping an active render.

Run the read-only live check with
`pwsh -NoProfile -File scripts/check_demo_readiness.ps1 -Scope slide` or
`-Scope all`. The slide-only preflight does not inherit the private hybrid
blocker, but still requires an authenticated MP4 E2E. A healthy HTTP
response is not a ready-to-demo verdict; the script separately reports
harness incompatibility and unverified E2E work.

## Demo gates, in order

1. Choose a **demo scope**. First-release slides are governed by
   `docs/product-requirements.md`; mixed film remains a private trial. Do not
   advertise every research capability as a supported product option.
2. Freeze a coherent API/worker/runner/web image set and Harness snapshots.
   Validate the runner's source modules and every exposed harness before
   switching any live container. Preserve historical job artifacts and avoid
   changing the runner while a job is in flight.
3. Use an isolated mock stack to complete one user journey: enter script,
   estimate, submit, watch status, play and download MP4, reopen and remake.
   Check both 16:9 and 9:16, subtitles on/off, music selection and failure
   recovery. Record request IDs and actual output hashes.
4. Restore or confirm the intended image entitlement **without** copying the
   desktop Codex session or silently changing to a paid API. A model-list
   response or auth 200 is not a successful scene-image E2E. Test one real
   image and one full slide job only when the quota allows.
5. Verify the first-release commitments still missing or conditional:
   Kakao/Naver/Google credentials and callback flow, creator voice catalogue
   and samples for ElevenLabs, payment/refund provider, wallet settlement,
   music licensing, and a full 10-minute then 30-minute single-MP4 run.
   Mock connectors are demonstration substitutes, not a public launch claim.
6. Review real output for narrated-script fidelity, actor/image consistency,
   subtitle synchronization, visual quality and source rights. Retain a
   rollback image tag and a recorded stop/go decision for the demo.

No paid generation, real login, production rollout or public-engine switch was
performed for this readiness check.

## Isolated product-path check

- A separate `slidegendemo` stack was built from current API, worker, runner,
  and web source. It runs on `http://127.0.0.1:18791/` with separate database,
  queue, storage, and an empty runner credential mount. The live 8080 stack
  was not replaced. Configuration is in `infra/demo-readiness.env` and
  `docker-compose.demo-readiness.yml`.
- A new `classic-slide@1.2.0` Mock job
  (`5e551644-4e5d-4fbd-b72a-39f9ebcdc2c6`) completed through API, queue,
  worker, runner, persisted status, and authenticated MP4 download. The file
  is `output/demo-readiness-smoke/slide.mp4`; SHA-256
  `22ddd45abfe67fd8def22a23153d9b0d7f7380c5c9fa0898f9b2a6ad1315118d`.
  Probe reported H.264/AAC, 1920x1080, 24 fps, 6.42 seconds. Its Mock artwork
  is a blurred placeholder, not an approved design or a real image test.
- The first local-motion submission (`0f75061a-49d9-4891-9880-0fb7cede9614`)
  failed because Mock mode cannot provide live scene direction. This exposed
  misleading availability and a runner 500 with invalid JSON. The API and UI
  now reject this configuration before queuing, and the runner returns a
  structured 400 if called directly. The isolated API returned the expected
  400 after rebuild; the slide job remained completed. This is an honest
  capability boundary, **not** a successful motion-graphics E2E.
- The isolated runner lists `classic-slide@1.2.0`, `astra-motion@0.9.1`, and
  private `hybrid-story@0.18.1` as compatible. Compatibility proves loading,
  not visual quality or production entitlement. Server tests: 38/38 pass.
- A second, post-rebuild slide job (`38c89661-e6bd-4688-8fc3-93cad73b9e5b`)
  with 9:16 output and subtitles disabled completed and downloaded as
  `output/demo-readiness-smoke/slide-vertical.mp4`. Probe reported H.264/AAC,
  1080x1920, 24 fps, 4.33 seconds; SHA-256
  `16a94b1082fd855cd31b894135b6e5f47b42dae55a57dc2e404951726824c176`.
  This checks routing and output dimensions, not the quality of real art or
  narration.
- `scripts/check_demo_readiness.ps1` now reports a separate
  `motion_scene_direction_unavailable` finding. The isolated stack passes its
  slide-only preflight and blocks an all-engine readiness verdict.

## Remaining blockers before a full demonstration

1. Run an authenticated, real-scene-direction motion job and inspect its
   objects, information hierarchy, typography, and playback. No Mock route
   can stand in for this result.
2. Produce one real image and voice sample using the intended entitlement,
   then a complete slide job. Do not borrow the desktop session or switch
   to a billable API silently.
3. Test replay/remake, music, interrupted-worker recovery, and a longer job
   in the isolated stack. The two short Mock slides are only technical smoke
   tests; the 9:16 and subtitles-off requests were exercised without a human
   playback review of every frame.
4. Keep API, worker, web, and runner versions coordinated for the next full
   release. The runner/source mismatch is repaired live; the existing API,
   worker, and web were not rebuilt in this runner-only change.
5. Complete the first-release account, payment, rights, and long-form gates
   above. Human design and story review remains separate from technical pass.
