# Director-only live review — 2026-09-22

## Scope

- Source: `harnesses/cinematic-slide/fixtures/director-benchmark-script.txt`
- Genre: `cartoon` (`0.1.0`, preview)
- Visual style: `fantasy_anime`
- Harness: `cinematic-slide@0.5.0`
- Model: `gpt-5.6-terra`, reasoning `low`
- Allowed work: one subscription scene-planning request
- Forbidden work: image, voice, render, automatic retry

## Receipt

- Planning requests attempted: 1
- Automatic retries: 0
- Image tasks: 0
- Voice tasks: 0
- Render jobs: 0
- Duration: 62.047 seconds
- Usage: 3,807 input tokens, 1,840 output tokens, 169 reasoning tokens
- Result: `REVISE`

## Review

The response preserved the source narration and attached the requested cartoon genre
contract and fantasy-anime style bible. It also returned a valid renderer contract.

It did not produce a usable shot design. The response proposed one scene for five
source units while the sequence requested keycut position 3. The deterministic compiler
then expanded that one scene to consume all remaining narration and clamped the keycut.
That preserved text but collapsed the intended progression:

1. late-night studio
2. monitor landscape reveal
3. traveler at the road
4. traveler expression close-up
5. return to the studio

The resulting single setup image cannot represent those spatial and shot-scale changes.

## Engine learning applied

- Lossy structural repairs are now production-blocking findings.
- Repair evidence is stored as `director-repairs.json` and restored on resume.
- The production pack receives repair and harness findings before any asset work.
- The prompt now requires exact source-unit coverage and valid keycut positions.
- The benchmark accepts only approved local subscription bridge addresses.
- The OAuth bridge copies only `auth.json`, not the full Codex working directory.

## Promotion decision

Do not promote this plan to style-frame, image, voice, or render work. A future approved
director-only run must produce multiple purposeful scenes with zero structural repairs
before human design review.
