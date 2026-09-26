# Runtime image origin

The production asset preparation path now records origin from the configured image
provider after the image task succeeds and image validation passes. It overwrites
planner-supplied layout.asset_origin and layout.asset_provenance, then persists the
runtime record in scene-plan.resume.json, scene-plan.final.json and tracker assets.

Fields: schema version, origin, provider, image task ID, actual output SHA-256,
recorded_by=runtime_asset_preparation and archive_verified=false.
Mock maps to mock, oauth to generated; unknown providers remain unknown. This is
generation provenance, NOT verification of depicted facts, references or licenses.
External archival ingestion is not implemented by this helper.

Evidence on 2026-09-22:
- Seven focused genre/style/origin tests passed.
- Isolated Docker runner rebuilt successfully.
- Five-genre HTTP submission/render/download smoke passed again, now checking each
  output image hash against the final plan's runtime provenance and mock origin.
- No paid providers were invoked by the isolated tests.

The public classic-slide output still does not draw evidence labels; the private
cinematic-slide supports them. Do not claim this change alone enables public
documentary production or replaces human review. Old completed plans are untouched;
newly prepared/resumed image tasks receive new runtime evidence.
