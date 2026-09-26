# Whole-reference reconstruction program

## Objective

Treat every user-supplied reference as a whole-film reconstruction task, not a completed style sample. Current registered set: ten links; six local sources have whole-film overview evidence, four earlier references still require source registration and inventory verification. The existing goal remains unfinished.

Learning here means accumulating measured source observations, reusable assets, execution contracts, regression fixtures and externally reviewed outcomes. It does not mean training or changing GPT model weights.

## Honest completion gates

1. Register source identity and hash, duration, available sound/transcript and rights boundaries.
2. Review every boundary candidate, including the ending. One-second sampling alone is insufficient for acting and movement.
3. Annotate scene function, design, layout, object states, motion, transition, rhythm and audio events. Measure native frames at movement and transition intervals. Separate object motion from camera motion.
4. Reconstruct consecutive source windows, preserve timing and object identity, and compare source/candidate in synchrony. Do not pad a four-second mechanism with a hold and count six source seconds.
5. Track design, layout, motion, transition, rhythm, audio and meaning separately. Technical success cannot replace human review of expressive similarity. Silent studies cannot pass full audio fidelity.
6. Keep best versions. A changed source or candidate hash invalidates the associated review. Completion requires all source intervals, not a few attractive samples.
7. Demonstrate transfer to a genuinely different script with a separate output and review. A repeated original file cannot qualify as transfer.

The source excerpts are local reference evidence, not freely redistributable production assets. Reconstructed videos use original assets; licenses and attribution must be recorded for any open assets. Do not claim ownership of the original film or reuse its audio in a public release without appropriate rights.

## What changed in this cycle

- `docs/reference-curriculum.json` registers all ten references and existing evidence locations.
- `scripts/reference_curriculum.py` builds new immutable backlog snapshots, preserves fractional tails, unions overlapping time spans, and distinguishes sampled/studied/approved coverage.
- Six source overviews produced 412 **automatic segment candidates**, not 412 fully annotated or approved shots. Missing fields remain null rather than fabricated.
- Posture and blood-pressure candidates exist, but their exact source-time mappings have not been registered. They receive no timing coverage credit until aligned.
- Reference review tests cover overlap, invalid ranges, tail loss, missing sources, stale hashes, missing audio review, model self-approval and missing transfer evidence.
- No production renderer defaults, model providers, user approvals or paid API behavior changed.

## Continuous bird-flu study

Previously only 256-262s had a six-second hand-contact study. New source extraction adds 480 frames for 262-282s and 208 for 282-290.707s. Combined with existing windows there are 1,119 extracted native frames and 46.707 seconds sampled in this source. Sampling is NOT equivalent to reviewing every frame.

The source contact sheets show the following visible events:

- Two agents hold contact while colored particles and a bright transition surround them.
- The pair disappears, and a blue agent with mixed surface markers appears.
- Facial expression changes and the agent moves toward another boundary.
- The following cuts return to an animal character and then a flock. These shots are not included in the new candidate.

`bird-flu-exchange-study` reconstructs the continuous 256-275s span as a 19-second silent experiment. This extends from relationship establishment to the transition and next movement. It is a visual metaphor study, not a validated biological simulation.

Remaining gaps: precise original timing, original character proportions, organic background structure, inherited marker topology, hand anatomy, original audio, and source-to-candidate spatial tracking. Human fidelity approval remains pending. Do not call this the full 389.734-second reproduction.

Actual v1 A/B inspection found the new agent too small and marker overlays visibly less coherent than the source. Native seek review passed 7/8 sampled times; at 14s, 3,173 pixels differed by at most two channel values. This strict failure is retained in the study contract; the candidate is REVISE, not technical PASS. The file is a playable comparison draft, not a promoted capability. The eight checkpoints do not cover the entire 19-second timeline.

Current snapshots: `.runtime/reference-study/curriculum-v1/` preserves the initial audit; `curriculum-v2/` includes the new continuous study. Bird-flu partial-study coverage is 31 unique source seconds after unioning overlapping intervals, not 37. All ten references remain incomplete, with zero human-approved whole-film coverage.

### Continuous study v2

The subsequent goal turn corrected the new agent's surface topology: the bitmap body paint is isolated from old markers, and ten independent inherited markers have their own stems. An explicit local SVG origin prevents changes to artwork bounds from moving the actor's pivot. The body scale and center are now measured against a source frame around 268.2s instead of being judged solely by eye.

At that keypoint, source center is (0.472925, 0.439836) and v2 center is (0.473843, 0.440332); source width is 0.240625 of the frame and v2 width is 0.241146. Height remains different: source 0.408333, candidate 0.428704. This is a one-frame registration measurement, not an overall similarity score.

Strict screenshot seek matching still fails at 9.5s and 14s (6/8 pass). A DOM inspection at an earlier failing 17s state found no differing attributes or computed transforms. Disabling GPU rasterization made agreement worse and was reverted. Do not falsely claim this experiment solved determinism. Keep the new artwork/pivot improvement while separately investigating rendered-pixel stability.

Reusable lesson: body paint, identity markers and performance layers require separate coordinate contracts. Register by normalized source geometry, preserve explicit pivots, and measure both center and silhouette dimensions. This remains experimental knowledge, not an automatically approved production rule.

## Order of work

Finish the bird-flu continuous sequence comparisons first, then systematically fill all its unreviewed source intervals. Repeat for posture, blood pressure, heat, NVIDIA and questions. Inventory earlier four references before scheduling their full reconstruction. Each film needs its own profile; do not mix paper illustration, saturated internal-world cartoons and dark information graphics into one template.

At every cycle record: source interval, hypothesis, measurements, asset/design decisions, candidate hash, failures, correction, comparison, reviewer decision, elapsed time and calls. Promote a rule only within its tested conditions, with counterexamples and known failures.

## Environment

C: reported zero free space. Bootstrap Docker check timed out; Mock service smoke was therefore not completed in this cycle. Local analysis and isolated rendering use D: temporary storage, existing assets and local Chrome/FFmpeg. No user files were deleted and no paid provider calls were made. Docker operational recovery is still outstanding and must not be described as healthy.
