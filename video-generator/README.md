# Python 영상 러너

FastAPI 단일 프로세스로 한 번에 한 영상만 처리합니다.

처리 순서:

1. 기능별 Markdown 프롬프트 로드 및 해시 생성
2. mock 결정론적 분할 또는 지속 실행 중인 ChatGPT OAuth 브리지를 통한 구조화 장면 기획
3. mock 이미지 또는 같은 브리지의 이미지 생성 API
4. mock 무음 또는 ElevenLabs Flash v2.5 음성·타임스탬프
5. ASS 자막과 내레이션 오디오 조립
6. FFmpeg Ken Burns·크로스페이드·H.264/AAC 렌더
7. Pillow 이미지 검사와 FFprobe 영상 검사

긴 영상은 기본 8장 단위로 렌더해 200장에서도 메모리 사용량이 장면 수에 비례해 커지지 않습니다. 중간 결과는 `/data/jobs/{job_id}/work`, 최종 영상은 `/data/jobs/{job_id}/output/video.mp4`에 저장됩니다.

프롬프트 수정 방법은 `prompts/README.md`를 참고하십시오.
