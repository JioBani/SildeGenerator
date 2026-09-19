FROM node:22-bookworm-slim AS build
WORKDIR /app
# 비워두면 같은 origin 의 /api (nginx 프록시) 를 호출
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine
# /api 프록시 대상. 서버 레포의 api 주소 (경로 없이, 끝에 / 없이)
ENV API_UPSTREAM=http://api:3000
COPY nginx/default.conf.template /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html
