# experimental-stable-zoom 0.1.0

`classic-slide@1.2.0`의 대본·이미지·음성·자막·전환 계약은 유지하고 카메라 계산만 비교하는 비공개 Harness입니다.

- 한 장면 안에서는 하나의 정규화 초점만 유지합니다. 기본값은 화면 중앙 `[0.5, 0.5]`입니다.
- 원본을 출력 크기의 4배 작업 좌표계로 확대한 뒤 최종 해상도로 샘플링해 정수 픽셀 계단 현상을 줄입니다.
- 확대 강도, FPS, crossfade와 장면 길이는 기준 Harness와 같습니다.
- 공개 생성 화면과 배포용 `classic-slide@1.2.0`에는 연결하지 않습니다.

검증: `scripts/harness validate experimental-stable-zoom` 및 Harness 단위 테스트.
