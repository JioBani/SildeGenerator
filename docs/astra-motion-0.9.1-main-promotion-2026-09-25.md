# Astra Motion 0.9.1 main-service promotion

Status: deployed to the main `slidegenerator` service on 2026-09-25. Technical production checks passed; human design, comprehension, and acting review remain pending.

## Scope

- The public motion harness is `astra-motion@0.9.1`. New motion jobs pin `productionRoute=local_graphic` when `MOTION_LOCAL_PRODUCTION=true`.
- The API and runner apply that route per job. Motion jobs use editable local graphics, local planning, and Edge narration. No Codex reauthentication or paid image API fallback is performed.
- Classic-slide and existing jobs keep their previous provider and stored snapshots. The global image provider remains `oauth`; only new motion jobs select local graphics. Previous service images were tagged `pre-motion-main-2026-09-25` before deployment, and persistent job volumes were not replaced.
- The site hides GPT image-model and continuity controls for local motion, but retains them for classic-slide. A transient polling error no longer permanently stops job-status updates.

## Verification

- Server tests: 34 passed; local-motion tests: 4 passed; web build passed.
- Isolated mixed-provider test: narrative job `fa1f69e7-f2d4-4f2f-89fe-737130b3191d` and educational job `2008b591-0979-49b5-b975-79c472f8426f` completed. UI test passed creation, playback, download, 60-second validation, and mobile layout.
- Main production options report `imageProvider=oauth`, `motionImageProvider=local_graphic`, `voiceProvider=microsoft_edge`. Public motion harness reports `0.9.1`.
- Main E2E with the same new narration: narrative job `bf8451a3-16c0-4a12-b696-70183c16a900` and educational job `975c6279-f15a-4bcf-bd80-ffdda1903a9b` completed with downloadable MP4s. Their representative frames differ in composition and visual function, not only labels or audio.
- The main-site browser flow also passed motion/slide control switching, 60-second validation, creation, playback, download, and mobile layout.
- The earlier completed job `da096157-6ffe-409a-aaf5-17bdd187f279` remains listed after deployment. Existing assets were not rewritten.

## Limits and follow-up

- Technical completion does not approve design, story comprehension, or character acting. The local graphic vocabulary is still limited and topic-dependent; the spotlight regression and broader transfer require human review.
- The separate image OAuth service is still unhealthy due to authorization. Classic-slide jobs that require it may fail until its own authentication is repaired. This promotion does not borrow the Codex desktop session or silently switch to a paid provider.
- Rollback is possible by disabling `MOTION_LOCAL_PRODUCTION` for new jobs and redeploying the API/runner, or by rebuilding the previous image tags. Preserve the job database and data volumes in either case.
