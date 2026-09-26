# Genre production validation - 2026-09-23

> **SUPERSEDED by the 0.4.0 scene-design contract reform.** The fixed genre-frame renderer validated here is no longer public or production-available. This document is retained only as failure and migration evidence.

## Scope

This validation proves the user-selected genre reaches the public `genre-slide`
harness and changes the rendered video. It uses isolated mock planner, image, and
voice providers. It does not claim final illustration quality or human approval.

## Corrected failures

- The GSAP timeline was not registered under the generated composition ID.
- The generated document omitted a proper `head`, allowing the inline timeline
  to run before GSAP was available. HyperFrames reported `gsap is not defined`.
- `render --strict` alone did not catch the browser runtime failure. The harness
  now runs `hyperframes check --strict` before every render.
- Composition IDs are now deterministic hashes of the canonical genre and scene
  contract. Different genre inputs cannot share a render identity.
- The HTTP smoke test rejects visually uniform sample frames and duplicate video
  hashes across distinct genre requests.

## Evidence

- Knowledge and cartoon: `output/genre-http-20260923-004221`
- History, tutorial, and documentary: `output/genre-http-20260923-004428`
- Final genre-only API run for all five formats: `output/genre-http-20260923-010356`
- Final visual comparison: `output/genre-http-20260923-010356/genre-contact-sheet.png`
- Deployed UI capture: `output/genre-ui-production.png`
- The current local product exposes the selector at `http://127.0.0.1:8080`.
- All five MP4 hashes are distinct.
- Every sampled frame has a non-trivial RGB range (`237-255`).
- Every output contains H.264 video and AAC audio, and is below the 60-second
  episode ceiling.
- UI selection routes to `genre-slide@0.2.1`; image, voice, and rendering options
  remain hidden behind the selected genre contract.

## Contract 0.2.0

- A genre-only request resolves its renderer and default art style on the server.
- A user-selected art style augments the genre direction instead of replacing it.
- Scene plans carry genre purpose, treatment, rhythm, and transition fields into
  the renderer.
- Knowledge, history, tutorial, cartoon, and documentary use distinct entrance
  motion grammars rather than only different colors.
- Historical and documentary source labels read runtime provenance evidence;
  generated assets are identified as AI reconstructions, never archives.

## Human-review boundary

These outputs prove routing, layout, timing, and renderer integrity only. Mock
assets are intentionally generic. History and documentary retain an explicit
source-verification label. Cartoon character acting, archival accuracy, final
art direction, and production approval still require their existing human gates.
