FROM node:22-bookworm-slim

ARG OPENAI_OAUTH_VERSION=2.0.0
RUN npm install -g openai-oauth@${OPENAI_OAUTH_VERSION}

COPY entrypoint.sh /usr/local/bin/slidegen-image-oauth
RUN chmod 0755 /usr/local/bin/slidegen-image-oauth

ENV CODEX_HOME=/tmp/codex-home
USER 1000:1000
EXPOSE 10531
ENTRYPOINT ["/usr/local/bin/slidegen-image-oauth"]
CMD ["openai-oauth", "--host", "0.0.0.0", "--port", "10531"]
