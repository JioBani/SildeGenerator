from app.config import settings
from app.models import VoiceSettings
from app.providers.elevenlabs import ElevenLabs
from app.providers.microsoft_edge import MicrosoftEdge
from app.providers.voice import create_voice_provider
from app.voice_broker import voice_settings_hash


def snapshot(provider: str, **updates):
    values = dict(provider=provider, model="edge-tts", voice_id="ko-KR-InJoonNeural", voice_name="인준", rate="-30%", pitch="+0Hz", volume="+0%", version=1)
    values.update(updates)
    return VoiceSettings(**values)


def test_provider_factory_is_independent_from_runner_mode():
    assert isinstance(create_voice_provider(snapshot("microsoft_edge"), settings), MicrosoftEdge)
    assert create_voice_provider(snapshot("mock", model="mock-silence-v1", voice_id="mock", voice_name="무음", rate=None, pitch=None, volume=None), settings) is None
    eleven = snapshot("elevenlabs", model="eleven_flash_v2_5", voice_id="voice", voice_name="Voice", rate=None, pitch=None, volume=None, stability=.6, similarity_boost=.6, speed=.7)
    assert isinstance(create_voice_provider(eleven, settings), ElevenLabs)


def test_settings_hash_separates_provider_voice_and_rate():
    base = snapshot("microsoft_edge").model_dump(exclude_none=True)
    first = voice_settings_hash("같은 문장", base)
    assert first != voice_settings_hash("같은 문장", {**base, "provider": "mock"})
    assert first != voice_settings_hash("같은 문장", {**base, "voice_id": "ko-KR-SunHiNeural"})
    assert first != voice_settings_hash("같은 문장", {**base, "rate": "-20%"})
    assert first != voice_settings_hash("같은 문장", {**base, "speed": 1.2})
