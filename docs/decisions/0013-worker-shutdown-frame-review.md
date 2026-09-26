# Worker shutdown and frame comparison

## Findings

The image broker waited indefinitely for active workers during close. Cancelling a
worker bypassed `except Exception` (CancelledError is a BaseException), leaving
the caller future unresolved. Dependency tasks were not tracked. This explains
a hanging isolated termination test; no production outage was reproduced.

## Changes

- Track dependency tasks and outstanding handles; reject submissions during close.
- Cancel workers and dependency waits on close, with a five-second acknowledgement
  bound. Bound Redis and PostgreSQL close operations as well.
- Resolve interrupted callers with an explicit error, persist WORKER_INTERRUPTED,
  clean partial images, and release provider leases.
- Replace an unexpectedly stopped worker slot for new jobs. Do not replay the
  interrupted provider request automatically: its external outcome can be unknown.
- Shield shared dependency futures so cancelling one dependent cannot cancel its source.
- Add /frame-review: paired local keyframe files matched by exact filename,
  numeric frame navigation, baseline/candidate/pixel difference, and explicit
  missing-frame, decoding and dimension errors. Files stay in the browser.
- Pixel differences are evidence, not acting/design approval. No automatic Gold promotion.

## Validation

Seven isolated image-broker tests pass in a network-disabled container, including
worker cancellation, lease release, dependency shutdown, and replacement-slot
execution without replaying the interrupted call. Two Playwright browser tests
cover pixel comparison, missing/mismatched frames and desktop/mobile layout.
Frontend TypeScript and production build pass. No paid provider requests used.

## Remaining scope

These tests cover cooperative asyncio task cancellation, not an OS/container kill
or a provider that suppresses cancellation. Such a shutdown raises a bounded
error and requires the service supervisor to terminate the process. Durable
reconciliation after a hard crash and whole-video A/B playback are separate work.
The review route currently accepts extracted keyframe files, not project IDs.
Changes are verified in isolation; the running production container is not replaced.

## Sources

- https://docs.python.org/3/library/asyncio-task.html#task-cancellation
- https://docs.python.org/3/library/asyncio-subprocess.html
- https://playwright.dev/docs/test-snapshots
- https://playwright.dev/docs/api/class-pageassertions

Use bounded cancellation and await cleanup. For browser evidence, wait for decoded
images and the explicit ready state; retain failure traces and disable animations
for screenshots. Do not interpret stable screenshots as a creative quality pass.
