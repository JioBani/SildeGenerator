# Motion graphics script grounding, 2026-09-25

## Incident

Different narration jobs produced nearly identical motion artwork. The local
route set `runner_mode=local`, which selected the deterministic scene plan.
`author_local_motion` then replaced objects and actions with keyword-selected
backgrounds, a recurring presenter, or the same three-node diagram. This was a
template replay with changed captions, not scene-specific direction.

## Isolated correction

- `productionRoute=local_graphic` now keeps `runner_mode=live`, so the Codex
  subscription director interprets the script while image rendering remains
  provider-free. This does not switch to a paid image API.
- The local adapter preserves the director's object inventory and supported
  actions. A bounded primitive renderer uses the selected objects, layout,
  labels, and motion. It rejects missing objects, unavailable actions, and
  unsupported artwork rather than silently substituting a generic presenter.
- Legacy fixed-template plans are not reused on retries in the new route.
  Existing finished videos remain unchanged.

## Evidence

- A UTF-8 Point Nemo script produced two scenes: an ocean/marker/distance/land
  scene and an Earth/ISS/vertical-distance/people scene. The compiled plan had
  no structural repair findings, and the Astra harness preflight had no
  findings.
- Both scenes rendered into a six-second, silent local test clip at
  `output/point-nemo-directed-smoke-v2.mp4`. The two visual compositions are
  distinct; no image or voice API was called for this render.
- Seven focused local-motion tests and three motion-style tests passed.
  The isolated site at port 18786 and its API/runner health checks returned OK.

## Not yet approved

The test clip is a technical proof, not a design-quality or acting approval.
Its map and satellite are simple editable vectors; the geography, spacing,
typography, and narrative clarity still need human review. The primitive
vocabulary is intentionally narrow. An actor reaction or an unknown object
requires reviewed assets rather than being replaced with a generic icon.

No new site-submitted full job with narration and download was completed in
this change. The main site at port 8080 was not redeployed. Promotion requires
one full site E2E, visual review of the resulting frames, and a second unrelated
script that demonstrates materially different content and motion.
