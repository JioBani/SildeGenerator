#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
RUNTIME="$ROOT/.runtime"; ENV_FILE="$RUNTIME/compose.env"; CHECK=0; RECONFIGURE=0; MOCK=0; WEB_PORT_VALUE=${SLIDEGEN_WEB_PORT:-8080}; API_PORT_VALUE=${SLIDEGEN_API_PORT:-3000}; SETUP_PORT_VALUE=${SLIDEGEN_SETUP_PORT:-8090}; PROJECT_NAME_VALUE=${SLIDEGEN_PROJECT_NAME:-slidegenerator}
for arg in "$@"; do case "$arg" in --check) CHECK=1;; --reconfigure) RECONFIGURE=1;; --mock) MOCK=1;; *) echo "unknown option: $arg" >&2; exit 2;; esac; done
cd "$ROOT"; docker version >/dev/null; docker compose version >/dev/null
[ "$(getconf LONG_BIT)" = 64 ] || { echo "64-bit architecture required" >&2; exit 1; }
echo "PASS Docker/Compose/architecture checks"
[ "$CHECK" -eq 0 ] || { docker compose config --quiet; exit; }
mkdir -p "$RUNTIME/codex"; chmod 700 "$RUNTIME" "$RUNTIME/codex"
if [ ! -f "$ENV_FILE" ]; then umask 077; password=$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n'); printf 'POSTGRES_PASSWORD=%s\nCOMPOSE_PROJECT_NAME=%s\nSETUP_PORT=%s\nAPI_PORT=%s\nWEB_PORT=%s\n' "$password" "$PROJECT_NAME_VALUE" "$SETUP_PORT_VALUE" "$API_PORT_VALUE" "$WEB_PORT_VALUE" > "$ENV_FILE"; fi
[ -f "$RUNTIME/runner.env" ] || { umask 077; printf '# Configured by the loopback setup portal.\n' > "$RUNTIME/runner.env"; }
if [ "$RECONFIGURE" -eq 1 ]; then
  backup_dir="$RUNTIME/backups/$(date -u +%Y%m%dT%H%M%SZ)"
  mkdir -p "$backup_dir"; chmod 700 "$RUNTIME/backups" "$backup_dir"
  for source_file in compose.env compose.user.env runner.env bootstrap-state.json; do
    [ ! -f "$RUNTIME/$source_file" ] || cp -p "$RUNTIME/$source_file" "$backup_dir/$source_file"
  done
  rm -f "$RUNTIME/setup-complete"
fi
compose() { docker compose --env-file "$ENV_FILE" "$@"; }
if [ "$MOCK" -eq 1 ] && [ ! -f "$RUNTIME/setup-complete" ]; then compose --profile setup up -d --build setup setup-proxy; ready=0; for attempt in 1 2 3 4 5 6 7 8 9 10; do if curl -fsS "http://127.0.0.1:$SETUP_PORT_VALUE/api/setup/status" >/dev/null 2>&1; then ready=1; break; fi; sleep 1; done; [ "$ready" -eq 1 ] || { echo "setup portal did not become ready" >&2; exit 1; }; curl -fsS -X POST "http://127.0.0.1:$SETUP_PORT_VALUE/api/setup/save" -H 'content-type: application/json' --data "{\"mode\":\"mock\",\"voiceProvider\":\"mock\",\"webPort\":$WEB_PORT_VALUE,\"imageConcurrency\":4,\"voiceConcurrency\":2,\"fps\":24,\"retentionHours\":720,\"edgeVoice\":\"ko-KR-InJoonNeural\",\"edgeRate\":\"-30%\",\"edgePitch\":\"+0Hz\",\"edgeVolume\":\"+0%\"}" >/dev/null; fi
if [ ! -f "$RUNTIME/setup-complete" ]; then compose --profile setup up -d --build setup setup-proxy; echo "Setup: http://127.0.0.1:$SETUP_PORT_VALUE"; while [ ! -f "$RUNTIME/setup-complete" ]; do echo "Waiting for setup..."; sleep 5; done; fi
compose --profile setup stop setup-proxy setup; grep -Ev '^(RUNNER_MODE|IMAGE_PROVIDER|VOICE_PROVIDER|WEB_PORT|IMAGE_TASK_CONCURRENCY|VOICE_TASK_CONCURRENCY|VIDEO_FPS|JOB_RETENTION_HOURS|ELEVENLABS_CONFIGURED|MICROSOFT_EDGE_|ELEVENLABS_VOICE_|ELEVENLABS_MODEL_ID)=' "$ENV_FILE" > "$ENV_FILE.tmp"; cat "$RUNTIME/compose.user.env" >> "$ENV_FILE.tmp"; mv "$ENV_FILE.tmp" "$ENV_FILE"; chmod 600 "$ENV_FILE" "$RUNTIME/runner.env"
mode=$(sed -n 's/^RUNNER_MODE=//p' "$ENV_FILE" | tail -1)
if [ "$mode" = live ]; then command -v codex >/dev/null || { echo "Codex CLI required: https://developers.openai.com/codex/cli" >&2; exit 1; }; CODEX_HOME="$RUNTIME/codex" codex login status >/dev/null 2>&1 || CODEX_HOME="$RUNTIME/codex" codex login -c 'cli_auth_credentials_store="file"'; chmod 600 "$RUNTIME/codex/auth.json"; voice_provider=$(sed -n 's/^VOICE_PROVIDER=//p' "$ENV_FILE" | tail -1); umask 077; printf '{"schemaVersion":1,"configured":true,"mode":"live","voiceProvider":"%s","codexLogin":"confirmed"}\n' "$voice_provider" > "$RUNTIME/bootstrap-state.json"; compose --profile live up -d --build; else compose up -d --build; fi
if [ ! -f "$RUNTIME/access-token.txt" ]; then umask 077; compose --profile ops run --rm keyctl issue local-admin 2>/dev/null | grep '^sg_' | tail -1 > "$RUNTIME/access-token.txt"; fi
sh "$ROOT/scripts/doctor.sh"; echo "Web: http://localhost:$WEB_PORT_VALUE"; echo "Token: .runtime/access-token.txt (scripts/show-token.sh)"
