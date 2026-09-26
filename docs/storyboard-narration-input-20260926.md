# Timed storyboard input: spoken text boundary

Status: deployed to the local main site on 2026-09-26. This change concerns
script extraction, not automated visual interpretation of shot directions.

## Contract

- If any `나레이션:`, `내레이션:`, `음성:`, or `VO:` label exists, only explicitly
  labeled lines (or a label-only narration block) become the production
  `scenario`. The labels and outer quote marks are removed.
- Markdown headings, concept descriptions, timestamped shot headers, visual
  notes, and table separators are excluded. If no spoken text remains, the
  estimate/create API rejects the input before queuing a job.
- The raw input is retained as `scenario_input` for audit/remake; the sanitized
  `scenario` is what the worker sends to the planner, speech provider,
  subtitles, and scene-image prompts. The raw visual notes are **not** passed
  through as on-screen text or automatically treated as executable direction.
- The public estimate response includes `narrationText`, used for the
  collapsible spoken-script preview and duration estimate. A labeled
  storyboard waits for this estimate instead of using the entire raw input
  length as a false 60-second gate.

## Evidence

- Server unit tests: 40/40 pass, including a five-beat timed storyboard and
  the fail-closed visual-only case. Web build and 12 unit tests pass;
  Playwright motion-format tests: 3/3 pass.
- Isolated Mock job `27575381-c619-4fdd-86b4-b696f7005c64` completed.
  Its stored production scenario, final scene plan, and subtitle file contain
  the two spoken sentences but not the distinct visual-note terms.
- The main site's `POST /api/jobs/estimate` returned only the two narration
  sentences from a timed storyboard. `doctor.ps1 -SkipSmoke` passed all four
  read-only checks after deployment. No live image or voice generation was
  triggered for this change.

## Limit

The director currently plans imagery from sanitized narration; user-supplied
shot directions are deliberately not executed or rendered as labels. To use
those directions as optional design guidance later, introduce a separate,
structured, rights-aware field and a nonverbatim review gate. Do not silently
recombine raw notes with speech or captions.

Rollback images: `slidegenerator-api:pre-script-parser-20260926` and
`slidegenerator-web:pre-script-parser-20260926`. Database backup:
`.runtime/backups/slidegen-pre-script-parser-20260926.dump`.
