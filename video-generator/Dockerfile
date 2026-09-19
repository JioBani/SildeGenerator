FROM python:3.11-slim-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg fonts-noto-cjk ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY video-generator/requirements.txt /app/requirements.txt
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r /app/requirements.txt

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    CODEX_HOME=/codex-home

WORKDIR /app
COPY video-generator/app ./app
COPY video-generator/schemas ./schemas
COPY harnesses ./harnesses

RUN mkdir -p /data/jobs /codex-home && chown -R 1000:1000 /app /data /codex-home

ARG SOURCE_REVISION=working-tree
LABEL slidegen.component=video-generator slidegen.source-revision=$SOURCE_REVISION
USER 1000:1000
EXPOSE 8081
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081", "--workers", "1"]
