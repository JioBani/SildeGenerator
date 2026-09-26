# Slide generator v0.5 integration handoff

Date: 2026-09-25
Branch: `feature/slide-generator-v05`
Scope: opt-in `classic-slide` additions to the existing SildeGenerator service. Do not copy the standalone project's server, database, authentication, or release state into this repository.

Historical handoff note: the checkout already contained substantial unrelated uncommitted work before this branch was created. The original integration handoff was not committed or pushed; review the final commit scope separately before preparing a PR.

## Status and boundaries

The integrated route runs in the separate `slidev05test` Compose stack on port 18786. The production stack on port 8080 has **not** been switched to this branch. `SLIDE_V05_LOCAL_IMAGES` defaults to `false`; the existing `astra-motion` and `classic-slide` routes remain unchanged with the flag off. Technical E2E has passed, while illustration/design quality and human review are pending. The local illustrator is still a static scene image generator, not an animated actor system or a GPT image provider.

The isolated stack now points to the restored subscription bridge through a dedicated internal `ai-link` network, without running a second OAuth process. Its runner uses `RUNNER_MODE=live` and `IMAGE_PROVIDER=oauth`; the local illustrator remains an explicit opt-in test route, never a silent substitute for AI scenes. The main service on port 8080 was not redeployed.

On 2026-09-25, the project-specific Codex login was renewed without copying the desktop credential. The bridge model-list request succeeded from both runners. One actual `gpt-image-2` generation request returned `429 usage_limit_reached`, with reset time 2026-09-28 12:49 KST. This confirms connectivity but **not** image-production readiness. The isolated API rejects AI-image jobs until that timestamp and shows the pause in the UI; the guard expires automatically. Do not describe AI scene generation as verified until a post-reset image and end-to-end slide job succeed. No paid API key or automatic provider fallback was introduced.

Regression incident: job `7098ac3e-958a-47a6-b126-bbcea92938be` completed with only a mock gradient and subtitles because the original UI left local illustration unchecked. It was preserved for diagnosis. Remake `5a699e44-4207-49d5-921c-9885563acc23` uses the same script with a pinned local illustration profile, completed at the same duration, and renders actual scene PNGs. The deep link `/?job=<job-id>` loads the new result for the token owner; headless Edge reported `video.readyState=4` with no decode error. Illustration relevance remains a separate human-quality review.

This repository already had ElevenLabs and Microsoft Edge voice providers, timestamped subtitle generation, PostgreSQL job storage, Redis/BullMQ processing, authenticated job listing, and authenticated video download. These were reused, not replaced by the pilot's standalone equivalents.

## Source-to-target map

| Standalone pilot | Main service adaptation |
| --- | --- |
| `slidegen/visuals.py` | Exact source copy in `video-generator/app/providers/slide_v05_visuals.py`, called through `scene_illustrations.py`; adds size/profile validation and keyword correction |
| `slidegen/pipeline.py` scene rendering | Existing plan and render pipeline; `providers/images.py` selects the local illustrator only for a pinned slide profile; `main.py` records and checks a scene-image manifest |
| `slidegen/providers.py` voice | Existing `voice_broker.py` and configured provider; no second voice account or mock voice introduced |
| `slidegen/subtitles.py` | Existing subtitle and narration timing path |
| `slidegen/pipeline.py` music | `background_music.py` for user uploads or local synthesized music, mixed at low volume after video assembly |
| `slidegen/server.py` uploads/events | `jobs.controller.ts` authenticated upload, preview, deletion, and SSE endpoints; owner checks in `jobs.service.ts` |
| `slidegen/store.py` SQLite | Existing PostgreSQL `generation_jobs` plus `music_uploads` table; shared data volume for media |
| `web/app.js` | Existing `web/src/App.tsx` creator and jobs screen with opt-in scene visuals, music, upload/preview/remove, and SSE with polling fallback |
| Pilot style art | The original two style images are now copied into the slide picker as visual references. The UI explicitly warns that the opt-in local geometric illustrator does not reproduce their quality or style. Actual local-output samples remain in `web/public/style-previews/slide-v05-*.png`. |
| Pilot tests | Contract tests in `server/test/music-upload.test.js`, `server/test/slide-visual-profile.test.js`, `video-generator/tests/test_background_music.py`, and `video-generator/tests/test_scene_illustrations.py` |

## Configuration and data

