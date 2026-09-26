# Director research promotion audit

This audit covers the source tree on 2026-09-25. It does not certify that the
running Docker service has been rebuilt or that any new video has been approved.
No paid model, image, or voice provider was used for this change.

## Promoted into the production code path

- `astra-motion@0.6.0` supplies a provider-free `validate_plan` hook. Before
  image or voice work, it rejects unsupported layouts, transitions, rhythms,
  motion effects, missing independent-object regions, and unreviewed actor
  reactions. The existing `classic-slide` path is unchanged. Plans requesting
  experimental actor capabilities still require an external human approval;
  declaring the capability in model output is not authorization.
- For Astra motion, the advisory creative-readiness report is now attached to
  the Scene Production Pack, including the per-scene asset-authoring route and
  missing evidence. This makes the design-to-asset decision traceable through
  the main job record. `production_ready: false` remains false and does not
  silently turn a separated image into an approved rig.
- The quality report now lists unresolved technical gates and separately tracks
  design, story comprehension, actor performance, and Gold comparison as human
  review axes. `TECHNICAL_PASS_HUMAN_PENDING` is not production approval.
- D's exact C/D comparison and the user's scoped naturalness/collar judgment
  are recorded as a research case in the director-learning ledger. It has
  `transfer_status: NOT_REVIEWED` and `promotion: NOT_APPROVED`. The runtime
  approved-director-rules catalog remains empty.

## Still blocked from automatic production

- Full actor rig, independent forearm/hand, curtain contact, and general
  `GRASP_AND_RETAIN` have no reviewed production asset for D.
- The creative-pilot audit has 9 bound evidence items and 19 pending reviews;
  the scene does not show a curtain decision/action or measured comprehension.
- All research director cases lack independent cross-script transfer approval.
  Reference reconstruction is partial and no whole-reference film is human
  approved. Neither evidence count nor test count is a quality score.
- The site-facing worker has not been rebuilt for this source change. Existing
  jobs pinned to an older `astra-motion` version need their matching runner image to retry;
  do not restart an active worker merely to expose this candidate version.
  At audit time the running API still reported `astra-motion@0.4.0`; the image
  OAuth helper was restarting. This source-level promotion is not a live-site
  deployment or a completed Mock end-to-end run.

## Next human review package

The next approval request must include an exact candidate video, matching
asset/program hashes, a full-path contact inspection, the same-narration
baseline, and separate questions for action comprehension, acting, design,
and neck/hand/curtain joins. The existing D response authorizes only the
previously observed naturalness and collar join, not the future curtain shot.

## Verification boundary

Run `scripts/harness.ps1 validate astra-motion`, the focused preflight,
creative-readiness, scene-contract, and learning tests in an isolated runner,
then a Mock end-to-end job before deploying. A Live job requires separate user
approval. Preserve the previous runner image and best-reviewed video.
