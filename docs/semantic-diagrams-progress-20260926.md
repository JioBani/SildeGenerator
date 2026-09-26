# Different Scripts, Different Information Structures

Status: GOAL_NOT_MET overall. Private hybrid-story@0.3.0 capability increment.
Production and the separate pure-slide engine were not deployed or changed.

## Requirement

New scripts must retain a comparable quality floor while choosing the right
visual structure. Swapping narration, colors or labels in the same old film is
not transfer. A correct chart is necessary here, not sufficient for final film
design, emotional storytelling or automatic directorial competence.

## Implemented

- Three quantitative/procedural render paths: common-scale horizontal comparison,
  ordered stacked increments with derived running totals, and step-chain progress.
- The five-grammar planning library retains cause/change/result and transport.
- The two additions are explicitly engineering hypotheses, not falsely attributed
  observations from the blood-pressure reference or approved transfer rules.
- Version 0.3 quantities need exact narration quotes, common units, bounded scale
  and short labels. Wrong numbers, units, cumulative overflow and ordering fail.
- Legacy 0.1/0.2 structured-output schemas exclude the new grammar and quote field.
- New rendering checks final reading hold. Long labels wrap rather than clipping.
- Offline speech supplies word events. These feed existing subtitle_cues and,
  in this benchmark, align the graphic change to the spoken value/action.
- No generated-image provider, paid API, login or model call was used.

## Actual Outputs

Authoritative run: output/semantic-diagrams-v03-run5/review.html.
All outputs are 1280x720, 24fps, H.264 with local Korean narration and subtitles.

| Test script | Visible relationship | Duration |
| --- | --- | --- |
| Three example travel durations | 20/35/50 minutes, same zero-based scale | 15.042s |
| Example library donations | Increments 2/3/5 books, totals 2/5/10 | 14.000s |
| Producing an information leaflet | Gather, organize, publish | 17.750s |

These are synthetic examples stated as examples in the narration, not statistics
about real travel services or a real institution. Scene plans were authored.
The live autonomous planner did not infer these three plans from unknown scripts.

## Evidence

- receipt.json: versioned harness snapshot, script, asset/audio/video hashes,
  measured durations, caption cues, word-based motion anchors, pixel observations.
- geometry-review.json: decoded video sampled at 6fps; actual bars and completion
  marks, temporal order and final hold. 281 samples across the three videos.
- Measured comparison lengths at 640px width: 108/188/270px (expected108/189/270).
  Cumulative increment lengths:96/144/240px. Both within4px tolerance.
- Nine fixture-scoped negative controls rejected: frozen initial, frozen final,
  and reversed frames for each of the three distinct information tasks.
- All 12 caption windows satisfy max(1.2s, characters/8) and preserve source text.
- Actual decoded contact sheets visually inspected for all three final videos;
  these are output frames, not HTML previews or unrendered timeline assertions.
- Focused regression suite:54 tests across hybrid, illustrated transport, planner,
  engine separation, narrative direction, semantic diagrams and voice cues.
  This is not a claim that the entire repository test suite passed.

## Failures Preserved and Repaired

1. Initial voice manifest used IDs outside the existing speech helper's contract.
   Corrected to scene-NNN; the failed input remains in the earlier output folder.
2. First assembly used the wrong delivery directory. Adopted the pipeline's
   delivery/work layout; retained the failed run2 instead of deleting evidence.
3. Run3 subtitles showed a whole paragraph. Added actual word-aligned short cues.
4. Run4 exposed mismatched SAPI event/file audio clocks. Explicit16kHz output
   corrected them; events outside measured audio now fail. Do not use run4.
5. Label wrapping and quantity-label bounds added before final run5.

## Limits and Next Gates

The color/geometry critic knows these fixture layouts. It is not an independent
general semantic, OCR, audio-listening or acting evaluator. Six-fps sampling is
not full-frame inspection. Caption and motion alignment use speech-engine events;
independent listening/forced-alignment validation remains outstanding.

This proves execution of distinct information structures on three authored inputs,
not equal reference quality or unseen-script automatic selection. Next: unseen
scripts and deliberately unsuitable grammars, automatic selection before assets,
independent AB/BA comprehension/design evaluation and held-out transfer. Complete
the remaining five information families and mixed-route continuity tests before
considering overall AUTO_VALIDATED. Do not convert this report to HUMAN_APPROVED.

The 0.2 snapshot is preserved under output/hybrid-story-0.2-baseline. No rollback
or production deployment was performed.
