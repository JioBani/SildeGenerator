# ADR-0006: 에이전트 우선 로컬 부트스트랩과 설정 웹

- 상태: 구현 승인
- 작성일: 2026-09-20
- 구현 담당: `pipeline-maintainer`
- 대상 환경: Windows + Docker Desktop, Linux + Docker Engine/Compose v2, 8GB RAM·GPU 없음

## 1. 사용자 목표

새 개발자 또는 영상 하네스 담당자가 GitHub에서 저장소를 clone한 뒤 README를 에이전트에게 읽게 하면, 에이전트가 프로젝트 내부 구조를 추측하지 않고 다음 과정을 완료할 수 있어야 한다.

```text
git clone
  -> README의 단일 부트스트랩 명령 실행
  -> 로컬 전용 설정 웹에서 ElevenLabs 등 서비스 값 입력
  -> Live 모드이면 호스트 Codex CLI로 ChatGPT 로그인
  -> Docker Compose 서비스 기동
  -> 자동 사전 점검 및 mock smoke test
  -> http://localhost:8080 사용 가능
```

목표는 소스 직접 실행이 아니라 Docker를 정본 실행 방식으로 만드는 것이다. Node, Python, FFmpeg, PostgreSQL, Redis를 호스트에 직접 설치하도록 요구하지 않는다.

## 2. 현재 상태와 차이

현재 루트 Compose는 mock 모드에서 기동할 수 있지만 처음 온 사람은 다음 내용을 직접 알아야 한다.

- 루트 `.env`와 `server/.env`의 역할 차이
- mock/live profile 차이
- ElevenLabs API key 위치
- Codex `auth.json`을 `.codex-runtime`에 복사하는 방법
- `keyctl`로 접근 토큰을 발급하는 방법
- 기동 후 무엇을 확인해야 성공인지

또한 2026-09-20 현재 Git 저장소는 첫 commit이 없고 remote도 없다. 제품과 무관한 다음 항목이 루트 Git ignore에 충분히 포함되어 있지 않다.

- `original/`
- `artifacts/`
- `scratchpad/`
- `.tmp_*`, `.tmp_youtube/`
- `astra-architecture-map/`
- 로컬 압축 파일

실제 `server/.env`와 `.codex-runtime/auth.json`은 현재 ignore되지만, 첫 공개 전 전체 staged 파일 secret scan이 반드시 필요하다.

## 3. 완료 후 사용자 경험

### 3.1 에이전트가 실행하는 명령

Windows PowerShell:

```powershell
git clone <repository-url> SlideGenerator
cd SlideGenerator
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
```

Linux/macOS/WSL:

```sh
git clone <repository-url> SlideGenerator
cd SlideGenerator
./scripts/bootstrap.sh
```

부트스트랩 스크립트는 다음을 수행한다.

1. Docker Engine과 Compose v2 확인
2. 아키텍처, RAM, 디스크, 필수 포트 확인
3. `.runtime/` 디렉터리와 안전한 기본 설정 생성
4. 로컬 loopback에만 설정 웹 컨테이너 기동
5. 설정 완료 marker를 기다림
6. 선택된 mock 또는 live profile로 본 서비스를 기동
7. 접근 토큰을 안전하게 발급
8. `scripts/doctor.*` 실행
9. 성공 URL과 다음 행동을 출력

스크립트는 정상 대기 중임을 주기적으로 한 줄만 표시하고, 비밀값을 터미널에 그대로 출력하지 않는다. 사람이 설정 웹을 완료하지 않으면 명확한 안내와 함께 대기하며 임의 기본 Live 키를 만들지 않는다.

### 3.2 사람이 보는 설정 웹

기본 주소:

```text
http://127.0.0.1:8090
```

설정 웹은 `127.0.0.1`에만 bind한다. LAN, Tailscale Funnel, nginx 공개 경로에 연결하지 않는다.

단계:

1. 실행 모드 선택
   - Mock 체험: 외부 호출과 과금 없음
   - Live 개인용: Codex/ChatGPT OAuth 이미지 + ElevenLabs
2. ElevenLabs 설정
   - API key 붙여넣기
   - voice ID, model, 안정성, 유사성, 속도
   - 기본값과 허용 범위 설명
3. Codex 상태 안내
   - credential 입력·업로드 필드는 두지 않는다.
   - `Codex CLI 로그인은 설정 저장 후 터미널에서 진행됩니다.`라고만 안내한다.
   - bootstrap state를 통해 최종적으로 `로그인 확인됨` 또는 `로그인 필요` 상태만 표시한다.
