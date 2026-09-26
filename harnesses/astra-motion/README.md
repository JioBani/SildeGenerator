# astra-motion 0.9.1

Astra의 장면 계약을 HyperFrames 0.8.46과 GSAP 3.14.2로 컴파일하는 첫 모션그래픽 Harness입니다.

- 장면 기능, 시선 순서, 객체 상태, 움직임 단계, 전환과 리듬을 렌더 입력으로 사용합니다.
- 한 개의 일시정지 GSAP timeline을 HyperFrames가 프레임 단위로 탐색합니다.
- 최종 영상은 기술 검수 뒤에도 사람의 디자인·Gold 검수를 요구합니다.
- 기존 `classic-slide`는 변경하지 않습니다.
- 사용자가 명시적으로 선택해야 하며 기본 Harness가 아닙니다.
- 사용자 모션그래픽 형식은 하나이며, 인과 설명·순서 안내·인물 반응·상징 압축·근거와 맥락은 장면별 내부 전략으로 선택합니다.
- 화풍은 제작 형식과 분리된 디자인 계약입니다.
- 인물 반응, 제한 메시, `GRASP_AND_RETAIN`, `INTERACTION_READY`, 장면별 HyperFrames 승격, 이론 규칙 승격은 외부 사람 승인 기록 없이는 제작에 들어가지 않습니다.
- 모델이 장면 JSON 안에 넣은 승인 문구는 승인으로 인정하지 않습니다.
- 장면 계약을 safe Scene Program으로 컴파일해 레이아웃·객체 역할·모션·전환·리듬을 실제 GSAP timeline에 반영합니다.
- 알 수 없는 레이아웃·효과·selector·코드는 실행하지 않고 안전한 기본 문법으로 낮춥니다.
- limited mesh는 실제 geometry evidence가 없으면 실험 계약도 통과하지 않습니다.
- 생성 이미지 안의 움직일 대상을 `region_hint`로 지정하고, 로컬 분할과 배경 복원 결과를 검수 가능한 레이어 장부로 남깁니다.
- 분할 성공만으로 제작에 사용하지 않습니다. `production_ready` 사람 승인을 받은 레이어만 HyperFrames 장면에 들어갑니다.
- 현재 승격 범위는 전체 실루엣 이동·반응입니다. 얼굴·관절·접촉은 별도 리그 계약을 통과해야 합니다.
- 생성 비용이 발생하기 전에 장면의 레이아웃·전환·리듬·동작 지원 여부와 독립 객체 분리 요구를 검사합니다. 배우 연기는 외부 검수 요청 없이 일반 `reaction`으로 대체하지 않습니다.
- 감독 설계 전에 지원 문법과 자산 제작 요건을 구조화한 계획 계약을 제공하고, 사용된 계약과 Harness snapshot을 작업에 보존합니다. 계획 계약은 배우 자산의 존재나 품질을 승인하지 않습니다.
- 0.8은 선택 가능한 `narrative`와 `educational_info` 제작 스타일을 도입합니다. 전자는 동일 주체의 연결을, 후자는 편집 가능한 정보 레이블을 장면 계약과 렌더에 반영합니다. 두 스타일 모두 사람 Gold 승인은 아직 필요합니다.

- 기준 문서: [`AI_AGENT_GUIDE.md`](../../docs/creative-harness/AI_AGENT_GUIDE.md)
- 검증: `scripts/harness validate astra-motion`, `scripts/harness test astra-motion`
