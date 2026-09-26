# ChatGPT OAuth 구독 브리지

개인용 ChatGPT/Codex 로그인 정보를 이용해 장면 기획과 이미지 생성을 처리하는 선택 서비스입니다.
`openai-oauth`는 OpenAI 공식 제품이 아닌 커뮤니티 패키지이며, 개인이 소유한 신뢰 가능한 서버에서만 사용합니다.
Docker 외부 포트는 열지 않으며 Python runner만 내부 네트워크에서 접근합니다. 현재 검증된 구독 이미지 모델은 `gpt-image-2`입니다.

## 준비

호스트의 기본 Codex 인증 파일을 복사하거나 직접 마운트하지 않습니다. 두 프로세스가 같은 refresh token을 갱신하면 Codex 데스크톱 세션과 영상 서비스가 서로의 로그인을 끊을 수 있습니다.

프로젝트 루트에서 bootstrap을 실행하면 `.runtime/codex`를 전용 `CODEX_HOME`으로 사용해 로그인을 확인하고, 필요할 때만 브라우저 승인을 엽니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\bootstrap.ps1
```

인증 파일은 비밀번호와 같은 민감 정보입니다. Git, 일반 백업, 웹/API에 노출하지 않습니다. bootstrap은 브리지의 실제 모델 조회까지 확인하며, 오래된 인증이 `401`을 반환하면 프로젝트 전용 로그인만 복구합니다.
실서비스 모드는 루트 `.env`의 `RUNNER_MODE=live`, `IMAGE_PROVIDER=oauth`와 `docker compose --profile live up -d`로 켭니다.
