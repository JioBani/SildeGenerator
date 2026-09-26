from __future__ import annotations

import html
import json
import shutil
import textwrap
from pathlib import Path
from typing import Any

from .scene_program import compile_scene_program
from .local_renderer import local_scene_html, local_styles, local_timeline_lines

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
    if program.get("local_visual"):
        return local_scene_html(scene, index, program)
    title = html.escape(scene.viewer_takeaway[:52 if program.get("motion_style_id") else 90])
    caption = html.escape(scene.narration.strip())
    function = html.escape(scene.scene_function.replace("_", " "))
    components = set(program["components"])
    disabled = lambda name: " is-disabled" if name not in components else ""
    semantic_layers = "".join(
        '<div class="semantic-object semantic-{variant} depth-{depth}" data-object-id="{object_id}" style="--object-index:{object_index}" aria-hidden="true">{parts}</div>'.format(
            variant=html.escape(item["variant"], quote=True),
            object_id=html.escape(item["object_id"], quote=True),
            object_index=object_index,
            depth=html.escape(item.get("depth_band", "midground"), quote=True),
            parts=(f'<img src="assets/{scene.id}--{html.escape(item["object_id"], quote=True)}.png" alt="">'
                   if item.get("asset_path") else (
                       f'<span class="object-role">{html.escape(item["role"][:32])}</span>'
                       f'<strong>{html.escape(item.get("initial", "")[:26])} → {html.escape(item.get("final", "")[:26])}</strong>'
                       if program.get("motion_style_id") == "educational_info" else "".join("<i></i>" for _ in range(8))
                   )),
        )
        for object_index, item in enumerate(program.get("semantic_objects", []))
    )
    scene_source = f"assets/{scene.id}--background.png" if program.get("background_path") else f"assets/{scene.id}.png"
    style = program.get("motion_style_id")
    if style in {"narrative", "educational_info"}:
        labels = "".join(
            '<div class="diagram-label" style="left:{x:.2f}%;top:{y:.2f}%">{text}</div>'.format(
                x=max(15, min(85, float(item.get("x", .5)) * 100)),
                y=max(5, min(85, float(item.get("y", .4)) * 100)),
                text=html.escape(str(item.get("text", ""))[:120]),
            ) for item in program.get("visual_labels", [])
        )
        return (
            f'<section id="scene-{index}" class="scene style-{style} layout-{program["layout"]}">'
            f'<img class="scene-image" src="{scene_source}" alt="" data-layout-allow-overflow>'
            '<div class="shade"></div>'
            f'<div class="semantic-stage">{semantic_layers}</div>'
            f'<div class="diagram-board">{labels}</div>'
            f'<h2 class="scene-title">{title}</h2><div class="caption">{caption}</div></section>'
        )
    return (
        f'<section id="scene-{index}" class="scene layout-{program["layout"]}" data-function="{function}">'
        f'<img class="scene-image" src="{scene_source}" alt="" data-layout-allow-overflow>'
        '<div class="shade"></div>'
        f'<div class="semantic-stage">{semantic_layers}</div>'
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
            target_type = action.get("target_type", "component")
            is_layer_asset = any(
                item.get("object_id") == target and item.get("variant") == "layer-asset"
                for item in program.get("semantic_objects", [])
            )
            target_selector = (
                f'{selector} .semantic-object[data-object-id="{target}"]'
                if target_type == "semantic" else f"{selector} .{target}"
            )
            if effect == "camera_push":
                lines.append(f"tl.fromTo('{target_selector}',{{scale:1.035,x:-18}},{{scale:1.105,x:18,duration:{move:.3f},ease:'sine.inOut'}},{cursor:.3f});")
                lines.append(f"tl.to('{target_selector}',{{x:14,scale:1.1,duration:{settle:.3f},ease:'sine.out'}},{cursor + duration - settle:.3f});")
            elif effect == "camera_pull":
                lines.append(f"tl.fromTo('{target_selector}',{{scale:1.12}},{{scale:1.02,duration:{move:.3f},ease:'sine.inOut'}},{cursor:.3f});")
            elif effect == "reveal" and target == "scene-title":
                lines.append(f"tl.fromTo('{selector} .scene-title, {selector} .function-label',{{y:28,opacity:0}},{{y:0,opacity:1,duration:{min(.55, enter):.3f},stagger:.08,ease:'power2.out'}},{cursor + .08:.3f});")
            elif effect == "reveal":
                lines.append(f"tl.fromTo('{target_selector}',{{y:42,opacity:0}},{{y:0,opacity:1,duration:{min(.7, enter):.3f},ease:'power2.out'}},{cursor + enter:.3f});")
                lines.append(f"tl.fromTo('{target_selector} i',{{y:28,opacity:0}},{{y:0,opacity:1,duration:.45,stagger:.09,ease:'power2.out'}},{cursor + enter + .12:.3f});")
            elif effect == "emphasize":
                lines.append(f"tl.fromTo('{target_selector}',{{scale:.45,opacity:0}},{{scale:1,opacity:.9,duration:{min(.6, enter):.3f},ease:'back.out(1.35)'}},{cursor + enter:.3f});")
            elif effect == "path_follow":
                if is_layer_asset:
                    lines.append(f"tl.fromTo('{target_selector}',{{x:-10,y:1,opacity:1}},{{x:18,y:-1,opacity:1,duration:{move:.3f},ease:'power1.inOut'}},{cursor + enter:.3f});")
                    lines.append(f"tl.to('{target_selector}',{{x:14,y:0,duration:{settle:.3f},ease:'sine.out'}},{cursor + duration - settle:.3f});")
                else:
                    lines.append(f"tl.fromTo('{target_selector}',{{x:-90,opacity:.2}},{{x:90,opacity:1,duration:{move:.3f},ease:'power1.inOut'}},{cursor + enter:.3f});")
                    lines.append(f"tl.to('{target_selector}',{{x:72,duration:{settle:.3f},ease:'sine.out'}},{cursor + duration - settle:.3f});")
            elif effect == "state_change":
                lines.append(f"tl.fromTo('{target_selector} i',{{scale:.35,opacity:0}},{{scale:1,opacity:1,duration:.42,stagger:.1,ease:'back.out(1.2)'}},{cursor + enter:.3f});")
                lines.append(f"tl.to('{target_selector} i:nth-child(n+5)',{{scale:.5,opacity:.22,duration:{min(.8, settle):.3f},stagger:.06,ease:'sine.inOut'}},{cursor + enter + move * .55:.3f});")
            elif effect == "group_split":
                lines.append(f"tl.fromTo('{target_selector} i',{{x:(i)=>(i-3.5)*62,y:(i)=>(i%2?50:-36),rotation:(i)=>(i-3)*7}},{{x:0,y:0,rotation:0,duration:{move:.3f},stagger:.04,ease:'power2.inOut'}},{cursor + enter:.3f});")
                lines.append(f"tl.to('{target_selector}',{{scale:.62,duration:{settle:.3f},ease:'back.out(1.1)'}},{cursor + duration - settle:.3f});")
            elif effect == "pulse":
                lines.append(f"tl.fromTo('{target_selector}',{{scale:.82,opacity:.55}},{{scale:1.14,opacity:1,duration:{max(.45, move * .45):.3f},yoyo:true,repeat:1,ease:'sine.inOut'}},{cursor + enter:.3f});")
            elif effect == "reaction":
                notice = min(.45, max(.2, move * .22))
                lines.append(f"tl.fromTo('{target_selector}',{{x:0,y:0,rotation:0,scale:1}},{{x:5,y:-7,rotation:.35,scale:1.012,duration:{notice:.3f},ease:'power2.out'}},{cursor + enter:.3f});")
                lines.append(f"tl.to('{target_selector}',{{x:3,y:-4,rotation:.12,scale:1.006,duration:{max(.35, settle):.3f},ease:'sine.out'}},{cursor + enter + notice:.3f});")
            elif effect == "hold":
                lines.append(f"tl.set('{target_selector}',{{opacity:1}},{cursor + enter:.3f});")
            elif effect == "progress":
                lines.append(f"tl.fromTo('{target_selector}',{{scaleX:0}},{{scaleX:1,duration:{max(.5, duration - .35):.3f},ease:'none'}},{cursor + .15:.3f});")
        if program.get("motion_style_id") in {"narrative", "educational_info"}:
            lines.append(f"tl.fromTo('{selector} .scene-title',{{y:22,opacity:0}},{{y:0,opacity:1,duration:{min(.55, enter):.3f},ease:'power2.out'}},{cursor + .08:.3f});")
        if program.get("motion_style_id") == "educational_info":
            lines.append(f"tl.fromTo('{selector} .diagram-label',{{opacity:0,scale:.88}},{{opacity:1,scale:1,duration:.45,stagger:.25,ease:'power2.out'}},{cursor + enter:.3f});")
        if program.get("local_visual"):
            lines.extend(local_timeline_lines(selector, cursor, duration, program))
        cursor += duration
    return "".join(lines) + "window.__timelines['astra-motion-segment']=tl;"


def compile_project(scenes: list[Any], project: Path, settings: Any) -> None:
    assets = project / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    gsap = RUNTIME / "node_modules" / "gsap" / "dist" / "gsap.min.js"
    if not gsap.is_file():
        raise RuntimeError("Pinned GSAP runtime is not installed")
    shutil.copy2(gsap, assets / "gsap.min.js")
    programs = [compile_scene_program(scene) for scene in scenes]
    for scene, program in zip(scenes, programs):
        shutil.copy2(Path(scene.image_path), assets / f"{scene.id}.png")
        if program.get("background_path"):
            shutil.copy2(Path(program["background_path"]), assets / f"{scene.id}--background.png")
        for item in program.get("semantic_objects", []):
            if item.get("asset_path"):
                shutil.copy2(Path(item["asset_path"]), assets / f'{scene.id}--{item["object_id"]}.png')
    duration = sum(float(scene.duration_seconds) for scene in scenes)
    meta = {"name": "astra-motion-segment", "description": "Astra scene contract render", "duration": duration, "resolution": {"width": settings.width, "height": settings.height}, "fps": settings.fps}
    (project / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (project / "scene-program.json").write_text(json.dumps({"scenes": programs}, ensure_ascii=False, indent=2), encoding="utf-8")
    styles = """
@font-face{font-family:'Astra Noto';src:local('Noto Sans CJK KR');font-style:normal;font-weight:100 900}*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#12232b;font-family:'Astra Noto',sans-serif}.scene{position:absolute;inset:0;overflow:hidden;opacity:0;background:#173642;color:#fff}.is-disabled{display:none!important}.scene-image{position:absolute;inset:-5%;width:110%;height:110%;object-fit:cover}.shade{position:absolute;inset:0;background:linear-gradient(90deg,rgba(10,24,30,.8),rgba(10,24,30,.08) 58%,rgba(10,24,30,.45))}.function-label{position:absolute;left:84px;top:72px;padding:10px 16px;border-left:7px solid #f4c453;background:rgba(13,32,40,.72);font-size:24px;font-weight:800}h2{position:absolute;left:84px;top:145px;width:880px;margin:0;font-size:58px;line-height:1.18}.evidence-card{position:absolute;right:110px;top:210px;width:390px;height:270px;border:8px solid #172a33;background:rgba(246,239,217,.94);padding:48px}.evidence-card i{display:block;height:24px;margin:0 0 28px;background:#4da5a9}.evidence-card i:nth-child(2){width:72%;background:#f06449}.evidence-card i:nth-child(3){width:88%;background:#efc95e}.accent-orbit{position:absolute;right:250px;top:520px;width:110px;height:110px;border:14px solid #f06449;border-radius:50%;box-shadow:0 0 0 24px rgba(239,201,94,.75)}.caption{position:absolute;left:84px;right:84px;bottom:58px;min-height:98px;padding:22px 28px;background:rgba(7,19,24,.68);font-size:34px;line-height:1.35}.progress-line{position:absolute;left:84px;right:84px;bottom:40px;height:8px;background:#efc95e;transform-origin:left}.layout-split h2{width:720px}.layout-split .scene-image{left:44%;width:66%}.layout-comparison .evidence-card{width:480px;height:320px}.layout-process .progress-line{height:14px}.layout-diagram .scene-image{filter:saturate(.82) contrast(1.05)}
.semantic-stage{position:absolute;inset:0;z-index:2;pointer-events:none}.semantic-object{position:absolute;left:55%;top:43%;width:330px;height:230px;transform-origin:center;filter:drop-shadow(0 12px 24px rgba(5,15,20,.35))}.semantic-object i{position:absolute;display:block;background:#efc95e;border:4px solid rgba(21,43,51,.92)}.semantic-cards{display:grid;grid-template-columns:repeat(4,68px);gap:14px;width:314px;height:auto}.semantic-cards i{position:relative;width:68px;height:82px;border-radius:7px;background:linear-gradient(145deg,#f7e7b0,#d99c3d)}.semantic-cards i:nth-child(2n){transform:rotate(5deg)}.semantic-cards i:nth-child(3n){background:linear-gradient(145deg,#e2eef0,#7495a2)}.semantic-sparks{left:55%;top:35%;width:360px;height:300px}.semantic-sparks i{left:50%;top:50%;width:22px;height:22px;border:0;background:#f8cf5b;clip-path:polygon(50% 0,61% 36%,100% 50%,61% 64%,50% 100%,39% 64%,0 50%,39% 36%)}.semantic-sparks i:nth-child(1){transform:translate(-170px,-90px)}.semantic-sparks i:nth-child(2){transform:translate(-70px,-132px)}.semantic-sparks i:nth-child(3){transform:translate(80px,-116px)}.semantic-sparks i:nth-child(4){transform:translate(150px,-35px)}.semantic-sparks i:nth-child(5){transform:translate(132px,88px)}.semantic-sparks i:nth-child(6){transform:translate(30px,118px)}.semantic-sparks i:nth-child(7){transform:translate(-105px,104px)}.semantic-sparks i:nth-child(8){transform:translate(-155px,20px)}.semantic-bar{left:25%;top:52%;width:58%;height:70px;border-radius:40px;background:rgba(217,229,226,.25);border:4px solid rgba(224,238,235,.35)}.semantic-bar i{position:relative;display:none}.semantic-bar i:first-child{display:block;left:0;top:0;width:20%;height:100%;border:0;border-radius:36px;background:linear-gradient(90deg,#d98f28,#f8cf5b);box-shadow:0 0 40px rgba(248,207,91,.6)}.semantic-path{left:46%;top:64%;width:43%;height:14px;border-radius:12px;background:linear-gradient(90deg,rgba(248,207,91,.15),#f8cf5b);transform:rotate(-9deg);transform-origin:left}.semantic-path i{display:none}.semantic-actor{left:57%;top:43%;width:54px;height:170px;border-radius:30px 30px 18px 18px;background:#f0c55a;border:5px solid #172a33}.semantic-actor:before{content:'';position:absolute;left:7px;top:-46px;width:32px;height:32px;border-radius:50%;background:#f0c55a;border:5px solid #172a33}.semantic-actor i{display:none}.semantic-symbol{width:110px;height:110px;border:10px solid #efc95e;border-radius:50%}.semantic-symbol i{display:none}.function-label,h2,.caption,.progress-line{z-index:4}.caption{z-index:5}
.semantic-layer-asset{inset:-5%;left:-5%;top:-5%;width:110%;height:110%;filter:none}.semantic-layer-asset img{display:block;width:100%;height:100%;object-fit:cover}.depth-background{z-index:1}.depth-midground{z-index:2}.depth-foreground{z-index:3}
.semantic-object[data-object-id="calendar-pages"]{left:66%;top:28%}.semantic-object[data-object-id="novel-memory-cards"]{left:15%;top:38%}.semantic-object[data-object-id="routine-cards"]{left:67%;top:38%}.semantic-object[data-object-id="memory-cards"]{left:43%;top:38%}.semantic-object[data-object-id="time-segment"]{left:42%;top:51%;width:16%}.semantic-object[data-object-id="child-year-segment"]{left:15%;top:56%;width:28%}.semantic-object[data-object-id="adult-year-segment"]{left:58%;top:56%;width:36%}.semantic-object[data-object-id="life-bar"]{left:22%;top:55%;width:70%}.semantic-object[data-object-id="walker"]{left:62%;top:45%}.semantic-object[data-object-id="memory-fragments"]{left:60%;top:25%}.semantic-object[data-object-id="new-path"],.semantic-object[data-object-id="vacation-path"]{left:38%;top:67%;width:52%}
.semantic-stage .semantic-layer-asset{inset:-5%;left:-5%;top:-5%;width:110%;height:110%}
/* 0.8 treatments retain the scene image as design context and animate authored objects. */
.style-narrative .shade{background:linear-gradient(0deg,rgba(7,22,26,.72),transparent 42%)}
.style-narrative .scene-title{top:auto;bottom:195px;left:84px;width:min(1180px,82%);font-size:54px;text-shadow:0 3px 14px #07161d}
.style-narrative .caption{background:rgba(8,24,28,.78)}
.style-narrative .semantic-object:not(.semantic-layer-asset){display:none}
.style-educational_info{background:#f5f8f4;color:#172e35}
.style-educational_info .scene-image{left:50%;width:55%;opacity:.7;filter:saturate(.78)}
.style-educational_info .shade{background:linear-gradient(90deg,#f5f8f4 5%,rgba(245,248,244,.94) 42%,rgba(245,248,244,.1) 100%)}
.style-educational_info .scene-title{top:78px;left:78px;width:42%;max-height:154px;overflow:hidden;font-size:49px;line-height:1.16}
.style-educational_info .diagram-board{position:absolute;top:210px;right:5%;bottom:180px;left:48%;z-index:4;pointer-events:none}
.diagram-board{display:none}.style-educational_info .diagram-board{display:block}
.diagram-label{position:absolute;max-width:320px;padding:14px 18px;border-left:6px solid #e46848;background:#fff;color:#17333a;font-size:27px;font-weight:750;line-height:1.25;box-shadow:0 6px 18px rgba(12,41,46,.14)}
.style-educational_info .semantic-object:not(.semantic-layer-asset){left:5%;top:calc(29% + var(--object-index) * 125px);width:37%;height:auto;min-height:90px;padding:14px 18px;border:3px solid #17333a;background:#fff;color:#17333a;filter:none}
.style-educational_info .semantic-object:not(.semantic-layer-asset) i{display:none}
.style-educational_info .semantic-object .object-role,.style-educational_info .semantic-object strong{display:block;font-size:21px}
.style-educational_info .semantic-object strong{font-size:26px}
.style-educational_info .caption{color:#fff;background:#18343a}
@media (max-aspect-ratio:1/1){
  .style-narrative .scene-title{left:55px;right:55px;width:auto;bottom:260px;max-height:180px;overflow:hidden;font-size:45px}
  .style-educational_info .scene-title{left:55px;right:55px;width:auto;max-height:180px;font-size:43px}
  .style-educational_info .diagram-board{left:8%;right:8%;top:360px;bottom:360px}
  .style-educational_info .scene-image{left:0;width:100%;opacity:.45}
  .style-educational_info .shade{background:linear-gradient(0deg,#f5f8f4 4%,rgba(245,248,244,.56) 55%,#f5f8f4)}
  .style-educational_info .semantic-object:not(.semantic-layer-asset){left:8%;top:calc(45% + var(--object-index) * 120px);width:72%}
  .style-narrative .caption,.style-educational_info .caption{left:55px;right:55px;font-size:29px}
}
"""
    styles += local_styles()
    body = "".join(_scene_html(scene, index, program) for index, (scene, program) in enumerate(zip(scenes, programs), 1))
    document = f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>Astra Motion</title><script src="assets/gsap.min.js"></script><style>{styles}</style></head><body><div id="master" data-composition-id="astra-motion-segment" data-width="{settings.width}" data-height="{settings.height}" data-start="0" data-duration="{duration:.6f}" data-fps="{settings.fps}">{body}</div><script>{_timeline_js(scenes, programs)}</script></body></html>'
    (project / "index.html").write_text(document, encoding="utf-8")


async def render_segment(scenes: list[Any], output: Path, settings: Any, config: dict[str, object], process: Any) -> None:
    project = output.with_suffix("")
    if project.exists():
        shutil.rmtree(project)
    project.mkdir(parents=True)
    compile_project(scenes, project, settings)
    cli = RUNTIME / "node_modules" / ".bin" / "hyperframes"
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