- Set `SLIDE_V05_LOCAL_IMAGES=true` on the API to expose the experimental controls. Default is false. The runner accepts a version-pinned `slide_visual_profile` only on `classic-slide` and selects `local_illustration` for that job without changing the global image provider.
- The database bootstrap adds nullable `generation_jobs.slide_visual_profile` and `generation_jobs.music_selection` JSONB fields and the `music_uploads` table. Old rows and existing API requests remain valid. The legacy continuity backfill excludes local illustration jobs.
- Music uploads are capped at 10 MB, checked by audio signature, scoped to the token owner, stored in the existing shared data volume, and checked again by SHA-256 before rendering. The public job response omits storage paths and digests.
- `music_selection` is pinned to each job and remake. Deleting an upload disables future selection but keeps the blob so an already queued job can finish. Retention/garbage collection of upload blobs is still required before broad rollout.
- The isolated test stack uses Microsoft Edge voice and can select either subscription AI images or the explicitly chosen local illustrator. The subscription bridge currently exposes `gpt-image-2` as its verified image model. AI-image jobs are paused until the reported subscription reset; local illustration jobs remain available without paid API calls.

## API delta

All non-public endpoints use the existing Bearer token guard and existing job ownership model. No `X-User-Id` header or `user_id` URL parameter was imported.

| Endpoint | Purpose |
| --- | --- |
| `GET /api/jobs/options/production` | Adds `slideV05LocalImages`, verified image-model selection, and the temporary image-generation pause deadline |
| `POST /api/jobs` | Optional `sceneVisualMode: "local_illustration"`, `musicMode: "none" \| "auto" \| "upload"`, `musicUploadId`; pins versioned route and music selection |
| `POST /api/jobs/music` | Multipart field `file`; returns upload ID and metadata |
| `GET /api/jobs/music/:id` | Owner-only audio preview |
| `DELETE /api/jobs/music/:id` | Owner-only soft delete |
| `GET /api/jobs/:id/events` | Authenticated `text/event-stream` job snapshots, feature-flagged; browser falls back to existing polling |
| `GET /api/jobs/:id` | Adds public slide visual and music selection metadata, no managed filesystem path |

Existing job/video endpoints, motion-style requests, and old jobs are unchanged.

## Verification

1. `cd server && npm test`: 38 tests passing after music checks.
2. `cd web && npm run build`: passing.
3. In the isolated runner, `python -m unittest discover -s /tmp -p 'test_*.py' -v` for the two new test modules: four tests passing, including actual FFmpeg music mixing.
4. Isolated `classic-slide` 16:9/9:16 jobs with local images completed with voice, subtitles, H.264/AAC, per-scene distinct image hashes, and a music report. Example IDs: `896cd4d9-0bd1-4c72-8e87-d5c705b88b73` (automatic music) and `1f727cf4-8ccf-4419-bd1f-ca13f29d2c79` (uploaded music).
5. Authenticated owner access to uploaded audio succeeds; unauthenticated SSE returns 401 and a second account gets 404 for another user's upload.
6. The source illustrator copy is hash-identical to the standalone `visuals.py`: SHA-256 `5b9816c4d6cc7570f89813a5748e465d17b9c644a8fbb461bdd993f6583a633b`.
7. Headless browser creation from the actual test site completed as job `2e0e034d-569a-4111-a06c-1f6493fd03df`, with a video preview and no UI error. Desktop/mobile screenshots showed no horizontal overflow. The final wrapper's boat-position correction passed a subsequent local renderer test; it does not imply human design approval.

## Activate and roll back

Keep the flag off for a normal build and run the full regression suite. Then enable it only in a separate internal deployment, inspect actual videos and upload cleanup behavior, and collect human design review before production use. The local isolated stack is defined by `experiments/slide-v05/docker-compose.yml` and uses ports 18785/18786. Switching `SLIDE_V05_LOCAL_IMAGES` back to false removes the new UI and blocks new local-image/music requests without changing old jobs or deleting files. Preserve the DB and media volume during rollback.

## Known gaps

- The deterministic v0.5 renderer draws relatively simple, static scenes. Its output does **not** match the detailed generated style-card artwork. It supplies a no-cost technical path, not approved final visual quality or per-object animation.
- Uploads are signature-checked at submission and decoded in the runner; a corrupt but header-valid upload can still fail during rendering. Decode preflight at upload time and music licensing/rights handling remain future work.
- The main service currently uses Bearer-token access and an authenticated local/shared-volume media endpoint, **not** session login, object storage, or signed object URLs. These are broader platform migrations and are not claimed as completed here.
- The pilot's local SQLite, `.runtime`, guest login, `X-User-Id`, URL `user_id`, `best_so_far`, and mock payment/voice records were deliberately excluded.
- Do not promote human design quality on the basis of the technical E2E or the source project's 26 tests. A short human-reviewed sample and a production-volume retention test remain rollout gates.
