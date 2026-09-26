# Actual director validation: execution boundary

The mock genre routes and authored cinematic samples do not prove live director
judgment. The next model experiment should be planning-only, with no image/voice
tasks, no render-queue submission and no automatic paid API fallback.

An explicit user question was sent for subscription-connected Terra/Sol low planning.
No such live call has been made in this turn. Production workers remain outside this
experiment; credentials/runtime settings were not inspected.

A configuration mismatch was found: fresh runner/server/Compose defaults used luna
max despite the requested low-effort Terra/Sol preference. Fresh defaults and the
example environment now use gpt-5.6-terra/low. Existing environment overrides are
preserved, not claimed to have changed. No production restart was performed.

Verification: server build and separate runner/server clean-environment default
tests passed. Runner test explicitly points to a nonexistent fixture environment
file, so it cannot read the normal secret file. This is configuration verification,
not an assertion about actual live billing or the running production configuration.

## Prepared benchmark

scripts/prepare_director_benchmark.py defaults to prepare-only. Five input packets
are stored at output/director-benchmark-inputs-v1, with identical source hashes and
distinct genre prompt hashes. Model/effort, schema and harness fingerprints are saved.
The supplied complete five-sentence fictional scenario is for comparing treatment,
not for validating archival facts or genre suitability across all possible scripts.

An explicit --execute-subscription option permits only one chosen genre per run,
uses the loopback subscription bridge with Terra/Sol low, and calls create_plan only.
It does not import job registration or generation/voice/render orchestration. No
automatic retries or API fallback. Execute only after explicit user approval.
The preparation was tested with HTTP client creation forbidden; all five records
reported zero requests and zero image/voice/render work. Live multi-genre batching
was tested to fail before even reading a script. Actual model execution is pending.
