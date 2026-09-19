# ChatGPT OAuth 구독 브리지

개인용 ChatGPT/Codex 로그인 정보를 이용해 장면 기획과 이미지 생성을 처리하는 선택 서비스입니다.
`openai-oauth`는 OpenAI 공식 제품이 아닌 커뮤니티 패키지이며, 개인이 소유한 신뢰 가능한 서버에서만 사용합니다.
Docker 외부 포트는 열지 않으며 Python runner만 내부 네트워크에서 접근합니다. 현재 검증된 구독 이미지 모델은 `gpt-image-2`입니다.

## 준비

MINI에서 Codex 로그인을 한 뒤 인증 파일을 프로젝트 전용 경로에 복사합니다.

```sh
mkdir -p ~/slidegen/.codex-runtime
cp ~/.codex/auth.json ~/slidegen/.codex-runtime/auth.json
chmod 700 ~/slidegen/.codex-runtime
chmod 600 ~/slidegen/.codex-runtime/auth.json
```

이 파일은 비밀번호와 같은 민감 정보입니다. Git, 백업, 웹/API에 노출하지 않습니다.
실서비스 모드는 루트 `.env`의 `RUNNER_MODE=live`, `IMAGE_PROVIDER=oauth`와 `docker compose --profile live up -d`로 켭니다.
