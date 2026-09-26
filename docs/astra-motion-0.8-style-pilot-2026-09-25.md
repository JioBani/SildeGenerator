# Astra Motion 0.8 production-style pilot

Status: isolated Mock E2E passed; human story/design review pending; not promoted to the main 8080 service.

## Scope

- Motion UI offers `narrative` and `educational_info`; slide UI keeps its existing image styles.
- The job request stores a versioned motion-style snapshot. The server selects the matching image preset, and the runner preserves the snapshot in artifacts and delivery receipts.
- Narrative planning asks for one script-appropriate subject through local change, wider context, and result. The pre-asset gate requires a repeated continuity group and subject object ID for multi-scene live plans. This checks identifiers, not visual identity or story quality.
- Educational planning asks for editable labels and semantic object states. The renderer uses HTML text/objects instead of baking the labels into the generated image. The current object renderer is limited; complex paths, actor performance, and contact still need reviewed assets and implementations.
- The new styles do not silently add generic camera push. Unsupported actor/contact/mesh work remains behind the existing preflight and human gates.
- Create stays clickable; missing script/token, estimated duration over 60 seconds, insufficient time balance, and rejected token each show a reason. The server retains the 60-second limit without automatic splitting.

## Verification

- Server tests: 32 passed. Web tests/build and two focused Playwright checks passed.
- New motion-style Python unit tests: 3 passed inside the pinned runner image.
- Harness validation passed for `astra-motion@0.8.0`.
- Isolated Mock service completed one job per style from site request to video download. Both used the same script/speed and produced 6.5-second videos; a classic-slide job also completed. The server rejected an over-60-second request.
- Playback and download were checked through the isolated web UI. Desktop and mobile captures were inspected for overflow.
- Mock output uses placeholder images and silent audio. It does not prove narrative continuity, information comprehension, design quality, voice quality, or new-script transfer. No paid image or voice calls were made for this pilot.

## Release boundary

- Main service at `http://127.0.0.1:8080/` remains on 0.7.0. The isolated Mock pilot is at `http://127.0.0.1:18776/`.
- The pre-change 0.7.0 Harness source is preserved under `release-archives/astra-motion-0.7.0`; its runner image was tagged `slidegenerator-runner:astra-motion-0.7.0`. A future 0.8 deployment must retain version-aware routing for retries of old 0.7 jobs; the archive alone does not provide automatic routing.
- Before promotion: repair the separate image authentication 401 without borrowing the desktop Codex session or automatically switching to a paid API; run a real representative scene in each style; review subject continuity, information understanding, actual object motion, text cropping, scene order, audio, and download with a human. Keep `Gold` and acting approval pending until then.

## Pilot artifacts

- `experiments/motion-style-v08/service-narrative.mp4`
- `experiments/motion-style-v08/service-educational.mp4`
- `experiments/motion-style-v08/pilot-desktop.png`
- `experiments/motion-style-v08/pilot-mobile.png`
