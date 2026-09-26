# Genre production implementation

## Current boundary

Tutorial V3 reuses the exact V2 narration files/timings and stream-copies the V2
AAC track into the24.7s delivery. It replaces the middle document shape with a
storage device and adds separate DOM labels for original file/storage/copy check.
The compositor now accepts bounded visual_labels; planning guidance documents
their media-relative anchors. Fifteen label/title/caption bounds pass; invalid
coordinates and empty text reject, and markup is escaped. The decoded12s frame
was inspected. Output: `.runtime/reference-study/tutorial-genre-v3/narrated.mp4`.
No new speech or paid image calls. Semantic clarity is improved in the inspected
frame, but not user-tested or approved. This fixture is still explicitly authored,
not proof of arbitrary script-to-asset generation.

### Offline voiced tutorial sample

Existing Windows SAPI Microsoft Heami Desktop was verified and used to create a
three-step file-backup tutorial with no network/provider calls. The synthesis
script is review-only, does not change the service voice provider, preserves old
audio and confines scene filenames to the manifest directory. Script execution
policy initially blocked V1 before audio creation; V2 used a process-local policy
override, without changing machine policy.

`.runtime/reference-study/tutorial-genre-v2/narrated.mp4`:24.700000s video and
24.700010s AAC audio,1920x1080,30fps,H.264. Scene lengths are measured from local
speech, not guessed. Text bounds pass; the12s decoded sample shows the explicit
second step and its narration. The diagram has three similar document shapes,
so storage-device versus file semantics are not sufficiently differentiated.
This remains REVISE, not approved instructional artwork. No listening assessment
or service E2E is claimed. Next improve distinct object roles and review human
understanding; do not infer arbitrary-script generation quality from this fixture.

### Knowledge narration fixture

`.runtime/reference-study/knowledge-genre-v1/narrated.mp4` is a15.833333s,
475frame original GPU schematic slideshow through genre-slide, using the existing
three-sentence narration excerpt. Its AAC hash remains
`7d08ec908a3317993cae37837f98332f094b64dcd7e028b36fd45795e3995dc8`.
The original schematic contrasts one calculation, queued sequential tasks and
parallel lanes. It is a concept illustration, not a CPU/GPU speed benchmark.
Decoded3s/8s/13s samples were visually inspected. Text-fit checks pass; negative
overflow testing still blocks. No new audio/image provider calls.

This is an actual-script slide fixture, not a full episode or automatic creation
proof. Schematic assets were explicitly authored for this fixture; automatic
asset selection remains unverified. Individual diagram marks do not animate;
the current compositor reveals the entire illustration. Design/understanding
approval and the other four narrated genre examples remain outstanding.

Renderer routing now rejects mismatched genre selections and harness IDs at the
request model boundary. genre-slide receives the same pre-render measured60s
ceiling and scene/asset budgets as astra-motion. The plugin checks positive
duration, dimensions, codecs and actual FPS; zero/NaN duration and wrong FPS no
longer pass. Registry tests distinguish private research harnesses from public
choices rather than assuming no private packages exist. These remain local
SDK/model tests, not a service queue or Docker E2E claim.

### Text safety gate

Genre compositor waits for fonts, fits title/caption/credit into fixed areas, and
does not expose its timeline if text still overflows at the minimum font size.
It never truncates narration. Title minimum32px, caption28px, credit20px at1080p.
Supported canvas is explicitly1920x1080; other sizes reject rather than relying on
untested fixed dimensions. Browser verification on genre-comparison-v3 passes all
twelve text containers across five scenes. A7500-character negative caption is
preserved intact and correctly blocks timeline readiness. Evidence:
`.runtime/reference-study/genre-comparison-v3/text-review.json`.
This gate does not prove all-object non-overlap, source truth or comprehension.

Real model integration verification now passes: five genre plans through
create_plan -> Pydantic serialize/restore -> validate_plan -> genre compositor,
with exactly the same narration sequence as the legacy plan. Input prompt maps
are not mutated. StyleBible now receives the selected visual direction, including
cartoon character-sheet constraints and documentary/ historical reconstruction
restrictions. These constraints still need asset-level review; prompt text alone
is not evidence that they were satisfied.

