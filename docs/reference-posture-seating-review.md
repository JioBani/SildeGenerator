# Posture seating study V1

## Scope

Original vector reconstruction study of OyK0oE5rwFY 162-192 seconds, using the existing native-frame window and two-second contact sheet. New experimental example under astra-motion 0.3.0. Core, production defaults, providers and approved actor capabilities are unchanged. Paid calls: 0. Docker Mock E2E remains unverified; existing local GSAP/Chrome renderer is used.

The same actor, chair and desk are reused across wide view, eye-line view and hand detail. State changes include phone removal, leg folding, desk entry, leaning, upright return and reachable work surface. Timings are manually estimated and must not be called frame-exact.

## Inspection and repairs

Initial screenshots revealed a detached monitor stand and a hand hidden behind the work surface at the final close-up. The stand now ends inside the monitor, and the wrist stays at keyboard height during the final horizontal reach. These are visual corrections, not just endpoint-coordinate fixes.

## Technical evidence

The 900-frame fixture check measures arm/hand and leg/foot attachment in screen space; maximum gap is zero. Settled foot drift is approximately 1.6e-13 world pixels after camera motion is removed. Eye-line start and target match pupil and monitor anchors. Final hand visibility is checked by browser hit testing at a selected hand point. Intentional detachment is detected. These checks do not prove anatomy, body weight, acting quality or full-surface contact.

All 21 out-of-order seek checkpoints pass. The output remains a silent study; narrative comprehension with narration and sound is pending.

## Process finding

Camera movement and actor movement need separate transforms. Otherwise a correctly stationary support point may look like it drifts in a screen-space test. Attachments should be checked in the rendered coordinate system, stability in world coordinates, and visibility independently. Merely defining a hand anchor is insufficient when a later-painted prop occludes it.

Do not promote this asset to INTERACTION_READY or treat it as a general seated rig. Further source-aligned review must assess the face, silhouette, proportions, action timing, camera framing and contact surfaces.

## Encoded comparison: REVISE

The source-left/candidate-right 30-second comparison and six-sample sheet were inspected. The sequence is recognizable, but the candidate actor is smaller and farther right in the wide shot, has a longer neck and more uniform expression, and uses different arm/body proportions. Leg folding and the face close-up occur later than in the source. The final hand detail is not enlarged enough. Camera targets are geometrically consistent but composition and event timing still need source-frame fitting. Audio is absent. No human approval is recorded.

Encoded video: 1920x1080, 30fps, 900 frames, 30 seconds; full decode passes. The 30-second window adds partial study coverage, not approved reconstruction coverage.
