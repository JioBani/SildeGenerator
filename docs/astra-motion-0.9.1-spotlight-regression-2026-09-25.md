# Astra Motion 0.9.1 spotlight regression

Status: isolated local-production pilot; technical checks passed; human design and story review pending.

## Failure and cause

- Job `4a49c18e-fd49-465f-8400-097b1d9c6d0a` described a shirt stain and the spotlight effect, but its 0.9.0 local plan selected `attention` because the whole-script keyword list matched generic words such as `관심`.
- The 0.9.0 narrative renderer drew four cars and the same city background for every narrative scene. The selected beat changed labels and timings, not the actual subject. A completed video with different narration therefore looked like the earlier car video.

## Change

- `spotlight` is a specific theme ahead of the generic attention match. Its local scene contract selects incident, definition, imagined gaze, evidence, question, other-people-busy, realization, and release modes from the narration. The repeated person, shirt mark, crowd, light cone, evidence panel, and scene actions are editable renderer elements.
- The spotlight background is a public indoor setting rather than the old street. The 0.9.0 harness source is preserved at `release-archives/astra-motion-0.9.0`; new work uses `astra-motion@0.9.1` in the isolated service. The original job and video were not overwritten.
- A regression test checks that the spotlight script does not compile car props, has multiple modes, and draws different background pixels from the attention script.

## Evidence and limits

- Three local-motion tests and harness validation passed. The same spotlight narration was rendered as job `6afc2f48-7edc-4371-a988-f889c99358a4`, 37.79 seconds, 1920x1080, H.264/AAC; status `TECHNICAL_PASS_HUMAN_PENDING`.
- Video: `experiments/motion-style-v08/spotlight-091.mp4`. Representative frames: `experiments/motion-style-v08/spotlight-091-contact-sheet.png` and `experiments/motion-style-v08/spotlight-091-end.png`.
- The new result is visually distinct from the car video, but the actor and crowd placement still repeats across several cuts. This is a limited authored vocabulary, not a general semantic-image generator or approved acting system. Human review should decide whether the story and emotion now read clearly. Other topic families still need their own executable visual treatments instead of relying on generic props.
