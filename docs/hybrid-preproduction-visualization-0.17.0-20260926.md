# Hybrid preproduction and motion graphics, 0.17.0

Status: private development candidate. The 0.16.0 harness is preserved in
`output/hybrid-story-0.16.0-baseline`; public slide and motion engines are not
changed. This work tests whether a design choice reaches actual rendered
geometry. It is not a completed narrated film or a viewer-quality approval.

## Preproduction path

Accepted script beats still determine `route` and diagram grammar before
concept selection. `preproduction-brief-0.3` now carries the viewer-state
change, attention target, required visual events, available diagram layouts,
reading hold, and research status into both concept selection and scene design.
Its hash remains bound to the selected concept. A missing registered source
still blocks a source scene. Registered catalog metadata is a candidate and
never changes `fact_verified: false` or grants media rights.

The research task distinguishes fact, design-reference and source-media needs.
It records the exact script passage, acceptance criteria, preferred primary
source class, candidate identity and meaning limit. External search,
independent factual validation, rights clearance and visual-reference ranking
are **not yet implemented**. These require a separate evidence provider and
review gate; a model-supplied URL cannot grant asset use.

## Executable visualization

`film-design-0.3` supports quantitative comparison as rows, columns or dot
tracks. Each uses one zero baseline and the same quoted values/unit. Layout
changes visual encoding only, not facts, scene route or event times. Dot
tracks do not connect samples into an invented trend. The prior
`snapshot_layout` remains scoped to `before_after`. A quantitative-only film
must present three distinct executable comparison layouts in its three
concept candidates; palette or type changes alone do not establish distinct
concepts. Other diagram grammars retain their implemented geometries.

The implementation follows [D3's continuous quantitative scale definition](https://d3js.org/d3-scale/linear)
and [Observable Plot's distinction between bar and dot marks](https://old.observablehq.com/plot/features/marks). These
sources inform the mapping and mark choices; neither certifies this film's
audience comprehension.

## Typography

Documentary uses Noto Serif CJK KR for titles and numeric values; editorial
uses stronger sans-serif value emphasis; explainer keeps compact, legible
sans-serif annotations. Each treatment changes actual CSS/SVG rendering.
Diagram axes, labels, values and annotations remain editable text; subtitles
keep the existing fixed style. The installed font families were checked in
the runner. Upstream [Noto CJK licensing](https://github.com/notofonts/noto-cjk)
is OFL, but distribution packaging still needs release review. Text palette
contrast and bounded SVG text are validated before asset work, with
[W3C's contrast criterion](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum)
as the primary design reference. No WCAG compliance claim is made for video.

## Verification and limits

- Harness manifest validation: `PASS hybrid-story@0.17.0`.
- Focused regression tests: 50 passed. Wider related regression: 166 passed,
  including three actual-frame layout render checks.
- The authored example of 20, 35 and 50 minutes rendered as three distinct
  1280x720 frames at 24 fps. All three text audits passed at 100 ms intervals
  with zero text overlap or text intrusion into the reserved caption zone.
- Visual inspection exposed a dot/value overlap in the first render. It was
  corrected and the dot layout was re-rendered and re-audited.

The tests use an authored fixture, not an unseen script. Script-to-shot quality,
source discovery, motion taste, emotional clarity and visual consistency of
generated images still need full-film and human A/B review. The static diagram
poster route remains separate from the animated selected-layout renderer and
should not be treated as proof of final-frame appearance.
