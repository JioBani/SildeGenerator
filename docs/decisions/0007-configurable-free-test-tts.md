# ADR-0007: 설정 가능한 무료 테스트 TTS provider

- 상태: 구현 승인
- 작성일: 2026-09-20
- 구현 담당: `pipeline-maintainer`
- 연관: ADR-0006 로컬 부트스트랩·설정 웹

## 1. 목표

개발·하네스·사용자 E2E에서 ElevenLabs credit을 소비하지 않고도 실제 한국어 음성이 포함된 영상을 만들 수 있게 한다. 음성 provider를 설정에서 선택하며, 선택값과 세부 설정은 작업 접수 시 snapshot으로 고정한다.

초기 provider:

| ID | 화면 표시 | 용도 | 비용/네트워크 |
|---|---|---|---|
| `mock` | 무음 Mock | CI와 완전 결정론적 빠른 검사 | 무료, 오프라인 |
| `microsoft_edge` | Microsoft Edge 음성 — 무료 테스트 | 사람이 듣는 개발·하네스 E2E | API key/직접 과금 없음, 온라인 필요 |
| `elevenlabs` | ElevenLabs — 운영 품질 | 실제 배포 영상 | credit 사용, 온라인 필요 |

`microsoft_edge`는 `edge-tts` 커뮤니티 Python client를 사용한다. 이 코드는 Docker runner 안에서 실행되지만 합성은 Microsoft Edge의 온라인 음성 서비스에 요청한다. UI와 문서에서 `로컬/오프라인 Microsoft TTS`라고 표시하지 않는다.

Windows 설치 음성을 사용하는 SAPI/`Windows.Media.SpeechSynthesis`는 진짜 로컬 음성이지만 Linux Docker와 MINI에서 직접 사용할 수 없으므로 이번 범위에 넣지 않는다. Microsoft Embedded Speech도 별도 제한 접근과 모델 배포가 필요한 제품이므로 무료 clone-and-run 경로로 간주하지 않는다.

## 2. 핵심 구조 변경

현재 runner는 `RUNNER_MODE=live`이면 ElevenLabs, 아니면 무음 Mock을 사용한다. 이를 분리한다.

```text
RUNNER_MODE    = mock | live             # Codex/이미지 계획 경로
IMAGE_PROVIDER = mock | oauth | ...      # 이미지 경로
VOICE_PROVIDER = mock | microsoft_edge | elevenlabs
```

허용 조합 예:

- CI: `RUNNER_MODE=mock`, `IMAGE_PROVIDER=mock`, `VOICE_PROVIDER=mock`
- 무료 시청 E2E: `RUNNER_MODE=mock`, `IMAGE_PROVIDER=mock`, `VOICE_PROVIDER=microsoft_edge`
- 구독 이미지 + 무료 테스트 음성: `RUNNER_MODE=live`, `IMAGE_PROVIDER=oauth`, `VOICE_PROVIDER=microsoft_edge`
- 운영 품질: `RUNNER_MODE=live`, `IMAGE_PROVIDER=oauth`, `VOICE_PROVIDER=elevenlabs`

voice provider를 runner mode에서 추론하지 않는다.

## 3. provider interface

ElevenLabs 구현, Edge 구현, Mock 구현을 같은 protocol로 감싼다.

```python
class VoiceProvider(Protocol):
    provider_id: str
    model_id: str

    async def synthesize(
        self,
        scene: Scene,
        output_path: Path,
        tracker: Tracker,
        *,
        record_usage: bool = True,
    ) -> VoiceResult: ...
```

`VoiceResult`에는 provider에 상관없이 다음을 담는다.

- 실제 audio duration
- characters
- alignment 또는 word boundaries가 있으면 해당 값
- provider request ID가 있으면 해당 값
- provider/model/voice/settings snapshot
- 비용 측정 상태

broker, retry, settings hash, cache/reuse, deterministic audio QC는 provider 공통으로 유지한다.

## 4. Microsoft Edge adapter

### 4.1 의존성

- Python `edge-tts` 버전을 `requirements.txt`에 정확히 pin한다.
- floating latest 또는 container 시작 시 동적 install을 금지한다.
- Docker image build 단계에서 설치한다.
- package license와 upstream URL을 NOTICE 또는 third-party 문서에 기록한다.

### 4.2 초기 기본값

```dotenv
VOICE_PROVIDER=microsoft_edge
MICROSOFT_EDGE_VOICE=ko-KR-InJoonNeural
MICROSOFT_EDGE_RATE=-30%
MICROSOFT_EDGE_PITCH=+0Hz
MICROSOFT_EDGE_VOLUME=+0%
```

