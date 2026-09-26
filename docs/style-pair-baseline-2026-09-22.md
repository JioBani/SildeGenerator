# Matched style baseline

Goal: compare art treatment with fixed narration, voice bytes, shot duration, output
format and camera settings. This baseline does NOT replace the pending
stimulus/gaze/reaction benchmark or prove arbitrary-script production readiness.

Fixtures: cinematic-slide/fixtures/style-pair-cute.json and style-pair-fantasy.json.
Both contain the same complete two-sentence observational script. Existing generated
art is reused. Each variant deliberately uses one still across its two shots; this
cannot test cross-image character consistency or character acting.

Outputs:
- output/style-pair-cute-v2/delivery/cinematic.mp4
- output/style-pair-fantasy-v1/delivery/cinematic.mp4

Both: 10.033333 seconds, 1920x1080, 30fps, H.264/AAC.
Receipt comparisons passed: exact narration hash, per-shot WAV hash, measured shot
durations and final duration. Private harness validation also passed.
New --reuse-voice-work validates exact narration/scene ID pairs before copying audio;
it does not synthesize a second voice or invoke a provider. Receipts now record image
and voice hashes per shot so future comparisons can establish what actually changed.

Sampled visual observations:
- Cute: broad shapes, uncluttered monitor and distinct colors make subject and result
  immediately identifiable. Character and result are comfortably inside the frame.
- Fantasy: lighting and material detail establish an intimate night scene; more
  background detail competes with the central information. Face and monitor remain
  visible in sampled frames.
- Subtitles sit on desk areas rather than faces or the displayed result in this pair.
- This shows style differences, not better acting, physical motion or a stronger
  fantasy narrative. Camera push is restrained and does not animate the character.

No paid API calls were made. Existing images were reused and offline SAPI supplied
the first voice. Audio listening and continuous-play human review are still pending.
No Gold or public cinematic-harness approval has been granted.

The first cute output directory (v1) is an incomplete attempt: local Python lacked
httpx before voice or rendering. The completed v2 used existing installed libraries,
without installing packages or deleting the failed attempt.
