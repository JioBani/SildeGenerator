# Genre-directed slide drafts

The former coupling of every genre to the private genre-slide renderer prevented
the requested slide-cinematic usage. Public API source now accepts genre-directed
drafts with the existing public classic-slide renderer. Both experimental renderers
remain private, and live genre rendering on those paths remains blocked.

Genre controls narrative purpose and constraints. The user's explicit image style
controls artwork and must not be overwritten by a genre's default design wording.
The frontend submits both selections and preserves the selected renderer. Unsupported
genre/renderer combinations fail before quota reservation on the server; browser
validation also explains the supported route. Production contracts remain unapproved
and quality reviews remain human-pending. 'Draft available' is not Gold promotion.

The profile's existing design field remains an archival recommendation, not permission
to override a selected style. Jobs persist selected genre/version; existing snapshots
still guard against incompatible retries. Source and narration preservation are tested.
Genre-directed classic projects now receive scene/asset budget checks and the same
measured 60-second pre-render guard as the episode renderers.

Verified: server build and four server choice/DTO tests, nine planner/contract tests,
two mocked-browser tests (draft payload routing and unavailable-preview behavior).
No provider calls. Docker daemon is unavailable, so DB migrations, real queue pickup,
live planning and full browser-to-download operation remain unverified. The running
dev UI alone cannot establish that this backend change is deployed or working live.
