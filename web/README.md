# Slide Generator — Web

시나리오를 입력하고 생성된 슬라이드 영상을 받는 프론트엔드 (React + Vite).
백엔드는 별도 레포(`slidegen-server`)로 배포하며, API 계약은 서버 레포 README 를 따른다.

## API 연결 방식

| 방식 | 설정 | 특징 |
|---|---|---|
| A. nginx 프록시 (기본) | 컨테이너 환경변수 `API_UPSTREAM` | 같은 origin 의 `/api` 호출. CORS 불필요, 재빌드 없이 변경 |
| B. 직접 호출 | 빌드 인자 `VITE_API_BASE_URL` + 서버 `CORS_ORIGIN` | 정적 호스팅(S3, Vercel 등)에 올릴 때 |

`API_UPSTREAM` 은 `https://api.example.com` 처럼 경로와 끝 `/` 없이 쓴다.

## 실행

```sh
cp .env.example .env
docker compose up -d --build
# http://localhost:8080
```

로컬에서 서버 레포를 `3000` 포트로 띄워두면 기본값(`host.docker.internal:3000`)으로 연결된다.

## 로컬 개발

```sh
npm install
npm run dev   # /api 는 localhost:3000 으로 프록시 (vite.config.ts)
```

## 구조

```
src/App.tsx                    시나리오 입력 → 작업 폴링 → 다운로드 (기존 프론트로 교체할 자리)
nginx/default.conf.template    정적 파일 서빙 + /api 프록시
Dockerfile                     빌드 → nginx 이미지
```

기존 프론트로 교체할 때는 빌드 결과가 `dist/` 이고 API 호출 앞에 `VITE_API_BASE_URL` 을 붙이기만 하면 Dockerfile·nginx 는 그대로 쓸 수 있다.
