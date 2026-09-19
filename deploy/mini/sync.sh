#!/bin/sh
# Source-only sync. Secrets, databases, generated media and Git history stay local to MINI.
set -eu
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
HOST=${MINI_HOST:-mini}

tar -C "$ROOT" -czf - \
  --exclude=node_modules --exclude=dist --exclude=.git --exclude=.env \
  --exclude=.codex-runtime --exclude=.runtime --exclude=private --exclude=data --exclude='__pycache__' \
  docker-compose.yml README.md AGENTS.md .env.example .github server video-generator web infra deploy setup scripts \
  | ssh "$HOST" 'mkdir -p ~/slidegen && tar -xzf - -C ~/slidegen'

echo "synced source to $HOST:~/slidegen"
echo "server/.env, .runtime, and .codex-runtime/auth.json were intentionally not copied"
