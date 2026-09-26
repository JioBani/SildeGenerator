# Blood factors V2: title ownership and particle launch

Experimental astra-motion@0.3.0 fixture, source 87-111s. V1 preserved; production/Core unchanged. No paid calls. Local GSAP/Chrome path only, not Docker Mock E2E.

## Changes

The body artwork moves independently of its title; the previously clipped title now stays inside the viewport throughout its visible first six seconds. Sixteen grains launch from one of three shaker holes, with launch positions computed from the shaker's deterministic rotation at each emission time. Grains are hidden before launch. A sampled accelerating path moves each grain downward; no grouped teleport/fade from a distant grid.

## Evidence and limits

The fixture verifier samples 180 title frames and all 16 launch events, checks monotonically downward flight, and deliberately introduces both an offscreen title and a misplaced grain to confirm detection. This validates emitter attachment, not source-matched dynamics or physical contact. The landing height is still a hypothesis and grains can remain above the tongue silhouette; do not claim a contact solver. The title belongs to the explanation overlay, while the body belongs to the moving content layer.

Reference timing, microscopic interaction, particle populations, diagram proportions and audio remain unverified or visibly different. Status REVISE; no human approval or automatic semantic-motion promotion. A future reusable emitter contract should name the source anchor, launch event, independent flight and landing surface explicitly, rather than treat particle visibility as sufficient.
