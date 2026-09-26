# Slide cinematic styles: 2026-09-22

## Direction

Two engine families remain the long-term architecture: slide cinematic and motion
graphics. Hybrid production is deferred. Narrative genre and visual style are separate:
a knowledge script can use cute characters or fantasy animation artwork without
changing its facts, narration or source order.

## Implemented in this iteration

- Added `cute_character` and `fantasy_anime` image-style choices, marked experimental.
- API enum, persisted database constraint, runner request, ScenePlan schema and director
  selection accept both choices. Existing default stays editorial illustration.
- Shared versioned preset Markdown is loaded and hashed alongside harness prompts.
  The existing active-preset filter records only the selected preset in each job.
  Released harness folders are unchanged; shared presets ship with the Core image.
- Rules cover silhouette, line, shading, texture, framing, expression stills, original
  identity and restrictions against inventing script events or unsupported animation.
- Explicit new style overrides genre art direction, not genre source-label requirements.

## Verification and limits

Planner/source preservation/prompt isolation tests and web/server builds passed.
No provider calls, asset generation, live job or database migration were executed.
Docker service end-to-end operation and visual quality are NOT proven by these tests.
The choices are prompt-driven experimental styles, not approved production capabilities.
They do not create a rig or guarantee identity when continuity references are disabled.

## Next visual acceptance work

For each style, prepare one original canonical character and an environment sheet.
Produce three different views using the same anchors: establishing shot, reaction
close-up, and explanatory composition. Inspect cropping, expression legibility,
identity, color/line continuity and information clarity. Make a short slide film with
purposeful camera framing and cuts, then transfer to a second script. Keep narration
and timestamps unchanged when comparing art iterations. Human approval and evidence
must precede any claim of a finished style. Do not add hybrid routing to evade this test.
