# Director visual output contract repair

Finding: cinematic prompts requested layout.camera and continuity_group, while the
strict scene-plan output schema disallowed them. Genre guidance similarly requested
visual_labels without a schema field. Authored fixtures bypassed this mismatch, so
their good render results did not prove autonomous planning could express the same
direction.

Repair:
- Add required nullable camera and continuity_group to structured layout output.
- Camera supports hold/push/pull, normalized two-coordinate focus and 0..0.08 strength.
- Add bounded visual_labels with independent text/coordinates (empty array allowed).
- Permit cinematic-slide as a renderer preference; it is still a private renderer.
- Null camera compiles as hold; existing stored layouts without the keys remain valid.
- Align private cinematic prompt with supported transitions and explicit fields.

Verification: 18 compiler/planner/preflight tests and a schema-validator test passed.
The semantic proposal is compiled into a real ScenePlan, preserving camera and label
coordinates and passing actual cinematic preflight. Structured objects are checked
for required/property parity. Invalid modes, strengths and label coordinates reject.

Limits: no live model call or public renderer promotion. The compiler preserving a
camera choice does not prove correct focal selection. classic-slide still does not
execute every cinematic field, and not every renderer draws visual_labels. Other
genre-specific layout vocabulary and full output-quality review remain necessary.
