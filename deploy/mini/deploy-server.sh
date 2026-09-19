#!/bin/sh
# Build and start the complete low-resource stack in mock mode or the mode selected in root .env.
set -eu
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
cd "$ROOT"

docker compose up -d --build postgres redis runner api worker web
docker compose ps
curl -fsS http://127.0.0.1:${API_PORT:-3000}/api/health
