from __future__ import annotations

import asyncio
import time
from pathlib import Path
from typing import Any

from ..models import Scene, VoiceSettings
from ..tracking import Tracker
from .elevenlabs import _now, _run, media_duration


class MicrosoftEdge:
    provider_id = "microsoft_edge"
    model_id = "edge-tts"

    def __init__(self, snapshot: VoiceSettings) -> None:
        self.snapshot = snapshot

    async def synthesize(self, scene: Scene, path: Path, tracker: Tracker, *, record_usage: bool = True) -> dict[str, Any]:
        started_at = _now()
        started = time.perf_counter()
        raw_path = path.with_suffix(".edge.mp3")
        boundaries: list[dict[str, Any]] = []
        try:
            import edge_tts
            communicate = edge_tts.Communicate(
                scene.narration,
                self.snapshot.voice_id,
                rate=self.snapshot.rate or "-30%",
                pitch=self.snapshot.pitch or "+0Hz",
                volume=self.snapshot.volume or "+0%",
            )
            with raw_path.open("wb") as stream:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        stream.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        boundaries.append({key: chunk.get(key) for key in ("offset", "duration", "text")})
            if not raw_path.is_file() or raw_path.stat().st_size == 0:
                raise RuntimeError("Microsoft Edge voice returned no audio")
            await _run(
                "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(raw_path),
                "-ar", "44100", "-ac", "1", "-c:a", "libmp3lame", "-b:a", "128k", str(path),
            )
        except Exception as error:
            raise RuntimeError("무료 테스트 음성 생성에 실패했습니다. Microsoft Edge 음성은 온라인 연결이 필요합니다.") from error
        finally:
            raw_path.unlink(missing_ok=True)
        duration = await media_duration(path)
        usage_event = dict(
            provider="microsoft_edge_tts", model=self.snapshot.voice_id, stage="voice_generation",
            scene_id=scene.id, characters=len(scene.narration), audio_duration_ms=round(duration * 1000),
            started_at=started_at, finished_at=_now(), duration_ms=round((time.perf_counter() - started) * 1000),
            raw_usage={"voice_id": self.snapshot.voice_id, "rate": self.snapshot.rate, "pitch": self.snapshot.pitch,
                       "volume": self.snapshot.volume, "word_boundaries": boundaries, "unpriced_test_provider": True},
        )
        if record_usage:
            tracker.add_usage(**usage_event)
        return {"duration": duration, "alignment": boundaries or None, "characters": len(scene.narration),
                "provider_usage": usage_event, "unpriced_test_provider": True}