The previous missing-pydantic test problem was resolved without installing any
packages: bundled Python3.12 supplies Pydantic, with the existing local pure-Python
HTTP dependencies available on its search path. Twelve planner regression tests
and eight genre tests pass. This is not Docker, queue or provider E2E.

Implemented five versioned research profiles: knowledge, history, tutorial,
cartoon and documentary. Purpose and visual treatment are separate fields.
Cartoon requires a character sheet and consistent line/texture; documentary
requires provenance and reconstruction labels. These are requirements, not claims
that the current renderer verifies them.

Local recommendation uses explicit text signals and reports ambiguity; it never
starts production. Snapshot hashes bind profile content. The director create_plan
entry point accepts an optional genre_id, adds visual guidance to a copied prompt
set, and attaches the snapshot to the resulting plan. Narration order and existing
motion are preserved. Legacy calls omit genre_id and keep existing behavior.

Service request genreId now propagates through persisted genre_id/genre_version,
queue data and both runner adapters into director planning. Python validates the
installed profile version before work and persists the full genre snapshot before
render/cache access. Retry mismatches or missing snapshots reject reuse. Legacy
requests have no genre and retain their previous route. Database migration code
is added but not applied to a running service in this session.

User radio controls and explicit recommendations are now connected to the public
genre catalog. Script edits never override manual selection. Catalog failure
retains the classic route; preview selections disable submission and the server
rejects them before quota reservation. Mocked-API browser testing passes manual
selection persistence, preview blocking, classic fallback and390px overflow check.
Web/server builds pass. The default test port5187 was OS-denied; port18767 worked.
This is not a running-service E2E or a production release. Profiles remain preview /
production_approved=false; live genre production is explicitly blocked before
provider work until compositor review passes. No paid calls were used. This is
foundational implementation, not completion of selectable genre video production.

## Remaining required work

### Initial compositor implementation

Private genre-slide0.1.0 now compiles five distinct image/text layouts using the
existing HyperFrames orchestration. History places the subject beside editorial
text, tutorial reserves a step lane (only explicit supplied step numbers), cartoon
uses strong panel borders, documentary uses full-frame evidence with labels,
and knowledge uses a bright central image stage. Unknown source material is
labelled unverified. This does not establish archival truth or character identity.

The local comparison reuses the independent posture character in all five
layouts, four seconds each, with no voice or paid calls. It tests composition,
not genre-specific storytelling or a finished sample for each genre. Existing
renderer/default harness is unchanged. UI, production binding, full narration,
automatic text-fit gates and Docker Mock E2E remain outstanding.

Rendered local20s/600frame comparison V1 exposed word splitting in history headings
and a documentary heading over the face. V2 adds keep-all heading wrapping and a
separate documentary media safe area. Decoded18s V2 frame was visually checked.
Files: `.runtime/reference-study/genre-comparison-v2/comparison.mp4` and review.png.
These are silent composition fixtures, not finished narrated genre samples or
evidence of approved cartoon style/archival authenticity. Harness validation and
the five-layout escaping/provenance unit test pass; no paid providers called.

1. Genre-specific slide compositor and demonstrated outputs for all five genres;
   preserve classic-slide and route unsupported layouts to explicit review.
2. Server snapshot persistence and request propagation through both runner types,
   retry/cache identity, and user-facing recommendation/selection.
3. Stable original character sheet fixtures and source-labelled documentary assets.
4. Three initial short samples, plus cartoon/documentary variants; same-script
   cross-genre comparison and 60-second episode checks.
5. Docker Mock end-to-end, existing-job regressions, readable small-view previews,
   human quality approval before general release. Previous Docker check failed
   because the daemon was unavailable; no deployment success is claimed.

Original reference research remains incomplete. Reusable measurements and failure
records are retained, not promoted to universal directing rules or completed study.
