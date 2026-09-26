# Narrated GPU excerpt transfer

Status: PARTIAL_TRANSFER_REVISE, not a complete GPU video or approved learning.
Experimental example: context-reveal-narrated-v1, hosted by astra-motion 0.3.0.
Core, production providers and default renderer are unchanged.

## What was transferred

The local-operation -> system overview -> detail/system comparison structure from
the blood-reference study is reused with independent GPU symbols. Calculation A
retains its marker and result. The source's time values are not forced onto a new
voice: a measured voice timeline retimes the existing visual timeline.

The three sentences are a contiguous excerpt of the user's GPU script, unchanged:

1. AI가 이미지를 만들 때는 수많은 숫자를 서로 곱하고 더하는 계산을 반복합니다.
2. 하나씩 계산하면 오래 걸리지만,
3. GPU는 이 계산을 수천 갈래로 나누어 동시에 처리합니다.

## Offline narration and timing

`scripts/synthesize_transfer_offline.ps1` uses installed Microsoft Heami Desktop,
System.Speech, rate 0. No network TTS or paid API calls. PowerShell 7 is required:
an initial PowerShell 5 run misread UTF-8 Korean and produced invalid narration.
That rejected output is retained in gpu-narration-v1 and MUST NOT be delivered.
gpu-narration-v2 has verified original text and measured WAV durations:

| Sentence | Start | End |
| --- | ---: | ---: |
| 1 | 0 | 6.613197 |
| 2 | 6.913197 | 10.122131 |
| 3 | 10.422131 | 15.515736 |

There is 0.3s silence after each sentence. Visual time 0-3.4 maps to sentence 1;
the outgoing transition reaches 4.384 by sentence 2 end; the system/comparison
reaches 11.9 by sentence 3 end. This is sentence-level authoring, not forced word
alignment. The slow initial hold and sequential-versus-parallel demonstration
still require perceptual review.

## Output and checks

`.runtime/reference-study/context-reveal-gpu-narrated-v1/gpu-narrated-transfer.mp4`
contains 475 video frames, 1920x1080, 30fps, 15.833333s video and 15.9s AAC audio.
The 0.067s audio overhang is in the added end silence; this is not a strict final
delivery receipt. Loudness normalization targets -16 LUFS but measured compliance
is not asserted. Sixteen sampled seeks were order independent. A 12s frame was
visually inspected: system board and caption fit. Pronunciation, comprehension and
the whole-motion design are not human approved. No auditory approval is claimed.

## Remaining work

- Demonstrate sequential versus parallel operation, not only a board full of symbols.
- Validate identity and timing invariants against retimed milestones; old absolute
  12-second identity checks cannot be reused unchanged.
- Review pronunciation and audio/visual emphasis, measure final loudness and trim
  trailing silence to the exact delivery duration.
- Complete the original two-reference sequences and the full new-script transfer.
  This excerpt is progress toward those requirements, not a substitute for them.

## V2 sequential/parallel demonstration

The `context-reveal-narrated-v2` experiment adds six numbered jobs with the same
input expressions/results in both representations. Sentence 2 activates one job
at a time (0.45s interval, 0.38s active); sentence 3 activates all six together
for an illustrative 0.7s. This timing is NOT a hardware benchmark or speed ratio.
The sequential panel explicitly labels that limitation. Existing narration is
reused with no new synthesis or paid calls.

`verify_transfer_jobs.mjs` checks the authored pending/active/completed states at
all 475 output frames: at most one sequential job is active, whereas parallel
active count is zero or six. It does not validate visual continuity or viewer
comprehension. Screenshots at 8s and 11.3s show the intended contrasting states.
Remaining concerns: pending expressions have low contrast, the original focal A
and the six-job comparison need a clearer narrative connection, and six identifiers
are replaced by results rather than retained as separate badges. These are REVISE,
not an approved reusable design rule.

Output: `.runtime/reference-study/context-reveal-gpu-narrated-v2/gpu-narrated-transfer.mp4`.
The old voice track is reused and its trailing added silence limited to 15.833333s.
This remains a short excerpt, not the complete new-script transfer or completion
of the two-reference reproduction goal.

Measured delivery audio: -16.39 LUFS integrated, -0.51 dBTP true peak, 2.30 LU LRA.
The intended -1.5 dBTP peak ceiling is NOT met after encoding. This is another
delivery revision; analysis-filter output values must not be reported as the
actual encoded input's loudness. Full media decode succeeded during measurement.

## V3 readability, identity markers and encoded audio

Pending sequential expressions now use cream rather than dark ink over a dimmed
teal box. Active expressions switch to dark ink on orange. Parallel job numbers
are persistent separate badges rather than replaced by completed values. The
12s rendered frame was inspected: badges 1-6 and results 7,9,11,13,15,17 coexist.
The 475-frame job-state test additionally checks each marker's text and own opacity.
It does not test inherited opacity, visual contrast ratios or human recognition.

The reused voice is normalized again with a -2 dBTP target and encoded as 48kHz
AAC. Measurement of the actual final file yields -16.20 LUFS, -2.00 dBTP and
2.00 LU LRA, meeting the intended -1.5 dBTP ceiling. These are input measurement
values from the final encoded file, not the analyzer's hypothetical output.

Output: `.runtime/reference-study/context-reveal-gpu-narrated-v3/gpu-narrated-transfer.mp4`.
Still PARTIAL_TRANSFER_REVISE: the focal A versus six-job relationship and a full
different-script narrative need work; pronunciation and comprehension have no
human approval. No new paid calls, production promotion or Core modifications.

## V4 shared exemplar and group identity

The prior study accidentally made focal A separate from six numbered jobs, so
the first result appeared twice. V4 maps A to system unit 0 and compares A-F in
both sequential and parallel panels. Local/detail A and parallel A share one
semantic ID and output 7; B-F yield 9,11,13,15,17. The focus stays orange after
completion. Unused units are dim contextual capacity, not additional jobs.
This is a conceptual parallelism diagram, not a hardware topology or speed test.

The system representation now follows the parallel schedule; local/detail states
follow measured narration retiming. The example metadata is corrected from the
inherited silent 12s to the actual 475 frames at 30fps (15.833333s).

Verification: all 475 authored job states and shared identity mapping passed.
Deliberately corrupting A's system semantic ID failed the mapping test while
state schedules still passed, demonstrating why schedule-only checks are weak.
Fourteen sampled out-of-order seeks matched. A rendered 12s frame was inspected:
A-F markers and six distinct results are legible, A is no longer duplicated.
This does not establish comprehension or full-motion artistic approval.

Output: `.runtime/reference-study/context-reveal-gpu-narrated-v4/gpu-narrated-transfer.mp4`.
The V3 AAC narration is reused by stream copy, without a new synthesis or paid
call. Docker preflight failed because its daemon was unavailable; this is a
local Chrome/GSAP/FFmpeg study, NOT a passing container Mock E2E. Core, provider
defaults and automatic production rules remain unchanged. Status remains
PARTIAL_TRANSFER_REVISE. Full reference coverage, complete new-script transfer
and human review are still outstanding.
