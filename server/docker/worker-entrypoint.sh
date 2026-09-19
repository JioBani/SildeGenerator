#!/bin/sh
# Legacy compatibility only; Compose starts the non-root worker directly.
set -eu
exec "$@"
