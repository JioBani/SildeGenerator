# Astra Layered Motion Lab Plan

## Status

Planned research engine. It is not registered in the product, is not public in the UI, and must not read or mutate production projects.

Proposed identity:

- harness id: `astra-layered-motion`
- first version: `0.1.0-lab`
- compose project: `astra-layered-lab`
- default provider mode: local and offline
- output class: review packet only

## Objective

Produce precise motion from AI artwork without flattening every shot into a new full-frame generation. The lab must discover when to use a master frame, how to regenerate editable layers from it, and how to prove that neutral recomposition preserves the approved artwork before motion begins.

## Non-goals

- Replacing `astra-motion@0.5.0`
- Appearing in the normal creation UI
- Automatically approving character acting, mesh deformation, contact, or clean plates
- Downloading large checkpoints into the production runner
- Sharing the production database, Redis queue, job volume, model cache, or ports
- Calling paid image APIs automatically

## Isolation Architecture

The lab will use a dedicated compose file and resource namespace.

```text
docker-compose.layered-lab.yml

astra-layered-lab-web       127.0.0.1:18870
astra-layered-lab-api       127.0.0.1:18871
astra-layered-lab-runner    GPU worker, concurrency 1
astra-layered-lab-postgres  separate volume
astra-layered-lab-redis     separate volume
astra-layered-lab-jobs      separate volume
astra-layered-lab-models    D: drive cache only
```

The experimental Harness manifest must set `public: false`. A lab export is a signed review packet; it cannot become a product delivery receipt. Production import is a later, explicit, hash-checked operation.

## Selective Master-frame Policy

A master frame is not generated for every scene. The director selects one production mode before asset work.

| Mode | Use | Master frame |
|---|---|---|
| `VECTOR_NATIVE` | process, comparison, number, route, diagram | no |
| `RIGGED_ACTOR` | recurring character and reusable acting | only when creating or changing the actor bible |
| `LAYERED_KEYART` | cinematic composition, unfamiliar space, emotional anchor | yes |
| `SOURCE_DECOMPOSED` | supplied photo or archive image | source is the master |
| `PROCEDURAL_3D` | camera rotation, strong perspective, physical contact | optional style target |

For a typical 60-second episode, the initial budget is one style frame and two to four master keyarts. Repeated locations, actors, and props reuse a versioned asset family. The budget is a guardrail, not a quota.

## Contracts

### LayeredScenePlan

```yaml
scene_id: scene-001
production_mode: LAYERED_KEYART
visual_family_id: lab-v1
master_frame_required: true
objects:
  - object_id: actor
    semantic_role: subject
    mobility: articulated
    depth_band: foreground
    occludes: [road]
    hidden_region_required: true
motion_intent:
  event: notice_and_step
  magnitude: subtle
```

### LayerPack

```text
master.png
clean-plate.png
depth.exr or depth.png
layers/
  actor.rgba.png
  foreground.rgba.png
  prop.rgba.png
masks/
  actor.png
  occlusion.png
shadows/
  actor-contact.png
manifest.json
```

The manifest records source and model hashes, prompts, masks, bounds, depth order, rights, review state, and every transformation. A layer is never production-ready merely because a model completed successfully.

## Research Pipeline

### Gate 0: Animatic

Build timing and composition with boxes, vectors, and proxy audio. Reject weak scene design before image work.

### Gate 1: Visual anchor

Generate only the style frame and required master keyarts. Group later shots by `visual_family_id` so they reuse the same actor, location, palette, and lighting contract.

### Gate 2: Object and depth analysis

Use semantic object requests from the director, Grounded SAM 2 for candidate boxes, SAM 2.1 for masks, and Depth Anything V2 Small for depth evidence. BiRefNet is a foreground-matting comparison candidate. No result is accepted from a single model without deterministic mask checks.

### Gate 3: Layer regeneration

Prefer master-conditioned regeneration over destructive removal:

1. regenerate the clean background using the master as composition reference;
2. regenerate movable objects at the same pose, lighting, and scale with transparency;
3. generate hidden regions only where the motion exposes them;
4. retain LaMa as a small-hole fallback, not the primary clean-plate generator.

LayerDiffuse is a benchmark candidate for transparent generation. Its source license and every base-model/checkpoint license must be recorded separately.

### Gate 4: Neutral reconstruction

Reassemble all layers at rest and compare them with the master before any motion.

Automatic evidence:

- output dimensions and alpha validity
- edge halo and transparent-color contamination
- connected components and frame touching
- neutral SSIM and edge difference
- object bounds, depth order, and occlusion consistency
- contact-shadow presence where required

Human questions:

