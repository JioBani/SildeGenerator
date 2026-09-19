#!/bin/sh
# Start the optional personal ChatGPT OAuth image bridge and reconnect the runner.
set -eu
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"

test -f .codex-runtime/auth.json || {
  echo '.codex-runtime/auth.json is required; see infra/image-oauth/README.md' >&2
  exit 1
}

docker compose --profile live up -d --build image-oauth runner
docker compose --profile live ps image-oauth runner
