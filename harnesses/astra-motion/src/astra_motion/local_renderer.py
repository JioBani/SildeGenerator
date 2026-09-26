"""Editable vector scenes for the isolated, provider-free motion path.

The figure has limited gaze/head/face/body cues, not a certified actor rig.
"""
from __future__ import annotations

import html
from typing import Any


def local_scene_html(scene: Any, index: int, program: dict[str, Any]) -> str:
    visual = program["local_visual"]
    if visual.get("mode") == "directed":
        objects = visual.get("objects", [])
        defaults = {
            "world": (.1, .02, .8, .95), "land": (.04, .38, .92, .28),
            "marker": (.46, .34, .08, .13), "satellite": (.38, .1, .24, .16),
            "orbit": (.12, .1, .76, .32), "distance": (.16, .4, .68, .18),
            "vertical_distance": (.47, .3, .06, .3),
            "people": (.08, .68, .84, .15),
            "frame_set": (.13, .2, .74, .46), "eye": (.43, .34, .14, .13),
            "balanced_panel": (.07, .2, .4, .52), "offset_panel": (.53, .2, .4, .52),
            "cloud": (.27, .25, .46, .32), "grid": (.16, .15, .68, .58),
            "eye_line": (.22, .3, .56, .08), "thirds_line": (.15, .31, .7, .1),
            "pin": (.46, .27, .08, .1), "figure": (.33, .19, .34, .54),
            "path": (.18, .35, .64, .2), "dots": (.2, .27, .6, .34),
            "wave": (.18, .48, .64, .15), "accent": (.47, .25, .12, .18),
            "tilted_frame": (.2, .17, .6, .56), "level_frame": (.2, .17, .6, .56),
            "frame": (.2, .17, .6, .56), "phone": (.35, .13, .3, .63),
            "crosshair": (.18, .2, .64, .5), "weights": (.28, .3, .44, .36),
        }
        shapes = []
        for position, item in enumerate(objects):
            primitive = str(item.get("primitive", "unsupported"))
            raw_bounds = item.get("bounds")
            x, y, width, height = raw_bounds if isinstance(raw_bounds, list) and len(raw_bounds) == 4 else defaults.get(primitive, (.2, .2, .6, .5))
            bounds = f"left:{max(0, min(90, float(x) * 100)):.1f}%;top:{max(0, min(90, float(y) * 100)):.1f}%;width:{max(5, min(100, float(width) * 100)):.1f}%;height:{max(5, min(100, float(height) * 100)):.1f}%"
            shapes.append(
                f'<div class="directed-object directed-object-{position} primitive-{html.escape(primitive, quote=True)}" '
                f'style="{bounds}" aria-label="{html.escape(str(item.get("label", "")), quote=True)}">'
                '<div class="directed-art"><i></i><i></i><i></i></div></div>'
            )
        graphics = "".join(shapes)
        labels = "".join(f'<span class="directed-label">{html.escape(value)}</span>'
                         for value in visual.get("labels", []))
        return (
            f'<section id="scene-{index}" class="scene local-scene directed-scene '
            f'directed-{html.escape(program["motion_style_id"] or "narrative", quote=True)} '
            f'directed-theme-{html.escape(str(visual.get("theme", "general")), quote=True)}">'
            f'<img class="scene-image" src="assets/{html.escape(scene.id, quote=True)}.png" alt="">'
            f'<h2 class="directed-heading">{html.escape(str(visual.get("heading", "")))}</h2>'
            f'<div class="directed-stage">{graphics}</div><div class="directed-labels">{labels}</div>'
            f'<div class="caption">{html.escape(scene.narration.strip())}</div></section>'
        )
    theme = visual.get("theme", "general")
    beat = visual.get("beat", "experience")
    image = f"assets/{html.escape(scene.id, quote=True)}.png"
    caption = html.escape(scene.narration.strip())
    if program["motion_style_id"] == "narrative":
        person = (
            '<div class="local-person"><div class="person-shadow"></div><div class="person-body">'
            '<div class="person-leg leg-back"></div><div class="person-leg leg-front"></div>'
            '<div class="person-arm arm-back"></div><div class="person-torso"><i class="shirt-mark"></i></div>'
            '<div class="person-neck"></div><div class="person-head"><div class="person-hair"></div>'
            '<div class="person-ear"></div><div class="person-brow brow-a"></div>'
            '<div class="person-brow brow-b"></div><div class="person-eye eye-a"><i></i></div>'
            '<div class="person-eye eye-b"><i></i></div><div class="person-nose"></div>'
            '<div class="person-mouth"></div></div><div class="person-arm arm-front"></div>'
            '</div></div>'
        )
        if theme == "spotlight":
            crowd = "".join(
                f'<div class="bystander bystander-{number}"><i class="bystander-head"></i>'
                '<i class="bystander-body"></i><i class="bystander-phone"></i></div>'
                for number in range(1, 5)
            )
            mode = visual.get("mode", "incident")
            note = {
                "incident": "작은 자국",
                "definition": "스포트라이트 효과",
                "imagined_gaze": "모두가 볼 것 같은 느낌",
                "evidence": "기억한 사람은 절반 미만",
                "question": "왜 그럴까?",
                "others_busy": "각자 자기 일에 집중",
                "realization": "상상과 현실의 차이",
                "release": "시선에서 벗어나기",
            }.get(mode, "")
            visual_html = (
                '<div class="spotlight-stage"><div class="spotlight-cone"></div>'
                '<div class="spotlight-crowd">' + crowd + '</div>'
                '<div class="imagined-rays"><i></i><i></i><i></i></div>'
                '<div class="spotlight-evidence"><strong>&lt; 50%</strong><span>타인의 차림새를 기억</span></div>'
                f'<div class="spotlight-note">{html.escape(note)}</div>'
                '</div>' + person
            )
        else:
            objects = "".join(
                f'<div class="local-prop local-prop-{number}"><span class="prop-body"></span>'
                '<i class="wheel wheel-a"></i><i class="wheel wheel-b"></i></div>'
                for number in range(1, 5)
            )
            visual_html = (
                '<div class="local-props">' + objects + '<div class="attention-ring"></div></div>'
                + person + '<div class="local-thinking"><span></span><span></span><span></span></div>'
            )
        scene_class = f"local-narrative theme-{theme} beat-{beat} mode-{visual.get('mode', beat)}"
        heading = ""
    else:
        labels = [html.escape(str(label)[:28]) for label in visual.get("labels", [])[:3]]
        labels += [""] * (3 - len(labels))
        nodes = "".join(
            f'<div class="info-node info-node-{number}"><div class="node-icon">'
            f'<span class="node-symbol">{symbol}</span></div><strong>{label}</strong></div>'
            for number, (label, symbol) in enumerate(zip(labels, ("?", "→", "✓")), 1)
        )
        visual_html = (
            '<div class="info-flow">' + nodes + '<div class="flow-track"></div>'
            '<div class="flow-token"></div><div class="flow-filter"></div></div>'
            '<div class="info-particles">' + "".join('<i></i>' for _ in range(12)) + '</div>'
        )
        scene_class = f"local-education theme-{theme} beat-{beat}"
        heading = f'<h2 class="local-heading">{html.escape(str(visual.get("heading") or scene.viewer_takeaway[:54]))}</h2>'
    return (
        f'<section id="scene-{index}" class="scene local-scene {scene_class}">'
        f'<img class="scene-image" src="{image}" alt="">'
        f'{heading}<div class="local-visual-stage">{visual_html}</div>'
        f'<div class="caption">{caption}</div></section>'
    )


