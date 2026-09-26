"""Authored light-pollution benchmark on Astra's pinned GSAP/HyperFrames runtime.

This is deliberately an authored Scene Program, not a claim that the public
script-to-video planner can yet invent these assets and motions unaided.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import shutil
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "light-pollution-motion-20260924"
PROJECT = OUTPUT / "project"
SCENES = [
    {
        "id": "scene-001", "function": "question", "title": "밤하늘을 올려다본 게 언제인가요?",
        "caption": "도시의 밤은 밝지만, 별은 점점 보이지 않습니다.",
        "narration": "밤하늘을 올려다본 게 언제이신가요? 우리는 사막이나 깊은 산속에 가지 않으면 수많은 별과 은하수를 보기 힘든 시대에 살고 있습니다.",
        "objects": ["city", "skyglow", "stars"], "motion": "city_glow_masks_stars",
    },
    {
        "id": "scene-002", "function": "evidence", "title": "80% 이상",
        "caption": "세계 인구의 80% 이상이 빛 공해가 있는 하늘 아래 삽니다.",
        "narration": "2016년 세계 밤하늘 지도에 따르면, 지구 인구의 80퍼센트 이상이 빛 공해가 있는 하늘 아래 살고 있습니다.",
        "objects": ["population-ring", "city-sky", "dark-sky"], "motion": "ratio_draw_then_compare",
        "source": "https://doi.org/10.1126/sciadv.1600377",
    },
    {
        "id": "scene-003", "function": "mechanism", "title": "빛은 위로 번집니다",
        "caption": "위로 새어 나간 빛이 하늘을 밝히고 별을 가립니다.",
        "narration": "가로등과 건물에서 위로 새어 나간 빛은 대기에서 퍼집니다. 하늘이 밝아질수록 희미한 별빛은 그 속에 묻힙니다.",
        "objects": ["lamps", "upward-rays", "skyglow", "stars"], "motion": "rays_scatter_and_stars_dim",
    },
    {
        "id": "scene-004", "function": "ecology", "title": "길을 잃는 생명",
        "caption": "밤의 인공조명은 야생동물의 이동을 흐트러뜨립니다.",
        "narration": "빛 공해는 별만의 문제가 아닙니다. 밤에 이동하는 새와 바다로 향하는 어린 거북은 인공조명 때문에 길을 잃을 수 있습니다.",
        "objects": ["natural-route", "artificial-route", "bird", "turtle", "shore-lights"],
        "motion": "routes_diverge",
        "source": "https://darksky.org/resources/what-is-light-pollution/effects/wildlife-ecosystems/",
    },
    {
        "id": "scene-005", "function": "human-impact", "title": "우리의 밤에도 스며듭니다",
        "caption": "밤의 빛은 수면 신호를 약하게 만들 수 있습니다.",
        "narration": "밤의 밝은 빛은 우리 몸의 수면 신호에도 영향을 줍니다. 수면 호르몬인 멜라토닌의 분비를 억제할 수 있기 때문입니다.",
        "objects": ["window", "light-beam", "sleep-signal"], "motion": "light_enters_signal_falls",
        "source": "https://darksky.org/resources/what-is-light-pollution/effects/human-health/",
    },
    {
        "id": "scene-006", "function": "resolution", "title": "별빛이 돌아오는 밤",
        "caption": "필요한 곳만 비추고, 불필요한 빛은 줄입니다.",
        "narration": "우리가 어둠을 잊으면, 다른 생명도 길을 잃습니다. 오늘 밤엔 불필요한 불을 꺼보세요. 어둠이 깊어질 때, 잊고 있던 별빛이 돌아옵니다.",
        "objects": ["shielded-lamps", "skyglow", "milky-way", "stars"],
        "motion": "lights_off_stars_return",
    },
]


def duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)
    ], text=True).strip())


def stars(count: int, seed: int, bright: bool = True) -> str:
    elements = []
    for index in range(count):
        x = 65 + ((index * 369 + seed * 223) % 1790)
        y = 95 + ((index * 173 + seed * 137) % 600)
        radius = [1.5, 2, 2.5, 3, 1.6][(index + seed) % 5]
        opacity = .35 + ((index * 7 + seed) % 6) * .09
        elements.append(f'<circle cx="{x}" cy="{y}" r="{radius}" opacity="{opacity:.2f}"/>')
    return f'<g class="stars {"bright-stars" if bright else "faint-stars"}">{"".join(elements)}</g>'


def skyline() -> str:
    blocks = [(0, 710, 210, 270), (175, 645, 145, 335), (306, 740, 165, 240),
              (462, 610, 165, 370), (615, 690, 230, 290), (828, 640, 145, 340),
              (955, 715, 155, 265), (1094, 592, 170, 388), (1250, 690, 194, 290),
              (1432, 635, 185, 345), (1600, 722, 320, 258)]
    result = []
    for index, (x, y, w, h) in enumerate(blocks):
        windows = []
        for col in range(1, max(2, w // 27)):
            for row in range(1, max(2, h // 42)):
                if (col * 11 + row * 7 + index) % 5 != 0:
                    windows.append(f'<rect class="window" x="{x + col * 24}" y="{y + row * 38}" width="8" height="13"/>')
        result.append(f'<g class="building"><rect x="{x}" y="{y}" width="{w}" height="{h}"/>{"".join(windows)}</g>')
    return '<g class="city">' + ''.join(result) + '</g>'


def art(index: int) -> str:
    if index == 0:
        return f'''<g class="night-sky">{stars(105, 1)}<ellipse class="skyglow" cx="960" cy="775" rx="900" ry="500"/></g>
            <path class="ridge" d="M0 765 Q430 680 800 788 T1920 748 V1080 H0Z"/>{skyline()}
            <g class="observer"><circle cx="440" cy="785" r="29"/><path d="M416 817 Q438 808 466 820 L490 952 H385Z"/></g>'''
    if index == 1:
        return f'''<defs><clipPath id="city-half"><rect x="0" y="0" width="955" height="1080"/></clipPath></defs>
            <g class="compare-left" clip-path="url(#city-half)"><rect x="0" y="0" width="955" height="840" fill="#142c39"/>
            <ellipse class="skyglow" cx="490" cy="715" rx="620" ry="390"/>{skyline()}</g>
            <g class="compare-right">{stars(90, 3)}<path class="ridge" d="M960 800 Q1300 660 1920 790 V1080 H960Z"/></g>
            <line x1="960" y1="130" x2="960" y2="815" stroke="#f3eee3" stroke-width="3" opacity=".5"/>
            <g class="donut" transform="translate(960 420)"><circle r="153" fill="none" stroke="#54717b" stroke-width="24"/>
            <circle class="donut-fill" r="153" fill="none" stroke="#f4bf67" stroke-width="24" transform="rotate(-90)" stroke-dasharray="961" stroke-dashoffset="961"/>
            <text x="0" y="21" text-anchor="middle" font-size="91" font-weight="800" fill="#f6f2e8">80%+</text></g>
            <text x="960" y="650" text-anchor="middle" font-size="25" fill="#b5c9cc">2016 세계 밤하늘 지도</text>'''
    if index == 2:
        return f'''{stars(85, 5)}<ellipse class="skyglow" cx="990" cy="680" rx="780" ry="470"/>
            <path class="horizon" d="M0 755H1920"/><g class="lamps">
            <path d="M300 810 V565 Q300 535 332 535 H385"/><path d="M870 810 V520 Q870 490 902 490 H955"/>
            <path d="M1450 810 V590 Q1450 560 1482 560 H1535"/>
            <circle cx="387" cy="539" r="21"/><circle cx="955" cy="494" r="21"/><circle cx="1535" cy="564" r="21"/></g>
            <g class="rays"><path d="M387 540 Q455 320 655 220"/><path d="M955 495 Q1030 272 1160 160"/>
            <path d="M1535 565 Q1440 300 1260 215"/><path d="M955 495 Q695 283 455 185"/></g>
            <g class="particles"><circle cx="655" cy="220" r="9"/><circle cx="1160" cy="160" r="9"/>
            <circle cx="1260" cy="215" r="9"/><circle cx="455" cy="185" r="9"/></g>'''
    if index == 3:
        return f'''{stars(72, 7)}<path class="coast" d="M0 795 Q410 730 790 802 T1540 772 Q1700 725 1920 790 V1080 H0Z"/>
            <path class="sea" d="M0 818 Q430 790 925 828 T1920 810 V1080 H0Z"/>
            <g class="shore-lights"><path d="M1230 812 V495 M1480 802 V570 M1700 808 V515"/>
            <circle cx="1230" cy="494" r="22"/><circle cx="1480" cy="569" r="22"/><circle cx="1700" cy="514" r="22"/></g>
            <path class="natural-route" d="M200 390 Q650 235 1120 360 T1840 350"/>
            <path class="artificial-route" d="M200 390 Q650 235 950 470 T1490 590"/>
            <g transform="translate(220 365)"><g class="bird"><path d="M-70 20 Q-15 -35 0 12 Q25 -40 80 8 Q25 -12 0 22 Q-22 -12 -70 20Z"/></g></g>
            <g transform="translate(390 780)"><g class="turtle"><ellipse rx="43" ry="29"/><circle cx="53" cy="0" r="14"/><path d="M-32 -20 l-38 -17 M-32 20 l-38 17 M22 -20 l25 -22 M22 20 l25 22"/></g></g>'''
    if index == 4:
        return f'''{stars(65, 9)}<g class="room"><path d="M0 795H1920"/><rect x="210" y="225" width="515" height="410" rx="9"/>
            <path d="M466 225 V635 M210 430 H725"/><path d="M865 805 H1640 V620 H865Z"/>
            <path d="M1035 632 Q1190 455 1320 622"/><circle cx="1337" cy="598" r="48"/></g>
            <g class="window-light"><path d="M719 277 L1340 640 L950 795 L719 605Z"/></g>
            <g class="sleep-signal"><path d="M235 760 C335 760 350 700 460 700 S620 720 700 646 S790 618 850 645"/>
            <circle class="signal-dot" cx="235" cy="760" r="17"/></g>
            <text x="440" y="676" text-anchor="middle" fill="#c7e4dc" font-size="28">수면 신호</text>'''
    return f'''{stars(180, 12)}<g class="milky-way">{stars(90, 19)}
        <path d="M205 215 Q920 680 1715 170" fill="none" stroke="#f3e8ce" stroke-width="95" opacity=".12"/></g>
        <ellipse class="skyglow" cx="960" cy="775" rx="900" ry="500"/>
        <path class="ridge" d="M0 800 Q360 705 720 820 T1430 776 T1920 795 V1080 H0Z"/>
        <g class="shielded-lamps"><path d="M370 800V690 M1550 800V690"/>
        <path d="M340 688 H400 L390 710 H350Z M1520 688 H1580 L1570 710 H1530Z"/>
        <path class="downlight" d="M355 712 L305 790 H435 L385 712Z M1535 712 L1485 790 H1615 L1565 712Z"/></g>
        <g class="final-stars"><circle cx="850" cy="225" r="9"/><circle cx="1185" cy="345" r="7"/><circle cx="450" cy="310" r="7"/></g>'''


CSS = """
@font-face{font-family:Night;src:local('Malgun Gothic');font-weight:100 900}
*{box-sizing:border-box}html,body{width:100%;height:100%;margin:0;overflow:hidden;background:#101e2b;color:#f6f2e8;font-family:Night,sans-serif;letter-spacing:0}
.scene{position:absolute;inset:0;opacity:0;overflow:hidden;background:#101e2b}
.art{position:absolute;inset:0;width:100%;height:100%}.stars circle{fill:#f4eee3;stroke:none}
.skyglow{fill:#e9a553;opacity:.38;filter:blur(65px)}.ridge{fill:#132e35}.city .building>rect{fill:#203943;stroke:#57717a;stroke-width:3}.window{fill:#f2bb68;opacity:.88}
.observer{fill:#101c28}.observer path{fill:#152b35}.horizon,.room path{fill:none;stroke:#84a6a8;stroke-width:5}
.lamps path,.shore-lights path,.shielded-lamps>path{fill:none;stroke:#a0c4bb;stroke-width:9;stroke-linecap:round}
.lamps circle,.shore-lights circle{fill:#ffe1a0;filter:drop-shadow(0 0 18px #ffca6b)}
.rays path{fill:none;stroke:#ffd98a;stroke-width:8;stroke-linecap:round;stroke-dasharray:14 20;opacity:.83}.particles circle{fill:#f8c869;filter:drop-shadow(0 0 15px #f4bd67)}
.coast{fill:#465157}.sea{fill:#1c5960}.natural-route,.artificial-route{fill:none;stroke-width:7;stroke-linecap:round;stroke-dasharray:18 15}
.natural-route{stroke:#a6dad2}.artificial-route{stroke:#faaf6d}.bird path{fill:#e9eee2}.turtle ellipse,.turtle circle{fill:#a4dfd0;stroke:#18343b;stroke-width:5}.turtle path{fill:none;stroke:#a4dfd0;stroke-width:12;stroke-linecap:round}
.room rect{fill:#203643;stroke:#acd0c8;stroke-width:7}.room path{stroke:#9db7b5}.room circle{fill:#dbb2a0}.window-light path{fill:#f5b865;opacity:.35}.sleep-signal path{fill:none;stroke:#8cdbcb;stroke-width:13;stroke-linecap:round}.signal-dot{fill:#f6c66f}
.milky-way{opacity:0}.final-stars circle{fill:#fff5cc;filter:drop-shadow(0 0 12px #fff4c6)}.downlight{fill:#edbe70!important;stroke:none!important;opacity:.32}
.header{position:absolute;z-index:4;left:82px;top:68px;font-size:22px;font-weight:800;color:#b9d8d3}.header span{color:#f3be6a;margin-right:15px}
.copy{position:absolute;z-index:4;left:82px;top:140px;max-width:1350px;padding-right:35px}.copy h1{font-size:68px;line-height:1.16;margin:0;word-break:keep-all;letter-spacing:0;text-shadow:0 3px 14px #132631}
.caption{position:absolute;z-index:5;left:82px;right:82px;bottom:54px;min-height:104px;padding:24px 30px;background:rgba(6,18,27,.72);border-left:7px solid #efbd68;font-size:32px;line-height:1.35;font-weight:600;word-break:keep-all}
.progress{position:absolute;z-index:6;left:82px;right:82px;bottom:36px;height:5px;background:#42636a}.progress i{display:block;width:100%;height:100%;background:#f0bf6c;transform:scaleX(0);transform-origin:left}
"""


def timeline(durations: list[float]) -> str:
    lines = ["window.__timelines={};const tl=gsap.timeline({paused:true});gsap.set('.scene',{opacity:0});"]
    cursor = 0.0
    for index, seconds in enumerate(durations):
        root = f"#scene-{index + 1}"
        if index:
            lines.append(f"tl.set('#scene-{index}',{{opacity:0}},{cursor:.3f});")
        lines.extend([
            f"tl.set('{root}',{{opacity:1}},{cursor:.3f});",
            f"tl.fromTo('{root} .copy',{{y:30,opacity:0}},{{y:0,opacity:1,duration:.65,ease:'power2.out'}},{cursor+.1:.3f});",
            f"tl.fromTo('{root} .caption',{{y:15,opacity:0}},{{y:0,opacity:1,duration:.5,ease:'power2.out'}},{cursor+.2:.3f});",
            f"tl.to('{root} .progress i',{{scaleX:1,duration:{seconds:.3f},ease:'none'}},{cursor:.3f});",
        ])
        if index == 0:
            lines.extend([
                f"tl.fromTo('{root} .skyglow',{{opacity:.04,scale:.6,transformOrigin:'50% 80%'}},{{opacity:.48,scale:1,duration:{seconds*.68:.3f},ease:'sine.inOut'}},{cursor+.4:.3f});",
                f"tl.to('{root} .stars',{{opacity:.17,duration:{seconds*.55:.3f},ease:'sine.inOut'}},{cursor+seconds*.35:.3f});",
            ])
        elif index == 1:
            lines.extend([
                f"tl.to('{root} .donut-fill',{{strokeDashoffset:192,duration:{seconds*.58:.3f},ease:'power2.out'}},{cursor+.45:.3f});",
                f"tl.fromTo('{root} .compare-right',{{opacity:.25}},{{opacity:1,duration:1.2,ease:'sine.out'}},{cursor+seconds*.34:.3f});",
            ])
        elif index == 2:
            lines.extend([
                f"tl.fromTo('{root} .rays path',{{strokeDashoffset:440,opacity:0}},{{strokeDashoffset:0,opacity:.84,duration:1.9,stagger:.18,ease:'none'}},{cursor+.65:.3f});",
                f"tl.fromTo('{root} .skyglow',{{opacity:.02,scale:.6,transformOrigin:'50% 80%'}},{{opacity:.48,scale:1,duration:{seconds*.55:.3f},ease:'sine.out'}},{cursor+1.2:.3f});",
                f"tl.to('{root} .stars',{{opacity:.14,duration:1.6,ease:'sine.inOut'}},{cursor+seconds*.52:.3f});",
            ])
        elif index == 3:
            lines.extend([
                f"tl.fromTo('{root} .natural-route',{{strokeDashoffset:850,opacity:.5}},{{strokeDashoffset:0,opacity:1,duration:2.5,ease:'none'}},{cursor+.5:.3f});",
                f"tl.fromTo('{root} .artificial-route',{{strokeDashoffset:850,opacity:0}},{{strokeDashoffset:0,opacity:1,duration:2.6,ease:'none'}},{cursor+2.6:.3f});",
                f"tl.fromTo('{root} .bird',{{x:0,y:0}},{{x:770,y:150,duration:3.1,ease:'power1.inOut'}},{cursor+.8:.3f});",
                f"tl.fromTo('{root} .turtle',{{x:0}},{{x:360,duration:2.3,ease:'power1.inOut'}},{cursor+seconds*.5:.3f});",
            ])
        elif index == 4:
            lines.extend([
                f"tl.fromTo('{root} .window-light',{{opacity:0}},{{opacity:1,duration:1.4,ease:'sine.out'}},{cursor+.65:.3f});",
                f"tl.fromTo('{root} .sleep-signal',{{scaleY:1,transformOrigin:'50% 100%'}},{{scaleY:.37,duration:2,ease:'power2.inOut'}},{cursor+seconds*.42:.3f});",
            ])
        else:
            lines.extend([
                f"tl.to('{root} .skyglow',{{opacity:0,scale:.4,transformOrigin:'50% 80%',duration:{seconds*.50:.3f},ease:'power2.inOut'}},{cursor+.35:.3f});",
                f"tl.fromTo('{root} .milky-way',{{opacity:0}},{{opacity:.9,duration:{seconds*.48:.3f},ease:'sine.inOut'}},{cursor+seconds*.35:.3f});",
                f"tl.fromTo('{root} .final-stars',{{opacity:0,scale:.6,transformOrigin:'50% 50%'}},{{opacity:1,scale:1,duration:1.5,ease:'power2.out'}},{cursor+seconds*.55:.3f});",
            ])
        cursor += seconds
    lines.append(f"tl.set({{}},{{}},{cursor:.3f});window.__timelines['light-pollution']=tl;")
    return ''.join(lines)


def prepare() -> None:
    audio = OUTPUT / "audio"
    audio.mkdir(parents=True, exist_ok=True)
    manifest = [{"id": item["id"], "narration": item["narration"]} for item in SCENES]
    (audio / "narration.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(audio / "narration.json")


def build() -> None:
    wavs = [OUTPUT / "audio" / f"{item['id']}.wav" for item in SCENES]
    if not all(path.is_file() for path in wavs):
        raise RuntimeError("Run --prepare and local speech synthesis first")
    # Measured speech sets scene duration. Do not fabricate timing from text length.
    raw = [duration(path) for path in wavs]
    speed = min(1.20, max(1.0, (sum(raw) + len(raw) * .32) / 58.0))
    audio = OUTPUT / "audio"
    padded = audio / "padded"
    padded.mkdir(exist_ok=True)
    processed = []
    for source in wavs:
        target = padded / source.name
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source), "-af", f"atempo={speed:.4f},apad=pad_dur=0.32", str(target)], check=True)
        processed.append(target)
    lengths = [duration(path) for path in processed]
    total = sum(lengths)
    if total > 60:
        raise ValueError(f"Narration {total:.2f}s exceeds episode ceiling; revise script before render")
    PROJECT.mkdir(parents=True, exist_ok=True)
    assets = PROJECT / "assets"
    assets.mkdir(exist_ok=True)
    shutil.copy2(ROOT / "video-generator/hyperframes-runtime/node_modules/gsap/dist/gsap.min.js", assets / "gsap.min.js")
    body = []
    for index, item in enumerate(SCENES):
        body.append(f'''<section class="scene" id="scene-{index + 1}"><svg class="art" viewBox="0 0 1920 1080" aria-hidden="true">{art(index)}</svg>
            <div class="header"><span>{index + 1:02}</span>밤의 지도</div>
            <div class="copy"><h1>{html.escape(item['title'])}</h1></div>
            <div class="caption">{html.escape(item['caption'])}</div><div class="progress"><i></i></div></section>''')
    page = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>빛 공해 | 밤의 지도</title>
        <script src="assets/gsap.min.js"></script><style>{CSS}</style></head><body>
        <main data-composition-id="light-pollution" data-width="1920" data-height="1080" data-start="0" data-duration="{total:.6f}" data-fps="30">{''.join(body)}</main>
        <script>{timeline(lengths)}</script></body></html>'''
    (PROJECT / "index.html").write_text(page, encoding="utf-8")
    (PROJECT / "meta.json").write_text(json.dumps({"name": "light-pollution", "duration": total, "resolution": {"width": 1920, "height": 1080}, "fps": 30}, ensure_ascii=False), encoding="utf-8")
    (PROJECT / "scene-program.json").write_text(json.dumps({
        "status": "AUTHORED_BENCHMARK", "runtime": "HyperFrames 0.8.46 + GSAP 3.14.2",
        "scenes": [{**item, "duration_seconds": round(lengths[i], 3)} for i, item in enumerate(SCENES)],
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    concat = audio / "concat.txt"
    concat.write_text(''.join(f"file '{path.as_posix()}'\n" for path in processed), encoding="utf-8")
    (OUTPUT / "production-record.json").write_text(json.dumps({
        "title": "빛 공해: 밤의 지도", "duration_seconds": round(total, 3),
        "speech_speed": round(speed, 3), "paid_api_calls": 0,
        "scope": "Authored director program on pinned runtime; not autonomous script-to-video E2E",
        "visuals": "original procedural SVG", "voice": "local Microsoft Heami Desktop",
        "source_facts": [item["source"] for item in SCENES if item.get("source")],
        "script_changes": ["80% refers to living under light-polluted skies", "human melatonin effect stated as possible"],
        "human_quality_review": "PENDING",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"duration": total, "speed": speed, "project": str(PROJECT)}, ensure_ascii=False))


def render() -> None:
    cli = ROOT / "video-generator/hyperframes-runtime/node_modules/.bin/hyperframes.cmd"
    silent = OUTPUT / "silent.mp4"
    temp = OUTPUT / "temp"
    temp.mkdir(exist_ok=True)
    env = dict(os.environ, TEMP=str(temp), TMP=str(temp), TMPDIR=str(temp))
    subprocess.run([str(cli), "render", f"--output={silent}", "--quality=looks", "--workers=2", "--low-memory-mode", "--strict", str(PROJECT)], cwd=cli.parent.parent.parent, env=env, check=True)
    audio = OUTPUT / "audio" / "narration.m4a"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(OUTPUT / "audio" / "concat.txt"), "-vn", "-c:a", "aac", "-b:a", "160k", str(audio)], check=True)
    final = OUTPUT / "light-pollution-motion-final.mp4"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-af", "loudnorm=I=-16:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(final)], check=True)
    digest = hashlib.sha256(final.read_bytes()).hexdigest()
    print(json.dumps({"video": str(final), "sha256": digest}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("step", choices=["prepare", "build", "render"])
    args = parser.parse_args()
    {"prepare": prepare, "build": build, "render": render}[args.step]()
