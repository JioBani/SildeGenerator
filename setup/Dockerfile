FROM node:22-alpine
WORKDIR /app
COPY package.json server.mjs index.html ./
USER node
EXPOSE 8090
CMD ["node", "server.mjs"]
