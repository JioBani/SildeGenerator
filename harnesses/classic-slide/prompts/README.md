# 프롬프트 유지관리 안내

이 폴더의 Markdown 파일만 수정하면 영상 기획과 이미지 프롬프트의 동작을 바꿀 수 있습니다.
Python/TypeScript 코드를 수정할 필요가 없습니다.

- `director/system.md`: 전체 영상 기획 원칙
- `director/analyze-script.md`: 입력 대본 해석과 장면 분리 요청
- `storyboard/system.md`: 슬라이드 영상의 장면 구성 규칙
- `storyboard/split-scenes.md`: 장면별 내레이션·화면 요약 생성 요청
- `image/system.md`: 이미지 생성 전역 규칙
- `image/build-image-prompt.md`: 장면 정보를 실제 이미지 프롬프트로 바꾸는 규칙
- `image/style-guide.md`: 영상 전체의 시각적 일관성 규칙
- `repair/revise-image-prompt.md`: 이미지 생성 실패 시 프롬프트 보정 규칙

`{{SCENARIO}}`, `{{SCENES_JSON}}`, `{{SCENE_JSON}}`, `{{ERROR}}` 표시는 런타임이 실제 값으로 치환합니다.
파일 내용과 SHA-256 해시는 영상 작업마다 PostgreSQL에 스냅샷으로 저장됩니다.
