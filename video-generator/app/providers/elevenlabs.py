from __future__ import annotations

import asyncio
import base64
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

from ..config import Settings
from ..models import Scene, VoiceSettings
from ..tracking import Tracker


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _run(*command: str) -> None:
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await process.communicate()
    if process.returncode:
        raise RuntimeError(stderr.decode("utf-8", errors="replace")[-1500:])


async def media_duration(path: Path) -> float:
    process = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    if process.returncode:
        raise RuntimeError(stderr.decode("utf-8", errors="replace")[-1000:])
    return float(stdout.decode().strip())


class ElevenLabs:
    provider_id = "elevenlabs"
    model_id = "elevenlabs"
    def __init__(self, settings: Settings, snapshot: VoiceSettings | None = None) -> None:
        self.settings = settings
        self.snapshot = snapshot
        self._voice_id: str | None = (snapshot.voice_id if snapshot else settings.elevenlabs_voice_id) or None

    async def _resolve_voice(self, client: httpx.AsyncClient) -> str:
        if self._voice_id:
            return self._voice_id
        response = await client.get(
            "https://api.elevenlabs.io/v2/voices",
            headers={"xi-api-key": self.settings.elevenlabs_api_key},
            params={"page_size": 100},
        )
        if response.status_code >= 400:
            raise RuntimeError(f"ElevenLabs voice lookup failed ({response.status_code}). Replace ELEVENLABS_API_KEY.")
        voices = response.json().get("voices") or []
        target = (self.snapshot.voice_name if self.snapshot else self.settings.elevenlabs_voice_name).casefold()
        match = next((voice for voice in voices if str(voice.get("name", "")).casefold() == target), None)
        if not match:
            match = next((voice for voice in voices if target in str(voice.get("name", "")).casefold()), None)
        if not match:
            available = ", ".join(str(voice.get("name")) for voice in voices[:15])
            raise RuntimeError(f"ElevenLabs voice '{self.snapshot.voice_name if self.snapshot else self.settings.elevenlabs_voice_name}' not found. Available: {available}")
        self._voice_id = str(match["voice_id"])
        return self._voice_id

    async def synthesize(self, scene: Scene, path: Path, tracker: Tracker, *, record_usage: bool = True) -> dict[str, Any]:
        if not self.settings.elevenlabs_api_key:
            raise RuntimeError("ELEVENLABS_API_KEY is required in live mode")
        started_at = _now()
        started = time.perf_counter()
        voice_settings = {
            "stability": self.snapshot.stability if self.snapshot and self.snapshot.stability is not None else self.settings.elevenlabs_stability,
            "similarity_boost": self.snapshot.similarity_boost if self.snapshot and self.snapshot.similarity_boost is not None else self.settings.elevenlabs_similarity_boost,
            "speed": self.snapshot.speed if self.snapshot and self.snapshot.speed is not None else self.settings.elevenlabs_speed,
            "style": 0.15,
        }
        async with httpx.AsyncClient(timeout=httpx.Timeout(180, connect=10)) as client:
            voice_id = await self._resolve_voice(client)
            response = await client.post(
                f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/with-timestamps",
                headers={"xi-api-key": self.settings.elevenlabs_api_key, "Content-Type": "application/json"},
                params={"output_format": self.settings.elevenlabs_output_format},
                json={
                    "text": scene.narration,
                    "model_id": self.snapshot.model if self.snapshot else self.settings.elevenlabs_model_id,
                    "language_code": "ko",
                    "apply_text_normalization": "on",
                    "seed": 20260919,
                    "voice_settings": voice_settings,
                },
            )
        if response.status_code >= 400:
            detail = response.text[:700]
            raise RuntimeError(f"ElevenLabs TTS failed ({response.status_code}): {detail}")
        payload = response.json()
        path.write_bytes(base64.b64decode(payload["audio_base64"]))
        duration = await media_duration(path)
        finished_at = _now()
        usage_event = dict(
            provider="elevenlabs",
            model=self.snapshot.model if self.snapshot else self.settings.elevenlabs_model_id,
            stage="voice_generation",
            scene_id=scene.id,
            request_id=response.headers.get("request-id"),
            characters=len(scene.narration),
            audio_duration_ms=round(duration * 1000),
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=round((time.perf_counter() - started) * 1000),
            raw_usage={
                "voice_id": voice_id,
                "voice_settings": voice_settings,
                "alignment": payload.get("normalized_alignment") or payload.get("alignment"),
            },
        )
        if record_usage:
            tracker.add_usage(**usage_event)
        return {"duration": duration, "alignment": payload.get("normalized_alignment") or payload.get("alignment"), "request_id": response.headers.get("request-id"), "characters": len(scene.narration), "provider_usage": usage_event}


async def mock_speech(scene: Scene, path: Path, tracker: Tracker, *, record_usage: bool = True) -> dict[str, Any]:
    duration = max(1.2, len(scene.narration.replace(" ", "")) / 6.7)
    started_at = _now()
    started = time.perf_counter()
    await _run(
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono", "-t", f"{duration:.3f}",
        "-c:a", "libmp3lame", "-b:a", "128k", str(path),
    )
    duration = await media_duration(path)
    finished_at = _now()
    usage_event = dict(
        provider="mock",
        model="mock-silence-v1",
        stage="voice_generation",
        scene_id=scene.id,
        characters=len(scene.narration),
        audio_duration_ms=round(duration * 1000),
        started_at=started_at,
        finished_at=finished_at,
        duration_ms=round((time.perf_counter() - started) * 1000),
        raw_usage={},
    )
    if record_usage:
        tracker.add_usage(**usage_event)
    return {"duration": duration, "alignment": None, "characters": len(scene.narration), "provider_usage": usage_event}