def local_timeline_lines(selector: str, cursor: float, duration: float, program: dict[str, Any]) -> list[str]:
    visual = program["local_visual"]
    if visual.get("mode") == "directed":
        lines = [f"tl.fromTo('{selector} .directed-heading',{{y:22,opacity:0}},{{y:0,opacity:1,duration:.4,ease:'power2.out'}},{cursor + .1:.3f});"]
        lookup = {item["id"]: index for index, item in enumerate(visual.get("objects", []))}
        for order, motion in enumerate(visual.get("motions", [])):
            position = lookup.get(motion["id"])
            if position is None:
                continue
            target = f"{selector} .directed-object-{position}"
            at = cursor + min(duration * .2 + order * .18, duration * .55)
            kind = motion["kind"]
            if kind == "path_follow":
                lines.append(f"tl.fromTo('{target}',{{x:-95,opacity:0}},{{x:0,opacity:1,duration:{min(1.1, duration * .48):.3f},ease:'power2.out'}},{at:.3f});")
            elif visual["objects"][position].get("primitive") == "tilted_frame" and kind == "state_change":
                lines.append(f"tl.fromTo('{target}',{{rotation:0,opacity:.5}},{{rotation:-9,opacity:1,duration:.8,ease:'power2.inOut'}},{at:.3f});")
            elif visual["objects"][position].get("primitive") == "eye_line":
                lines.append(f"tl.fromTo('{target} .directed-art',{{scaleX:0,opacity:0}},{{scaleX:1,opacity:1,duration:.65,ease:'power2.out'}},{at:.3f});")
            elif visual["objects"][position].get("primitive") == "frame_set" and kind == "group_split":
                lines.append(f"tl.fromTo('{target} i',{{y:28,opacity:0}},{{y:0,opacity:1,duration:.38,stagger:.16,ease:'power2.out'}},{at:.3f});")
            elif kind == "pulse":
                lines.append(f"tl.fromTo('{target}',{{scale:.91,opacity:.5}},{{scale:1,opacity:1,duration:.42,yoyo:true,repeat:1,ease:'sine.inOut'}},{at:.3f});")
            elif kind == "group_split":
                lines.append(f"tl.fromTo('{target}',{{y:45,opacity:0}},{{y:0,opacity:1,duration:.6,ease:'power2.out'}},{at:.3f});")
            elif kind == "hold":
                lines.append(f"tl.set('{target}',{{opacity:1}},{at:.3f});")
            else:
                lines.append(f"tl.fromTo('{target}',{{y:24,opacity:0}},{{y:0,opacity:1,duration:.45,ease:'power2.out'}},{at:.3f});")
        return lines
    start = cursor + min(.22, duration * .08)
    move = max(.4, min(duration * .55, 2.0))
    lines: list[str] = []
    if program["motion_style_id"] == "narrative":
        beat = visual.get("beat", "experience")
        if visual.get("theme") == "spotlight":
            mode = visual.get("mode", "incident")
            cue = start + min(.25, duration * .14)
            lines.append(f"tl.fromTo('{selector} .local-person',{{y:14,opacity:0}},{{y:0,opacity:1,duration:.35,ease:'power2.out'}},{start:.3f});")
            lines.append(f"tl.fromTo('{selector} .spotlight-crowd',{{opacity:0}},{{opacity:1,duration:.4,ease:'power2.out'}},{cue:.3f});")
            lines.append(f"tl.fromTo('{selector} .spotlight-note',{{y:18,opacity:0}},{{y:0,opacity:1,duration:.35,ease:'power2.out'}},{cue:.3f});")
            if mode in {"definition", "imagined_gaze", "question"}:
                lines.append(f"tl.fromTo('{selector} .spotlight-cone',{{scaleY:.15,opacity:0}},{{scaleY:1,opacity:1,duration:.5,ease:'power2.out'}},{cue:.3f});")
                lines.append(f"tl.fromTo('{selector} .person-brow',{{y:0}},{{y:-7,duration:.25,ease:'sine.out'}},{cue + .12:.3f});")
            if mode == "imagined_gaze":
                lines.append(f"tl.fromTo('{selector} .imagined-rays i',{{scaleX:0,opacity:0}},{{scaleX:1,opacity:.75,duration:.35,stagger:.08,ease:'power2.out'}},{cue + .15:.3f});")
            if mode == "evidence":
                lines.append(f"tl.fromTo('{selector} .spotlight-evidence',{{scale:.82,opacity:0}},{{scale:1,opacity:1,duration:.5,ease:'back.out(1.15)'}},{cue:.3f});")
            if mode in {"incident", "definition", "imagined_gaze"}:
                lines.append(f"tl.fromTo('{selector} .shirt-mark',{{scale:.7}},{{scale:1.15,duration:.35,yoyo:true,repeat:1,ease:'sine.inOut'}},{cue:.3f});")
            if mode in {"others_busy", "realization", "release"}:
                lines.append(f"tl.fromTo('{selector} .person-mouth',{{rotation:0}},{{rotation:-11,duration:.35,ease:'sine.out'}},{cue + .1:.3f});")
                lines.append(f"tl.fromTo('{selector} .bystander-phone',{{y:12,opacity:0}},{{y:0,opacity:1,duration:.35,stagger:.08,ease:'power2.out'}},{cue:.3f});")
            if mode == "release":
                lines.append(f"tl.to('{selector} .local-person',{{x:42,duration:{min(.9, duration * .4):.3f},ease:'power1.inOut'}},{cue + .15:.3f});")
            return lines
        mouth_turn = -9 if beat == "reflection" else 2 if beat == "explanation" else -3
        head_turn = -5 if beat == "experience" else 2 if beat == "explanation" else -2
        lines.append(f"tl.fromTo('{selector} .local-person',{{y:18,opacity:0}},{{y:0,opacity:1,duration:.55,ease:'power2.out'}},{start:.3f});")
        lines.append(f"tl.fromTo('{selector} .local-prop',{{x:150,opacity:0}},{{x:0,opacity:1,duration:{move:.3f},stagger:.09,ease:'power2.out'}},{start:.3f});")
        lines.append(f"tl.fromTo('{selector} .person-eye i',{{x:0}},{{x:9,duration:.22,ease:'power2.out'}},{start + .34:.3f});")
        lines.append(f"tl.fromTo('{selector} .person-brow',{{y:0}},{{y:-8,duration:.27,ease:'power2.out'}},{start + .52:.3f});")
        lines.append(f"tl.fromTo('{selector} .person-head',{{rotation:0}},{{rotation:{head_turn},duration:.5,ease:'sine.out'}},{start + .68:.3f});")
        lines.append(f"tl.fromTo('{selector} .person-mouth',{{scaleX:.6,rotation:0}},{{scaleX:1,rotation:{mouth_turn},duration:.35,ease:'sine.out'}},{start + .9:.3f});")
        lines.append(f"tl.fromTo('{selector} .person-torso',{{y:0}},{{y:-7,duration:.55,ease:'sine.out'}},{start + 1.05:.3f});")
        lines.append(f"tl.fromTo('{selector} .attention-ring',{{scale:.55,opacity:0}},{{scale:1,opacity:1,duration:.5,ease:'power2.out'}},{start + .6:.3f});")
        lines.append(f"tl.to('{selector} .attention-ring',{{scale:1.13,opacity:.55,duration:.55,ease:'sine.out'}},{start + 1.45:.3f});")
        lines.append(f"tl.fromTo('{selector} .local-thinking span',{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:.35,stagger:.14,ease:'back.out(1.2)'}},{start + 1.1:.3f});")
    else:
        lines.append(f"tl.fromTo('{selector} .local-heading',{{y:24,opacity:0}},{{y:0,opacity:1,duration:.48,ease:'power2.out'}},{start:.3f});")
        lines.append(f"tl.fromTo('{selector} .info-node',{{y:42,opacity:0}},{{y:0,opacity:1,duration:.5,stagger:.38,ease:'power2.out'}},{start + .2:.3f});")
        lines.append(f"tl.fromTo('{selector} .flow-track',{{scaleX:0}},{{scaleX:1,duration:{move:.3f},ease:'power2.inOut'}},{start + .55:.3f});")
        lines.append(f"tl.fromTo('{selector} .flow-token',{{x:-280,opacity:0}},{{x:280,opacity:1,duration:{move:.3f},ease:'power1.inOut'}},{start + .65:.3f});")
        lines.append(f"tl.fromTo('{selector} .flow-filter',{{scale:.75,opacity:0}},{{scale:1,opacity:1,duration:.45,ease:'back.out(1.2)'}},{start + 1.0:.3f});")
        lines.append(f"tl.fromTo('{selector} .info-particles i',{{y:36,opacity:0}},{{y:0,opacity:1,duration:.4,stagger:.06,ease:'power2.out'}},{start + 1.3:.3f});")
    return lines


