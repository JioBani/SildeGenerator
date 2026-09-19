#!/bin/sh
set -eu
cd "$HOME/slidegen/server"
umask 077
mkdir -p private/broker "$HOME/.config/systemd/user"
python3 - <<'PY'
from pathlib import Path
import hashlib,json,secrets
p=Path('private')
f=p/'redis-password'
if not f.exists(): f.write_text(secrets.token_hex(32)+'\n')
f.chmod(0o600)
(p/'redis.conf').write_text('bind 0.0.0.0\nprotected-mode yes\nappendonly yes\nmaxmemory 160mb\nmaxmemory-policy noeviction\nrequirepass '+f.read_text().strip()+'\n')
(p/'redis.conf').chmod(0o600)
b=p/'broker.json'
if not b.exists(): b.write_text(json.dumps({'runner':'mock','concurrency':5,'daily_jobs':30,'timeout_seconds':900}))
print('Existing .env SHA256:',hashlib.sha256(Path('.env').read_bytes()).hexdigest())
PY
# The runner image is built from the video-generator repo: deploy/mini/deploy-video-generator.sh
docker compose build api worker egress-proxy
# Existing data volumes predate non-root services; adjust only these two named volumes.
docker run --rm --network none --cap-drop ALL --cap-add CHOWN --cap-add DAC_OVERRIDE --user 0:0 \
  -v slidegen-server_job-data:/jobs -v slidegen-server_redis-data:/redis \
  alpine:3.22 chown -R 1000:1000 /jobs /redis
cat > "$HOME/.config/systemd/user/slidegen-broker.service" <<EOF
[Unit]
Description=SlideGenerator constrained one-shot container broker
After=default.target
[Service]
Type=simple
WorkingDirectory=$HOME/slidegen/server
ExecStart=/usr/bin/python3 $HOME/slidegen/server/docker/broker.py
Restart=on-failure
RestartSec=3
UMask=0077
MemoryMax=768M
TasksMax=96
[Install]
WantedBy=default.target
EOF
systemctl --user daemon-reload
systemctl --user enable slidegen-broker
systemctl --user restart slidegen-broker
# Recreate only application services; Funnel is never started here.
docker compose up -d redis api worker egress-proxy
