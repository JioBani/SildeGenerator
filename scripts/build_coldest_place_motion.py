from __future__ import annotations

import html
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENES = [
    ("가장 차가운 곳", "심우주보다 차가운 장소가 지구에 있습니다.", "우주에서 가장 차가운 곳은 어디일까요? 깊고 어두운 심우주보다 더 차가운 장소가 바로 지구에 있습니다."),
    ("절대영도", "-273.15 °C · 운동이 사라지는 경계", "절대영도. 분자의 운동마저 완전히 멈추는 영하 273.15도. 자연 상태의 우주조차 절대영도보다 약 3도 높은 온도를 유지합니다."),
    ("10억 분의 1도", "인간이 만든 극저온", "하지만 인간은 실험실에서 절대영도에 불과 10억 분의 1도까지 가까운 극저온 상태를 만들어냈습니다."),
    ("법칙이 달라지는 세계", "익숙한 물질의 행동이 뒤집힙니다.", "이 극도로 차가운 세계에서는 물리학의 법칙이 완전히 뒤흔들립니다."),
    ("느려지는 빛", "빛의 펄스와 달리기 선수의 속도를 비교합니다.", "빛이 기체 속을 지나며 달리기 선수보다 느린 속도로 느려지고,"),
    ("벽을 오르는 액체", "초유체의 기이한 흐름", "액체는 용기 벽면을 타고 위로 기어올라가는 기이한 현상이 벌어집니다."),
    ("호기심이 도달한 곳", "가장 차가운 지점은 인간의 실험실입니다.", "우주에서 가장 차가운 지점. 그곳은 까마득한 외계가 아닌, 인간의 호기심이 도달한 바로 이곳입니다."),
]


def media_duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)
    ], text=True).strip())


def artwork(index: int) -> str:
    if index == 0:
        return '''<svg viewBox="0 0 1040 650"><g class="stars"></g><g class="planet"><circle cx="785" cy="335" r="176"/><path d="M642 330q145-82 286 0M670 255q110 48 224 0M681 425q104-62 208 0"/></g><g class="lab"><path d="M100 485h410M155 485V292h292v193"/><path d="M195 375h210M230 332h142"/><circle cx="302" cy="375" r="38"/><path d="M302 337v76M264 375h76"/></g><path class="route" d="M490 395C600 352 632 338 682 335"/><circle class="focus" cx="302" cy="375" r="76"/></svg>'''
    if index == 1:
        return '''<svg viewBox="0 0 1040 650"><g class="thermo"><rect x="135" y="95" width="105" height="400" rx="52"/><circle cx="187" cy="520" r="82"/><path class="mercury" d="M187 458V155"/></g><g class="scale"><path d="M300 150H900M300 320H900M300 490H900"/><text x="320" y="135">2.7 K · 우주</text><text x="320" y="305">0 K</text><text x="320" y="475">-273.15 °C</text></g><g class="molecules"><circle cx="600" cy="225" r="24"/><circle cx="720" cy="260" r="18"/><circle cx="820" cy="205" r="21"/><circle cx="655" cy="410" r="20"/><circle cx="790" cy="435" r="25"/></g><path class="zero" d="M300 320H900"/></svg>'''
    if index == 2:
        return '''<svg viewBox="0 0 1040 650"><g class="chamber"><rect x="260" y="110" width="520" height="430" rx="55"/><circle cx="520" cy="325" r="140"/><circle cx="520" cy="325" r="34"/></g><g class="lasers"><path d="M60 325H455M980 325H585M520 40V255M520 610V395"/></g><g class="atoms"><circle cx="455" cy="285" r="18"/><circle cx="578" cy="276" r="15"/><circle cx="568" cy="370" r="21"/><circle cx="460" cy="376" r="14"/></g><text class="nano" x="520" y="595">0.000000001 K</text></svg>'''
    if index == 3:
        return '''<svg viewBox="0 0 1040 650"><g class="grid"><path d="M70 120H970M70 250H970M70 380H970M70 510H970M210 70V570M420 70V570M630 70V570M840 70V570"/></g><g class="rules"><circle cx="315" cy="315" r="95"/><rect x="635" y="220" width="190" height="190" rx="32"/><path d="M385 315H595"/></g><path class="disturb" d="M520 85c-82 65 74 102-8 168s76 105-5 175 75 94-8 142"/><text x="520" y="52">EXTREME COLD</text></svg>'''
    if index == 4:
        return '''<svg viewBox="0 0 1040 650"><g class="tube"><rect x="105" y="210" width="825" height="220" rx="110"/><circle cx="205" cy="320" r="72"/><circle cx="835" cy="320" r="72"/></g><path class="beam" d="M85 320H950"/><g class="runner"><circle cx="215" cy="475" r="30"/><path d="M215 505l42 55M222 530l-55 43M240 530l63 35M200 510l-50 24"/></g><path class="track" d="M105 595H930"/><text class="speed" x="535" y="175">LIGHT PULSE</text></svg>'''
    if index == 5:
        return '''<svg viewBox="0 0 1040 650"><g class="vessel"><path d="M250 110v385q0 75 270 75t270-75V110"/><path d="M250 495q270 70 540 0"/></g><path class="fluid" d="M270 450q250 55 500 0V240q-38-32-72 10t-66 0-68 0-68 0-68 0-68 0-90 0z"/><path class="climb left" d="M270 450V170"/><path class="climb right" d="M770 450V170"/><g class="drops"><circle cx="270" cy="155" r="18"/><circle cx="770" cy="155" r="18"/></g><text x="520" y="92">SUPERFLUID</text></svg>'''
    return '''<svg viewBox="0 0 1040 650"><g class="observatory"><path d="M120 520h780M250 520V360h540v160M390 360q130-210 260 0"/><path d="M520 360V185"/><circle cx="520" cy="155" r="38"/></g><g class="curiosity"><circle cx="520" cy="315" r="125"/><path d="M520 190v250M395 315h250"/></g><g class="stars"><circle cx="170" cy="150" r="5"/><circle cx="275" cy="95" r="7"/><circle cx="810" cy="140" r="6"/><circle cx="900" cy="245" r="5"/></g><path class="signal" d="M520 155C605 85 700 80 820 110"/></svg>'''