def local_styles() -> str:
    return """
.directed-theme-film_framing{background:#13242f;color:#f6f3e9}.directed-theme-film_framing .scene-image{opacity:.72}
.directed-theme-film_framing .directed-heading{color:#f6f3e9;text-shadow:0 2px 10px rgba(0,0,0,.35)}
.directed-theme-film_framing .directed-label{background:#1e3540;color:#f6f3e9;border-color:#edb75e}
.directed-theme-film_framing .directed-stage{overflow:visible}
.primitive-frame_set{z-index:2}.primitive-frame_set i{top:12%;width:29%;height:76%;border:5px solid #f1d7a2;background:linear-gradient(#233d48 0 31%,#e8bb69 31% 33%,#233d48 33%);box-shadow:0 10px 24px #07161c}.primitive-frame_set i:first-child{left:0}.primitive-frame_set i:nth-child(2){left:35%}.primitive-frame_set i:nth-child(3){right:0}
.primitive-eye{z-index:5}.primitive-eye .directed-art{border:5px solid #efb967;border-radius:80% 15%;transform:rotate(45deg);background:#f4ead4}.primitive-eye i:first-child{left:38%;top:30%;width:29%;height:40%;border-radius:50%;background:#193845}.primitive-eye i:nth-child(n+2){display:none}
.primitive-balanced_panel,.primitive-offset_panel{z-index:2}.primitive-balanced_panel .directed-art,.primitive-offset_panel .directed-art{border:5px solid #f1d7a2;background:#27424b;box-shadow:inset 0 -22px 0 #1b343e}.primitive-balanced_panel .directed-art:before,.primitive-offset_panel .directed-art:before{content:'';position:absolute;left:50%;top:16%;height:68%;border-left:3px dashed #e8ba64}.primitive-offset_panel .directed-art{transform:rotate(-8deg);border-color:#dc745f}.primitive-offset_panel .directed-art:before{left:60%;border-color:#dc745f}
.primitive-cloud{z-index:4}.primitive-cloud .directed-art{border-radius:50%;background:radial-gradient(ellipse,#becbd0 0,#79939d 55%,transparent 73%);filter:blur(5px)}
.primitive-grid{z-index:2}.primitive-grid .directed-art{border:5px solid #edc27c;background:linear-gradient(90deg,transparent 32%,rgba(237,194,124,.55) 32% 33%,transparent 33% 66%,rgba(237,194,124,.55) 66% 67%,transparent 67%),linear-gradient(transparent 32%,rgba(237,194,124,.55) 32% 33%,transparent 33% 66%,rgba(237,194,124,.55) 66% 67%,transparent 67%)}
.primitive-eye_line,.primitive-thirds_line{z-index:5}.primitive-eye_line .directed-art,.primitive-thirds_line .directed-art{top:50%;height:0;border-top:7px solid #efb967;transform-origin:left}.primitive-thirds_line .directed-art{border-top-style:dashed}
.primitive-pin{z-index:6}.primitive-pin .directed-art{left:30%;width:40%;height:80%;border-radius:50% 50% 15% 15%;background:#eeb969;box-shadow:0 0 0 8px rgba(238,185,105,.2)}
.primitive-figure{z-index:3}.primitive-figure .directed-art{left:25%;width:50%;height:90%;border-radius:45% 45% 8% 8%;background:#d19c73}.primitive-figure .directed-art:before{content:'';position:absolute;left:22%;top:6%;width:56%;height:38%;border-radius:50%;background:#edc7a2}.primitive-figure .directed-art:after{content:'';position:absolute;left:5%;bottom:0;width:90%;height:53%;border-radius:42% 42% 5% 5%;background:#47717a}
.primitive-path{z-index:4}.primitive-path .directed-art{top:44%;height:35%;border-top:6px dashed #e9b766;border-radius:50%}
.primitive-dots{z-index:5}.primitive-dots i{top:35%;width:13%;aspect-ratio:1;border-radius:50%;background:#efb967}.primitive-dots i:first-child{left:5%}.primitive-dots i:nth-child(2){left:44%;background:#dc745f}.primitive-dots i:nth-child(3){right:5%}
.primitive-wave{z-index:4}.primitive-wave .directed-art{top:30%;height:45%;border-top:6px solid #e9b766;border-bottom:6px solid #e9b766;clip-path:polygon(0 50%,10% 50%,15% 5%,23% 95%,31% 30%,40% 70%,50% 10%,60% 90%,70% 30%,80% 65%,90% 50%,100% 50%,100% 100%,0 100%)}
.primitive-accent{z-index:6}.primitive-accent .directed-art{left:37%;width:26%;height:100%;border-radius:8px;background:#dc745f;transform:rotate(35deg)}
.primitive-level_frame,.primitive-tilted_frame,.primitive-frame{z-index:2}.primitive-level_frame .directed-art,.primitive-tilted_frame .directed-art,.primitive-frame .directed-art{border:7px solid #edc27c;background:#28444e;box-shadow:inset 0 -35px 0 #1b333c}.primitive-tilted_frame .directed-art{border-color:#dc745f}
.primitive-phone{z-index:3}.primitive-phone .directed-art{left:12%;width:76%;height:100%;border:9px solid #f0d9aa;border-radius:26px;background:#24414c;box-shadow:inset 0 0 0 10px #142b35}.primitive-phone .directed-art:before{content:'';position:absolute;left:35%;top:3%;width:30%;height:7px;border-radius:5px;background:#f0d9aa}
.primitive-crosshair{z-index:5}.primitive-crosshair .directed-art:before,.primitive-crosshair .directed-art:after{content:'';position:absolute;background:#df7867}.primitive-crosshair .directed-art:before{left:49%;top:0;width:2%;height:100%}.primitive-crosshair .directed-art:after{left:0;top:49%;width:100%;height:2%}
.primitive-weights{z-index:4}.primitive-weights .directed-art:before{content:'';position:absolute;left:8%;top:28%;width:84%;height:5px;background:#efb967;transform:rotate(-8deg)}.primitive-weights i{bottom:8%;width:25%;height:42%;background:#e4ad5d;clip-path:polygon(50% 0,100% 100%,0 100%)}.primitive-weights i:first-child{left:3%}.primitive-weights i:nth-child(2){right:3%;background:#dc745f}.primitive-weights i:nth-child(3){display:none}
.directed-scene .scene-image{opacity:.55}.directed-heading{position:absolute;left:6%;top:8%;width:88%;max-height:19%;overflow:hidden;margin:0;color:#18343a;font-size:48px;line-height:1.2}
.directed-stage{position:absolute;left:6%;right:6%;top:22%;bottom:25%;overflow:hidden;z-index:2}
.directed-labels{position:absolute;left:6%;right:6%;bottom:23%;display:flex;justify-content:center;gap:22px;z-index:3}.directed-label{padding:6px 12px;border-bottom:5px solid #d4664e;background:#f8fbf8;color:#183b43;font-size:24px;font-weight:700}
.directed-object{position:absolute}.directed-art{position:absolute;inset:0}.directed-art i{position:absolute;display:block}
.primitive-world{z-index:0}.primitive-world .directed-art{border:7px solid #244c55;border-radius:50%;background:#4b9eaa;box-shadow:inset 0 -35px 0 rgba(19,75,88,.25)}.primitive-world .directed-art:after{content:'';position:absolute;inset:13% 18%;border:3px solid rgba(255,255,255,.28);border-radius:50%}
.primitive-land{z-index:1}.primitive-land i{top:13%;width:15%;height:70%;background:#d7c98f;border:5px solid #244c55;clip-path:polygon(5% 30%,60% 0,100% 33%,74% 100%,12% 85%)}.primitive-land i:first-child{left:0}.primitive-land i:nth-child(2){right:0;transform:scaleX(-1)}.primitive-land i:nth-child(3){display:none}
.primitive-marker{z-index:4}.primitive-marker .directed-art{width:46%;height:46%;left:27%;top:20%;border:7px solid #173e48;border-radius:50%;background:#f7b953;box-shadow:0 0 0 15px rgba(247,185,83,.3)}
.primitive-distance{z-index:2}.primitive-distance .directed-art{top:50%;height:45%;width:100%;border-top:7px dashed #f7c86e;border-radius:50%}.primitive-distance .directed-art:after{content:'';position:absolute;right:0;top:-14px;width:18px;height:18px;border-radius:50%;background:#f7c86e}
.primitive-vertical_distance{z-index:3}.primitive-vertical_distance .directed-art{left:45%;top:0;width:10%;height:100%;border-left:8px dashed #f7c86e}
.primitive-orbit{z-index:2}.primitive-orbit .directed-art{top:38%;height:50%;width:100%;border-top:6px dashed #f4c765;border-radius:50%}
.primitive-satellite{z-index:5}.primitive-satellite .directed-art{left:40%;top:20%;width:20%;height:55%;border:5px solid #1c434c;border-radius:8px;background:#f4c76b}.primitive-satellite .directed-art:before,.primitive-satellite .directed-art:after{content:'';position:absolute;top:10%;width:110%;height:75%;border:5px solid #1c434c;background:#5e8e9c}.primitive-satellite .directed-art:before{right:115%}.primitive-satellite .directed-art:after{left:115%}
.primitive-people{z-index:4}.primitive-people i{top:7%;width:5%;height:82%;border:5px solid #244c55;border-radius:45% 45% 20% 20%;background:#e49d74}.primitive-people i:before{content:'';position:absolute;left:-18%;top:-38%;width:140%;height:45%;border:5px solid #244c55;border-radius:50%;background:#eac18e}.primitive-people i:first-child{left:5%}.primitive-people i:nth-child(2){right:5%}.primitive-people i:nth-child(3){display:none}
@media (max-aspect-ratio:1/1){.directed-heading{left:7%;top:6%;width:86%;font-size:43px}.directed-stage{left:5%;right:5%;top:27%;bottom:35%}.directed-labels{left:8%;right:8%;bottom:30%;flex-wrap:wrap;gap:8px}.directed-label{font-size:20px}}
.local-scene{color:#18313a;background:#eaf2ef}.local-scene .scene-image{inset:0;width:100%;height:100%;object-fit:cover}
.local-scene .caption{color:#fff;background:rgba(19,44,48,.94);border-left:9px solid #ed7655;bottom:52px;min-height:90px;padding:20px 28px;font-size:33px}
.local-visual-stage{position:absolute;inset:0 0 170px;overflow:hidden}
.local-narrative .caption{background:rgba(14,38,42,.94)}
.local-person{position:absolute;left:17%;bottom:20%;width:310px;height:650px;z-index:3;transform-origin:bottom center}
.person-shadow{position:absolute;left:40px;right:5px;bottom:-5px;height:30px;border-radius:50%;background:rgba(15,43,48,.35)}
.person-body{position:absolute;inset:0}.person-torso{position:absolute;left:40px;bottom:120px;width:230px;height:290px;border:8px solid #173941;border-radius:83px 85px 12px 12px;background:#e66c51;transform-origin:bottom center;z-index:2}
.person-leg{position:absolute;bottom:0;width:73px;height:172px;border:8px solid #173941;border-radius:12px 12px 19px 19px;background:#346c70;z-index:1}
.leg-back{left:74px}.leg-front{left:169px}.person-leg:after{content:'';position:absolute;left:-12px;bottom:-3px;width:86px;height:31px;border:6px solid #173941;border-radius:25px 15px 11px 11px;background:#f6e6c5}
.person-torso:after{content:'';position:absolute;left:46px;top:0;width:124px;height:36px;border:7px solid #173941;border-top:0;border-radius:0 0 80px 80px;background:#f4c58d}
.person-neck{position:absolute;left:129px;top:182px;width:70px;height:82px;border:7px solid #173941;border-radius:26px;background:#efba84;z-index:3}
.person-head{position:absolute;left:65px;top:18px;width:208px;height:230px;border:8px solid #173941;border-radius:49% 48% 46% 45%;background:#f4c58d;z-index:4;transform-origin:50% 88%}
.person-hair{position:absolute;left:-10px;top:-24px;width:211px;height:96px;border:8px solid #173941;border-radius:80px 86px 24px 24px;background:#243e44}
.person-hair:after{content:'';position:absolute;right:-12px;top:38px;width:49px;height:90px;border-radius:45px;background:#243e44}
.person-ear{position:absolute;right:-19px;top:106px;width:35px;height:48px;border:7px solid #173941;border-radius:50%;background:#f4c58d}
.person-eye{position:absolute;top:118px;width:34px;height:26px;border:5px solid #173941;border-radius:50%;background:#fff;overflow:hidden}.eye-a{left:42px}.eye-b{left:115px}
.person-eye i{position:absolute;left:9px;top:2px;width:12px;height:15px;border-radius:50%;background:#173941}
.person-brow{position:absolute;top:100px;width:39px;height:7px;border-radius:6px;background:#173941}.brow-a{left:38px}.brow-b{left:113px}
.person-nose{position:absolute;left:96px;top:142px;width:16px;height:28px;border-right:5px solid #bd8760;border-bottom:5px solid #bd8760;border-radius:40%}
.person-mouth{position:absolute;left:82px;top:185px;width:45px;height:14px;border-bottom:5px solid #984d42;border-radius:50%}
.person-arm{position:absolute;bottom:180px;width:65px;height:225px;border:8px solid #173941;border-radius:36px;background:#e66c51;transform-origin:top center}.arm-back{left:8px;transform:rotate(13deg)}.arm-front{right:4px;transform:rotate(-17deg);z-index:3}
.local-props{position:absolute;left:49%;right:5%;top:25%;height:43%;display:grid;grid-template-columns:repeat(2,1fr);gap:40px 75px}
.local-prop{position:relative;align-self:center;width:72%;height:75px;border:6px solid #153a42;border-radius:44px 80px 16px 16px;background:#e7b85f;box-shadow:0 12px 0 rgba(15,45,51,.2)}
.local-prop:nth-child(even){background:#79b1ab}.local-prop-3{background:#e56d53}.local-prop .prop-body{position:absolute;left:30%;top:-37px;width:45%;height:37px;border:6px solid #153a42;border-bottom:0;border-radius:45px 50px 0 0;background:inherit}
.wheel{position:absolute;bottom:-20px;width:28px;height:28px;border:6px solid #153a42;border-radius:50%;background:#f2eee1}.wheel-a{left:20%}.wheel-b{right:20%}
.theme-light .local-prop{width:80px;height:170px;border-radius:45px 45px 8px 8px;background:#f7d181;box-shadow:0 0 0 18px rgba(247,209,129,.18)}
.theme-temperature .local-prop{width:105px;height:105px;border-radius:50%;background:#9ed3cc;box-shadow:0 0 0 16px rgba(158,211,204,.25)}
.theme-compute .local-prop{width:135px;height:105px;border-radius:10px;background:#9bc4bb;box-shadow:8px 8px 0 #ed7759}
.theme-history .local-prop{width:125px;height:140px;border-radius:7px;background:#e4c691;border-top:22px solid #244b53}
.theme-general .local-prop{width:105px;height:105px;border-radius:16px;background:#e7b85f}
.local-narrative:not(.theme-attention) .local-prop .prop-body,.local-narrative:not(.theme-attention) .wheel{display:none}
.beat-explanation .local-prop:nth-child(2n){filter:saturate(.45)}.beat-reflection .local-prop:nth-child(2n){filter:saturate(.4) opacity(.65)}
.attention-ring{position:absolute;left:9%;top:8%;width:31%;aspect-ratio:1;border:10px solid #f77b58;border-radius:50%;box-shadow:0 0 0 12px rgba(255,255,255,.55);pointer-events:none}
.local-thinking{position:absolute;left:38%;top:20%;display:flex;gap:12px;transform:rotate(-18deg)}.local-thinking span{display:block;width:25px;height:25px;border:5px solid #183b43;border-radius:50%;background:#f7d282}.local-thinking span:nth-child(2){width:38px;height:38px}.local-thinking span:nth-child(3){width:54px;height:54px}
.local-education .local-heading{left:6%;top:8%;width:88%;font-size:50px;line-height:1.2;color:#18313a}
.info-flow{position:absolute;left:7%;right:7%;top:35%;height:38%;display:flex;align-items:center;justify-content:space-between;gap:4%;z-index:2}
.info-node{position:relative;display:flex;flex-direction:column;align-items:center;justify-content:center;width:27%;height:90%;border:6px solid #183b43;border-radius:8px;background:#fff;box-shadow:12px 14px 0 #c7dcd5;z-index:2;text-align:center}
.info-node-2{border-color:#e66c51}.node-icon{display:grid;place-items:center;width:90px;height:90px;margin-bottom:22px;border:5px solid #183b43;border-radius:50%;background:#f7d182;color:#183b43;font-size:54px;font-weight:800}
.info-node-2 .node-icon{background:#f3b9a8}.info-node-3 .node-icon{background:#9cc9bc}.info-node strong{padding:0 12px;font-size:35px;line-height:1.25}
.flow-track{position:absolute;left:13%;right:13%;top:50%;height:13px;border-radius:9px;background:#e66c51;transform-origin:left;z-index:1}
.flow-token{position:absolute;left:50%;top:calc(50% - 16px);width:32px;height:32px;border:5px solid #183b43;border-radius:50%;background:#f7d182;z-index:3}
.flow-filter{position:absolute;left:calc(68% - 40px);top:calc(50% - 60px);width:80px;height:120px;border:8px solid #e66c51;border-radius:50%;z-index:3}
.info-particles{position:absolute;left:14%;right:14%;top:25%;display:flex;justify-content:space-around}.info-particles i{width:13px;height:13px;border-radius:50%;background:#e66c51}.info-particles i:nth-child(3n){background:#3e807d}
.theme-spotlight .local-person{left:21%;bottom:16%}.theme-spotlight .person-torso,.theme-spotlight .person-arm{background:#497d93}
.shirt-mark{display:none;position:absolute;left:47%;top:44%;width:34px;height:25px;border-radius:46% 57% 30% 55%;background:#ce6957;transform:rotate(-18deg)}
.theme-spotlight .shirt-mark{display:block}.theme-spotlight .person-brow{transform:rotate(-7deg)}
.spotlight-stage{position:absolute;inset:0}.spotlight-crowd{position:absolute;right:9%;bottom:20%;width:48%;height:54%;z-index:1}
.bystander{position:absolute;bottom:0;width:20%;height:54%;opacity:.86}.bystander-1{left:2%;height:60%}.bystander-2{left:27%;height:48%}.bystander-3{left:54%;height:67%}.bystander-4{left:80%;height:53%}
.bystander-head{position:absolute;left:25%;top:0;width:55%;height:29%;border:6px solid #33535b;border-radius:50%;background:#e6b388}.bystander-body{position:absolute;left:3%;bottom:0;width:94%;height:70%;border:7px solid #33535b;border-radius:45% 45% 12px 12px;background:#a8bdb0}.bystander:nth-child(2n) .bystander-body{background:#c68b7d}.bystander:nth-child(3n) .bystander-body{background:#d3aa73}
.bystander-phone{position:absolute;right:-8%;top:42%;width:30%;height:36%;border:5px solid #33535b;border-radius:8px;background:#f3e6c8;transform:rotate(-12deg)}
.spotlight-cone{display:none;position:absolute;left:20%;top:-8%;width:39%;height:82%;background:rgba(249,196,91,.48);clip-path:polygon(47% 0,53% 0,100% 100%,0 100%);z-index:2;transform-origin:50% 0}
.mode-definition .spotlight-cone,.mode-imagined_gaze .spotlight-cone,.mode-question .spotlight-cone{display:block}
.imagined-rays{display:none;position:absolute;left:42%;top:40%;width:33%;height:20%;z-index:3}.mode-imagined_gaze .imagined-rays{display:block}.imagined-rays i{display:block;position:absolute;left:0;width:100%;height:4px;background:#d66b58;transform-origin:left}.imagined-rays i:nth-child(1){top:10%;transform:rotate(-13deg)}.imagined-rays i:nth-child(2){top:48%}.imagined-rays i:nth-child(3){top:88%;transform:rotate(13deg)}
.spotlight-note{position:absolute;right:8%;top:15%;max-width:42%;padding:15px 24px;border-left:8px solid #e67455;background:#fff;color:#263f46;font-size:35px;font-weight:750;line-height:1.25;z-index:4}
.spotlight-evidence{display:none;position:absolute;right:11%;top:30%;width:35%;min-height:25%;padding:42px 24px;border:8px solid #2b5058;border-radius:8px;background:#fff;color:#29444b;z-index:4;text-align:center;box-shadow:14px 14px 0 #b8d0c4}.spotlight-evidence strong{display:block;font-size:83px;color:#df6c50}.spotlight-evidence span{display:block;margin-top:18px;font-size:28px}.mode-evidence .spotlight-evidence{display:block}
.mode-evidence .spotlight-crowd{opacity:.38}.mode-others_busy .spotlight-crowd,.mode-release .spotlight-crowd{opacity:1}.mode-realization .shirt-mark,.mode-release .shirt-mark{opacity:.65}
@media (max-aspect-ratio:1/1){
  .local-scene .caption{left:50px;right:50px;bottom:95px;font-size:31px;min-height:150px}
  .local-visual-stage{bottom:310px}.local-person{left:7%;bottom:12%;transform:scale(1.05);transform-origin:bottom left}
  .local-props{left:42%;right:5%;top:19%;height:43%;gap:35px 26px}.local-prop{width:95%}.attention-ring{left:3%;width:51%}
  .local-thinking{left:30%;top:12%}.local-education .local-heading{left:7%;top:6%;width:86%;font-size:48px}
  .info-flow{left:13%;right:13%;top:25%;height:61%;flex-direction:column;gap:24px}
  .info-node{width:100%;height:29%;flex-direction:row;gap:25px}.node-icon{width:80px;height:80px;margin:0;font-size:48px}.info-node strong{font-size:32px}
  .flow-track{left:50%;right:auto;top:14%;bottom:14%;width:13px;height:auto;transform-origin:top}.flow-token,.flow-filter{display:none}
  .theme-spotlight .local-person{left:7%;bottom:13%;transform:scale(1.05);transform-origin:bottom left}.spotlight-crowd{right:4%;bottom:18%;width:55%;height:42%}
  .spotlight-note{right:5%;top:9%;max-width:73%;font-size:31px}.spotlight-cone{left:3%;top:-3%;width:74%;height:70%}.spotlight-evidence{right:6%;top:38%;width:53%;min-height:15%;padding:24px 12px}.spotlight-evidence strong{font-size:66px}.spotlight-evidence span{font-size:23px}
}
"""
