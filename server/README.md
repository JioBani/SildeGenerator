# Slide Generator API

NestJS API와 BullMQ worker입니다. PostgreSQL을 영구 기록 저장소로, Redis를 작업 큐와 사용량 제한 저장소로 사용하며 실제 영상 처리는 별도 Python runner에 HTTP로 요청합니다.

## 책임 분리

- `api`: 사용자 키 검사, 작업 생성·조회·영상 다운로드, 관리자 조회 API
- `worker`: 큐 소비, runner 호출, 진행률 수집, 재시도와 구간별 계측 저장
- `PostgreSQL`: 작업, 단계 실행, provider 사용량, 프롬프트 snapshot, 자산, 이벤트
- `Redis`: BullMQ 큐와 사용자·전체 대기 작업 제한
- `runner`: 이미지·음성·자막·FFmpeg 합성 및 결정론적 검사

API와 worker는 영상을 직접 렌더링하지 않습니다. 관리자 API는 현재 개인용 초기 운영을 위해 인증 없이 열려 있습니다. 외부 공개 전에는 관리자 인증을 추가해야 합니다.

## 환경 변수

`server/.env.example`을 참고해 `server/.env`를 만듭니다. 주요 값은 다음과 같습니다.

```dotenv
DATABASE_URL=postgresql://slidegen:slidegen@postgres:5432/slidegen
REDIS_URL=redis://redis:6379
RUNNER_URL=http://runner:8081
WORKER_CONCURRENCY=1
USD_KRW_RATE=1400

ELEVENLABS_API_KEY=
ELEVENLABS_VOICE_ID=nPczCjzI2devNBz1zQrb
ELEVENLABS_VOICE_NAME=Brian - Deep, Resonant and Comforting
ELEVENLABS_MODEL_ID=eleven_flash_v2_5
ELEVENLABS_STABILITY=0.60
ELEVENLABS_SIMILARITY_BOOST=0.60
ELEVENLABS_SPEED=0.70

CODEX_MODEL=gpt-5.6-luna
CODEX_REASONING_EFFORT=max
CODEX_FAST_MODE=false
CODEX_MODEL_OPTIONS=gpt-5.6-luna,gpt-5.6-terra,gpt-5.6-sol
```

`ELEVENLABS_API_KEY`는 runner에 읽기 전용 파일로 전달됩니다. 프론트엔드나 PostgreSQL에는 저장하지 않습니다.

## 사용자 키

사용자 API는 `Authorization: Bearer <token>` 형식의 키가 필요합니다. `issue`는 무작위 `sg_...` 키를 만들고, 개인용 배포에서는 `set`으로 6자 이상의 고정 키를 지정할 수 있습니다. 두 방식 모두 저장소에는 SHA-256 해시만 보관합니다.

```sh
docker compose --profile ops run --rm keyctl issue local
docker compose --profile ops run --rm keyctl set local MY_FIXED_TOKEN "personal"
docker compose --profile ops run --rm keyctl list
docker compose --profile ops run --rm keyctl revoke local
```

## API

| 메서드 | 경로 | 인증 | 용도 |
|---|---|---|---|
| `GET` | `/api/health` | 없음 | API 상태 |
| `POST` | `/api/jobs` | 사용자 키 | `{ "scenario": "..." }` 작업 생성 |
| `GET` | `/api/jobs/:id` | 사용자 키 | 본인 작업 상태·진행률 |
| `GET` | `/api/jobs/:id/video` | 사용자 키 | 완성 MP4 다운로드 |
| `GET` | `/api/admin/dashboard` | 현재 없음 | 작업·비용·단계 집계 |
| `GET` | `/api/admin/jobs` | 현재 없음 | 작업 목록 |
| `GET` | `/api/admin/jobs/:id` | 현재 없음 | 단계·사용량·자산·프롬프트·이벤트 상세 |
| `PUT` | `/api/admin/jobs/:id/quality` | 현재 없음 | 관리자 품질 점수(0–100)와 메모 저장 |
| `GET` | `/api/admin/analytics?groupBy=promptVersion\|model\|effort` | 현재 없음 | 개선 버전별 정규화 시간·토큰·비용·품질 비교 |
| `GET` | `/api/admin/prompts` | 현재 없음 | 현재 프롬프트 내용과 사용 시점·조건·역할 조회 |
| `PUT` | `/api/admin/prompts/:id` | 현재 없음 | 등록된 Markdown 프롬프트 수정 |
| `GET` | `/api/admin/prompts/:id/versions` | 현재 없음 | 프롬프트 문서의 버전 기록 조회 |
| `PUT` | `/api/admin/prompts/:id/versions/:version/restore` | 현재 없음 | 이전 프롬프트 내용 복원 |
| `GET` | `/api/admin/codex-settings` | 현재 없음 | 현재 Codex 모델·effort·Fast 설정 조회 |
| `PUT` | `/api/admin/codex-settings` | 현재 없음 | 이후 접수 작업에 적용할 Codex 설정 저장 |
| `GET` | `/api/admin/jobs/:id/codex-transcripts` | 현재 없음 | 파일로 보존된 스트리밍 시도 목록·요약 조회 |
| `GET` | `/api/admin/jobs/:id/codex-transcripts/:attempt/:part` | 현재 없음 | `request`, `output`, `events`, `final`, `summary` 원문 파일 조회 |
| `GET` | `/api/admin/models` | 현재 없음 | 환산 단가와 모델 목록 |

## 기록 원칙

- 총 소요 시간은 제출 시각부터 완료 또는 실패까지 기록합니다.
- 큐 대기, 재시도 대기, 장면 기획, 이미지, 음성, 자막, 오디오 조립, 영상 렌더, 검사를 각각 기록합니다.
- 외부 호출마다 provider, model, 토큰·문자·이미지 수, 요청 시간과 provider request id를 남깁니다.
- ElevenLabs는 정확한 문자 수에 당시 API 정가를 적용한 추정 비용을, ChatGPT/Codex 구독 호출은 같은 사용량의 공식 API 환산 비용을 원화로 계산합니다. 실제 구독 청구액과는 다를 수 있습니다.
- 사용한 모든 Markdown 프롬프트 내용·SHA-256·문서 버전을 작업별 snapshot으로 보존하고, 동일한 8개 문서 조합을 하나의 프롬프트 묶음 버전으로 관리합니다.
- 생성 파일은 상대 경로, 크기, 길이, 해상도, SHA-256을 기록합니다.
- Codex 스트리밍 원문은 DB가 아니라 공유 작업 볼륨의 고정 경로에 보존합니다. 관리자 API는 허용된 다섯 파일명만 읽어 경로 순회를 차단합니다.

## 로컬 검증

루트에서 전체 mock 구성을 실행하는 것이 기본입니다.

```sh
docker compose up -d --build
npm run build --prefix server
```

실제 구독 이미지와 ElevenLabs 호출은 루트 `.env`의 `RUNNER_MODE=live`, `IMAGE_PROVIDER=oauth` 및 `server/.env`의 유효한 ElevenLabs 키를 준비한 뒤 `docker compose --profile live up -d --build`로 켭니다.
