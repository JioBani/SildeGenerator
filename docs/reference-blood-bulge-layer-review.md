# Blood bulge V2: layer diagnostic

Status: REVISE. No human approval or automatic production promotion.

The prior goal turn added verified source research and experimental acceptance criteria. This continuation adds measured diagnostic evidence, not a completed reconstruction.

## Evidence

Candidate: `.runtime/reference-study/blood-bulge-study-v2/study.mp4`.
Diagnostic images and structured report: `.runtime/reference-study/blood-bulge-diagnostic-v4/`.
The side-by-side review at candidate 4 seconds was inspected. The independent candidate still differs in cell density, cell shape and wall texture. Passing a boundary test alone would not prove matching manner and tone.

At x=320, candidate second 4:

| Representation | Bright-fluid support |
| --- | --- |
| Measured source target | 172..202 |
| Geometry without edges or particles | 172..201 |
| Candidate without particles | 172..201 |
| Full browser screenshot | 172..199 |
| Decoded candidate MP4 | 172..195 |

At second 0, all four candidate representations return 163..211 (source target 163..212).

The observed 7px source-to-output discrepancy decomposes here into 1px geometry support difference, 2px particle visibility difference and a further 4px screenshot-to-encoded difference. The final component may include encoding/resampling sensitivity; this experiment does not prove that compression alone caused it. No threshold was loosened. The existing raster failure remains valid as a visible-support comparison, but it cannot alone diagnose a geometric error.

## Reusable diagnostic lesson

Separate source support, authored geometry, occluded composite and encoded delivery. Compare matching columns and report missing columns explicitly instead of treating absence as zero error. Keep visual review separate from numerical boundary agreement.

`scripts/report_bulge_layer_diagnostics.py` now reports these differences over all matched sample columns at seconds 0 and 4. Its three unit tests cover two-edge error, missing columns and reordered column identities. This is still a two-frame diagnostic, not whole-motion validation.

Next work: inspect the moving candidate's particle trajectories against its narrowing channel, then correct authored containment and wall design where needed. Do not reposition particles solely to make x=320 pass. Whole-scene motion, texture and pacing require comparison across the source window before any approval.

No paid calls, source asset reuse, production defaults or engine approval policy changes were made.
