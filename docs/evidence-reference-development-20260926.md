# Evidence References and Cross-Script Quality

Status: GOAL_NOT_MET. Private hybrid-story0.12.1, not astra-motion or a public
release. The user's latest requirement is the acceptance target: a different
script must retain output quality, and graphics must express diverse information
relationships rather than reuse the same picture with different narration.

## Scope and Compatibility

- Preserve0.12.0 under output/hybrid-story-0.12.0-baseline.
- Core semantic-sufficiency0.2 selects exact source-span IDs, with beat ownership,
  offsets and catalog hash. This fixes quote transcription failures without
  weakening meaning, routing, grammar, causality or information-sufficiency gates.
- Legacy0.1 schema and review behavior remain unchanged. The private harness alone
  opts into0.2. Source/actor/film quality is never approved by an evidence ID.
- Development render adapter requires a trusted source registry before voice and
  binds both catalog and selected file hashes. A changed source fails before render.
- Original family-fairytale CLI label maps to the existing disney_animation API
  identifier. This is compatibility, not licensed character or brand content.

## Actual Experiments

1. Frozen stock analysis, output/evidence-id-stock-resume-01:
   independent review passed and real Core concept/scene design completed in
   128.455 seconds, five subscription calls. This reused prior analysis; it is not
   a fresh held-out end-to-end run. Three executable concepts were compared in
   anonymous forward/reverse order. Selected design uses fixed dot tracks.
2. Stock output, output/evidence-id-stock-film-01/delivery/preview.mp4:
   19.917 seconds,1280x720,24fps, local Heami voice, zero external voice/image calls.
   SHA256 b6f862c13177d47b9f21c4772581d4224d4df02377c6f0b922a99f314e965d6c.
   478 decoded/downsampled frames preserve45/45 on equal scales; initial/final
   frozen and reversed negative controls are detected. Font bounds and two layout
   negatives pass. These are component results, not film approval.
3. Visual inspection of stock frame13 found a critical incomplete heading:
   model output says `가상의 측정 예시 · 중간 입출고 여부는 알 수`.
   It is already incomplete in the model's output, not cropped by the renderer.
   The26-character limit was satisfied at the expense of a complete assertion.
   Narration retains the full negation, but the heading remains unacceptable.
   Keep this render as REVISE. Do not silently append words or overwrite evidence.
4. The first intended negative probe accidentally selected the complete positive
   toy-mechanism analysis. It passed, correctly; its expected-REVISE mismatch is
   test setup error, not critic false acceptance. Preserved under
   output/evidence-id-toy-negative-01. No result is discarded to improve statistics.
5. Correct fragmented negative analysis, output/evidence-id-toy-negative-02:
   actual independent critic rejects introduction/disclaimer-only scenes.
   One subscription call,19.033 seconds. This is development replay, not held-out.
6. Fresh mixed fiction/source/comparison script, output/ice-return-director-01:
   four actual subscription calls,286.482 seconds,one analysis revision.
   Initial separate framing scenes were rejected and then merged correctly.
   Revised inferred food-to-decision motivation received UNKNOWN and stopped before
   concepts/assets. Critic accepted a related inferred motivation in the first
   pass but questioned it in the second: calibration/alternative evidence remains
   unresolved. Do not report a stable causality diagnosis from this pair.
   No mixed film was generated, no script rewrite, no repeated critic sampling.

## Learning, Not Promotion

- H1: exact source references remove transcription failures while retaining
  meaningful negative detection. Development evidence supports testing further;
  not enough for general quality or held-out superiority claims.
- H2: fitting text inside a rectangle is not meaning preservation. Compare final
  visible titles/labels against narration and require a complete claim; reject
  lost negation, qualifier, unit or referent. Add independent post-design review,
  not a special-case suffix patch for this one Korean title.
- H3: inferred narrative motivation needs explicit policy and alternative-plan
  comparison when uncertain. Sequence/context must remain distinguishable from
  causal assertions. Preserve inference labels and do not invent stronger narration.
- Existing supported grammar tests and source provenance checks remain separate
  from render aesthetics, emotional engagement and full-film quality.

## Verification

- Focused evidence/source/gate tests:23 passed in12.928s.
- Broad Core/SDK/harness/renderer/separation regression:137 passed in72.178s.
- Numeric pixel audit:478 frames,three negative manipulations detected.
- Text geometry:pass with two negative manipulations detected, yet semantic title
  failure escaped. This limitation is now an explicit failed development case.
- Separate paid API calls0. No login, token, provider credential or public service
  change. Subscription calls consume subscription usage; not described as zero usage.
- No HUMAN_APPROVED or AUTO_VALIDATED full-film result, no held-out quality claim.

## Next Work

Add final title/label semantic checks with negative controls before more expensive
artwork. Resolve uncertain relations with distinct bounded alternatives rather
than repeated judgment sampling. Then finish a genuine cinematic/diagram/source
film. Keep development, validation and unseen scripts separate; do not shrink
the goal to two-measurement diagrams. Whole/detail, category decomposition and
evidence/judgment still need executable contracts/renderers and transfer tests.
