# Evidence-linked visual meaning corrections

The first registered correction is the posture source 207s guard/sentry box previously mistaken for an anatomical overlay. It contains the source hash, enlarged image hash, exact analysis partition, observed timestamp, discriminating visible cues, rejected hypothesis, correction and unresolved narration claim. It is a model observation awaiting human review, not an approved Director Experience.

Use the research atlas compiler with `--observations docs/reference-semantic-observations.json` to attach this evidence. The current compiled output is `.runtime/reference-study/director-atlas-v8/director-records.json`. Its posture 204-216 record contains the guard observation, while other partitions remain unreviewed. Existing production/Core paths are unchanged; this is not yet a global runtime guard.

Checks reject a mismatched source, changed evidence image, incorrect partition, out-of-scope timestamp, missing cues/evidence, or a scene state contradicting the correction. Duplicate IDs and unknown reference IDs are rejected before output. Artifact hashes bind the observation to inspected material, not truth: semantic correctness still depends on visual review. A point observation does not prove every frame of a partition.

The compiler keeps three levels separate:

- Visible identity and supporting cues: a uniformed guard, garment details and shelter.
- Story-function hypothesis: why this posture appears here, still tentative.
- Narration claim: null until audio meaning is verified.

No observation can switch render_authorized, human_approved or production_promotion to true. No model statement is accepted as human approval. Old failed videos remain preserved and excluded from reconstruction coverage where marked REJECTED_SEMANTICS.

Six focused tests cover valid non-promoting attachment, source mismatch, wrong interval, changed image, contradictory scene state and out-of-scope timestamp. This mechanism supports conditional recall of a correction, not weight training, a universal visual classifier or proof of full reconstruction.
