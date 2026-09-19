# 보안 강화 검증 보고 — 2026-09-15

## 적용한 범위

- 사용자별 256비트 API 키, 해시 저장, CLI 발급·사용자 단위 폐기.
- 본인 작업만 생성·조회·다운로드. 요청 속도·일일 작업 수·사용자/전역 대기열 제한.
- 본문 80KB·시나리오 20,000자·CORS 허용 목록·영상 경로 심볼릭 링크 방어.
- Redis 비밀번호 및 외부 미노출. API는 호스트 127.0.0.1:3000에만 바인딩.
- worker는 제어만 수행. 호스트의 제한된 브로커가 고정 옵션으로 작업별 새 runner 컨테이너를 실행.
- runner UID 1000, 읽기 전용 rootfs, 권한 capability 전부 제거, no-new-privileges, CPU/메모리/PID 제한, network=none.
- runner에 Docker 소켓·호스트 파일·작업 저장소·Redis·API 키를 마운트하지 않음. 임시 작업공간과 프로세스는 컨테이너 종료 시 소멸.
- 인터넷은 UNIX 소켓 프록시를 경유하며 허용 도메인과 공인 IPv4 조건을 모두 만족해야 함.
- 미니 PC mock 배포, 동시 실행 5 유지. 기존 .env 유지. 커밋하지 않음.
- 호스트 Codex 권한/설정과 Tailscale 정책은 변경하지 않음. Funnel은 꺼진 상태.

## 검증 결과

| 검사 | 결과 |
|---|---|
| 키 없음·유효하지 않은 키·폐기된 키 | 401 |
| 다른 사용자 상태 조회·다운로드 | 404 |
| 추가 필드·공백 입력 | 400 |
| 본문 초과 / 미허용 Origin | 413 / 403 |
| 관리 HTTP 엔드포인트 | 없음, 404 |
| 일일·요청 속도·사용자 대기·전역 대기 한도 | 모두 429 |
| mock 생성 → 영상 다운로드 | 202 → 200, MP4 확인 |
| worker가 키 파일을 가리키는 심볼릭 링크 삽입 | 다운로드 410, 키 노출 차단 |
| 동시 작업 5개 | 서로 다른 컨테이너 5개 동시 실행·모두 완료 |
| 완료 후 작업 컨테이너 잔존 | 없음 |
| 브로커 command/image/mode 주입·잘못된 입력 | 5개 사례 모두 400 |
| Redis 비인증 연결 | NOAUTH |
| API/worker/Redis/프록시 런타임 | UID 1000, rootfs 읽기 전용, cap_drop ALL, 자원 제한 확인 |
| runner → 사설망/tailnet/link-local/호스트 게이트웨이 | 모두 ENETUNREACH |
| 프록시 → 사설 IP·임의 사이트 | 403 |
| 프록시 → chatgpt.com/auth.openai.com | CONNECT 200 |
| 자식 환경 변수 | 부모에 REDIS_PASSWORD/APP_ACCESS_TOKEN 검사용 값을 넣어도 자식에는 전달되지 않음 |
| Codex 실행 파일 | codex-cli 0.154.0 실행 확인 |
| 실제 codex exec | 프록시 경유 서비스 도달, 구독 사용량 한도로 종료. 모델 작업 완료 미검증 |
| worker → 호스트 게이트웨이 SSH | **연결 가능. 사용자 방화벽 적용 대기** |
| 호스트 사용자 서비스 지속 실행 | Linger=no. 사용자 enable-linger 적용 대기 |

API 자동 검사 24개와 브로커 입력 검사 5개를 통과했습니다. 원시 비밀값을 포함하지 않은 결과는 `ops/api-verification.json`, `ops/isolation-verification.json`, `ops/codex-verification.json`에 있습니다.

## 사용자가 직접 할 조치

1. `README.md`의 API 전용 방화벽 설치 절차 실행: `ops/apply-firewall.sh` 및 `ops/slidegen-firewall.service`. sudo가 필요하므로 자동 적용하지 않았습니다.
2. `python3 ops/verify-security.py`를 다시 실행해서 호스트 게이트웨이 접근 차단 확인. 재부팅·Docker 재시작 후에도 재확인.
3. `sudo loginctl enable-linger dev`로 브로커 사용자 서비스가 로그아웃 후에도 유지되도록 설정.
4. `docker compose run --rm keyctl issue <사용자>`로 실제 사용자 키 발급. 검증용 키는 모두 폐기했습니다.
5. Codex 구독 한도 회복 후 `python3 ops/verify-codex.py` 재실행. 현재 모드는 mock 유지.

Tailscale 전체 차단 정책은 사용자 결정에 따라 적용 항목에서 제외했습니다. 외부 공개는 방화벽 재검증 후 별도 진행해야 합니다.

## 남는 위험

- Codex가 작업용 ChatGPT 인증을 읽을 수 있으므로 악성 작업의 인증 유출·공유 계정 남용 가능성은 남습니다. 복사본의 인증 갱신도 동일 로그인 세션에 영향을 줄 수 있습니다.
- Docker는 호스트 커널을 공유하며 브로커는 Docker 실행 권한을 가진 신뢰 프로세스입니다. 커널·런타임·브로커 취약점으로 호스트가 침해되면, 전체 Tailscale 차단을 하지 않았으므로 사용자 PC로의 연결 위험은 남습니다.
- 실제 제작 스킬은 아직 placeholder입니다. 완성 스킬의 1080p 영상·작업공간 요구량은 현재 영상 32MB/작업 tmpfs 384MB/메모리 768MB 한도 안에서 별도 검증해야 합니다.
- API/worker 자체 침해는 공유 작업 데이터와 Redis에 영향을 줄 수 있습니다. Codex runner에는 이 자원을 노출하지 않습니다.
