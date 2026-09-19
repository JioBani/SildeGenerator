from __future__ import annotations

import math
import textwrap
from pathlib import Path
from typing import Any


def _ass_time(seconds: float) -> str:
    centiseconds = max(0, round(seconds * 100)); hours, remainder = divmod(centiseconds, 360_000); minutes, remainder = divmod(remainder, 6_000); secs, cs = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def _ass_text(value: str) -> str:
    clean = value.replace("\\", "／").replace("{", "(").replace("}", ")").replace("\n", " ")
    return r"\N".join(textwrap.wrap(clean, width=32, break_long_words=True, break_on_hyphens=False))


def write_subtitles(scenes: list[Any], path: Path, settings: Any, config: dict[str, object]) -> None:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {settings.width}
PlayResY: {settings.height}
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{config.get('subtitle_font','Noto Sans CJK KR')},{config.get('subtitle_size',54)},&H00FFFFFF,&H00FFFFFF,&H00101010,&H78000000,-1,0,0,0,100,100,0,0,1,3,1,2,100,100,{config.get('subtitle_margin_vertical',72)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    cursor = 0.0; events: list[str] = []
    for scene in scenes:
        end = cursor + scene.duration_seconds; events.append(f"Dialogue: 0,{_ass_time(cursor)},{_ass_time(end)},Default,,0,0,0,,{_ass_text(scene.narration)}"); cursor = end
    path.write_text(header + "\n".join(events) + "\n", encoding="utf-8-sig")


def video_filter(scenes: list[Any], subtitles: Path, settings: Any, config: dict[str, object], transition: str) -> tuple[str, str]:
    fade = max(0.0, min(float(config.get("crossfade_seconds", settings.crossfade_seconds)), min(scene.duration_seconds for scene in scenes) / 3)); zoom = float(config.get("zoom_strength", 0.045)); filters: list[str] = []
    for index, scene in enumerate(scenes):
        duration = scene.duration_seconds + (fade if index < len(scenes) - 1 else 0); frames = max(1, math.ceil(duration * settings.fps)); x = ("(iw-iw/zoom)*(1-on/{frames})" if index % 2 else "(iw-iw/zoom)*(on/{frames})").replace("{frames}", str(frames))
        filters.append(f"[{index}:v]scale={settings.width}:{settings.height}:force_original_aspect_ratio=increase,crop={settings.width}:{settings.height},zoompan=z='1+{zoom}*on/{frames}':x='{x}':y='(ih-ih/zoom)/2':d=1:s={settings.width}x{settings.height}:fps={settings.fps},trim=duration={duration:.6f},setpts=PTS-STARTPTS[v{index}]")
    current = "v0"; cursor = scenes[0].duration_seconds
    for index in range(1, len(scenes)):
        output = f"x{index}"; filters.append(f"[{current}][v{index}]xfade=transition={transition}:duration={fade:.6f}:offset={cursor:.6f}[{output}]"); current = output; cursor += scenes[index].duration_seconds
    subtitle_path = subtitles.as_posix().replace("'", r"\'").replace(":", r"\:"); filters.append(f"[{current}]subtitles=filename='{subtitle_path}'[video]")
    return ";".join(filters), "video"


async def render_segment(scenes: list[Any], subtitles: Path, output: Path, settings: Any, config: dict[str, object], process: Any, transition: str = "fade") -> None:
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y"]; fade = max(0.0, min(float(config.get("crossfade_seconds", settings.crossfade_seconds)), min(scene.duration_seconds for scene in scenes) / 3))
    for index, scene in enumerate(scenes):
        duration = scene.duration_seconds + (fade if index < len(scenes) - 1 else 0); command.extend(["-framerate", str(settings.fps), "-loop", "1", "-t", f"{duration:.6f}", "-i", scene.image_path])
    filters, label = video_filter(scenes, subtitles, settings, config, transition)
    command.extend(["-filter_complex", filters, "-map", f"[{label}]", "-c:v", "libx264", "-preset", settings.ffmpeg_preset, "-crf", "20", "-pix_fmt", "yuv420p", "-r", str(settings.fps), "-threads", "2", "-an", "-movflags", "+faststart", str(output)])
    await process.run(command)


async def concatenate_audio(scenes: list[Any], work: Path, process: Any) -> Path:
    manifest = work / "audio-concat.txt"; manifest.write_text("\n".join(f"file '{Path(scene.audio_path).as_posix()}'" for scene in scenes) + "\n", encoding="utf-8"); output = work / "narration.m4a"
    await process.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(manifest), "-vn", "-c:a", "aac", "-b:a", "128k", str(output)])
    return output


async def assemble_video(segments: list[Path], audio: Path, output: Path, process: Any) -> None:
    render_dir = output.parent.parent / "work" / "render-segments"; manifest = render_dir / "video-concat.txt"; manifest.write_text("\n".join(f"file '{path.as_posix()}'" for path in segments) + "\n", encoding="utf-8"); visual = render_dir / "visual.mp4"
    await process.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(manifest), "-c", "copy", str(visual)])
    await process.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(visual), "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "copy", "-shortest", "-movflags", "+faststart", str(output)])
