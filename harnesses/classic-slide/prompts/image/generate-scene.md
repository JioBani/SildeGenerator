# 장면 이미지 합성

장면의 narration과 visual_summary를 한 장의 16:9 이미지로 표현한다. 장면 image_prompt를 우선하며 공통 스타일 가이드와 참조 계약을 함께 적용한다. 참조가 없으면 독립 장면으로 생성한다.

장면: {{SCENE_JSON}}
참조 계약: {{REFERENCE_CONTRACT}}
공통 스타일: {{STYLE_GUIDE}}
