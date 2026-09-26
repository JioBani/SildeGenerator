# Deposit study V1: 141-165s

Independent vector reconstruction attempt,24s/720 frames/1920x1080/30fps, silent. Paid calls0. Experimental astra-motion0.3.0 local seek renderer; Core/providers/production defaults unchanged. Not Docker E2E.

## Inputs and implementation

-576 independently sampled wall profiles: `blood-deposit-walls-v1.json`.
-Yellow region extent: `blood-deposit-growth-v2.json`.
-19 conservative particle fragments: `blood-deposit-particles-v1.json`.
-Separate vector objects for walls, deposit, internal subdivisions and light particles.
-Absolute source PTS mapped to local timeline; no source artwork pixels in output.
-Deposit lens shape,19 subdivisions, introduction fade and subdivision reveal remain authored approximations, NOT measured source facts.

## Verification

Geometry tests4 and deposit tests8 pass. Random-order seek report passes all sampled times; full MP4 decode passes. These verify stability, not visual fidelity.
Comparison atlocal22s/source163s shows wall deformation and growing region in broadly corresponding positions, but substantial differences remain.

## Visual verdict: REVISE

1. Source has more visible particles than candidate. Merged/occluded detections broke tracks and disappeared from output. Conservative identity tracking must not become absence in the picture: add visible cluster representation while keeping identity unresolved.
2. All candidate particles share one color. Source includes different light tones. Preserve measured appearance without pretending color proves identity.
3. Source wall wraps above the deposit; current measured outer-band strokes only reproduce part of this structure. Need separate inner-wall contour and occlusion ownership.
4. Deposit internal columns differ in number/height and shape. Envelope is not sufficient design geometry.
5. Intro timing, narration and audio remain unverified. No contact/retention/general medical capability approval.

## Artifacts

`.runtime/reference-study/blood-deposit-study-v1.mp4`
`blood-deposit-study-v1-ab.mp4` (source left)
`blood-deposit-study-v1-comparison.png`
`blood-deposit-study/seek-review.json`

## Process finding

Separate semantic identity confidence from visible-object coverage. A tracker is allowed to say unknown, but the renderer must not silently delete visible evidence. Record uncertain clusters as unresolved visual assets and block fidelity approval until represented and compared.

Full reference reconstruction and new-script transfer remain incomplete. This adds a partial24s candidate, not approved coverage.