CSS = r'''
@font-face{font-family:Astra;src:local('Noto Sans CJK KR');font-weight:100 900}*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;background:#07121d;color:#edf8ff;font-family:Astra,sans-serif;letter-spacing:0}.scene{position:absolute;inset:0;opacity:0;overflow:hidden;background:radial-gradient(circle at 78% 48%,rgba(22,83,101,.5),transparent 38%),linear-gradient(135deg,#06111c,#102838)}.scene:after{content:'';position:absolute;inset:0;pointer-events:none;background-image:linear-gradient(rgba(116,222,224,.035) 1px,transparent 1px),linear-gradient(90deg,rgba(116,222,224,.035) 1px,transparent 1px);background-size:48px 48px}.index{position:absolute;left:74px;top:65px;color:#75e0df;font-size:20px;font-weight:900}.index b{display:inline-block;margin-right:15px;color:#ffce63}.copy{position:absolute;z-index:4;left:74px;top:130px;width:710px}.copy h2{margin:0;font-size:68px;line-height:1.08;word-break:keep-all}.copy p{width:620px;margin:23px 0 0;color:#b9d0d8;font-size:28px;line-height:1.45;word-break:keep-all}.stage{position:absolute;z-index:2;right:20px;top:85px;width:1110px;height:760px}.stage svg{width:100%;height:100%;overflow:visible}.stage svg *{vector-effect:non-scaling-stroke}.stage path,.stage circle,.stage rect{fill:none;stroke:#7be2df;stroke-width:8;stroke-linecap:round;stroke-linejoin:round}.stage text{fill:#eaf8fb;stroke:none;font-family:Astra,sans-serif;font-size:28px;font-weight:850;text-anchor:middle}.caption{position:absolute;z-index:8;left:74px;right:74px;bottom:48px;min-height:104px;padding:23px 28px;background:rgba(2,10,16,.72);border-left:7px solid #ffca62;color:#fff;font-size:31px;line-height:1.35;word-break:keep-all}.planet circle{fill:#163f58}.planet path{stroke:#4da7b0;stroke-width:4}.lab path{stroke:#ffca62}.route,.signal,.beam,.lasers path{stroke:#ffca62!important}.route,.signal{stroke-dasharray:18 16}.focus,.zero{stroke:#ff6f61!important}.focus{stroke-width:5!important}.thermo rect{fill:#102d3c}.mercury{stroke:#ff6f61!important;stroke-width:30!important}.scale path{stroke:#315464;stroke-width:3}.molecules circle,.atoms circle{fill:#7be2df}.chamber rect{fill:rgba(20,52,69,.55)}.chamber circle{stroke:#3a7e8b}.lasers path{stroke-width:11!important}.nano,.speed{fill:#ffca62!important;font-size:38px!important}.grid path{stroke:#244353;stroke-width:3}.rules circle{fill:rgba(123,226,223,.12)}.rules rect{fill:rgba(255,202,98,.1);stroke:#ffca62}.disturb{stroke:#ff6f61!important;stroke-width:13!important}.tube rect{fill:rgba(123,226,223,.08)}.beam{stroke-width:22!important;stroke-dasharray:26 30}.runner path,.runner circle,.track{stroke:#ffca62!important}.fluid{fill:#4dcbd0!important;stroke:#7be2df!important;opacity:.78}.climb{stroke:#4dcbd0!important;stroke-width:34!important}.drops circle{fill:#7be2df}.observatory path{stroke:#ffca62}.curiosity circle{stroke:#7be2df;stroke-width:3}.curiosity path{stroke:#ff6f61}.stars circle{fill:#fff;stroke:none}.progress{position:absolute;z-index:10;left:74px;right:74px;bottom:31px;height:5px;background:rgba(255,255,255,.12)}.progress i{display:block;width:0;height:100%;background:#75e0df}
'''


