FROM node:22-bookworm-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 python3-venv ffmpeg chromium fonts-noto-cjk ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY video-generator/requirements.txt /app/requirements.txt
RUN python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

COPY video-generator/hyperframes-runtime/package.json video-generator/hyperframes-runtime/package-lock.json /app/hyperframes-runtime/
RUN cd /app/hyperframes-runtime && npm ci --omit=dev --ignore-scripts

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CODEX_HOME=/codex-home \
    HYPERFRAMES_BROWSER_PATH=/usr/bin/chromium \
    HYPERFRAMES_NO_TELEMETRY=1 \
    DO_NOT_TRACK=1 \
    PRODUCER_BROWSER_GPU_MODE=software

WORKDIR /app
COPY video-generator/app ./app
COPY video-generator/schemas ./schemas
COPY harnesses ./harnesses
COPY docs/director-learning-ledger.json /app/research-root/docs/director-learning-ledger.json
COPY docs/evidence/light-pollution-v1-v2 /app/research-root/docs/evidence/light-pollution-v1-v2
COPY docs/evidence/reference-blood-pressure /app/research-root/docs/evidence/reference-blood-pressure

RUN mkdir -p /data/jobs /codex-home && chown -R 1000:1000 /app /data /codex-home

ARG SOURCE_REVISION=working-tree
LABEL slidegen.component=video-generator slidegen.source-revision=$SOURCE_REVISION
USER 1000:1000
EXPOSE 8081
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081", "--workers", "1"]
