# Fantasy valley complete short-script probe

## Input and delivery

Fixture: harnesses/cinematic-slide/fixtures/fantasy-valley.json.
Two complete source sentences, not excerpts from a longer script. The deterministic
planner preserves both source units; authored shot directions and generated images
are attached explicitly. This is not an autonomous director quality evaluation.

Output: output/fantasy-valley-delivery-v1/delivery/cinematic.mp4.
Measured 12.777506 seconds, 1920x1080, 30fps, H.264/AAC. Offline Windows SAPI narration.
ScenePlan, production pack and receipt are written alongside intermediate artifacts.
Two built-in image-generation operations supplied new illustrations. No application
paid provider/API calls were executed. Built-in billing is not inferred.

## Visual evaluation

- Character retains short bob, jade cape, oval clasp, ivory tunic and satchel across
  wide and medium views. Face is entirely inside the sampled final moving frame.
- Wide shot gives geographic context; medium shot makes the expression readable.
- Restrained pull and push run through the actual camera expressions in FFmpeg.
- A true cut replaces the old unconditional dissolve at zero fade duration.
- Caption remains legible, but crosses the illustrated lower torso/path. The image
  prompt's quiet-bottom request was not fully obeyed; composition is not automatically
  approved by a successful render.
- Mist clearance is weak evidence: the path is already visible in the wide shot and
  neither still animates wind. The narrative transition is inferred through editing,
  not a physically animated reveal. Future refinement should stage conceal/reveal more
  clearly before promoting this as an explanatory or action capability.

## Reusable improvements and limits

The local delivery smoke now accepts a fixture containing a full script, visual style,
shot assets and camera intent. It produces a real ScenePlan and runs source validation,
production-pack validation and camera preflight before offline voice/render work.
It uses the registry-loaded harness and task graph. It is not Docker/HTTP/queue E2E.
The public style picker still selects experimental art presets; private cinematic
rendering is not automatically routed there. Full-length and second-script human
style review remain outstanding. No automatic Gold promotion.
