# Slide Generator

한국어 대본을 장면 이미지, 음성, 자막이 포함된 1080p MP4로 만드는 Docker 기반 서비스입니다.
장면 기획·이미지·음성을 병렬 처리하고, 작업별 설정·시간·토큰·비용을 관리자 화면에 기록합니다.
호스트에는 Node, Python, FFmpeg, PostgreSQL 또는 Redis를 직접 설치할 필요가 없습니다.

## Agent quick start

에이전트는 먼저 저장소 루트에서 사전 점검만 실행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1 -Check
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
```

```sh
sh scripts/bootstrap.sh --check
sh scripts/bootstrap.sh
```

에이전트 지침:

- secret 값을 출력하거나 Git에 추가하지 않습니다.
- 먼저 `scripts/bootstrap.* --check`만 실행합니다.
- 사람이 setup 웹에서 값을 넣어야 하면 `http://127.0.0.1:8090`과 필요한 필드만 안내합니다.
- Mock smoke가 통과하기 전에 Live 호출을 하지 않습니다.
- 사용자의 명시적 승인 없이 ElevenLabs sample 또는 Live 영상을 만들지 않습니다.
- 완료 보고에는 URL, health, container 상태, Mock E2E 결과만 포함합니다.

## Human quick start

Docker Desktop의 Linux container 모드 또는 Docker Engine + Compose v2가 필요합니다.

1. 위 운영체제용 bootstrap 명령을 실행합니다.
2. 브라우저에서 <http://127.0.0.1:8090>을 엽니다.
3. Mock 또는 Live와 음성 공급자를 선택하고 저장합니다.
4. bootstrap이 doctor와 Mock smoke를 마치면 <http://localhost:8080>을 엽니다.
5. 접근 토큰은 `.runtime/access-token.txt`에 저장됩니다. 필요할 때만 `scripts/show-token.*`로 확인합니다.

CI처럼 무인 Mock 설치가 필요하면 `sh scripts/bootstrap.sh --mock` 또는 `bootstrap.ps1 -Mock`을 사용합니다.

## 필수 사양

- 64-bit Windows 10/11 또는 Linux
- Docker Engine과 Compose v2
- RAM 8GB 권장(6GB 미만 경고)
- 초기 이미지 빌드 여유 공간 8GB 권장
- 기본 포트 8080, 8090, 3000
- Live만 호스트 Codex CLI 필요

## Mock와 Live

| 모드 | 장면·이미지 | 음성 | 과금 |
|---|---|---|---|
| Mock | 결정론적 Mock | `mock` 무음 또는 선택한 Edge | 기본 0원 |
| Live | Codex/ChatGPT OAuth | Edge 또는 ElevenLabs | ElevenLabs는 credit 사용 |

음성 provider는 실행 모드와 독립적입니다.

- `mock`: CI용 무음 MP3
- `microsoft_edge`: API key와 직접 과금 없이 테스트할 수 있지만 음성 합성은 온라인 Microsoft 서비스에서 이루어집니다. `edge-tts` 커뮤니티 client를 사용하며 오프라인 TTS 또는 공식 무료 API가 아닙니다.
- `elevenlabs`: 운영 품질 경로이며 credit을 소비합니다. 자동 fallback 대상으로 사용하지 않습니다.

Microsoft Edge 실패 시 ElevenLabs로 자동 전환하지 않습니다. provider 변경은 관리자 `모델 설정 > 음성 설정`에서 저장한 뒤 새 작업부터 적용됩니다.

## 설정 웹

설정 웹은 `127.0.0.1:8090`에만 열리고 완료 후 중지됩니다. Docker socket, Codex credential, 외부 스크립트·폰트·분석 도구를 사용하지 않습니다.

- 실행 모드
- 음성 provider, voice, 속도, pitch, volume
- ElevenLabs key/voice/model/stability/similarity/speed
- 웹 포트, 이미지·음성 동시성, FPS, 보존기간

secret은 `.runtime/runner.env`에 0600으로 저장되고 조회 API가 없습니다. Codex 인증은 웹에 업로드하지 않습니다.

