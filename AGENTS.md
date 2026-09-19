# Agent bootstrap contract

먼저 [README의 Agent quick start](README.md#agent-quick-start)를 따르세요.

- secret, `.runtime`, auth JSON, 접근 토큰을 읽어 출력하거나 Git에 추가하지 마세요.
- `scripts/bootstrap.* --check`와 Mock smoke를 먼저 통과시키세요.
- Live/ElevenLabs 작업은 사용자의 명시적 승인 없이 실행하지 마세요.
- Docker Compose가 정본 실행 방식입니다.

Creative Harness 작업은 코드를 수정하기 전에 반드시 [`docs/creative-harness/AI_AGENT_GUIDE.md`](docs/creative-harness/AI_AGENT_GUIDE.md)와 [`harnesses/AGENTS.md`](harnesses/AGENTS.md)를 처음부터 끝까지 읽으세요. 연출 변경은 기본적으로 `harnesses/<id>/**` 안에서 수행하며 Core private module을 우회 import하지 않습니다.

Core를 수정하지 않는 것은 결합도를 낮추기 위한 기본 권고이지 절대 규칙이 아닙니다. 사용자 기능을 올바르게 제공하려면 Core 또는 Harness SDK 변경이 필요한 경우, 영향 범위를 확인하고 공개 인터페이스·테스트·문서를 함께 갱신하여 적절하게 수정하세요. Harness에서 Core private module을 우회 import하는 방식으로 해결하지 마세요.
