# First release requirement audit

Source: `C:/Users/user/Downloads/slide-generator-product-requirements-v1.pdf` (9 pages, dated 2026-09-23). The PDF names `docs/product-requirements.md` as its maintained source. This audit records implementation evidence, not a release approval.

## Release scope

The first release is a single, up-to-30-minute narrated slide video for a user with little editing experience. A motion-graphics engine and per-shot editing are later work. An episode is not a user-visible output unit in this release. A generated job must yield one downloadable MP4, even when the renderer uses internal segments.

| PDF requirement | Current evidence | State |
| --- | --- | --- |
| Free-form script: headings, notes, directions separated from narration | `server/src/shared/scenario-input.ts` recognizes common headings, production notes, numbered lines and chat wrappers; novel formats remain unproven | Partial |
| Predicted duration and max 30 minutes, no minimum | Public estimate endpoint strips recognized non-narration notes before duration calculation; slide jobs use `single_30m` with a measured-voice pre-render gate | Partial; unfamiliar script formats and long E2E unverified |
| One video file from a long script | Planner chunks directed requests internally and compiles one plan; renderer assembles one MP4 | Implemented in source; 10/30-minute E2E unverified |
| Slide style cards with images | Creator now shows two selectable styles with representative images on desktop/mobile | Partial; sample art and final output quality not approved |
| ElevenLabs voice list, descriptions, samples, selected voice | `server/src/settings/voice-settings.service.ts` exposes one global voice snapshot; `web/src/VoiceSettings.tsx` is admin-only | Missing in creator |
| Narration speed reflected in estimate and output | `web/src/App.tsx`, `server/src/shared/voice-settings.ts`, `video-generator/app/main.py` | Partial; requires measured E2E |
| 16:9 and 9:16 composition | Creator, API, queue and runner now carry per-job ratio; slide harnesses render 1920x1080 or 1080x1920. Per-ratio art direction and publishing E2E remain unverified | Partial |
| Subtitles on by default, optional off; short timed sentences | Creator toggle reaches the render filter; ElevenLabs character alignment is converted to short timed cues; portrait font/wrapping is adjusted | Partial; non-aligned voices still show full-scene text and visual E2E is unverified |
| User music upload or automatic multi-track selection; voice-balanced mix | `main.py` assembles narration only | Missing |
| Contextual scene and shot planning, continuity, camera movement, transitions | `planner.py`, scene production pack, classic-slide harness | Partial; 10/30-minute quality unverified |
| Image, audio, subtitle, render QC and bounded recovery | `main.py` blocks non-Mock silent speech; `media.py` checks final decodable frames at three positions and rejects all-black renders; image and provider brokers exist | Partial; semantic image, subtitle synchronization, complete playback and bounded recovery unproven |
| Social login (Kakao, Naver, Google); anonymous pre-creation | `server/src/auth/token.guard.ts` requires an operator-issued bearer token | Missing |
| Per-account jobs, independent concurrent work, resume after leaving page | Creator now shows a per-account job list with status and preview thumbnail; BullMQ and PostgreSQL persist work | Partial; social identity and deployed E2E absent |
| Internal completion notification | Persistent in-service unread completion notifications and creator banner are implemented in source | Implemented in source; deployment unverified |
| Playback, download, remake with identical settings, retain both results | `POST /jobs/:id/remake` copies saved script/settings and preserves prior job; rejects unavailable harness snapshots | Implemented in source; integration and balance check absent |
| Time balance, one-off products, reservation, actual-length debit, no debit on failure | Optional PostgreSQL wallet, reservation, idempotent grant/settlement, fail release, creator balance display; isolated PostgreSQL integration test passes | Partial; flag off, no payment provider/product catalog/social account integration |
| Retention without unannounced deletion | `AUTO_DELETE_JOB_FILES=false` now disables automatic job-folder removal by default; BullMQ queue metadata may still expire without deleting MP4 files | Implemented in source; existing live worker still runs old code until carefully redeployed |
| 10/30-minute reliability and YouTube upload proof | No matching release fixture and measured acceptance run found | Unverified |

## Explicitly unresolved in the PDF

These are release decisions, not permission to invent public claims: success threshold and generation-time target; 16:9/9:16 encoding profile; approved public styles and voice list; music sources and upload limits; queue concurrency and wallet reservation order; retention; product prices, payment method and refunds. Implement configuration and tests before launch, then record the chosen values and user-facing policy.

## Implementation order

1. Make the long-form, single-output contract true across API, planner, runner, renderer and creator UI. Preserve historical `episode_60` jobs.
2. Add creator controls for ratio, subtitles, voice and music, then verify settings in actual MP4s.
3. Add social identity, per-account job list and reliable completion notification.
4. Add a transactional time ledger and payment integration with idempotent reservation and final settlement.
5. Broaden automatic image/AV quality gates, run 10/30-minute acceptance fixtures, and record release thresholds.

All rows must be checked against deployed Docker behavior as well as source before declaring the first release complete.

## Current implementation boundary

- Source checks: server tests, web build/Playwright, runner unit tests and an isolated PostgreSQL wallet trial have passed. The running `http://127.0.0.1:8080` service has **not** been redeployed with this work.
- No paid image, ElevenLabs or Codex generation was used for this audit. A 10-minute or 30-minute end-to-end video has not been produced, so reliability and publishing claims are unverified.
- `TIME_WALLET_ENABLED` defaults to false. Before enabling it, a verified payment webhook and an account-identity provider must be connected; the in-source `grantVerifiedTime` function is not a purchase endpoint.
- The user confirmed Kakao/Naver/Google credentials and a payment provider are not available yet. Mock integration is appropriate; public checkout and social sign-in must remain unavailable until verified credentials and webhook policies exist.
- The installed classic-slide version was advanced to `1.2.0` and cinematic-slide to `0.6.0` for new output behavior. Historical retries pinned to older harness snapshots require their older runtime to remain available; do not silently redirect those jobs.
- At audit time the current worker had 12 job folders and the oldest was about 3.5 days old; its old 30-day cleanup has not been stopped by source edits. Redeploy only after verifying no in-flight jobs and preserving historical harness snapshots.
- A release still needs music upload/licensing and automatic multi-track selection, public voice catalog and samples, actual social login, verified payments/refunds, nontechnical creator UX, 10/30-minute full runs, and semantic/visual acceptance gates.