Live에서는 bootstrap이 프로젝트 전용 경로를 사용합니다.

```sh
CODEX_HOME="$PWD/.runtime/codex" codex login -c 'cli_auth_credentials_store="file"'
CODEX_HOME="$PWD/.runtime/codex" codex login status
```

원격 호스트는 로그인 명령에 `--device-auth`를 추가합니다. 계정 정보나 device code를 에이전트에게 전달하지 마세요.

## 운영 명령

```sh
sh scripts/doctor.sh
sh scripts/bootstrap.sh --reconfigure
docker compose --env-file .runtime/compose.env stop
git pull
sh scripts/bootstrap.sh
```

백업 대상은 PostgreSQL volume, `job-data`, `harnesses/*/prompts`, `.runtime`입니다. 작업·DB 삭제나 volume purge는 복구가 어려우므로 자동 purge 명령을 제공하지 않습니다.

## Doctor와 문제 해결

doctor는 Compose health, API, same-origin web, runner/FFmpeg, Mock 작업 생성·폴링·MP4·ffprobe를 검사합니다.

```text
PASS 4 / WARN 0 / FAIL 0
Web: http://localhost:8080
Mode: mock
Ready for local use: yes
```

- 8090 충돌: `.runtime/compose.env`의 `SETUP_PORT`를 다른 loopback 포트로 바꾸고 재실행합니다.
- Live Codex 미로그인: 동일한 프로젝트 `CODEX_HOME`으로 `codex login status`를 확인합니다.
- Edge 음성 실패: 온라인 연결을 확인합니다. ElevenLabs 자동 fallback은 없습니다.
- 설정을 바꾸려면 `--reconfigure`를 명시적으로 사용합니다.

## 보안 및 공개 배포 경고

`.runtime/`, 실제 `.env`, auth JSON, 접근 토큰, DB dump, 생성물은 Git 대상이 아닙니다. 관리자 API와 프롬프트 편집 화면은 개인용 운영을 전제로 하므로 인터넷에 직접 노출하지 마세요. 설정 웹은 Tailscale Funnel 또는 nginx 공개 경로에 연결하면 안 됩니다.

## 개발 구조

| 경로 | 역할 |
|---|---|
| `web/` | React 생성·관리자 화면 |
| `server/` | NestJS API, BullMQ worker, PostgreSQL 계측 |
| `video-generator/` | Python planner, 이미지·TTS provider, FFmpeg |
| `harnesses/classic-slide/prompts/` | 기본 Harness의 기능별 Markdown 프롬프트 |
| `harnesses/` | 버전 고정 Creative Harness 코드·설정·fixture |

## Creative Harness 개발

연출 코드를 변경하기 전에 [AI 작업자 가이드](docs/creative-harness/AI_AGENT_GUIDE.md)와 [scoped AGENTS.md](harnesses/AGENTS.md)를 읽습니다. 기본 연출은 `classic-slide@1.0.0`이며, released package를 직접 덮어쓰지 않고 복제해서 실험합니다.

```powershell
.\scripts\harness.ps1 list
.\scripts\harness.ps1 inspect classic-slide
.\scripts\harness.ps1 clone classic-slide my-experiment
.\scripts\harness.ps1 validate my-experiment
.\scripts\harness.ps1 test my-experiment
```

Linux/macOS에서는 같은 인자를 `sh scripts/harness.sh ...`에 전달합니다. Plugin은 신뢰된 repository code이며 웹 업로드·runtime package 설치를 지원하지 않습니다.
| `setup/` | loopback-only 초기 설정 서비스 |
| `scripts/` | bootstrap, doctor, token helper |
| `docs/decisions/` | 승인된 설계 결정 |

영상 창작 방향과 프롬프트 품질은 프롬프트 담당자가 결정하고, 런타임·데이터·배포 변경은 유지보수 담당자가 검증합니다.

## GitHub 게시 상태

remote 생성, push, public/private 선택은 아직 수행하지 않습니다. 사용자가 계정과 공개 범위를 명시적으로 승인한 뒤 진행합니다.