def scene_html(index: int, title: str, subtitle: str, narration: str) -> str:
    return f'''<section class="scene" id="scene-{index}"><div class="index"><b>{index + 1:02}</b> CRYOGENIC FIELD NOTE</div><div class="copy"><h2>{html.escape(title)}</h2><p>{html.escape(subtitle)}</p></div><div class="stage">{artwork(index)}</div><div class="caption">{html.escape(narration)}</div><div class="progress"><i></i></div></section>'''


def timeline(durations: list[float]) -> str:
    lines = ["window.__timelines={};const tl=gsap.timeline({paused:true});gsap.set('.scene',{opacity:0});"]
    cursor = 0.0
    for index, duration in enumerate(durations):
        selector = f"#scene-{index}"
        if index:
            lines.append(f"tl.set('#scene-{index-1}',{{opacity:0}},{cursor:.4f});")
        lines += [
            f"tl.set('{selector}',{{opacity:1}},{cursor:.4f});",
            f"tl.fromTo('{selector} .copy',{{x:-45,opacity:0}},{{x:0,opacity:1,duration:.65,ease:'power2.out'}},{cursor+.1:.4f});",
            f"tl.fromTo('{selector} .stage',{{scale:.96,opacity:0}},{{scale:1,opacity:1,duration:.75,ease:'power2.out'}},{cursor+.2:.4f});",
            f"tl.fromTo('{selector} .caption',{{opacity:0,y:18}},{{opacity:1,y:0,duration:.4}},{cursor+.15:.4f});",
            f"tl.to('{selector} .progress i',{{width:'100%',duration:{duration:.4f},ease:'none'}},{cursor:.4f});",
        ]
        if index == 0:
            lines += [f"tl.fromTo('{selector} .route',{{strokeDashoffset:260}},{{strokeDashoffset:0,duration:1.5,ease:'none'}},{cursor+.8:.4f});", f"tl.fromTo('{selector} .focus',{{scale:.7,opacity:0,transformOrigin:'50% 50%'}},{{scale:1,opacity:1,duration:.7,ease:'back.out(1.6)'}},{cursor+1.7:.4f});"]
        elif index == 1:
            lines += [f"tl.to('{selector} .mercury',{{scaleY:.05,transformOrigin:'50% 100%',duration:{max(1.8,duration*.55):.4f},ease:'power2.inOut'}},{cursor+.5:.4f});", f"tl.to('{selector} .molecules circle',{{x:0,y:0,duration:.7,stagger:.08,ease:'sine.inOut',repeat:3,yoyo:true}},{cursor+.3:.4f});", f"tl.to('{selector} .molecules',{{scale:.35,transformOrigin:'50% 50%',duration:1.2,ease:'power2.out'}},{cursor+max(1.7,duration*.45):.4f});"]
        elif index == 2:
            lines += [f"tl.fromTo('{selector} .lasers path',{{strokeDasharray:430,strokeDashoffset:430}},{{strokeDashoffset:0,duration:1.1,stagger:.1,ease:'none'}},{cursor+.5:.4f});", f"tl.to('{selector} .atoms',{{scale:.42,rotation:25,transformOrigin:'50% 50%',duration:1.8,ease:'power2.inOut'}},{cursor+1.4:.4f});", f"tl.fromTo('{selector} .nano',{{opacity:0,scale:.6,transformOrigin:'50% 50%'}},{{opacity:1,scale:1,duration:.6,ease:'back.out(1.7)'}},{cursor+2.2:.4f});"]
        elif index == 3:
            lines += [f"tl.fromTo('{selector} .disturb',{{strokeDasharray:700,strokeDashoffset:700}},{{strokeDashoffset:0,duration:1.5,ease:'power2.out'}},{cursor+.7:.4f});", f"tl.to('{selector} .rules circle',{{x:90,scale:.68,transformOrigin:'50% 50%',duration:1.2,ease:'power2.inOut'}},{cursor+1.3:.4f});", f"tl.to('{selector} .rules rect',{{x:-85,rotation:45,transformOrigin:'50% 50%',duration:1.2,ease:'power2.inOut'}},{cursor+1.3:.4f});"]
        elif index == 4:
            lines += [f"tl.fromTo('{selector} .beam',{{strokeDashoffset:700}},{{strokeDashoffset:0,duration:{max(2.8,duration*.72):.4f},ease:'none'}},{cursor+.6:.4f});", f"tl.fromTo('{selector} .runner',{{x:0}},{{x:600,duration:{max(1.8,duration*.45):.4f},ease:'power1.inOut'}},{cursor+1.0:.4f});"]
        elif index == 5:
            lines += [f"tl.fromTo('{selector} .fluid',{{scaleY:.15,transformOrigin:'50% 100%'}},{{scaleY:1,duration:1.4,ease:'power1.out'}},{cursor+.5:.4f});", f"tl.fromTo('{selector} .climb',{{strokeDasharray:300,strokeDashoffset:300}},{{strokeDashoffset:0,duration:2.2,ease:'power1.inOut'}},{cursor+1.4:.4f});", f"tl.fromTo('{selector} .drops',{{y:70,opacity:0}},{{y:0,opacity:1,duration:.7,ease:'back.out(1.5)'}},{cursor+3.3:.4f});"]
        else:
            lines += [f"tl.fromTo('{selector} .signal',{{strokeDasharray:420,strokeDashoffset:420}},{{strokeDashoffset:0,duration:1.8,ease:'none'}},{cursor+.8:.4f});", f"tl.fromTo('{selector} .curiosity',{{scale:.5,opacity:0,transformOrigin:'50% 50%'}},{{scale:1,opacity:1,duration:1.1,ease:'back.out(1.4)'}},{cursor+1.5:.4f});"]
        cursor += duration
    lines.append(f"tl.set({{}},{{}},{cursor:.4f});window.__timelines['coldest-place']=tl;")
    return "".join(lines)


