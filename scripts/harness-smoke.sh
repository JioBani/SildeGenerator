#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$ROOT"
web_port=${HARNESS_WEB_PORT:-8080}
env_file=${HARNESS_COMPOSE_ENV:-.runtime/compose.env}
harness_id=${1:-experimental-cut-move}
token=$(cat .runtime/access-token.txt)
job=$(curl -fsS -X POST "http://127.0.0.1:$web_port/api/jobs" -H "authorization: Bearer $token" -H 'content-type: application/json' --data "{\"scenario\":\"The first scene introduces a question. The next scene moves in a new direction.\",\"harnessId\":\"$harness_id\"}")
id=$(printf %s "$job" | sed -n 's/.*"id":"\([^"]*\)".*/\1/p')
[ -n "$id" ] || { echo "job creation failed" >&2; exit 1; }
status=queued; n=0
while [ "$n" -lt 180 ]; do
  sleep 2
  payload=$(curl -fsS "http://127.0.0.1:$web_port/api/jobs/$id" -H "authorization: Bearer $token")
  status=$(printf %s "$payload" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')
  [ "$status" = completed ] && break
  if [ "$status" = failed ]; then printf '%s\n' "$payload" >&2; exit 1; fi
  n=$((n+1))
done
[ "$status" = completed ] || { echo "job timed out" >&2; exit 1; }
docker compose --env-file "$env_file" exec -T runner ffprobe -v error -show_entries stream=codec_type,codec_name,sample_rate,channels,width,height,r_frame_rate -show_entries format=duration -of compact=p=0:nk=1 "/data/jobs/$id/output/video.mp4"
docker compose --env-file "$env_file" exec -T postgres psql -U slidegen -d slidegen -tAc "select harness_id||'|'||harness_version||'|'||length(harness_manifest_sha256)||'|'||length(harness_source_sha256)||'|'||length(harness_config_sha256)||'|'||harness_source_revision||'|'||left(harness_image_digest,7)||'|'||length(harness_image_digest) from generation_jobs where id='$id'::uuid; select 'harness_stage|'||count(*) from job_stage_runs where job_id='$id'::uuid and stage='harness_loading'; select 'segments|'||count(*) from render_segments where job_id='$id'::uuid and settings->'harness'->>'id'='$harness_id'; select 'transition|'||(settings->'harness_config'->>'transition') from render_segments where job_id='$id'::uuid order by segment_index limit 1;"
echo "harness_job=$id"
