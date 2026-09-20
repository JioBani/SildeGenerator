from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _read_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        # Be tolerant of a common secret-file typo: KEY==value.
        # Only the first accidental separator is discarded.
        if key == "ELEVENLABS_API_KEY" and value.startswith("="):
            value = value[1:].lstrip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        values[key] = value
    return values


def _value(name: str, fallback: str = "") -> str:
    env_file = Path(os.getenv("RUNNER_ENV_FILE", "/run/secrets/slidegen.env"))
    return os.getenv(name) or _read_env_file(env_file).get(name, fallback)


def _integer(name: str, fallback: int) -> int:
    try:
        return int(_value(name, str(fallback)))
    except ValueError:
        return fallback


def _float(name: str, fallback: float) -> float:
    try:
        return float(_value(name, str(fallback)))
    except ValueError:
        return fallback


def _bounded_float(name: str, fallback: float, minimum: float, maximum: float) -> float:
    return min(maximum, max(minimum, _float(name, fallback)))


@dataclass(frozen=True)
class Settings:
    data_dir: Path = Path(_value("DATA_DIR", "/data"))
    harnesses_dir: Path = Path(_value("HARNESSES_DIR", "/app/harnesses"))
    prompts_dir: Path = Path(_value("PROMPTS_DIR", "/app/harnesses/classic-slide/prompts"))
    schemas_dir: Path = Path(_value("SCHEMAS_DIR", "/app/schemas"))
    runner_mode: str = _value("RUNNER_MODE", "mock").lower()
    image_provider: str = _value("IMAGE_PROVIDER", "mock").lower()
    subscription_base_url: str = _value(
        "CHATGPT_OAUTH_BASE_URL",
        _value("IMAGE_OAUTH_BASE_URL", "http://127.0.0.1:10531"),
    ).rstrip("/")
    codex_model: str = _value("CODEX_MODEL", "gpt-5.6-luna")
    codex_reasoning_effort: str = _value("CODEX_REASONING_EFFORT", "max").lower()
    codex_fast_mode: bool = _value("CODEX_FAST_MODE", "false").lower() in {"1", "true", "yes", "on"}
    codex_read_timeout_seconds: float = _float("CODEX_READ_TIMEOUT_SECONDS", 300.0)
    codex_connect_timeout_seconds: float = _float("CODEX_CONNECT_TIMEOUT_SECONDS", 10.0)
    image_generation_model: str = _value("IMAGE_GENERATION_MODEL", "gpt-image-2.5-sunburst")
    image_task_concurrency: int = min(16, max(1, _integer("IMAGE_TASK_CONCURRENCY", 12)))
    voice_task_concurrency: int = min(8, max(1, _integer("VOICE_TASK_CONCURRENCY", 2)))
    voice_provider: str = _value("VOICE_PROVIDER", "mock").lower()
    microsoft_edge_voice: str = _value("MICROSOFT_EDGE_VOICE", "ko-KR-InJoonNeural")
    microsoft_edge_rate: str = _value("MICROSOFT_EDGE_RATE", "-30%")
    microsoft_edge_pitch: str = _value("MICROSOFT_EDGE_PITCH", "+0Hz")
    microsoft_edge_volume: str = _value("MICROSOFT_EDGE_VOLUME", "+0%")
    ffmpeg_task_concurrency: int = min(4, max(1, _integer("FFMPEG_TASK_CONCURRENCY", 1)))
    database_url: str = _value("DATABASE_URL", "postgresql://slidegen:slidegen@postgres:5432/slidegen")
    redis_url: str = _value("REDIS_URL", "redis://redis:6379")
    elevenlabs_api_key: str = _value("ELEVENLABS_API_KEY")
    elevenlabs_voice_id: str = _value("ELEVENLABS_VOICE_ID", "nPczCjzI2devNBz1zQrb")
    elevenlabs_voice_name: str = _value("ELEVENLABS_VOICE_NAME", "Brian - Deep, Resonant and Comforting")
    elevenlabs_model_id: str = _value("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")
    elevenlabs_output_format: str = _value("ELEVENLABS_OUTPUT_FORMAT", "mp3_44100_128")
    elevenlabs_stability: float = _bounded_float("ELEVENLABS_STABILITY", 0.60, 0.0, 1.0)
    elevenlabs_similarity_boost: float = _bounded_float("ELEVENLABS_SIMILARITY_BOOST", 0.60, 0.0, 1.0)
    # ElevenLabs only accepts 0.7-1.2. A requested 60% pace maps to the closest supported value.
    elevenlabs_speed: float = _bounded_float("ELEVENLABS_SPEED", 0.70, 0.70, 1.20)
    width: int = _integer("VIDEO_WIDTH", 1920)
    height: int = _integer("VIDEO_HEIGHT", 1080)
    fps: int = _integer("VIDEO_FPS", 24)
    ffmpeg_preset: str = _value("FFMPEG_PRESET", "veryfast")
    crossfade_seconds: float = _float("CROSSFADE_SECONDS", 0.35)
    render_segment_scenes: int = min(12, max(2, _integer("RENDER_SEGMENT_SCENES", 8)))


settings = Settings()
