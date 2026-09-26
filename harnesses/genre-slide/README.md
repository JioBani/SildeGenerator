# Genre Slide 0.1.0

Private fork of astra-motion0.3.0. Existing render orchestration and pinned
HyperFrames/GSAP runtime are retained; genre composition is a separate compiler.
Only declared genre_id values are accepted. No automatic acting or fact invention.
Archival/generated provenance must be declared; unknown provenance is shown as
unverified rather than silently passed off as a real record. Cartoon presentation
does not prove a character sheet or acting quality. Preview only pending reviews.

Optional layout.visual_labels uses text and normalized media-region x/y anchors.
Up to eight labels are escaped and bounds checked; their font fit is validated
before rendering. Anchors are relative to the media region, not image pixels;
authoring must account for object-fit letterboxing. This is not automatic object
detection, semantic correctness or all-pair overlap approval.
