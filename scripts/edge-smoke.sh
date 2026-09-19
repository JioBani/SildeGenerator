#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
web_port=${EDGE_WEB_PORT:-8080}
env_file=${EDGE_COMPOSE_ENV:-.runtime/compose.env}
curl -fsS -X PUT "http://127.0.0.1:$web_port/api/admin/settings/voice" \
  -H 'content-type: application/json' \
  --data '{"provider":"microsoft_edge","model":"edge-tts","voiceId":"ko-KR-InJoonNeural","voiceName":"인준","rate":"-30%","pitch":"+0Hz","volume":"+0%"}' >/dev/null
token=$(cat .runtime/access-token.txt)
job=$(curl -fsS -X POST "http://127.0.0.1:$web_port/api/jobs" \
  -H "authorization: Bearer $token" -H 'content-type: application/json' \
  --data '{"scenario":"작은 질문이 내일을 만듭니다."}')
id=$(printf %s "$job" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
[ -n "$id" ] || { echo "job creation failed" >&2; exit 1; }
status=queued; n=0
while [ "$n" -lt 150 ]; do
  sleep 2
  payload=$(curl -fsS "http://127.0.0.1:$web_port/api/jobs/$id" -H "authorization: Bearer $token")
  status=$(printf %s "$payload" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  [ "$status" = completed ] && break
  if [ "$status" = failed ]; then printf '%s\n' "$payload" >&2; exit 1; fi
  n=$((n+1))
done
[ "$status" = completed ] || { echo "job timed out" >&2; exit 1; }
docker compose --env-file "$env_file" exec -T runner ffprobe -v error \
  -show_entries stream=codec_type,codec_name,sample_rate,channels,width,height,r_frame_rate \
  -show_entries format=duration -of json "/data/jobs/$id/output/video.mp4"
docker compose --env-file "$env_file" exec -T postgres psql -U slidegen -d slidegen -tAc \
  "select voice_provider||'|'||voice_model||'|'||voice_id from generation_jobs where id='$id'::uuid;
   select provider||'|'||count(*) from provider_usage_events where job_id='$id'::uuid group by provider order by provider;
   select 'elevenlabs_calls|'||count(*) from provider_usage_events where job_id='$id'::uuid and provider='elevenlabs';"
echo "edge_job=$id"
