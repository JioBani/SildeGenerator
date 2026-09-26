# Hybrid camera settle, private 0.18.0

## Scope

The 0.17.0 source is preserved at `output/hybrid-story-0.17.0-baseline`.
No public engine, production service, account or paid provider was changed.
The goal status is `GOAL_NOT_MET` for automatic high-quality mixed films.

## Change

The previous cinematic route used a full-duration `ease:'none'` image zoom.
Now an explicit push/pull is divided, inside measured narration time, into
an initial hold, a `sine.inOut` travel of at least 1.8 seconds and an ending
settle. Short measured scenes fail instead of silently switching to a snap
effect. The selected focal point, strength, easing and timing are saved to
`program.json`. Diagram and registered-source scenes still use fixed cameras.
This implementation follows [GSAP's timeline `fromTo` placement contract](https://gsap.com/docs/v3/GSAP/Timeline/fromTo%28%29/)
and [easing API](https://gsap.com/docs/v3/Eases/).

The move is more controlled, but the engine does not yet verify that the
chosen focus is the story's meaningful target or that a face/hand remains
uncropped. Those are separate director and frame-evaluation requirements.

## Real-film A/B

`output/hybrid-story-0.18.0-camera-ab/candidate.mp4` reuses the earlier
authored 33.8-second mixed-route test film. The original and candidate have
byte-identical cinematic images and prepared source, plus the same narration
and captions. The source was re-prepared from the hash-verified registered
NASA file; it remains explicitly a **2016 Antarctic observation**, not a
historical exploration photo. This is a technical controlled comparison,
not a held-out script or automatic director success.

The candidate decodes as 1280x720, 24fps, 33.792 seconds, with video and
audio streams. `output/hybrid-story-0.18.0-camera-ab/observations.json`
reports `PIXEL_CHECKS_PASS`, zero findings. The pinned-runtime camera test
checks identical early-hold frames, visible travel and identical late-settle
frames. The full candidate's representative frames are in
`output/hybrid-story-0.18.0-camera-ab/contact-sheet.png`.
Harness validation reports `PASS hybrid-story@0.18.0`; 168 related regression
tests pass. The candidate and baseline stills, prepared source, voice and
caption file hashes were checked separately.

## Quality finding and next action

Visual inspection still shows a static figure whose expression and pose do
not change. The closing shot deliberately reuses the opening still, and its
dramatic justification remains unverified. The diagram explains a causal
relation but is visually basic. The 2016 source verifies the modern
observation only. Thus a smoother camera is **not** evidence that story,
acting, factual proof, style continuity or audience understanding improved.
The next substantive work is a new-script full mixed film with an appropriate
verified source and purpose-built visual assets, followed by independent
actual-frame and blinded comparison checks.
