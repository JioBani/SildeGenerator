# Full-source mixed audio timing evidence

Both local primary reference files contain stereo 48kHz Opus audio. Their stream origins are zero. Local FFmpeg decodes to 16kHz stereo float PCM for 20ms RMS/peak measurements; channel energy is combined after squaring, avoiding cancellation of antiphase stereo. Values are dBFS, not LUFS.

First evidence pass: posture 266.613 decoded seconds, 13,331 windows, 137 low-energy intervals and 528 energy-rise candidates; blood pressure 271.373 seconds, 13,569 windows, 116 low-energy intervals and 555 energy-rise candidates. Video lengths differ by 1ms from decoded audio, inside the explicit 150ms duration check. Nonzero or unknown audio start timestamps must be reviewed before analysis.

Low energy means RMS below -38 dBFS for at least 120ms. A rise candidate is at least 12dB over one of the preceding three windows and above -30 dBFS, with 200ms spacing. These are arbitrary detector settings, not verified words, beats, pauses or sound effects. The large candidate counts make automatic sound-event assignment inappropriate. Background music can mask a speech pause; speech syllables can generate rise candidates.

## Process connection

The director atlas compiler accepts source-hashed audio reports and attaches measurements to all 37 existing analysis partitions. Hash mismatch, stale atlas, different partition range or different scene function rejects the attachment. Existing partition boundaries remain unverified shot boundaries. Rhythm status becomes MIXED_AUDIO_MEASURED_SEMANTIC_REVIEW_REQUIRED, not PASS. Speech alignment and sound identity remain null, audio reuse unauthorized, production gates closed.

The next semantic review must listen to each interval, identify the spoken proposition and distinguish music/voice/effects, then mark evidence-backed hold and transition anchors. Energy minima alone must never move a cut, truncate narration or choose an effect. New-script transfer needs newly timed narration and independent/cleared audio, not reuse of source audio. All current study renders remain silent.

## Verification

Five envelope tests cover antiphase sound, silence, tail duration, partition overlap and nonfinite PCM. Four attachment tests cover non-promotion, wrong source, stale atlas and incorrect interval. Five existing atlas tests pass. This is analysis-tool evidence, not perceptual audio quality, speech recognition or product Docker E2E. No paid provider calls or new dependencies.
