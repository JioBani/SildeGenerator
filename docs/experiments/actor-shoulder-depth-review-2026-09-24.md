# Character shoulder-depth review

## Human observation

The two downloaded V3/V4 review records contain the same verdict. Treat them as
one user's repeated observation, not two independent reviewers. The viewer chose
`NO_DIFFERENCE` and read both performances as noticing the computer turning on
and smiling slightly. Both records identify the shoulder attachment as unnatural:
from the viewer's perspective, one sleeve is behind the shoulder and the other
is in front. This is feedback about image layering, not a request to change the
already-liked facial reaction.

## Isolated correction

V6 is an experimental render only. It keeps V5's image, face states, motion
curves, shot timing, and audio-free test duration. Both hanging arms now render
behind the torso; both hands remain in front. The old V5 is preserved for blind
comparison. This is a candidate correction, not evidence that acting is approved.

## Evidence and next gate

- `output/layered-motion-acting-v6/technical-report.json` confirms the intended
  layer order, 240 frames, no paid calls, and no performance-curve change.
- `output/layered-motion-acting-v6/review-receipt.json` records the file hashes
  and pending human appearance review.
- `http://127.0.0.1:18771/` compares V5 and V6 with randomized A/B labels.
- The V3/V4 and V4/V5 comparisons remain available at `?compare=arms` and
  `?compare=pose` respectively.

Do not promote the rig to production until a viewer confirms the shoulders look
more coherent without weakening the facial response. If both versions still look
attached unnaturally, change the shoulder contours or sleeve artwork rather than
adding more motion curves.
