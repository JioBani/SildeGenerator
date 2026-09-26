from __future__ import annotations

import html
import json
import shutil
import textwrap
from pathlib import Path
from typing import Any

from .scene_program import compile_scene_program

RUNTIME = Path("/app/hyperframes-runtime")


def _ass_time(seconds: float) -> str:
    centiseconds = max(0, round(seconds * 100))
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    secs, cs = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


def _ass_text(value: str) -> str:
    clean = value.replace("\\", "／").replace("{", "(").replace("}", ")").replace("\n", " ")
    return r"\N".join(textwrap.wrap(clean, width=32, break_long_words=True, break_on_hyphens=False))


def write_subtitles(scenes: list[Any], path: Path, settings: Any, config: dict[str, object]) -> None:
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {settings.width}
PlayResY: {settings.height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{config.get('subtitle_font','Noto Sans CJK KR')},{config.get('subtitle_size',54)},&H00FFFFFF,&H00FFFFFF,&H00101010,&H78000000,-1,0,0,0,100,100,0,0,1,3,1,2,100,100,{config.get('subtitle_margin_vertical',72)},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    cursor = 0.0
    events: list[str] = []
    for scene in scenes:
        end = cursor + scene.duration_seconds
        events.append(f"Dialogue: 0,{_ass_time(cursor)},{_ass_time(end)},Default,,0,0,0,,{_ass_text(scene.narration)}")
        cursor = end
    path.write_text(header + "\n".join(events) + "\n", encoding="utf-8-sig")


def _scene_html(scene: Any, index: int, program: dict[str, Any]) -> str:
    title = html.escape(scene.viewer_takeaway[:90])
    caption = html.escape(scene.narration.strip())
    function = html.escape(scene.scene_function.replace("_", " "))
    components = set(program["components"])
    disabled = lambda name: " is-disabled" if name not in components else ""
    return (
        f'<section id="scene-{index}" class="scene layout-{program["layout"]}" data-function="{function}">'
        f'<img class="scene-image" src="assets/{scene.id}.png" alt="" data-layout-allow-overflow>'
        '<div class="shade"></div>'
        f'<div class="function-label{disabled("scene-title")}">{function}</div><h2 class="scene-title{disabled("scene-title")}">{title}</h2>'
        f'<div class="evidence-card{disabled("evidence-card")}"><i></i><i></i><i></i></div>'
        f'<div class="accent-orbit{disabled("accent-orbit")}"></div><div class="progress-line{disabled("progress-line")}"></div>'
        f'<div class="caption">{caption}</div></section>'
    )


def _timeline_js(scenes: list[Any], programs: list[dict[str, Any]]) -> str:
    lines = [
        "window.__timelines=window.__timelines||{};",
        "const tl=gsap.timeline({paused:true,defaults:{overwrite:false}});",
        "gsap.set('.scene',{opacity:0});",
    ]
    cursor = 0.0
    for index, (scene, program) in enumerate(zip(scenes, programs), 1):
        duration = max(.5, float(scene.duration_seconds))
        settle = max(.2, duration * float(program["timing"]["settle"]))
        enter = max(.2, duration * float(program["timing"]["enter"]))
        move = max(.3, duration - settle - enter)
        selector = f"#scene-{index}"
        if index > 1:
            previous = f"#scene-{index - 1}"
            if program["transition"] == "crossfade":
                lines.append(f"tl.to('{previous}',{{opacity:0,duration:.2,ease:'none'}},{cursor:.3f});")
                lines.append(f"tl.fromTo('{selector}',{{opacity:0}},{{opacity:1,duration:.2,ease:'none'}},{cursor:.3f});")
            else:
                lines.append(f"tl.set('{previous}',{{opacity:0}},{cursor:.3f});")
                lines.append(f"tl.set('{selector}',{{opacity:1}},{cursor:.3f});")
        else:
            lines.append(f"tl.set('{selector}',{{opacity:1}},{cursor:.3f});")
        for action in program["actions"]:
            target = action["target"]
            effect = action["effect"]
            if effect == "camera_push":
                lines.append(f"tl.fromTo('{selector} .{target}',{{scale:1.035,x:-18}},{{scale:1.105,x:18,duration:{move:.3f},ease:'sine.inOut'}},{cursor:.3f});")
                lines.append(f"tl.to('{selector} .{target}',{{x:14,scale:1.1,duration:{settle:.3f},ease:'sine.out'}},{cursor + duration - settle:.3f});")
            elif effect == "reveal" and target == "scene-title":
                lines.append(f"tl.fromTo('{selector} .scene-title, {selector} .function-label',{{y:28,opacity:0}},{{y:0,opacity:1,duration:{min(.55, enter):.3f},stagger:.08,ease:'power2.out'}},{cursor + .08:.3f});")
            elif effect == "reveal":
                lines.append(f"tl.fromTo('{selector} .{target}',{{x:72,opacity:0}},{{x:0,opacity:1,duration:{min(.6, enter):.3f},ease:'power2.out'}},{cursor + enter:.3f});")
            elif effect == "emphasize":
                lines.append(f"tl.fromTo('{selector} .{target}',{{scale:.45,opacity:0}},{{scale:1,opacity:.9,duration:{min(.6, enter):.3f},ease:'back.out(1.35)'}},{cursor + enter:.3f});")
            elif effect == "progress":
                lines.append(f"tl.fromTo('{selector} .{target}',{{scaleX:0}},{{scaleX:1,duration:{max(.5, duration - .35):.3f},ease:'none'}},{cursor + .15:.3f});")
        cursor += duration
    return "".join(lines) + "window.__timelines['astra-motion-segment']=tl;"


def compile_project(scenes: list[Any], project: Path, settings: Any) -> None:
    assets = project / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    gsap = RUNTIME / "node_modules" / "gsap" / "dist" / "gsap.min.js"
    if not gsap.is_file():
        raise RuntimeError("Pinned GSAP runtime is not installed")
    shutil.copy2(gsap, assets / "gsap.min.js")
    for scene in scenes:
        shutil.copy2(Path(scene.image_path), assets / f"{scene.id}.png")
    duration = sum(float(scene.duration_seconds) for scene in scenes)
    programs = [compile_scene_program(scene) for scene in scenes]
    meta = {"name": "astra-motion-segment", "description": "Astra scene contract render", "duration": duration, "resolution": {"width": settings.width, "height": settings.height}, "fps": settings.fps}
    (project / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (project / "scene-program.json").write_text(json.dumps({"scenes": programs}, ensure_ascii=False, indent=2), encoding="utf-8")
    styles = """
@font-face{font-family:'Astra Noto';src:local('Noto Sans CJK KR');font-style:normal;font-weight:100 900}*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#12232b;font-family:'Astra Noto',sans-serif}.scene{position:absolute;inset:0;overflow:hidden;opacity:0;background:#173642;color:#fff}.is-disabled{display:none!important}.scene-image{position:absolute;inset:-5%;width:110%;height:110%;object-fit:cover}.shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(10,24,30,.8),rgba(10,24,30,.08) 58%,rgba(10,24,30,.45))}.function-label{position:absolute;left:84px;top:72px;padding:10px 16px;border-left:7px solid #f4c453;background:rgba(13,32,40,.72);font-size:24px;font-weight:800}h2{position:absolute;left:84px;top:145px;width:880px;margin:0;font-size:58px;line-height:1.18}.evidence-card{position:absolute;right:110px;top:210px;width:390px;height:270px;border:8px solid #172a33;background:rgba(246,239,217,.94);padding:48px}.evidence-card i{display:block;height:24px;margin:0 0 28px;background:#4da5a9}.evidence-card i:nth-child(2){width:72%;background:#f06449}.evidence-card i:nth-child(3){width:88%;background:#efc95e}.accent-orbit{position:absolute;right:250px;top:520px;width:110px;height:110px;border:14px solid #f06449;border-radius:50%;box-shadow:0 0 0 24px rgba(239,201,94,.75)}.caption{position:absolute;left:84px;right:84px;bottom:58px;min-height:98px;padding:22px 28px;background:rgba(7,19,24,.68);font-size:34px;line-height:1.35}.progress-line{position:absolute;left:84px;right:84px;bottom:40px;height:8px;background:#efc95e;transform-origin:left}.layout-split h2{width:720px}.layout-split .scene-image{left:44%;width:66%}.layout-comparison .evidence-card{width:480px;height:320px}.layout-process .progress-line{height:14px}.layout-diagram .scene-image{filter:saturate(.82) contrast(1.05)}
"""
    body = "".join(_scene_html(scene, index, program) for index, (scene, program) in enumerate(zip(scenes, programs), 1))
    document = f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>Astra Motion</title><script src="assets/gsap.min.js"></script><style>{styles}</style></head><body><div id="master" data-composition-id="astra-motion-segment" data-width="{settings.width}" data-height="{settings.height}" data-start="0" data-duration="{duration:.6f}" data-fps="{settings.fps}">{body}</div><script>{_timeline_js(scenes, programs)}</script></body></html>'
    (project / "index.html").write_text(document, encoding="utf-8")


async def render_segment(scenes: list[Any], output: Path, settings: Any, config: dict[str, object], process: Any) -> None:
    project = output.with_suffix("")
    if project.exists():
        shutil.rmtree(project)
    project.mkdir(parents=True)
    from .compositor import compile_project as compile_genre_project
    compile_genre_project(scenes, project, settings, RUNTIME)
    cli = RUNTIME / "node_modules" / ".bin" / "hyperframes"
    await process.run([
        str(cli), "check", "--strict", str(project),
    ], cwd=RUNTIME, timeout=180)
    await process.run([
        str(cli), "render", f"--output={output}",
        f"--quality={config.get('hyperframes_quality', 'looks')}",
        f"--workers={int(config.get('hyperframes_workers', 1))}",
        "--low-memory-mode", "--strict", str(project),
    ], cwd=RUNTIME, timeout=1800)


async def concatenate_audio(scenes: list[Any], work: Path, process: Any) -> Path:
    manifest = work / "audio-concat.txt"
    manifest.write_text("\n".join(f"file '{Path(scene.audio_path).as_posix()}'" for scene in scenes) + "\n", encoding="utf-8")
    output = work / "narration.m4a"
    await process.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(manifest), "-vn", "-c:a", "aac", "-b:a", "128k", str(output)])
    return output


async def assemble_video(segments: list[Path], audio: Path, output: Path, process: Any) -> None:
    render_dir = output.parent.parent / "work" / "render-segments"
    manifest = render_dir / "video-concat.txt"
    manifest.write_text("\n".join(f"file '{path.as_posix()}'" for path in segments) + "\n", encoding="utf-8")
    visual = render_dir / "visual.mp4"
    await process.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(manifest), "-c", "copy", str(visual)])
    await process.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(visual), "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", "-movflags", "+faststart", str(output)])
