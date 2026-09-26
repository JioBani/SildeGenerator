# Isolated genre service test

Docker Desktop was started on 2026-09-22 after explicit user authorization.
Production worker, runner and image-oauth containers auto-started with Docker and were
then stopped to prevent unintended generation. Their volumes were preserved. No
existing credentials or runtime auth files were read; production calls during that
brief auto-start interval were not audited, so zero production calls is not asserted.

`docker-compose.genre-test.yml` is standalone, NOT an override of production Compose.
It uses the fixed project astra-genre-test, separate volumes, no bind mounts or secrets,
mock image/voice/planner, isolated worker networking, loopback ports and no restart policy.
API and web also use local_ui networking: an internal-only Docker network prevented
published host ports from working. Runner and worker remain on the internal network.
The hardcoded token local-genre-test-only is intentionally a disposable local fixture,
not a production credential. Never publish these test ports or use this token in production.

After Docker is safely available:

```powershell
python scripts/check_genre_test_isolation.py
docker compose -p astra-genre-test -f docker-compose.genre-test.yml up -d --build
python scripts/genre_http_smoke.py
```

The HTTP smoke checks actual runner mock settings, submits every advertised genre,
polls the original job without retry submissions, downloads each MP4 and probes it.
A timeout does not cancel or resubmit; inspect the original job. Rendering is mock
and cannot establish art quality. Receipts remain under output/genre-http-*.

UI test URL: http://127.0.0.1:18770 (only after stack starts).
Stop only this test stack with `docker compose -p astra-genre-test -f docker-compose.genre-test.yml stop`.
Do not remove volumes until test evidence has been collected. Production compose and
existing jobs are outside this test's scope.

## Current checkpoint

Docker image builds and actual HTTP smoke passed for knowledge, history, tutorial,
cartoon and documentary. Each job completed, downloaded an MP4 with video and audio,
passed duration checks, and preserved selected genre/version, cute_character style,
classic-slide harness and source narration in the final plan.
Evidence: output/genre-http-20260922-173223/results.json and five MP4 files.
The earlier 173105 attempt failed at the initial options GET before any submission
because published ports were unavailable on the internal-only network.
These are short mock fixtures, not visual-quality, full-script or human approval.
The overall genre-production objective remains unmet until those checks pass.
