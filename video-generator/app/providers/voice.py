from __future__ import annotations

from pathlib import Path
from typing import Any, Protocol

from ..config import Settings
from ..models import Scene, VoiceSettings
from ..tracking import Tracker
from .elevenlabs import ElevenLabs
from .microsoft_edge import MicrosoftEdge


class VoiceProvider(Protocol):
    provider_id: str
    model_id: str
    async def synthesize(self, scene: Scene, output_path: Path, tracker: Tracker, *, record_usage: bool = True) -> dict[str, Any]: ...


def create_voice_provider(snapshot: VoiceSettings, settings: Settings) -> VoiceProvider | None:
    if snapshot.provider == "elevenlabs":
        return ElevenLabs(settings, snapshot)
    if snapshot.provider == "microsoft_edge":
        return MicrosoftEdge(snapshot)
    return None