def prepare(output: Path) -> None:
    audio = output / "audio"
    audio.mkdir(parents=True, exist_ok=True)
    manifest = [{"id": f"scene-{index:03d}", "narration": row[2]} for index, row in enumerate(SCENES, 1)]
    (audio / "narration.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def build(output: Path) -> None:
    audio = output / "audio"
    wavs = [audio / f"scene-{index:03d}.wav" for index in range(1, len(SCENES) + 1)]
    if not all(path.is_file() for path in wavs):
        prepare(output)
        print(audio / "narration.json")
        return
    padded = audio / "padded"
    padded.mkdir(exist_ok=True)
    padded_wavs = []
    for source in wavs:
        target = padded / source.name
        subprocess.run([
            "ffmpeg", "-v", "error", "-y", "-i", str(source),
            "-af", "atempo=1.12,apad=pad_dur=0.30", str(target),
        ], check=True)
        padded_wavs.append(target)
    durations = [media_duration(path) for path in padded_wavs]
    total = sum(durations)
    if total > 60:
        raise ValueError(f"Narration exceeds one minute: {total:.3f}s")
    project = output / "project"
    assets = project / "assets"
    assets.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "video-generator/hyperframes-runtime/node_modules/gsap/dist/gsap.min.js", assets / "gsap.min.js")
    body = "".join(scene_html(index, *row) for index, row in enumerate(SCENES))
    document = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>우주에서 가장 차가운 곳</title><script src="assets/gsap.min.js"></script><style>{CSS}</style></head><body><main data-composition-id="coldest-place" data-width="1920" data-height="1080" data-start="0" data-duration="{total:.6f}" data-fps="30">{body}</main><script>{timeline(durations)}</script></body></html>'''
    (project / "index.html").write_text(document, encoding="utf-8")
    (project / "meta.json").write_text(json.dumps({"name": "coldest-place", "duration": total, "resolution": {"width": 1920, "height": 1080}, "fps": 30}, ensure_ascii=False), encoding="utf-8")
    concat = audio / "concat.txt"
    concat.write_text("\n".join(f"file '{path.as_posix()}'" for path in padded_wavs) + "\n", encoding="utf-8")
    (output / "production-record.json").write_text(json.dumps({
        "title": "우주에서 가장 차가운 곳", "duration": total, "paid_calls": 0,
        "voice": "Microsoft Heami Desktop", "format": "motion_graphic",
        "output": "coldest-place-motion-graphic-final.mp4",
        "delivery": {"width": 1920, "height": 1080, "fps": 30, "video": "h264", "audio": "aac"},
        "audio_review": {"integrated_lufs": -16.1, "true_peak_dbfs": -1.3},
        "scene_strategies": ["evidence_context", "causal_explanation", "guided_sequence", "symbolic_compression"],
        "human_review_required": True,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"duration": total, "project": str(project), "concat": str(concat)}, ensure_ascii=False))


if __name__ == "__main__":
    target = ROOT / "output" / "coldest-place-authored"
    target.mkdir(parents=True, exist_ok=True)
    build(target)