4. 실행 옵션
   - 웹 포트
   - 이미지/음성 동시성
   - 영상 FPS
   - 작업 보존기간
   - 고급값은 접어서 기본값 유지
5. 검증과 저장
   - JSON 및 필수 필드 형식 검사
   - 포트 충돌 재확인
   - 비밀값 마스킹 상태로 저장 결과 표시

고급 사용자용으로 `.env` 텍스트 붙여넣기 영역을 제공할 수 있지만, 알려진 allowlist 변수만 파싱한다. 임의 환경변수명, shell expansion, command substitution을 허용하지 않는다.

### 3.3 Codex CLI 로그인

Codex 인증 JSON을 설정 웹에 붙여넣거나 업로드하지 않는다. Live 모드를 선택하면 bootstrap script 또는 README를 수행하는 에이전트가 호스트에서 공식 Codex CLI 로그인을 실행한다.

프로젝트 전용 credential 경로를 사용하고 bridge가 읽을 수 있는 파일 저장 방식을 명시한다.

Linux/macOS/WSL:

```sh
mkdir -p .runtime/codex
CODEX_HOME="$PWD/.runtime/codex" codex login -c 'cli_auth_credentials_store="file"'
CODEX_HOME="$PWD/.runtime/codex" codex login status
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force .runtime\codex | Out-Null
$slidegenCodexHome = (Resolve-Path .runtime\codex).Path
$env:CODEX_HOME = $slidegenCodexHome
codex login -c 'cli_auth_credentials_store="file"'
codex login status
Remove-Item Env:CODEX_HOME
```

브라우저 callback을 열 수 없는 원격·헤드리스 호스트에서는 같은 명령에 `--device-auth`를 추가한다.

```sh
CODEX_HOME="$PWD/.runtime/codex" codex login \
  -c 'cli_auth_credentials_store="file"' \
  --device-auth
```

운영 규칙:

- bootstrap은 `codex --version`과 `codex login status`를 먼저 확인한다.
- Live인데 Codex CLI가 없으면 자동으로 임의 package를 설치하지 않는다. 공식 설치 문서 링크와 필요한 명령만 에이전트/사용자에게 안내한다.
- 로그인은 사용자의 브라우저 또는 device code 승인이 필요한 대화형 단계다. 에이전트가 계정 정보나 일회용 코드를 요구하거나 대신 입력하지 않는다.
- status가 성공한 뒤 `.runtime/codex/auth.json` 존재와 파일 권한을 확인한다.
- credential 내용을 읽거나 로그·채팅·설정 웹에 출력하지 않는다.
- 로그인 완료 후 bootstrap이 Live Compose를 시작하며 `.runtime/codex`를 image OAuth bridge에 read-only mount한다.
- logout/re-login은 프로젝트 전용 `CODEX_HOME`을 지정한 상태에서 수행한다.

## 4. 보안 설계

설정 편의를 이유로 Docker socket을 setup/API/web 컨테이너에 mount하지 않는다. 컨테이너가 호스트 Docker daemon을 제어하게 만들면 로컬 root 권한과 동일한 위험이 생긴다.

대신 bootstrap script가 Compose lifecycle을 소유하고, setup container는 `.runtime/`에 검증된 설정 파일과 완료 marker만 쓴다.

```text
bootstrap script             setup container
      |                            |
      | docker compose up setup    |
      |--------------------------->|
      |                            | localhost form
      | watches marker             | write validated files
      |<---------------------------|
      | docker compose up app      |
```

필수 보안 규칙:

- setup 포트는 loopback only
- 외부 CDN, analytics, 원격 font, third-party script 없음
- setup response와 로그에 secret echo 금지
- 저장 후 secret 조회 API 없음; configured/masked 상태만 조회
- `Cache-Control: no-store`
- strict CSP와 frame-ancestors none
- request body size 제한
- 설정 웹은 Codex credential을 받지 않는다. Codex 인증 검증은 호스트의 `codex login status` exit code와 credential 파일 존재·권한만 사용한다.
- `.env` 값은 newline, NUL, shell syntax를 그대로 허용하지 않고 allowlist별 validation
- 완료 후 setup service를 bootstrap script가 중지
- 재설정은 로컬 터미널에서 명시적인 `bootstrap --reconfigure`를 실행해야 함
- `.runtime/`, `.env`, auth 파일은 Git/Docker build context에서 제외
- Linux에서 directory 0700, secret file 0600을 적용

## 5. 설정 파일 구조

