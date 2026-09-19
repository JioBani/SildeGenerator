#!/bin/sh
set -eu

# Keep the host login directory read-only. The broker may refresh access
# metadata, so it receives a private writable copy inside the container.
runtime_home=${CODEX_HOME:-/tmp/codex-home}
umask 077
mkdir -p "$runtime_home"
cp -R /codex-source/. "$runtime_home/"
chmod -R u=rwX,go= "$runtime_home"

exec "$@"
