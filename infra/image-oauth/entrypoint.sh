#!/bin/sh
set -eu

# Keep the host login directory read-only. The broker may refresh access
# metadata, so it receives a private writable copy inside the container.
runtime_home=${CODEX_HOME:-/tmp/codex-home}
umask 077
mkdir -p "$runtime_home"
if [ ! -f /codex-source/auth.json ]; then
  echo "Missing /codex-source/auth.json" >&2
  exit 1
fi
cp /codex-source/auth.json "$runtime_home/auth.json"
chmod 600 "$runtime_home/auth.json"

exec "$@"
