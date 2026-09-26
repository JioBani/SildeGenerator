# Hybrid preproduction and visualization, 2026-09-26

## Scope and status

Private `hybrid-story@0.16.0`, based on preserved 0.15.0. No public engine,
service selection, paid provider, account or source-media registry was changed.
Status: development evidence only, `GOAL_NOT_MET` for the complete mixed-film
objective. The previous 0.15.0 baseline is in `output/hybrid-story-0.15.0-baseline`.

## Preproduction change

Accepted semantic beats now compile into `preproduction-brief-0.2`. Each declared
research need yields a script-grounded task with purpose (`fact`, `design`, or
`source`), question, exact passage, preferred primary-source class, acceptance
criteria, rights requirements, candidate IDs and status. The same hash-bound
brief enters concept selection and scene design. A catalog entry is only a
candidate: `fact_verified=false`; direct video use still requires rights review.
No source URL or rights grant is inferred from a model answer. A missing source
route continues to stop before asset work. Automatic web search, candidate
ranking, fact checking and rights clearance are still unimplemented.

The brief also carries each beat's transition intent. It does not add a shot,
alter narration, or claim a cinematic action the still-image renderer cannot do.

## Visualization and type

Semantic comparison, accumulation and step diagrams now distinguish `axis`,
`label`, `value`, `annotation` and `step` roles in editable SVG. The existing
Noto Sans CJK KR font and palette remain fixed by the film design contract;
role size and weight are constrained. Korean words are not silently split;
overlong text fails preflight. Korean/counting units join values (`20분`),
while Latin units retain a space (`4 kg`). Comparison axes and cumulative
labels were shifted above the reserved subtitle region after a real-frame
audit detected the original collision risk.

Design choices were informed by [D3's documented common-scale mapping](https://d3js.org/d3-scale)
and [W3C text/non-text contrast criteria](https://www.w3.org/TR/wcag/).
These sources support the design constraints, not a claim of WCAG certification
for the final video. The installed font is `fonts-noto-cjk 1:20220127+repack1-1`,
family `Noto Sans CJK KR`, with Regular TTC SHA-256
`b76b0433203017ca80401b2ee0dd69350349871c4b19d504c34dbdd80541690a`.
The [upstream Noto CJK project](https://github.com/notofonts/noto-cjk) records
OFL 1.1; packaging and distribution review remains a separate release check.

## Verification

- Docker-based harness validation: `PASS hybrid-story@0.16.0`.
- Focused tests: 44 passed (preproduction, semantic diagrams, graphic concepts,
  snapshot pairs, semantic gate and hybrid rendering).
- Rendered authored 1280x720, 24 fps, 10-second silent probe:
  `output/hybrid-story-0.16.0-typography-probe-v4/visual.mp4`.
- Inspected comparison and final cumulative frames. Both preserve exact values,
  common-scale geometry, Korean units and reading order.
- Browser DOM audit at 100 ms intervals: `TEXT_GEOMETRY_PASS`, zero visible
  text overlap or caption-safe-region failures. Its negative control was fixed
  to move a visible label in a multi-shot composition. Evidence:
  `output/hybrid-story-0.16.0-typography-probe-v4/text-audit-v2.json`.

This is a geometry/technical probe with authored values and no voice or actual
sources. It does not prove narrative quality, audience understanding, emotional
response, automatic source discovery, unseen-script transfer or final-film
typography. Snapshot, spatial and generic graph typography still need the same
role coverage and actual-frame checks. Full mixed-film and held-out comparison
remain open.
