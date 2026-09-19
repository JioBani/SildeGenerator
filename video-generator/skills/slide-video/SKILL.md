---
name: "slide-video"
description: "PLACEHOLDER — 기존에 완성된 슬라이드 영상 제작 스킬로 이 폴더 전체를 교체하세요."
---

# Slide Video Skill (placeholder)

이 폴더는 기존 스킬로 교체할 자리입니다. worker 는 이 스킬을 아래 계약으로 호출합니다.

## 입력
- `$JOB_DIR/input/scenario.md` — 사용자가 입력한 시나리오

## 출력 (필수)
- `$OUTPUT_PATH` — 최종 mp4 파일 (기본 `$JOB_DIR/output/video.mp4`)

## 진행률 (선택)
- `$JOB_DIR/progress.json` 에 `{"step": "이미지 생성", "percent": 30}` 형태로 기록하면 웹에 표시됩니다.

## 작업 공간
- 중간 산출물은 현재 작업 디렉터리(`$JOB_DIR/work`)에 둡니다.
