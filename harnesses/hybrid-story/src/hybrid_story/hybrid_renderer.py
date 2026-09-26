from __future__ import annotations

import html
import json
import shutil
import textwrap
from pathlib import Path
from app.harness_sdk.hybrid import HybridScene
from app.harness_sdk.film_design import shared_design, design_sha256
from .illustrated_transport import composition_markup
from .effects.camera import camera_window
from .semantic_diagrams import markup as semantic_markup
from .snapshot_diagram import markup as snapshot_markup
from .spatial_diagram import markup as spatial_markup, poster as spatial_poster

RUNTIME = Path("/app/hyperframes-runtime")


def diagram_poster(scene, output, width, height):
    from PIL import Image, ImageDraw, ImageFont
    hybrid = HybridScene.model_validate(scene.layout["hybrid"])
    diagram = hybrid.diagram
    palette = hybrid.design.palette if hybrid.design else None
    if diagram is None:
        raise ValueError("diagram_required")
    image = Image.new("RGB", (width, height), palette.background if palette else "#f4f7f7")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", max(20, width // 45))
    draw.text((width * .07, height * .07), diagram.title, fill=palette.text if palette else "#172923", font=font)
    if diagram.spatial_map:
        spatial_poster(draw,diagram.spatial_map,width,height,font,palette)
        image.save(output,format='PNG')
        return
    if diagram.snapshot_pair:
        pair=diagram.snapshot_pair
        draw.text((width*.07,height*.18),f'{pair.entity} · {pair.metric}',fill=palette.text,font=font)
        for i,state in enumerate((pair.before,pair.after)):
            x=width*(.3+i*.4); top=height*.7-height*.3*state.value/pair.scale_max
            draw.rectangle((x-width*.05,top,x+width*.05,height*.7),fill=pair.color)
            draw.text((x,height*.75),f'{state.time_label}: {state.value:g} {pair.unit}',fill=palette.text,font=font,anchor='mt')
        image.save(output,format='PNG')
        return
    nodes = {n.id: n for n in diagram.nodes}
    for edge in diagram.edges:
        a, b = nodes[edge.source], nodes[edge.target]
        draw.line((a.x * width, a.y * height, b.x * width, b.y * height), fill=palette.line if palette else "#5d7878", width=max(2, width // 320))
    for node in diagram.nodes:
        cx, cy = node.x * width, node.y * height
        draw.ellipse((cx - width * .025, cy - width * .025, cx + width * .025, cy + width * .025), fill=node.color)
        draw.text((cx, cy + height * .045), node.label, fill=palette.text if palette else "#172923", font=font, anchor="mt")
    image.save(output, format="PNG")


def _text(value, x, y, css="label"):
    lines = textwrap.wrap(value, 14, break_long_words=True)
    return f'<text x="{x}" y="{y}" class="{css}" text-anchor="middle">' + ''.join(
        f'<tspan x="{x}" dy="{0 if i == 0 else 24}">{html.escape(line)}</tspan>' for i, line in enumerate(lines)) + '</text>'


def diagram_markup(diagram, index, duration, cursor, design=None):
    parts, actions = [], []
    nodes = {n.id: n for n in diagram.nodes}
    selector = f"#shot-{index}"
    for j, edge in enumerate(diagram.edges):
        a, b = nodes[edge.source], nodes[edge.target]
        x1, y1, x2, y2 = a.x * 1000, a.y * 600, b.x * 1000, b.y * 600
        parts.append(f'<path id="edge-{index}-{j}" d="M{x1},{y1} L{x2},{y2}" pathLength="1" class="edge" marker-end="url(#arrow-{index})"/>')
        parts.append(_text(edge.label, (x1 + x2) / 2, (y1 + y2) / 2 - 22, "edge-label"))
        start, span = cursor + duration * edge.start_at, duration * (edge.end_at - edge.start_at)
        actions.append(f"tl.fromTo('#edge-{index}-{j}',{{strokeDashoffset:1}},{{strokeDashoffset:0,duration:{span}}},{start});")
        if diagram.grammar == "transport_track":
            parts.append(f'<circle id="parcel-{index}-{j}" cx="{x1}" cy="{y1}" r="9" fill="{a.color}"/>')
            actions.append(f"tl.fromTo('#parcel-{index}-{j}',{{attr:{{cx:{x1},cy:{y1}}},opacity:0}},{{attr:{{cx:{x2},cy:{y2}}},opacity:1,duration:{span},ease:'none'}},{start});")
    for j, node in enumerate(diagram.nodes):
        x, y = node.x * 1000, node.y * 600
        shape = f'<circle cx="{x}" cy="{y}" r="20" fill="{node.color}"/>'
        if diagram.grammar == "quantitative_comparison":
            bar_height = 120 * node.quantity / diagram.comparison_scale_max
            shape = f'<rect x="{x-30}" y="{y-bar_height}" width="60" height="{bar_height}" fill="{node.color}"/>'
            shape += _text(f'{node.quantity:g} {node.unit}', x, y - bar_height - 15, "quantity")
        parts.append(f'<g id="node-{index}-{j}">{shape}{_text(node.label,x,y+46)}'
                     f'<g id="before-{index}-{j}">{_text(node.before,x,y+100,"state")}</g>'
                     f'<g id="after-{index}-{j}" opacity="0">{_text(node.after,x,y+100,"state")}</g></g>')
        actions += [f"tl.fromTo('#node-{index}-{j}',{{opacity:0}},{{opacity:1,duration:.25}},{cursor + duration * node.reveal_at});",
                    f"tl.to('#before-{index}-{j}',{{opacity:0,duration:.2}},{cursor + duration * node.change_at});",
                    f"tl.to('#after-{index}-{j}',{{opacity:1,duration:.2}},{cursor + duration * node.change_at});"]
    title = html.escape(diagram.title)
    arrow = design.palette.line if design else "#5d7878"
    return (f'<h2>{title}</h2><svg viewBox="0 0 1000 600" aria-label="{title}"><defs><marker id="arrow-{index}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10" fill="{arrow}"/></marker></defs>{"".join(parts)}</svg>', actions)


def compile_project(scenes, project, settings):
    design = shared_design(scenes)
    assets = project / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(RUNTIME / "node_modules/gsap/dist/gsap.min.js", assets / "gsap.min.js")
    shutil.copy2(RUNTIME / "node_modules/gsap/dist/MotionPathPlugin.min.js", assets / "MotionPathPlugin.min.js")
    sections, actions, programs = [], [], []
    cursor = 0.0
    for index, scene in enumerate(scenes):
        hybrid = HybridScene.model_validate(scene.layout["hybrid"])
        if hybrid.version in {"hybrid-scene-0.4", "hybrid-scene-0.5", "hybrid-scene-0.6"} and hybrid.route != "cinematic":
            if (scene.layout.get("camera") or {}).get("mode", "hold") != "hold":
                raise ValueError("local_route_requires_fixed_camera")
        duration = float(scene.duration_seconds)
        if duration <= 0:
            raise ValueError("measured_duration_required")
        content = ""
        camera_program = None
        if hybrid.route == "diagram":
            if hybrid.composition is not None:
                content, motion = composition_markup(scene, hybrid, assets, index, duration, cursor, settings.width, settings.height)
            elif hybrid.diagram.grammar == 'before_after':
                content,motion=snapshot_markup(hybrid.diagram,index,duration,cursor,design)
            elif hybrid.diagram.grammar == 'map_spatial':
                content,motion=spatial_markup(hybrid.diagram,index,duration,cursor,design)
            elif hybrid.version in {"hybrid-scene-0.3", "hybrid-scene-0.4", "hybrid-scene-0.5", "hybrid-scene-0.6"} and hybrid.diagram.grammar in {"quantitative_comparison", "cumulative_change", "step_sequence"}:
                content, motion = semantic_markup(hybrid.diagram, index, duration, cursor, design)
            else:
                content, motion = diagram_markup(hybrid.diagram, index, duration, cursor, design)
            actions.extend(motion)
        else:
            shutil.copy2(Path(scene.image_path), assets / f"shot-{index}.png")
            content = f'<img class="scene-image" src="assets/shot-{index}.png" alt="">'
            if hybrid.route == "source":
                proof = scene.layout.get("hybrid_source") or {}
                if proof.get("prepared_by") != "trusted_source_registry" or proof.get("id") != hybrid.source_id:
                    raise ValueError("source_runtime_provenance_required")
                import hashlib
                if hashlib.sha256(Path(scene.image_path).read_bytes()).hexdigest() != proof.get("prepared_sha256"):
                    raise ValueError("source_runtime_hash_mismatch")
                label = " · ".join(proof[key] for key in ("date_label", "attribution"))
                content += f'<div class="source-label">{html.escape(label)}</div>'
            else:
                camera_program = camera_window(scene, duration, .035)
                if camera_program is not None:
                    strength = camera_program["strength"]
                    scale_start, scale_end = ((1, 1 + strength) if camera_program["mode"] == "push"
                                              else (1 + strength, 1))
                    focus = camera_program["focus"]
                    start = cursor + camera_program["lead_seconds"]
                    travel = camera_program["travel_seconds"]
                    actions.append(f"tl.fromTo('#shot-{index} .scene-image',"
                        f"{{scale:{scale_start},transformOrigin:'{focus[0]*100}% {focus[1]*100}%'}},"
                        f"{{scale:{scale_end},duration:{travel},ease:'sine.inOut'}},{start});")
                content += '<div class="source-label">AI 재현 삽화</div>'
        sections.append(f'<section id="shot-{index}" class="shot {hybrid.route}">{content}</section>')
        actions += [f"tl.set('#shot-{index}',{{opacity:1}},{cursor});", f"tl.set('#shot-{index}',{{opacity:0}},{cursor+duration});"]
        programs.append({"scene_id": scene.id, "start": cursor, "duration": duration,
                         "camera_window": camera_program, **hybrid.model_dump(mode="json")})
        cursor += duration
    styles = """*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#f4f7f7;font-family:'Noto Sans CJK KR',sans-serif}.shot{position:absolute;inset:0;opacity:0;overflow:hidden;background:#f4f7f7}.scene-image{width:100%;height:100%;object-fit:cover}.source{background:#161c1b}.source .scene-image{object-fit:contain}.source-label{position:absolute;top:3%;left:4%;right:4%;font-size:20px;color:white;background:#162522dd;padding:8px 12px;line-height:1.3}h2{position:absolute;left:6%;top:4%;right:6%;font-size:34px;color:#172923;margin:0}svg{position:absolute;inset:0;width:100%;height:100%}.label{font-size:25px;font-weight:700;fill:#172923}.state{font-size:21px;fill:#425753}.quantity{font-size:22px;fill:#172923}.edge-label{font-size:18px;fill:#425753}.edge{stroke:#5d7878;stroke-width:4;fill:none;stroke-dasharray:1;stroke-dashoffset:1}"""
    styles += ".composition-plate{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}"
    if design:
        p, t = design.palette, design.typography
        styles += (f"html,body,.shot,.source{{background:{p.background};font-family:'{t.font}',sans-serif}}"
            f"h2{{color:{p.text};font-size:{t.title_px}px}}"
            f".label,.quantity{{fill:{p.text}}}.state,.edge-label{{fill:{p.secondary_text}}}"
            f".edge{{stroke:{p.line};stroke-width:{design.line_width}}}"
            f".source-label{{color:{p.text};background:{p.surface}}}")
        treatment = getattr(design, "type_treatment", None)
        if treatment == "documentary":
            styles += "h2{font-family:'Noto Serif CJK KR',serif;font-weight:600}.source-label{font-weight:400}"
        elif treatment == "editorial":
            styles += "h2{font-weight:800}.source-label{font-weight:600}"
        elif treatment == "explainer":
            styles += "h2{font-weight:700}.source-label{font-weight:500}"
        (project / "design.json").write_text(json.dumps({"sha256": design_sha256(design),
            "contract": design.model_dump(mode="json"), "scope": "Rendered graphics and text; image pixels are not recolored"},
            ensure_ascii=False, indent=2), encoding="utf-8")
    metadata = {"name": "hybrid-story-segment", "duration": cursor,
                "resolution": {"width": settings.width, "height": settings.height}, "fps": settings.fps}
    (project / "meta.json").write_text(json.dumps(metadata), encoding="utf-8")
    (project / "program.json").write_text(json.dumps(programs, ensure_ascii=False, indent=2), encoding="utf-8")
    timeline = "gsap.registerPlugin(MotionPathPlugin);window.__timelines=window.__timelines||{};const tl=gsap.timeline({paused:true});" + "".join(actions) + "window.__timelines['hybrid-story-segment']=tl;"
    fonts = ("@font-face{font-family:'Noto Sans CJK KR';src:local('Noto Sans CJK KR');font-weight:100 900;font-style:normal}"
             "@font-face{font-family:'Noto Serif CJK KR';src:local('Noto Serif CJK KR');font-weight:100 900;font-style:normal}")
    root_style = f'#master{{position:relative;width:{settings.width}px;height:{settings.height}px;overflow:hidden}}'
    document = f'<!doctype html><html lang="ko"><head><meta charset="utf-8"><script src="assets/gsap.min.js"></script><script src="assets/MotionPathPlugin.min.js"></script><style>{fonts}{styles}{root_style}</style></head><body><div id="master" data-composition-id="hybrid-story-segment" data-width="{settings.width}" data-height="{settings.height}" data-duration="{cursor}" data-start="0" data-fps="{settings.fps}">{"".join(sections)}</div><script>{timeline}</script></body></html>'
    (project / "index.html").write_text(document, encoding="utf-8")


async def render_hybrid(scenes, subtitles, output, settings, config, process):
    import uuid
    project = output.parent / f"{output.stem}-project-{uuid.uuid4().hex[:8]}"
    project.mkdir(parents=True)
    compile_project(scenes, project, settings)
    visual = project / "visual.mp4"
    await process.run([str(RUNTIME / "node_modules/.bin/hyperframes"), "render", f"--output={visual}",
        "--quality=looks", "--workers=1", "--low-memory-mode", "--strict", str(project)], cwd=RUNTIME, timeout=1800)
    if getattr(settings, "subtitles_enabled", True):
        path = subtitles.as_posix().replace("'", r"\'").replace(":", r"\:")
        await process.run(["ffmpeg", "-v", "error", "-y", "-i", str(visual), "-vf", f"subtitles=filename='{path}'",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", settings.ffmpeg_preset, "-an", str(output)], timeout=600)
    else:
        shutil.copy2(visual, output)
