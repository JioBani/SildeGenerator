# Astra Motion 0.9 local production pilot

Status: isolated service E2E passed; human narrative/design review pending; main 8080 service unchanged.

## Production path

- Site: `http://127.0.0.1:18776/`. This stack uses `astra-motion@0.9.0`, `IMAGE_PROVIDER=local_graphic`, and `VOICE_PROVIDER=microsoft_edge`. It does not call the GPT image API or use the Codex desktop login.
- The site offers only the two motion styles in this local mode. The image model selector is hidden, and the job receipt records the local graphics provider. Existing slide jobs and the main service are not converted.
- Both styles use a scene plan, a versioned motion-style contract, locally authored background art, editable browser-rendered objects, GSAP timing, Edge Korean narration, and captions. The narrative path repeats one stylized character and varies its attention/response across scenes. The educational path animates a three-stage editable explanation diagram.
- This solves the subtitle-only Mock output in the isolated test site. The current drawings and scene grammar are intentionally limited; a repeated character ID does not prove strong identification with that character, and a diagram does not prove audience comprehension. Neither style is Gold-approved.
- The Edge voice was measured at 69.64 seconds for the 514-character attention script previously estimated at about 57 seconds. A provisional Edge-specific duration estimate now warns at roughly 73 seconds and blocks a greater-than-60-second request before production. No automatic split or paid retry occurs.

## Verification

- Narrative and educational jobs completed through the isolated API with Korean voice, H.264 video, and downloadable files. The same short script was used for both. Both styles also rendered at 9:16; representative frames were inspected for visual presence, text fit, and clipping.
- Browser E2E passed: local-mode controls, over-60-second warning, job creation, playback, download, and mobile layout.
- The two local-motion unit tests passed inside the runner. Server suite: 33 passed. Web build and harness validation passed.
- The full attention script was **not** rendered as a 60-second episode; its measured narration exceeded the product limit. The estimate is based on limited observations and must be recalibrated with more real speech samples.
- Human review of character identification, animation naturalness, explanation accuracy, rhythm, and style coherence is still pending. Generic vector character motion must not be represented as certified actor rigging or contact acting.

## Release boundary and artifacts

- The main `http://127.0.0.1:8080/` stack remains on its previous path. The 0.8.0 harness source and runner image were archived before this pilot. The isolated compose override remains at `experiments/motion-style-v08/docker-compose.mock.yml` for compatibility with the running stack, though this pilot is no longer a Mock output path.
- Sample videos: `experiments/motion-style-v08/local-narrative-v2.mp4`, `experiments/motion-style-v08/local-educational_info-v2.mp4`, and their `-portrait.mp4` counterparts.
- Site E2E capture and download: `experiments/motion-style-v08/local-ui-desktop.png`, `experiments/motion-style-v08/local-ui-mobile.png`, `experiments/motion-style-v08/local-ui-download.mp4`.
- Promotion to the main service requires human quality review, broader script/topic coverage, version-aware retries of existing jobs, and a production decision about local graphics versus the still-failing image authentication bridge. Do not borrow or refresh the desktop Codex session as a shortcut.
