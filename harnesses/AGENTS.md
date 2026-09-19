# Creative Harness 작업 규칙

이 디렉터리를 수정하기 전에 반드시 다음을 완독합니다.

1. [`docs/creative-harness/AI_AGENT_GUIDE.md`](../docs/creative-harness/AI_AGENT_GUIDE.md)
2. 대상 Harness의 `README.md`, `harness.yaml`, `CHANGELOG.md`

연출 변경은 `harnesses/<id>/**` 안에서 수행합니다. Core private module, secret, runtime package 설치, shell string 실행은 금지합니다. 검증은 `scripts/harness validate <id>`부터 시작합니다.
