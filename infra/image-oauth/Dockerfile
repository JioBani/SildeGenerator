FROM node:22-bookworm-slim

ARG OPENAI_OAUTH_VERSION=2.0.0
RUN npm install -g openai-oauth@${OPENAI_OAUTH_VERSION}

ENV CODEX_HOME=/codex-home
USER 1000:1000
EXPOSE 10531
CMD ["openai-oauth", "--host", "0.0.0.0", "--port", "10531"]