- Is identity and drawing style preserved?
- Are lighting and perspective unchanged?
- Are revealed hidden regions plausible?
- Is the recomposed still indistinguishable at normal viewing distance?

Failure stops the scene before rigging.

### Gate 5: Motion authoring

- rigid objects: GSAP/HyperFrames transforms and path constraints
- simple organic objects: limited mesh with geometry evidence
- recurring 2D actors: OpenToonz Plastic or Blender Grease Pencil Gold rigs
- reusable real-time actor states: Rive benchmark, not a required production dependency
- spatial/parallax scenes: Blender camera and Grease Pencil layers

Motion is blocked into semantic poses first, then eased and supplemented with overlap, follow-through, contact shadows, and settle time.

### Gate 6: Motion review

Review neutral, midpoint, maximum deformation, contact, and settle frames. Compare against the static baseline and keep the best-so-far result. The lab may produce A/B/C candidates but may not auto-promote one.

## Tool Decisions

| Tool | Initial decision | Reason |
|---|---|---|
| SAM 2.1 Tiny/Small | P0 benchmark | promptable masks and later video tracking; suitable first comparison for 6GB VRAM |
| Grounded SAM 2 | P1 benchmark | text-to-object discovery; heavier dependency chain, so boxes remain optional evidence |
| Depth Anything V2 Small | P0 benchmark | 24.8M model, Apache-2.0, supports depth ordering evidence |
| LaMa | P0 fallback | useful for small holes; large structured removals require regeneration and human review |
| LayerDiffuse | P1 benchmark | transparent layer generation; quality, VRAM, and base-model licenses need validation |
| BiRefNet | P1 benchmark | high-resolution foreground matting comparison; weights and redistribution terms need review |
| OpenToonz Plastic | Gold authoring reference | mesh, skeleton, rigidity, and stacking order |
| Blender Grease Pencil | Gold authoring and 2.5D | layered drawing, masks, armatures, camera, frame correction |
| HyperFrames + GSAP | deterministic compositor | already pinned and measurable; receives only approved LayerPacks |

## Hardware Policy

The current machine has an RTX 2060 with 6GB VRAM. The lab therefore runs one GPU model at a time, concurrency 1, with a hard memory watchdog. Start with 1024px proxy analysis and SAM 2.1 Tiny/Small. Full-resolution masks are refined or tiled after the proxy pass. Model files live on D: and are never copied into the normal runner image.

## Benchmarks

Actor performance is the first research target. Do not add more scene effects until both actor benchmarks pass.

1. `ACTOR_NEUTRAL_01`: the authored actor reconstructs exactly at rest and all pivots, hidden regions, and contact shadows pass review.
2. `WEIGHT_SHIFT_01`: the actor transfers weight without foot sliding, volume loss, seam exposure, or mechanical simultaneous motion.
3. `REACTION_ACTOR_01`: eyes acquire the target before brows, head, face, torso, and hair react in sequence.
4. `RIGID_ICE_01`: only after the actor benchmarks, several ice floes drift independently while water and shore remain stable.

Each benchmark keeps the master, candidate LayerPack, reconstruction report, motion proof, failure record, and human verdict.

## Promotion Criteria

The lab can propose an adapter for the main engine only after all conditions hold:

- isolated bootstrap and shutdown pass repeatedly;
- no production database, queue, or job path is touched;
- three benchmarks reproduce from pinned hashes;
- neutral reconstruction passes technical evidence and human A/B review;
- failed masks, clean plates, and motion never auto-promote;
- GPU peak remains inside the configured budget without destabilizing the normal service;
- licenses for code, checkpoints, and generated assets are recorded;
- the adapter contract can be disabled with one feature flag and falls back to the existing renderer.

Promotion means porting a narrow adapter, not merging the research service or its model environment into the product runner.

## Implementation Order

1. Create the isolated compose profile, private Harness skeleton, model registry, and zero-provider smoke test.
2. Implement `LayeredScenePlan`, `LayerPack`, immutable manifests, and review packet export.
3. Author one deliberately simple actor from an approved design and pass `ACTOR_NEUTRAL_01`.
4. Run rigid-part and limited-mesh candidates for `WEIGHT_SHIFT_01` and keep the best-so-far result.
5. Add the face-state rig and run `REACTION_ACTOR_01`.
6. Add neutral reconstruction and Playwright A/B review for both actor scenes.
7. Benchmark SAM 2.1 Small against GrabCut only where master art must be decomposed after generation.
8. Add Depth Anything V2 Small and occlusion-graph evidence.
9. Compare LaMa with master-conditioned clean-background regeneration, then run `RIGID_ICE_01`.
10. Review data, remove ineffective steps, and write a production-adapter proposal.