기본 voice는 한국어 남성 음성으로 두되 설정 UI에서 사용 가능한 한국어 voice로 변경할 수 있게 한다. voice 이름은 provider의 실제 목록에서 검증한다. 네트워크로 목록을 가져오지 못하면 마지막 cache와 알려진 기본값을 사용하되, 실제 합성 실패를 숨기지 않는다.

`-30%`는 ElevenLabs speed 0.70과 수치상 비슷하게 느리게 읽도록 잡은 초기값일 뿐 동일한 속도를 보장하지 않는다. 실제 생성 audio duration이 scene 길이의 정본이다.

### 4.3 생성과 정규화

- scene별 narration을 Edge adapter로 합성한다.
- 임시 파일에 쓰고 성공 후 atomic rename하는 기존 broker 계약을 유지한다.
- 결과 형식이 달라도 ffmpeg로 최종 `mp3`, 44.1kHz, mono, 128kbps로 정규화한다.
- ffprobe로 실제 길이를 측정한다.
- 무음, 지나치게 짧은 길이, decode 실패, peak/mean volume을 기존 결정론적 QC에 포함한다.
- Edge가 word boundary metadata를 제공하면 raw usage에 보존하되 자막 생성이 이에 의존하도록 강제하지 않는다.

### 4.4 실패와 재시도

- 기존 voice broker의 네트워크/429/5xx retry 규칙을 사용한다.
- Edge 최종 실패 시 ElevenLabs로 자동 fallback하지 않는다. 테스트 중 예기치 않은 유료 사용을 막는다.
- 화면에는 `무료 테스트 음성 생성에 실패했습니다. Microsoft Edge 음성은 온라인 연결이 필요합니다.`처럼 표시한다.
- fallback은 사용자가 provider 설정을 명시적으로 바꾼 다음 새 작업에서만 가능하다.

## 5. 설정 모델

### 5.1 초기 setup 웹

ADR-0006의 설정 웹에 `음성 공급자`를 추가한다.

- 무음 Mock
- Microsoft Edge 음성 — 무료 테스트, 온라인
- ElevenLabs — 운영 품질, credit 사용

선택에 따라 필드를 조건부 표시한다.

Microsoft Edge:

- 한국어 voice
- 말하기 속도
- pitch
- volume
- `API key 없이 동작하지만 온라인 서비스이며 테스트 전용` 안내

ElevenLabs:

- API key
- voice ID/name
- model
- stability/similarity/speed
- `credit이 소비됨` 안내

Mock:

- 별도 입력 없음
- `영상에는 실제 음성이 아니라 무음이 들어감` 안내

### 5.2 관리자 설정

기존 관리자 `모델 설정`과 분리된 `음성 설정` 영역 또는 같은 화면의 명확한 section으로 제공한다.

- 현재 provider
- provider별 설정
- ElevenLabs key configured 여부만 표시; secret readback 금지
- Edge voice 목록 새로고침
- 테스트 문장 1회 합성 버튼

테스트 합성 버튼은 Edge에서는 무료 테스트임을 표시하고, ElevenLabs에서는 credit 소모 경고와 사용자 확인 후 실행한다. 테스트 파일은 짧은 TTL 후 삭제하고 작업 통계에 포함하지 않는다.

설정 변경은 진행 중 또는 이미 queue에 들어간 작업에 영향을 주지 않는다. 새 작업부터 적용한다.

## 6. 작업별 snapshot

작업 접수 시 다음 값을 DB와 BullMQ payload에 고정한다.

- `voice_provider`
- `voice_model`
- `voice_id`
- provider-specific non-secret settings
- `voice_settings_version`

ElevenLabs API key 자체는 DB, queue payload, job JSON, 로그에 넣지 않는다. runner의 secret file에서 실행 시 읽는다.

voice task의 settings hash에는 provider/model/voice/rate/pitch/volume 또는 ElevenLabs stability/similarity/speed를 포함한다. provider를 바꾸면 기존 cache audio를 재사용하면 안 된다.

## 7. API

관리자 API 의미:

```text
GET /api/admin/settings/voice
PUT /api/admin/settings/voice
GET /api/admin/settings/voice/options?provider=microsoft_edge&locale=ko-KR
POST /api/admin/settings/voice/sample
```

응답에는 secret을 포함하지 않는다. `elevenLabsConfigured: true|false`만 제공한다.

일반 job status와 관리자 job detail에 실제 snapshot provider/model/voice를 노출한다. 일반 사용자가 작업별 provider를 임의 선택하게 할 필요는 없다. 관리자 기본 설정이 새 작업에 적용된다.

## 8. 비용과 분석

provider usage event를 다음처럼 분리한다.

Microsoft Edge:

