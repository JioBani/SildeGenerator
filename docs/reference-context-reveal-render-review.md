# Context reveal study and GPU transfer

Experimental example: `harnesses/astra-motion/examples/context-reveal-study`.
Host: astra-motion 0.3.0. Core, default renderer and providers unchanged.
Research-only example; no automatic production promotion.

## Outputs

- `context-reveal-blood-v2.mp4`: independently authored 12-second silent study
  corresponding to reference 183-195s.
- `context-reveal-gpu-v2.mp4`: the same transition applied to a calculation,
  processor overview and detail/system comparison. A transfer prototype,
  not a completed new-script video or verified teaching improvement.

Files live under `.runtime/reference-study`. Both use existing local GSAP and
the local seek renderer. No paid providers or new dependencies.

## Measured versus authored

`blood-context-title-v2.json` stores title template correlation and divider
measurements. Title acceptance threshold is .85; 51 of 96 frames accepted.
The accepted title patch moves from y=23 to y=283 between 185.018167s and
187.103583s. These are patch coordinates, not the title baseline.

The full-height pale divider is first detected near x=1 at 189.77s and settles
near x=321.5. V1 incorrectly completed the split by 189.75s. V2 uses measured
divider coordinates instead. Detection at the border has clipping uncertainty.

Outgoing title and vessel share one parent transform. The final outgoing
completion after tracking becomes unreliable is an explicit .28s hypothesis.
Heart position adjustment, network geometry and highlight cadence are authored
approximations. The local particle field is still static. No inference of
anatomical connectivity or biological particle identity is validated here.

## Visual review

V1 side-by-side review exposed premature comparison timing. It also showed
that the candidate branch structure is too sparse, the heart silhouette too
symbolic, the heading too heavy, and the deposit/cluster arrangement too regular.
V2 addresses divider timing only; those design and movement deficits remain.

GPU staging is readable in the sampled storyboard, but this is model review,
not a comprehension study. The opening calculation does not yet visibly map
to an identifiable processor unit. Lower explanatory text becomes small in
the split view. Both are required revisions before approval.

## Reproduction

Generate measurement using `scripts/measure_context_title.py` with the native
`blood-obstruction-165/motion.json`. Copy the example to a runtime directory,
along with existing pinned GSAP. Set `assets/config.js` to `window.studyConfig`
with mode `blood` or `gpu`, accepted `title` rows and non-null `divider` rows.
Use `scripts/render_reference_local.mjs` and `scripts/verify_reference_seek.mjs`.
Do not replace missing measurements with guessed evidence.

## Promotion gate

Current decision: REVISE; human approval false; transfer approval false.
Next: maintain operation identity through reveal, correct sparse source design,
measure particle movement, then add narration-aligned transfer and viewer
comparison. Deterministic seeking proves reproducibility, not fidelity.

## V3: identity-preserving GPU transfer

Example `context-reveal-study-v3` adds an explicit calculation A: inputs 2, 3,
1 and result 7. Local, system and detail representations share the same marker,
accent and result. The focal unit is excluded from the dimmed group animation.
The illustrative state changes to completed at 1.8s in all representations.

`scripts/verify_context_identity.mjs` checks all 360 frame states, plus negative
controls for a wrong marker, color, result and an oversized board. These checks
are deliberately separate from viewer comprehension and scientific accuracy.

Visual inspection found right-edge clipping that the identity checks could not
detect. V3 shifts the final system placement left and adds settled right-pane
bounds checks for board and caption. The pre-fix video is retained as
`context-reveal-gpu-v3-before-layout-fix.mp4` rather than treated as approved.

The focus fixture and invariants are stored beside the example in
`focus-contract.json`. They are experimental tests, not automatic rules or
approved Director Experience. No Core/provider/default behavior changes.
The full two-reference reproduction goal and complete narration-aligned
new-script transfer remain unfinished.
