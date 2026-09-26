#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
ENV_FILE="$ROOT/.runtime/compose.env"
cd "$ROOT"
pass=0; warn=0; fail=0
api_port=$(sed -n 's/^API_PORT=//p' "$ENV_FILE" | tail -1)
web_port=$(sed -n 's/^WEB_PORT=//p' "$ENV_FILE" | tail -1)
api_port=${api_port:-3000}; web_port=${web_port:-8080}
ok(){ pass=$((pass+1)); echo "PASS $*"; }
bad(){ fail=$((fail+1)); echo "FAIL $*"; }
docker compose --env-file "$ENV_FILE" ps >/dev/null && ok "Compose services" || bad "Compose services"
expected_mode=$(sed -n 's/^RUNNER_MODE=//p' "$ENV_FILE" | tail -1)
expected_provider=$(sed -n 's/^IMAGE_PROVIDER=//p' "$ENV_FILE" | tail -1)
actual=$(docker compose --env-file "$ENV_FILE" exec -T runner python -c "from app.config import settings; print(settings.runner_mode+'|'+settings.image_provider)" 2>/dev/null || true)
worker_actual=$(docker compose --env-file "$ENV_FILE" exec -T worker node -e "const c=require('/app/dist/config/app-config.js').config; console.log(c.runnerMode+'|'+c.imageProvider)" 2>/dev/null || true)
if [ "$actual" = "$expected_mode|$expected_provider" ] && [ "$worker_actual" = "$expected_mode|$expected_provider" ] && { [ "$expected_mode" != live ] || { [ "$expected_mode" != mock ] && [ "$expected_provider" != mock ]; }; }; then
  ok "Running runner configuration"
else
  bad "Running runner configuration: expected $expected_mode/$expected_provider, runner $actual, worker $worker_actual"
fi
curl -fsS "http://127.0.0.1:$api_port/api/health" >/dev/null && ok "API health" || bad "API health"
curl -fsS "http://127.0.0.1:$web_port/api/health" >/dev/null && ok "Web same-origin health" || bad "Web same-origin health"
mode=$(sed -n 's/^RUNNER_MODE=//p' "$ENV_FILE" | tail -1)
if [ "$mode" = live ]; then
  if [ -n "$(docker compose --env-file "$ENV_FILE" --profile live ps -q image-oauth 2>/dev/null)" ] && docker compose --env-file "$ENV_FILE" exec -T runner python -c "import json,urllib.request; data=json.load(urllib.request.urlopen('http://image-oauth:10531/v1/models',timeout=5)); assert isinstance(data.get('data'),list)" >/dev/null 2>&1; then
    ok "Project Codex OAuth bridge"
  else
    bad "Project Codex OAuth bridge"
  fi
fi
if [ "$mode" = mock ]; then
  token=$(cat "$ROOT/.runtime/access-token.txt")
  job=$(curl -fsS -X POST "http://127.0.0.1:$web_port/api/jobs" -H "authorization: Bearer $token" -H 'content-type: application/json' --data '{"scenario":"A small question changes tomorrow. Curiosity opens a new path."}')
  id=$(printf %s "$job" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
  n=0; status=queued; payload=$job
  while [ "$n" -lt 150 ]; do
    sleep 2
    payload=$(curl -fsS "http://127.0.0.1:$web_port/api/jobs/$id" -H "authorization: Bearer $token")
    status=$(printf %s "$payload" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
    [ "$status" = completed ] && break
    [ "$status" = failed ] && break
    n=$((n+1))
  done
  if [ "$status" = completed ] && docker compose --env-file "$ENV_FILE" exec -T runner ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of json "/data/jobs/$id/output/video.mp4" >/dev/null; then
    ok "Mock create/download/ffprobe"
  else
    printf '%s\n' "$payload" >&2
    bad "Mock create/download/ffprobe"
  fi
else
  warn=$((warn+1)); echo "WARN Mock smoke skipped in live mode"
fi
echo "PASS $pass / WARN $warn / FAIL $fail"
echo "Web: http://localhost:$web_port"
echo "Mode: $mode"
[ "$fail" -eq 0 ]
