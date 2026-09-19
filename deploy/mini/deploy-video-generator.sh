#!/bin/sh
# Replace only the Python runner. The BullMQ job stays retryable if a replacement happens mid-job.
set -eu
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"

docker compose build runner
docker compose up -d --no-deps runner
docker compose ps runner
