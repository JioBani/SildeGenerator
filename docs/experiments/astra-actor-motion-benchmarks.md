# Astra Actor Motion Benchmarks

## Decision

Implementation evidence (2026-09-24): the first original vector actor and offline two-scene bench are in `experiments/layered-motion/`. See `actor-motion-v1-review.md`. This is a candidate design with technical checks, not a human-approved Gold actor. OpenToonz/Blender comparisons and raster interchange remain pending.

The Layered Motion Lab will first prove two small acting units:

1. `WEIGHT_SHIFT_01`: a whole-body weight transfer with planted feet.
2. `REACTION_ACTOR_01`: stimulus, gaze acquisition, facial change, head follow, torso response, hold, and settle.

The objective is not maximum movement. It is readable acting with an approved design, stable identity, correct contact, and no image damage.

## Asset Production Strategy

### Preferred Gold path

```text
AI or authored character concept
→ approved design master
→ redraw as clean production layers
→ restore hidden overlap regions
→ place pivots and anchors
→ neutral reconstruction review
→ rig
```

The concept image defines shape language, palette, texture, proportions, and appeal. It is not itself assumed to be a riggable production asset.

### Allowed experiment path

Use the approved master as an image-editing reference and regenerate one requested layer at a time. Every layer keeps the same canvas, pose, camera, lighting, and scale. The full set must pass neutral reconstruction before animation.

### Rejected path

Do not independently prompt each body part from text. Separate generations tend to drift in line weight, lighting, anatomy, scale, and texture, and they do not preserve hidden overlap geometry.

## Gold Actor Pack

```text
actor-v1/
  design/
    master.png
    palette.json
    proportion-guide.png
  body/
    torso.rgba.png
    pelvis.rgba.png
    upper-arm-left.rgba.png
    forearm-left.rgba.png
    hand-left.rgba.png
    upper-arm-right.rgba.png
    forearm-right.rgba.png
    hand-right.rgba.png
    leg-left.rgba.png
    leg-right.rgba.png
    foot-left.rgba.png
    foot-right.rgba.png
  head/
    head.rgba.png
    hair-back.rgba.png
    hair-front.rgba.png
  face/
    eye-left.rgba.png
    eye-right.rgba.png
    pupil-left.rgba.png
    pupil-right.rgba.png
    brow-left.rgba.png
    brow-right.rgba.png
    mouth-neutral.rgba.png
    mouth-notice.rgba.png
    mouth-pleased.rgba.png
  contact/
    foot-shadow.rgba.png
  rig/
    anchors.json
    hierarchy.json
    limits.json
  review/
    neutral-reconstruction.png
    manifest.json
```

The first rig uses rigid parts and face-state swaps. Limited mesh deformation is added only when a bend cannot be achieved without visible gaps. This keeps design and acting failures separable.

## WEIGHT_SHIFT_01

### Story function

The actor notices or considers something and subtly transfers weight before deciding. The motion should read as life and intention, not walking.

### Performance phases

```text
REST
→ pressure begins at one foot
→ pelvis shifts toward support foot
→ torso counterbalances
→ shoulder line follows
→ head follows with a small delay
→ contact shadow settles
→ HOLD
```

### Initial timing hypothesis

```text
0.00–0.35s  rest
0.35–0.85s  pelvis and center-of-mass shift
0.55–1.05s  torso and shoulder counter-motion
0.75–1.20s  head follows
1.20–2.20s  hold
2.20–3.00s  settle
```

### Technical evidence

- planted-foot displacement
- pelvis and shoulder trajectories
- center-of-mass proxy relative to the support area
- exposed seam and transparent-hole count
- silhouette area change
- contact-shadow alignment
- neutral return error

Provisional 1080p targets, to be calibrated rather than treated as Gold truth:

- planted-foot drift at hold: at most 3 px
- unplanned seam gap: at most 2 px
- flipped mesh triangles: 0
- frame-edge contact: 0

### Human review

- Does the actor feel alive while remaining restrained?
- Is weight visibly supported by one leg?
- Do the feet remain attached to the ground?
- Does the head lag rather than lead mechanically?
- Is the approved character design unchanged?

## REACTION_ACTOR_01

### Story function

An image appears on a monitor. The actor sees it, understands it, becomes slightly pleased, holds the reaction, and settles.

### Performance order

```text
STIMULUS
→ eyes acquire target
→ eyelids and brows register notice
→ head follows gaze
→ mouth changes
→ torso releases
→ hair and shoulders follow through
→ HOLD
→ SETTLE
```

### Initial timing hypothesis

```text
0.00s        stimulus appears
0.10–0.35s  pupils move to target
0.25–0.55s  eyelids and brows change
0.35–0.85s  head aligns
0.55–1.00s  mouth changes to slight pleasure
0.75–1.25s  torso and shoulders respond
1.25–3.20s  reaction hold
3.20–4.00s  settle
```

### Technical evidence

- stimulus frame
- gaze start and target-acquisition frames
- brow, head, mouth, torso, and secondary-motion start frames
- eye target error
- pivot drift and facial popping
- identity and silhouette continuity
- hold and settle duration

### Human review

- Is the target of attention immediately understandable without sound?
- Do the eyes move before the emotional expression?
- Is the reaction subtle rather than theatrical?
- Do head, torso, and hair cooperate without moving simultaneously?
- Is there enough hold time to read the new emotional state?

## Authoring Tool Comparison

Create the same actor and timing contract in two authoring paths.

### OpenToonz Plastic

Use raster layers, mesh, skeleton, rigidity, and stacking order. This path tests whether approved textured artwork can retain its look during restrained acting.

### Blender Grease Pencil

Use layer groups, masks, armature parenting, and selective frame correction. This path tests stronger control of hidden regions, silhouette, and 2.5D camera integration.

Rive remains an optional third benchmark after the two open authoring paths. HyperFrames receives only approved rendered layers or an approved deterministic motion contract.

## Pass Order

```text
DESIGN_READY
→ ACTOR_NEUTRAL_READY
→ WEIGHT_SHIFT_TECHNICAL_READY
→ WEIGHT_SHIFT_ACTING_READY
→ REACTION_TECHNICAL_READY
→ REACTION_ACTING_READY
→ ACTOR_MOTION_READY
```

No later state can be inferred from an earlier technical pass. Every acting-ready state requires a recorded human verdict.