생성물은 모두 Git ignored `.runtime/` 아래 둔다.

```text
.runtime/
  compose.env             # 포트, concurrency 등 비민감/저민감 Compose 값
  runner.env              # ElevenLabs key와 voice 설정
  codex/
    auth.json             # Codex CLI가 직접 생성한 OAuth 인증; 웹 업로드 금지
  bootstrap-state.json    # schema version, mode, 완료 여부; secret 없음
  access-token.txt        # 최초 발급 토큰, 0600, Git ignore
```

기존 `server/.env`를 Live 실행의 필수 수동 파일로 사용하지 않는다. 하위 호환을 위한 개발자 경로는 잠시 유지할 수 있지만 새 부트스트랩과 README의 정본은 `.runtime/runner.env`다.

Compose는 명시적으로 다음을 사용한다.

```sh
docker compose --env-file .runtime/compose.env ...
```

runner에는 `.runtime/runner.env:/run/secrets/slidegen.env:ro`, image OAuth에는 `.runtime/codex:/codex-source:ro`를 mount한다. OAuth broker가 access metadata를 갱신할 수 있도록 컨테이너 시작 시 이 읽기 전용 원본을 컨테이너 내부의 임시 쓰기 가능 `CODEX_HOME=/tmp/codex-home`으로 복사한다. 호스트 credential에는 쓰기 권한을 주지 않는다.

PostgreSQL password와 내부용 랜덤값은 bootstrap 단계에서 cryptographically secure random으로 자동 생성한다. 사용자가 직접 입력할 필요가 없다. 비밀값을 Docker image layer나 build arg로 전달하지 않는다.

## 6. setup service

저장소에 작은 setup service를 추가한다. 구현 언어는 기존 팀 유지보수를 고려해 Node 또는 Nest와 격리된 최소 Node service가 적절하다. React 전체 앱을 다시 복제하지 말고 정적 HTML/CSS/JS 또는 작은 Vite build를 사용한다.

Compose 예시 의미:

```yaml
setup:
  build: ./setup
  profiles: [setup]
  ports:
    - "127.0.0.1:${SETUP_PORT:-8090}:8090"
  volumes:
    - ./.runtime:/runtime
  network_mode: none  # 가능하면 host 요청 수신과 모순 없는 별도 격리 구성을 사용
```

`network_mode: none`에서는 port publish가 불가능하므로 실제 구현은 전용 internal network 또는 기본 bridge를 사용하되, 서비스의 outbound network를 차단한다. 중요한 요구는 외부 egress 없음과 host loopback bind다.

API:

- `GET /api/setup/status`: secret 없는 상태만
- `POST /api/setup/validate`: 메모리에서 검증, 저장 안 함
- `POST /api/setup/save`: atomic temp file + fsync/rename 방식 저장
- `GET /api/setup/schema`: UI가 표시할 필드·설명·기본값

저장 payload 전체를 application log에 남기지 않는다.

## 7. 모드

### 7.1 Mock

- 키 없이 실행 가능
- `RUNNER_MODE=mock`, `IMAGE_PROVIDER=mock`
- Codex auth와 ElevenLabs key 입력 영역 비활성
- clone 직후 CI 및 개발자 smoke test의 기본 모드
- 한글 대본 제출부터 MP4 생성·다운로드까지 검증

### 7.2 Live

- `RUNNER_MODE=live`, `IMAGE_PROVIDER=oauth`
- ElevenLabs API key 필수
- 프로젝트 전용 `CODEX_HOME=.runtime/codex`에서 `codex login` 성공 필수
- 저장 시 형식 검증은 하되 외부 유료 생성 요청은 하지 않음
- read-only/auth health probe가 가능하면 doctor에서 사용하되 이미지/TTS 생성은 명시적인 Live smoke opt-in에서만 실행

Live 설정 이후 브리지/runner가 설정 파일을 시작 시 읽도록 한다. bootstrap script는 파일 저장 완료 후 처음으로 Live 컨테이너를 띄우므로 hot reload나 Docker socket이 필요 없다.

## 8. 접근 토큰

기존 `keyctl`을 재사용한다.

- bootstrap script가 앱 health 이후 `keyctl issue local-admin`을 정확히 한 번 실행한다.
- 결과 토큰을 `.runtime/access-token.txt`에 0600으로 저장한다.
- 터미널에는 전체 토큰을 기본 출력하지 않고 파일 위치와 웹에서 복사하는 방법을 안내한다.
- setup 완료 화면은 bootstrap status polling으로 토큰 준비 여부를 알 수 있지만, 전체 토큰을 재조회 가능하게 만들지 않는다.
- 초기 편의를 위해 `scripts/show-token.*`가 로컬에서만 파일을 읽어 출력할 수 있다.
- 재실행 시 기존 토큰이 있으면 새 토큰을 무한 발급하지 않는다.

