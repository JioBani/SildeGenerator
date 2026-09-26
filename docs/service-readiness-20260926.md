# Local service acceptance - 2026-09-26

## Scope and verdict

The local main service at http://127.0.0.1:8080 has passed the tested creator
journey: narration intake, supported engine/style selection, submission,
progress, completion, browser playback, download, reload and mobile layout.
This is not a public-launch security audit, a guarantee for arbitrary scripts,
or a human design/acting/Gold approval.

## Running routes

- classic-slide@1.2.0: live subscription AI images and Microsoft Edge narration.
- astra-motion@0.9.1: live director planning, authored local graphics and Edge narration.
- Production mock images and local illustration test mode remain disabled.
- No desktop authentication was changed. No paid API fallback was used.
- Private experimental engines remain private.

## Fixes in this pass

1. Load real published engine and provider settings together. Do not invent
   fallback versions when discovery fails; offer a settings retry instead.
2. Preserve a valid engine selection and show only supported slide shortcuts.
3. Surface narration parsing failures before submission. Require the current
   narration estimate instead of submitting while analysis is unavailable.
4. Key playback by job and credential, abort stale fetches, validate media
   responses, revoke object URLs and expose media retry/errors.
5. Keep job selection ordered when requests complete out of order. Discard
   cancelled progress responses after a job switch.
6. Catch restoration, download and remake connection failures; offer retry for
   failed jobs without changing their saved engine or provider.
7. Reduce history polling to 30 seconds and active progress polling to 5 seconds.
   Hidden tabs stop polling. History thumbnails load near the viewport, not all
   at once. Back off for 60 seconds after rate limiting.
8. Correct local director guidance: film-framing objects are for film composition,
   not every topic. Advertise existing geography/diagram objects, the eight-object
   limit, executable motion kinds and narrative subject identity.

## Evidence

Fresh live slide job: `570e82ee-baf3-42b2-bc09-c04184e93052`.

- Submitted through the main site's UI with cute_character, classic-slide, 1.10x.
- Two narration sentences about a traveler watching a sunset city.
- Completed with two `chatgpt_oauth_image` usage records and Edge narration.
- MP4: 1920x1080, H.264 + AAC, 24 fps, 7.75 seconds, 1,982,533 bytes.
- Audio mean -20.7 dB, peak -5.6 dB; not silent.
- Actual generated illustration and caption visually checked in the player.
- Browser playback time advances, download succeeds, refresh restores the same
  job, 390px mobile viewport has no horizontal overflow, no browser runtime errors.

Existing live motion job rechecked through the updated player:
`f306dc0d-619f-4659-9521-a044a446e837`.

- astra-motion@0.9.1, educational_info, local_graphic.
- 1080x1920, 43.041667 seconds; playback/download/reload/mobile checks pass.
- No new motion production call in this acceptance pass. Its original creation
  was verified separately; this pass does not claim a fresh full motion render.

Both jobs remain `TECHNICAL_PASS_HUMAN_PENDING`.
Reports, screenshots and downloaded files: `output/service-readiness-20260926/`.

## Verification

- Bootstrap prerequisite check: passed (existing service ports already in use).
- Doctor: 5 pass, 0 fail; live mode skips its production-mutating mock smoke.
- Independent network-disabled mock render: narrative and educational_info both
  produced MP4s. No production configuration was changed for this test.
- Browser creator suite: 16 passed, including auth rejection, duration limits,
  renderer separation, preview images, stale playback, media retry, failed-job
  retry, hidden-tab polling and lazy thumbnails.
- Server tests: 43 passed.
- Planner tests: 21 passed.
- Web unit tests: 12 passed.
- Web and runner rebuilt and deployed; API, runner, PostgreSQL, Redis healthy;
  web, worker and image bridge running.

## Repeating acceptance

From `web/`, set an unused `PLAYWRIGHT_PORT`, then run:

```powershell
npx playwright test e2e/creator-journey.spec.ts e2e/motion-format.spec.ts e2e/engine-separation.spec.ts e2e/style-preview.spec.ts --workers=2
```

For an existing completed job, set `SERVICE_E2E_JOB` and run
`node e2e/audit-service-journey.mjs`. The script reads the local access-token file
without printing it or saving traces. Reports contain no credentials.

A fresh live test requires explicit authorization and `SERVICE_E2E_CREATE=1`
with `SERVICE_E2E_JOB` unset. It requires OAuth images and Edge voice, and does
not change authentication, retry failed creations or switch providers.

## Remaining boundaries

- Live image quota, subscription expiration and upstream outages can still fail
  production. Such failures must remain visible, never become mock-image success.
- Only one slide style was freshly generated here; the other style cards and
  submitted settings were verified with isolated browser tests.
- Local motion vocabulary is limited. Unsupported artwork/acting is not silently
  replaced with a generic video, and arbitrary-topic visual quality is not proven.
- Existing browser tabs need a reload to receive the polling and player fixes.
- Remaking a job whose saved renderer version is unavailable remains a visible
  version conflict; the service does not silently change its creative contract.
- Rollback must preserve jobs, media, DB and credentials. Restore a previously
  verified web/runner image only when the queue is idle; do not purge volumes.
