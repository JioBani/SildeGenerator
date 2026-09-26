# Bronze Age collapse pilot review

Date: 2026-09-25. This is a test of the promoted `astra-motion@0.7.0`
runtime, not an approved example of final motion-graphic quality.

## Production record

- Video: `output/bronze-age-collapse-astra-0.7.0/bronze-age-collapse.mp4`
- Scene and voice schedule: `output/bronze-age-collapse-astra-0.7.0/prepared.json`
- Runtime receipt: `output/bronze-age-collapse-astra-0.7.0/receipt.json`
- Technical result: 56.633 seconds, 1920x1080, 30 fps, H.264/AAC,
  -16.2 LUFS integrated, -0.6 dBFS true peak.
- Cost record: 0 paid API calls. Eight Microsoft Edge neural voice requests
  were made; this is an external online service with no per-call price
  recorded here. Artwork was drawn locally with Pillow.

## Editorial decisions

The user-supplied script described Egypt, the Hittites, and the Mycenaeans as
all vanishing together. The pilot preserves the mystery but distinguishes the
regional outcomes. It treats the Sea Peoples as a recorded set of groups, not
a sole established cause. Possible drought, conflict, and network disruption
are stated as hypotheses. These decisions align with the following research:

- [Cambridge Antiquity: Getting closer to the Late Bronze Age collapse](https://www.cambridge.org/core/journals/antiquity/article/getting-closer-to-the-late-bronze-age-collapse-in-the-aegean-and-eastern-mediterranean-c-1200-bc/482564326A668899FF183DD949FC520F)
- [Cambridge: The end of Mycenaean civilization](https://www.cambridge.org/core/books/abs/mycenaean-civilization/end-of-mycenaean-civilization/3731D3A5212BA97DD1DE0CA3E557336A)
- [Metropolitan Museum: Assyria to Iberia](https://resources.metmuseum.org/resources/metpublications/pdf/Assyria_to_Iberia_Art_and_Culture_in_the_Iron_Age.pdf)

## Visual review

Frame samples in `output/bronze-age-collapse-astra-0.7.0/review_frames/` show:

- Narrative: a coherent network -> disruptions -> Sea Peoples evidence ->
  uncertain causes -> different outcomes -> network vulnerability sequence.
- Design: consistent colors and legible Korean narration/subtitles.
- `REVISE`: English internal function labels (`setup`, `explain`, etc.) are
  visible to the viewer. A production display label needs localization or
  removal without changing the contract's machine-readable scene function.
- `REVISE`: parts of the map, palace, and ship art are cut off at the right
  edge in scenes 1, 2, and 4. Asset safe-area checking must cover the
  renderer's full layout transform, not just the source image.
- `REVISE`: the same left-text/right-diagram treatment dominates the video.
  Scene 7 has an especially empty central band. The motion is largely
  entrance/exit and layout movement, not an evidence-based reenactment or
  character performance. There is no approved actor rig in this output.

## Promotion boundary and next experiment

The 0.7.0 runtime, scene grammar contract, and preflight are technically
promoted. This video is `TECHNICAL_PASS_HUMAN_PENDING` and visual `REVISE`.
Do not use it as a Gold reference or automatic actor-performance approval.

Next: make scene-function labels non-viewer-facing, add output-frame safe-area
checks, then compare a version with differentiated object choreography to
this fixed narration and timing. Retain this candidate as the baseline and
ask for separate human judgements on historical clarity and visual quality.
