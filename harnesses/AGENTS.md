# Creative Harness 작업 규칙

이 디렉터리를 수정하기 전에 반드시 다음을 완독합니다.

1. [`docs/creative-harness/AI_AGENT_GUIDE.md`](../docs/creative-harness/AI_AGENT_GUIDE.md)
2. 대상 Harness의 `README.md`, `harness.yaml`, `CHANGELOG.md`

연출 변경은 기본적으로 `harnesses/<id>/**` 안에서 수행합니다. 이 범위는 연출 구현의 소유 위치를 뜻하며 프론트엔드 변경을 제한하지 않습니다. 사용자에게 노출되는 기능을 추가하거나 변경할 때는 필요에 따라 `web/`, `server/`, Core 및 Harness SDK를 함께 수정합니다. Core를 수정하지 않는 것은 결합도를 낮추기 위한 권고이며 절대 규칙은 아닙니다. 사용자 기능 구현에 Core 또는 Harness SDK 변경이 필요하면 영향 범위를 확인하고 공개 인터페이스·테스트·문서를 함께 갱신하여 적절하게 수정합니다. 단, Harness에서 Core private module을 우회 import하는 방식은 금지합니다. secret, runtime package 설치, shell string 실행도 금지합니다. 검증은 `scripts/harness validate <id>`부터 시작합니다.