- provider: `microsoft_edge_tts`
- model: 실제 voice ID
- characters/audio duration/provider duration 기록
- actual cost: 0
- API equivalent cost: null 또는 0으로 거짓 환산하지 않고 `unpriced_test_provider=true`
- 관리자 UI: `직접 과금 0원 · 테스트 provider` 표시

Mock:

- provider: `mock`
- model: `mock-silence-v1`
- 비용 집계에서 외부 음성비와 분리

ElevenLabs:

- 기존 문자 기반 실제 비용과 분당 비용 유지

개선 분석 차원에 `voiceProvider`, `voiceModel`을 추가한다. 서로 다른 provider의 품질 점수와 생성시간을 비교할 수 있어야 하지만, Edge 0원을 ElevenLabs 공식 API 가격과 같은 의미의 생산 비용으로 해석하지 않도록 라벨을 구분한다.

## 9. health와 readiness

runner health에 secret 없이 다음만 추가한다.

```json
{
  "voiceProvider": "microsoft_edge",
  "voiceConfigured": true,
  "voiceNetworkRequired": true,
  "elevenLabsConfigured": false
}
```

- Mock은 항상 configured
- Edge는 voice 설정 형식이 유효하면 configured; 온라인 도달성은 별도 probe
- ElevenLabs는 key 존재와 필수 설정이 있어야 configured
- health request 자체가 유료 TTS를 호출하면 안 된다.

## 10. README와 에이전트 안내

README는 `무료 테스트 음성`을 다음처럼 정확히 설명한다.

```text
Microsoft Edge 음성은 API key와 직접 과금 없이 테스트할 수 있지만,
음성 합성은 온라인 Microsoft 서비스에서 이루어집니다. 오프라인 TTS가
아니며 운영 SLA가 없는 테스트 provider입니다.
```

에이전트 Quick Start 기본 선택:

- CI/자동 검증: `mock`
- 사용자가 실제 음성을 듣는 무료 로컬 개발 E2E: `microsoft_edge`
- 사용자가 명시한 Live 품질 검증: `elevenlabs`

에이전트는 사용자의 명시적 승인 없이 ElevenLabs sample 또는 Live 영상 생성을 호출하지 않는다.

## 11. 테스트

### 11.1 단위·통합

- provider factory가 세 provider를 정확히 선택
- runner mode와 voice provider 독립성
- settings validation: voice/rate/pitch/volume
- Edge client는 network mock으로 MP3와 word boundary 처리 검증
- 결과 44.1kHz mono MP3 정규화와 ffprobe 길이
- voice settings hash가 provider/voice/rate 변경 시 달라짐
- Microsoft Edge 작업이 ElevenLabs key 없이 성공
- Edge 실패 시 ElevenLabs 자동 fallback 없음
- 비용 event가 `microsoft_edge_tts`, 직접 비용 0, 테스트 provider로 기록
- queue/parallel/retry/cache 동작이 ElevenLabs와 동일

### 11.2 사용자 E2E

1. setup 또는 관리자에서 Microsoft Edge 선택
2. 짧은 한국어 대본으로 영상 생성
3. 작업 상세 provider/model/voice 확인
4. MP4에 실제 한국어 음성 존재 확인
5. 음성 길이와 영상 길이 sync 계측
6. ElevenLabs usage event와 credit 호출이 0건인지 확인
7. 설정을 ElevenLabs로 되돌린 뒤 기존 Live 경로 회귀 테스트는 사용자 승인된 짧은 문장으로만 수행

### 11.3 Docker·플랫폼

- Windows Docker Desktop과 MINI Ubuntu의 동일 Linux image에서 Edge provider 동작
- 호스트 SAPI나 Windows 전용 DLL 의존 없음
- 8GB MINI 메모리 피크 기록
- 네트워크 차단 시 명확한 실패 메시지와 retry 상한

## 12. 완료 조건

1. 설정 웹과 관리자에서 `mock`, `microsoft_edge`, `elevenlabs`를 선택할 수 있다.
2. Microsoft Edge 선택 시 ElevenLabs key와 credit 없이 실제 한국어 음성 영상이 생성된다.
3. UI가 Microsoft Edge provider를 로컬/오프라인 또는 공식 무료 API로 오해하게 표시하지 않는다.
4. provider 설정이 작업별로 고정되고 cache, 비용, 분석이 provider별로 분리된다.
5. Edge 실패 시 유료 ElevenLabs 자동 fallback이 없다.
6. CI는 무음 Mock으로 외부 네트워크 없이 통과한다.
7. 사용자가 듣는 무료 E2E는 Edge provider로 통과하고 ElevenLabs 호출 0건을 증명한다.
