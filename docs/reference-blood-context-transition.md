# Blood pressure: obstruction to system context

Status: observed reference window, not an approved reconstruction or production rule.

Source: https://www.youtube.com/watch?v=Ab9OZsDECZw
Source SHA256: `31d041c98dfe3c0f3cb55fc8c530180d545ba15af7756f65d88a158a2e2db75b`.
Window: 165-195 seconds; 719 decoded frames with original source timestamps in
`.runtime/reference-study/blood-obstruction-165/motion.json`.

## Evidence and correction

The 3-second overview suggested a persistent small vessel inset next to the heart.
Enlarged native-frame inspection contradicts that interpretation. Do not author
a persistent inset from the overview alone.

- Around 165-183 seconds, the gold lower-wall structure persists, light circles
  sit above it, and a dark cluster with short light marks develops at its right.
  These are visual observations, not a verified explanation of biological identity.
- Frame 518, 186.603083s: a narrow red/teal network strip is already visible at
  the top while the labeled vessel still occupies most of the screen.
- Frame 520, 186.6865s: that network strip is taller and the vessel content lower.
- Frame 530, approximately 187.10s: the network and central heart occupy most
  of the screen; the previous title is exiting below. A light radial mark is visible.
- Frame 571, approximately 188.81s: the network/heart fills the screen; the
  vessel panel and its heading are gone.
- Frame 624, approximately 191.02s: a light vertical divider separates the
  left wavy red vessel field from the right network/heart field.

Exact event boundaries, motion easing, pulse cadence and narration alignment
are not yet measured. Sample timestamps are not authored keyframes.

## Measurement

`scripts/measure_blood_context_transition.py` records teal pixel fraction and
per-frame hashes. A 1% threshold sustained for three frames first occurs at
186.644792s. The preceding inspected frame already contains a smaller teal
strip, so the threshold is NOT the start of the transition. This measurement
is a search aid, not a semantic classifier or a timing contract by itself.

## Candidate authoring contract

1. Preserve the deposit composition and target count from the preceding study.
2. Represent the later right-side cluster as a separate stateful layer; do not
   silently relabel particles without narration and semantic evidence.
3. Keep the outgoing title and vessel under one parent so their translation
   remains coherent during the vertical reveal.
4. Author a separate independent network/heart layer behind the outgoing panel.
   Do not approximate the network by random decorative lines.
5. After the full-context hold, introduce the split comparison and divider;
   retain the heart's identity, colors and connectivity on the right.
6. Attach highlighting to an explicit local target. Do not animate the whole
   heart as a substitute for a localized emphasis mark.

Scene-function hypothesis: local mechanism -> whole-system consequence ->
comparison. Verify against narration before promoting this interpretation.

## Next verification

- Track outgoing panel/title bounds across 186-189s, not teal coverage alone.
- Measure split-divider entry and final position across 189-192s.
- Reconstruct with independent artwork; compare at native-time samples and
  random seek order. Check object identity, clipping and outgoing-layer cleanup.
- Transfer the local-to-system transition to one GPU calculation -> processor
  overview. Compare comprehension against an abrupt cut, not only aesthetics.
- Keep human approval and new-script transfer approval false until reviewed.

No paid calls. No source art or narration included in a delivery artifact.
