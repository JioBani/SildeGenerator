# Continuous posture study: 60-120 seconds

Three independent excerpts were assembled in narrative order for a 60-second
silent inspection. This is not a completed reference reconstruction or delivery.

## Authoritative artifacts

Root: `.runtime/reference-study/posture-continuous-60-120-v1`.

- `continuous.mp4`: 1800 frames, normalized 1920x1080, 30fps H.264.
- `continuous.receipt.json`: ordered input windows, hashes, durations, output hash.
- `boundaries.png`: frames 899/900 (source 90s) and 1379/1380 (source 106s).

The latest consequences V3 had no MP4 despite existing code and sampled checks.
It was rendered before assembly. `assemble_reference_study.py` rejects empty,
gapped, overlapping or reordered intervals, duration mismatch and audio-bearing
inputs (this explicitly silent tool must not discard narration). Three unit
tests cover coverage validation. Output frame count and full decode passed.
This does not substitute for Docker Mock E2E or source fidelity review.

## Failed continuity review

At source 90s the candidate changes passenger count, pose, costume and carriage
geometry. These excerpts independently authored the same continuous transit shot.
At 106s the frontal actor changes face, pose, scale and crop abruptly. This is
not a planned source cut; the independent drawings and camera states disagree.

These are substantial regressions invisible to isolated duration/seek tests.
Do not designate the assembly as a best version or a quality pass. Preserve it
as the first continuous baseline. No narration or human approval is present.

## Required structural repair

Use one independent transit ensemble and one frontal actor rig shared across
adjacent study programs, with explicit end-to-start state transfer. The linked
`posture-continuity-contract.json` specifies identities, asset hashes, pose/face,
prop attachments and world/camera transforms. It is a pending study contract,
not yet an implemented production gate. A crossfade would conceal rather than
repair identity discontinuity and is not accepted as the fix.

Next render must retain all 60 seconds and fix both joins before reviewing finer
acting. Existing head, proportion, posture and source-timing gaps remain in
addition to the joins. The whole two-reference and full new-script objectives
remain incomplete.

## V2 shared assets and verified static handoffs

`posture-shared-v1` contains independent transit and frontal SVG geometry exported
from our authored browser DOM, NOT source-video pixels. The export manifest records
source study and content hashes. `posture-consequences-v4` and `posture-context-90-v3`
both consume the same transit.svg. The latter uses the initial frontal geometry
from alignment V7 and reaches its unit scale before the 106s join. Existing
alignment V7 then performs the abstraction. This is static-pose asset reuse, not
a general rig/state-transfer system and not INTERACTION_READY.

Revised 60s output: `posture-continuous-60-120-v2/continuous.mp4`, 1800 frames;
ordered receipt and input/output hashes saved. Sixteen context reverse-seek samples
passed with both SVG assets explicitly loaded. `verify_posture_joins.py` compares
the two intended static handoff poses in the decoded combined video:

| Boundary | V1 mean channel difference | V2 mean channel difference |
| --- | ---: | ---: |
| 90s | 32.55885 | 0.01474 |
| 106s | 6.81491 | 0.01222 |

Experimental acceptance is mean difference <1.5/255 and fraction of pixels with
any channel difference >30 below .005. V1 fails both; V2 passes both. A boundary
contact sheet was visually inspected: the identity/layout jumps are gone. These
thresholds are specific to static handoffs, not applicable to intentional cuts
or moving boundaries. Compression tolerance is not aesthetic approval.

Remaining source-fidelity issues include mismatched facial expression (the shared
smile is not approved as the source emotion), proportions, early frontal framing,
static transit action and hypothesized zoom. Sharing an asset prevents accidental
identity swaps but does not prove that the shared asset is good. Preserve both
versions and keep overall status REVISE. No paid calls or Core/default changes.