현재 사용자 MINI에 쓰는 개인 토큰 `708502`를 저장소 기본값 또는 예제에 넣지 않는다.

## 9. README 정보 구조

README 첫 화면은 긴 아키텍처 설명보다 설치 성공 경로를 먼저 보여 준다.

필수 순서:

1. 무엇을 만드는 프로젝트인지 3줄
2. Agent quick start
3. Human quick start
4. 필수 사양
5. Mock와 Live 차이 및 과금 경고
6. 설정 웹 각 필드 취득처와 의미
7. 기동·중지·업데이트·백업·초기화 명령
8. doctor와 문제 해결
9. 보안 및 공개 배포 경고
10. 개발 구조와 프롬프트 담당자 안내

README의 Agent quick start에는 다음 계약을 명시한다.

```text
에이전트 지침:
- secret 값을 출력하거나 Git에 추가하지 말 것
- 먼저 scripts/bootstrap의 --check만 실행할 것
- 사람이 setup 웹에서 값을 넣어야 하면 URL과 필요한 필드만 요청할 것
- mock smoke가 통과하기 전 Live 호출을 하지 말 것
- Live smoke는 사용자의 명시적 승인 없이 실행하지 말 것
- 완료 시 URL, health, container 상태, mock E2E 결과만 보고할 것
```

루트에 짧은 `AGENTS.md`도 두어 코드 에이전트가 README와 같은 부트스트랩 계약을 찾게 한다. 중복되는 긴 문서를 만들지 말고 README의 해당 anchor를 가리킨다.

## 10. 사전 점검과 doctor

공통 결과 코드와 한글/영문 짧은 메시지를 사용하는 PowerShell 및 shell wrapper를 제공한다.

### 10.1 bootstrap --check

- Docker daemon 응답
- Compose v2 지원
- 지원 CPU architecture
- RAM: 8GB 권장, 6GB 미만 경고
- 여유 디스크: 초기 build 기준 최소 8GB 권장
- 포트 8080, 8090, 3000 충돌
- repo 경로 쓰기 가능
- `.runtime` 권한
- Compose interpolation 결과에 빈 필수값 또는 secret 노출 없음
- Windows에서는 Docker Desktop Linux container 모드 확인

### 10.2 doctor

- `docker compose ps`의 health
- API `/api/health`
- web same-origin `/api/health`
- PostgreSQL migration 완료
- Redis ping과 global queue concurrency
- prompt catalog 파일 및 쓰기/읽기 mount 정책
- runner health, FFmpeg, Noto CJK font
- mock 작업 생성 -> polling -> MP4 다운로드
- MP4 ffprobe: video/audio stream, 1920x1080, FPS, 길이
- 로그의 secret pattern redaction 확인

doctor는 성공/경고/실패를 구분하고 마지막에 다음과 같은 요약을 출력한다.

```text
PASS 18 / WARN 1 / FAIL 0
Web: http://localhost:8080
Mode: mock
Ready for local use: yes
```

## 11. GitHub 게시 전 저장소 정리

첫 commit 전에 제품 범위를 명시적으로 정한다.

포함:

- `web/`
- `server/`
- `video-generator/`
- `infra/`
- `deploy/` 중 일반화 가능한 파일
- `scripts/`
- `setup/`
- `docs/decisions/`와 사용자/개발 문서
- root Compose, README, examples, license

기본 제외:

- `original/` 모체 프로젝트
- `artifacts/` 생성 이미지·음성·영상
- `scratchpad/`, `.tmp_*`, `.tmp_youtube/`
- `astra-architecture-map/`
- `.agent_party_app/`
- `.codex-runtime/`, `.runtime/`
- 실제 `.env`, auth JSON, access token, DB dump
- `node_modules`, build output, caches
- 로컬 tar/zip

`original/`을 별도 private reference repository로 보존할지는 별도 결정이다. 현재 제품 저장소 첫 commit에는 포함하지 않는다.

첫 commit 전 필수 검사:

1. `git status --short` 검토
2. ignore 대상이 staging되지 않았는지 검사
3. secret scanner 실행
4. 대용량 파일 목록 검사
5. clean clone을 임시 디렉터리에 만들고 Mock bootstrap 실행
6. README만 보고 다른 에이전트가 설치 가능한지 E2E

