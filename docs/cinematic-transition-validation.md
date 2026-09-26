# Per-shot transition execution

Private cinematic-slide 0.3.0 respects outgoing cut/crossfade/dissolve boundaries
inside each rendered segment. Missing transitions retain the legacy fade default;
unsupported explicit transitions are rejected by preflight, not silently replaced.
Narration timestamps stay on the cumulative original shot durations; outgoing images
are extended only by their own dissolve duration.

Real FFmpeg test: three 3-second color shots, a cut at 3 seconds followed by a
0.3-second dissolve at 6 seconds. Output duration is checked against 9 seconds;
pixels before/after the cut, during the dissolve and after settling are asserted.
The test found a real concat (1/1000000) versus xfade (1/fps) timebase mismatch.
Normalizing concat output FPS/timebase fixed it. Seven private harness tests pass.

No providers are involved. This does not validate human pacing or image aesthetics.
Version 0.4.0 adds a segment-planning hook: final assembly remains concat-only, but
dissolve-linked scenes stay inside one segment. Core validates exact ordered coverage.
The preferred segment size can expand, within the existing episode complexity limits.
Existing harnesses without the hook retain fixed-size scheduling.

Actual scheduler integration was tested inside the isolated Docker runner with real
FFmpeg/GraphExecutor and mocked database/lease operations. Three 3-second scenes with
preferred size 1 yielded 3-second and 6-second segments, preserving the dissolve.
An unchanged rerun acquired no new render lease; changing the second segment's camera
rerendered only that segment. Full scene metadata now participates in cache hashing,
including captions, layout, transition and rhythm. Two Docker integration/cache tests
and eleven local partition/private-harness tests passed.

Full-script visual validation and public adoption are still pending. No paid calls,
production queue changes or released classic-slide creative edits were performed.
