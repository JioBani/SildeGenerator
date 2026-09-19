FROM node:22-bookworm-slim AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY tsconfig.json nest-cli.json ./
COPY src ./src
RUN npm run build && npm prune --omit=dev

FROM node:22-bookworm-slim AS api
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/dist ./dist
COPY --from=build /app/package.json ./
RUN mkdir /data /keys && chown node:node /data /keys
USER 1000:1000
CMD ["node", "dist/main.js"]

FROM api AS worker
CMD ["node", "dist/worker.js"]

FROM node:22-bookworm-slim AS proxy
WORKDIR /app
COPY docker/egress-proxy.mjs ./
RUN mkdir /proxy && chown node:node /proxy
USER 1000:1000
CMD ["node", "egress-proxy.mjs"]