GitHub remote 생성·push·public/private 선택은 외부 상태 변경이므로 사용자가 저장소 공개 범위와 계정을 지정하기 전에는 수행하지 않는다.

## 12. CI

GitHub Actions 또는 동등 CI에서 실제 유료 key 없이 다음을 실행한다.

- server typecheck/test
- web typecheck/build/test
- Python unit tests
- prompt/template/schema validation
- `docker compose config`
- Docker images build
- mock stack 기동
- mock user E2E와 MP4 ffprobe
- secret scan
- dependency/cache가 repository에 추적되지 않았는지 검사

Fork PR에서 secret을 요구하지 않는다. Live E2E는 self-hosted 또는 수동 workflow에서만 별도로 운영한다.

## 13. 업데이트와 데이터 보존

README에 다음 운영 명령을 제공한다.

- 안전한 update: pull -> build -> migration -> rolling/restart
- stop: volume 유지
- reset jobs: 명시적 경고와 확인
- backup: PostgreSQL + job-data + prompts + runtime config
- restore
- uninstall: 기본은 volume 유지, `--purge`에서만 삭제

bootstrap 재실행은 idempotent해야 한다. 기존 데이터, access token, secret을 덮어쓰지 않고 현재 상태를 감지한다. `--reconfigure`에서만 설정 웹을 다시 열고, 저장 전 backup을 남긴다.

## 14. 테스트 시나리오

### 14.1 Clean clone Mock E2E

새 임시 디렉터리에서 repository clone과 동일한 tracked 파일만 복사한 뒤 실행한다.

- 로컬 env/auth 없음
- bootstrap 명령 한 번
- Mock 선택 및 저장
- 컨테이너 healthy
- 자동 발급 토큰으로 한글 대본 제출
- queue -> running -> completed
- MP4 다운로드 및 ffprobe 성공
- 관리자/프롬프트/설정 화면 로드
- 브라우저 콘솔/네트워크 오류 없음

### 14.2 Clean clone Live readiness

- 잘못된 ElevenLabs key 형식 경고
- Live 선택 후 Codex 미로그인 상태를 정확히 안내
- `codex login status` 성공 후 파일 권한과 read-only mount 확인
- headless 환경의 `codex login --device-auth` 안내 확인
- secret이 API, HTML, logs, `docker inspect` environment에 평문으로 노출되지 않는지 검사
- 이미지·음성 유료 생성은 사용자 승인된 짧은 E2E에서만 실행

### 14.3 플랫폼

- Windows PowerShell + Docker Desktop
- Ubuntu/Linux shell + Docker Engine
- 경로에 공백과 한글이 있는 경우
- 이미 포트가 사용 중인 경우 대체 포트 안내
- bootstrap 중단 후 재실행
- 기존 volume이 있는 update

## 15. 구현 단계

1. 저장소 hygiene와 `.gitignore`/`.dockerignore` 정리
2. `.runtime` config schema 및 setup service
3. `bootstrap.ps1`, `bootstrap.sh`, `doctor.ps1`, `doctor.sh`
4. Compose profile/mount 변경과 기존 `server/.env` 의존 제거
5. README/AGENTS.md 재작성
6. Mock clean-clone 자동 E2E
7. MINI 기존 설정 migration 및 회귀 테스트
8. 사용자가 GitHub 공개 범위/remote를 지정한 뒤에만 remote 생성과 push

## 16. 완료 조건

다음을 모두 만족해야 완료다.

1. clean clone에 `.env`, auth, token이 전혀 없어도 bootstrap check와 Mock setup이 가능하다.
2. 사용자는 설정 파일을 직접 편집하지 않고 localhost 설정 웹에서 Live 값을 입력할 수 있다.
3. 설정 웹은 Docker socket과 외부 egress가 없고 loopback에서만 열린다.
4. bootstrap 후 별도 호스트 개발도구 설치 없이 Docker만으로 서비스가 뜬다.
5. doctor가 사용자 관점 Mock 영상 생성·다운로드까지 자동 검증한다.
6. README의 Agent quick start만으로 새 에이전트가 설치할 수 있다.
7. secret, 원본 프로젝트, 생성물, 임시 파일이 Git에 들어가지 않는다.
8. 기존 MINI 데이터와 Live 설정을 안전하게 migration하고 기존 기능 회귀가 없다.
9. GitHub push는 사용자 명시 승인 전 수행하지 않는다.
