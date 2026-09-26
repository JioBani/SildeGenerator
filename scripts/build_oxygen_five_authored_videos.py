"""Build five independently authored motion-graphic treatments without paid providers."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCENES = [
    ("가정", "산소가 5초 동안 사라진다면?", "만약 지금 당장, 지구상에서 산소가 단 5초 동안 사라진다면 무슨 일이 벌어질까요?"),
    ("오존", "보호막이 사라진다", "자외선을 막아주던 오존층이 파괴되어, 야외에 있는 모든 생명체는 순간적으로 심각한 화상을 입게 됩니다."),
    ("연소", "동력이 멈춘다", "내연기관의 산화 연소가 중단되며, 모든 이동 수단이 동력을 잃고 추락합니다."),
    ("구조", "결합이 무너진다", "콘크리트를 바인딩하던 산소 분자가 사라지며, 현대의 모든 건축물이 순식간에 먼지가 되어 무너집니다."),
    ("지각", "땅과 하늘이 변한다", "지구 지각의 45%는 산소입니다. 발밑의 땅이 사라져 우리는 자유낙하하게 되며, 빛을 산란시킬 입자가 사라진 하늘은 완전한 검은색으로 변합니다."),
    ("결말", "당연한 숨이 지탱하는 것", "단 5초의 부재. 우리가 공기처럼 당연하게 쉬는 이 한 모금의 숨 속에, 지구 전체를 지탱하는 힘이 들어있습니다."),
]
GENRES = {
    "knowledge": {"number": "01", "name": "지식 설명형", "grammar": "질문 → 인과 도식 → 결과", "accent": "#EE5B47"},
    "tutorial": {"number": "02", "name": "교육형", "grammar": "학습 목표 → 단계별 관찰 → 핵심 정리", "accent": "#F0A83A"},
    "character": {"number": "03", "name": "캐릭터형", "grammar": "자극 → 시선 → 반응 → 설명", "accent": "#FF725E"},
    "cartoon": {"number": "04", "name": "만화형", "grammar": "설정 → 충돌 → 과장 → 결과", "accent": "#F04A3E"},
    "documentary": {"number": "05", "name": "다큐형", "grammar": "가정 → 관찰 항목 → 맥락 → 해석", "accent": "#E4B65A"},
}


def write_manifest(output: Path) -> None:
    audio = output / "audio"
    audio.mkdir(parents=True, exist_ok=True)
    manifest = [{"id": f"scene-{index:03}", "narration": scene[2]} for index, scene in enumerate(SCENES, 1)]
    (audio / "narration.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def duration(path: Path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)
    ], text=True).strip())


def art(beat: int) -> str:
    if beat == 0:
        return '''<svg class="art" viewBox="0 0 900 620"><g class="globe motif"><circle cx="445" cy="312" r="205"/><path d="M245 305h400M445 107c-95 92-95 318 0 410M445 107c95 92 95 318 0 410"/></g><g class="oxygen pulse"><circle cx="400" cy="282" r="74"/><circle cx="510" cy="338" r="74"/><text x="455" y="330">O₂</text></g><g class="timer" data-layout-allow-overlap><text x="690" y="132" data-layout-allow-overlap>00:05</text></g></svg>'''
    if beat == 1:
        return '''<svg class="art" viewBox="0 0 900 620"><g class="sun pulse"><circle cx="145" cy="105" r="58"/><path class="ray" d="M190 150L420 375M205 110L520 300M150 175L320 470"/></g><path class="shield motif" d="M350 95Q620 115 690 245Q650 475 510 535Q370 465 325 250Z"/><path class="crack" d="M510 120l-45 120 65 55-80 110 25 115"/><g class="person"><circle cx="520" cy="310" r="55"/><path d="M520 365v145M520 410l-95 70M520 410l95 70"/></g><text class="impact" x="590" y="120">UV</text></svg>'''
    if beat == 2:
        return '''<svg class="art" viewBox="0 0 900 620"><g class="road motif"><path d="M70 470H830"/><path d="M170 540H730"/></g><g class="car fall"><rect x="185" y="325" width="275" height="105" rx="28"/><circle cx="250" cy="445" r="42"/><circle cx="400" cy="445" r="42"/><path d="M255 325l65-78h95l55 78"/></g><g class="plane fall"><path d="M585 185l245 80-18 34-105-12-55 116-35-12 25-121-80-35z"/></g><g class="engine"><circle cx="330" cy="375" r="35"/><path d="M330 340v70M295 375h70"/></g><text class="impact" x="555" y="500">STOP</text></svg>'''
    if beat == 3:
        return '''<svg class="art" viewBox="0 0 900 620"><g class="building fall"><path d="M190 510V150h235v360M470 510V95h245v415"/><path d="M235 205h55M330 205h55M520 155h55M620 155h55M235 285h55M330 285h55M520 245h55M620 245h55M235 365h55M330 365h55M520 335h55M620 335h55"/></g><path class="crack" d="M540 100l-45 130 75 65-85 110 55 105M320 155l40 95-65 80 70 85-45 95"/><g class="dust"><circle cx="220" cy="505" r="28"/><circle cx="300" cy="520" r="42"/><circle cx="410" cy="515" r="32"/><circle cx="520" cy="525" r="46"/><circle cx="650" cy="515" r="36"/></g></svg>'''
    if beat == 4:
        return '''<svg class="art" viewBox="0 0 900 620"><rect class="sky" x="65" y="55" width="770" height="220"/><g class="crust fall"><path d="M65 275h770v245H65z"/><path d="M65 350l120-45 110 60 130-50 115 62 120-55 175 50"/><path d="M65 430l110-55 130 55 105-45 145 55 115-60 165 45"/></g><g class="person fall"><circle cx="445" cy="180" r="38"/><path d="M445 218v118M445 250l-70 55M445 250l70 55M445 336l-55 95M445 336l55 95"/></g><text class="impact" x="610" y="135">45%</text></svg>'''
    return '''<svg class="art" viewBox="0 0 900 620"><g class="globe motif"><circle cx="520" cy="315" r="205"/><path d="M320 310h400M520 110c-92 90-92 315 0 410M520 110c92 90 92 315 0 410"/></g><g class="breath"><path d="M95 310c120-95 195 95 315 0M95 370c125-75 195 75 300 0"/></g><g class="oxygen pulse"><circle cx="410" cy="205" r="65"/><circle cx="505" cy="245" r="65"/><text x="457" y="250">O₂</text></g></svg>'''


def frame(genre: str, index: int, label: str, title: str, narration: str) -> str:
    escaped_title, escaped_narration = html.escape(title), html.escape(narration)
    drawing = art(index)
    if genre == "knowledge":
        return f'''<section class="scene knowledge" id="s{index}"><div class="kicker">CAUSE / EFFECT · {index+1:02}</div><h2>{escaped_title}</h2><div class="logic"><span>산소 부재</span><b>→</b><span>{html.escape(label)}</span><b>→</b><span>상태 변화</span></div><div class="stage">{drawing}</div><div class="caption">{escaped_narration}</div></section>'''
    if genre == "tutorial":
        steps = "".join(f'<i class="step-dot {"active" if n == index else ""}">{n+1}</i>' for n in range(len(SCENES)))
        return f'''<section class="scene tutorial" id="s{index}"><div class="lesson">관찰 {index+1} / {len(SCENES)}</div><h2>{escaped_title}</h2><div class="steps">{steps}</div><div class="instruction"><strong>확인할 변화</strong><span>{html.escape(label)}이 어떻게 달라지는지 살펴봅니다.</span></div><div class="stage">{drawing}</div><div class="caption">{escaped_narration}</div></section>'''
    if genre == "character":
        mouth = "M-22 12Q0 28 22 12" if index in (0, 5) else "M-20 22Q0 8 20 22"
        return f'''<section class="scene character" id="s{index}"><div class="host"><svg viewBox="0 0 300 620"><g class="host-body"><circle cx="150" cy="170" r="105"/><path d="M85 270Q150 225 215 270L245 540H55Z"/></g><g class="eyes"><circle cx="112" cy="155" r="13"/><circle cx="188" cy="155" r="13"/></g><path class="mouth" d="{mouth}" transform="translate(150 175)"/><path class="arm" d="M210 310Q270 325 285 250"/></svg><div class="host-tag">O₂ 안내자</div></div><div class="speech"><small>{html.escape(label)}</small><h2>{escaped_title}</h2></div><div class="stage">{drawing}</div><div class="caption">{escaped_narration}</div></section>'''
    if genre == "cartoon":
        impacts = ["5초?!", "쨍!", "뚝!", "와르르", "푹!", "후우—"]
        return f'''<section class="scene cartoon" id="s{index}"><div class="panel-label">PANEL {index+1}</div><div class="panel"><div class="burst"></div>{drawing}<div class="impact-word" data-layout-allow-overlap>{impacts[index]}</div></div><div class="bubble"><h2>{escaped_title}</h2></div><div class="caption">{escaped_narration}</div></section>'''
    return f'''<section class="scene documentary" id="s{index}"><div class="timecode">HYPOTHETICAL / 00:0{min(5,index)}</div><div class="doc-label" data-layout-allow-overlap>극단적 가정 시뮬레이션 · 실제 관측 자료 아님</div><div class="stage" data-layout-allow-overflow>{drawing}</div><div class="doc-card"><small>관찰 항목 {index+1:02}</small><h2>{escaped_title}</h2><p>{html.escape(label)}의 변화로 서술된 장면</p></div><div class="caption">{escaped_narration}</div></section>'''


CSS = r'''
@font-face{font-family:Astra;src:local('Noto Sans CJK KR');font-weight:100 900}*{box-sizing:border-box}html,body{margin:0;width:100%;height:100%;overflow:hidden;font-family:Astra,sans-serif;letter-spacing:0}.scene{position:absolute;inset:0;overflow:hidden;opacity:0}.scene h2{margin:0;line-height:1.12;word-break:keep-all}.caption{position:absolute;z-index:20;left:70px;right:70px;bottom:48px;padding:20px 26px;font-size:31px;line-height:1.35;background:rgba(8,17,22,.78);color:#fff}.stage{position:absolute}.art{width:100%;height:100%;overflow:visible}.art *{vector-effect:non-scaling-stroke}.art text{font-family:Astra,sans-serif;font-weight:900;fill:currentColor}.art path,.art circle,.art rect{stroke:currentColor;stroke-width:8;fill:none;stroke-linecap:round;stroke-linejoin:round}.art .oxygen circle,.art .sun circle,.art .dust circle{fill:var(--accent)}.art .oxygen text{font-size:70px;text-anchor:middle;stroke:none}.art .timer text,.art .impact{font-size:62px;stroke:none}.knowledge{--accent:#ee5b47;background:#f3f0e6;color:#18343c;padding:70px}.knowledge .kicker{font-size:23px;font-weight:900;color:#c84838}.knowledge h2{font-size:68px;width:800px;margin-top:20px}.knowledge .logic{display:flex;gap:18px;align-items:center;position:absolute;left:70px;top:295px;width:660px}.knowledge .logic span{padding:18px 20px;background:#fff;border:4px solid #18343c;font-size:25px;font-weight:800}.knowledge .logic b{font-size:35px;color:#ee5b47}.knowledge .stage{right:40px;top:80px;width:1000px;height:760px}.knowledge .art .globe{fill:#d8e7e2}.tutorial{--accent:#f0a83a;background:#f8faf7;color:#173c36;padding:58px 70px;border-top:22px solid #2f796b}.tutorial .lesson{color:#2f796b;font-size:26px;font-weight:900}.tutorial h2{font-size:64px;margin-top:16px;width:900px}.tutorial .steps{display:flex;gap:18px;position:absolute;left:70px;top:225px}.tutorial .step-dot{width:58px;height:58px;border-radius:50%;display:grid;place-items:center;border:4px solid #9cb7af;font-style:normal;font-size:24px;font-weight:900}.tutorial .step-dot.active{background:#f0a83a;border-color:#173c36}.tutorial .instruction{position:absolute;left:70px;top:335px;width:520px;padding:30px;background:#e2efea;border-left:10px solid #2f796b}.tutorial .instruction strong,.tutorial .instruction span{display:block;font-size:26px}.tutorial .instruction span{margin-top:14px;line-height:1.5}.tutorial .stage{right:40px;top:155px;width:1120px;height:720px}.character{--accent:#ff725e;background:#fff4da;color:#283d4a}.character .host{position:absolute;left:25px;top:70px;width:390px;height:780px}.character .host svg{width:100%;height:100%}.character .host-body circle{fill:#79c8c3;stroke:#283d4a;stroke-width:9}.character .host-body path{fill:#f4c859;stroke:#283d4a;stroke-width:9}.character .eyes circle{fill:#283d4a}.character .mouth,.character .arm{fill:none;stroke:#283d4a;stroke-width:10;stroke-linecap:round}.character .host-tag{position:absolute;left:95px;bottom:35px;padding:10px 18px;background:#283d4a;color:white;font-weight:800}.character .speech{position:absolute;left:365px;top:55px;width:750px;padding:30px 38px;background:white;border:7px solid #283d4a;border-radius:24px}.character .speech:before{content:'';position:absolute;left:-45px;top:70px;border:24px solid transparent;border-right-color:#283d4a}.character .speech small{font-size:25px;font-weight:900;color:#d94d42}.character .speech h2{font-size:57px;margin-top:10px}.character .stage{right:20px;top:180px;width:1170px;height:700px}.cartoon{--accent:#f04a3e;background:#36b6c7;color:#162a35;padding:42px}.cartoon:after{content:'';position:absolute;inset:0;pointer-events:none;background-image:radial-gradient(rgba(22,42,53,.18) 2px,transparent 2px);background-size:15px 15px}.cartoon .panel-label{position:absolute;left:58px;top:34px;z-index:4;padding:12px 18px;background:#ffe15a;border:6px solid #162a35;font-size:25px;font-weight:900}.cartoon .panel{position:absolute;z-index:2;left:60px;right:60px;top:70px;bottom:190px;background:#fff7de;border:13px solid #162a35;box-shadow:18px 18px 0 #162a35;overflow:hidden}.cartoon .panel .art{position:absolute;right:20px;top:15px;width:78%;height:96%}.cartoon .bubble{position:absolute;z-index:5;left:120px;top:135px;width:650px;padding:26px 34px;background:#fff;border:7px solid #162a35;border-radius:50%}.cartoon .bubble h2{font-size:52px;text-align:center}.cartoon .impact-word{position:absolute;right:85px;top:55px;font-size:82px;font-weight:1000;color:#f04a3e;transform:rotate(-7deg);text-shadow:5px 5px 0 #ffe15a}.documentary{--accent:#e4b65a;background:#0d151a;color:#eef1ec}.documentary:before{content:'';position:absolute;inset:0;background:linear-gradient(90deg,rgba(0,0,0,.7),transparent 65%),repeating-linear-gradient(0deg,rgba(255,255,255,.018),rgba(255,255,255,.018) 1px,transparent 1px,transparent 4px)}.documentary .timecode{position:absolute;z-index:4;left:65px;top:48px;font-family:monospace;font-size:23px;color:#e4b65a}.documentary .doc-label{position:absolute;z-index:4;right:55px;top:45px;padding:10px 14px;border:1px solid #d0d4cf;font-size:21px}.documentary .stage{inset:-15px 0 0 380px;height:860px;color:#cbd2cf;opacity:.72}.documentary .doc-card{position:absolute;z-index:5;left:65px;top:180px;width:620px;padding:32px;border-left:7px solid #e4b65a;background:rgba(11,21,26,.82)}.documentary .doc-card small{font-size:22px;color:#e4b65a;font-weight:800}.documentary .doc-card h2{font-size:58px;margin-top:16px}.documentary .doc-card p{font-size:25px;line-height:1.5;color:#c6ceca}.documentary .caption{background:rgba(0,0,0,.72)}
'''
CSS += ".knowledge .logic b{color:#b83e32}.documentary .oxygen text{fill:#0d151a}"


def timeline(genre: str, durations: list[float]) -> str:
    lines = ["window.__timelines={};const tl=gsap.timeline({paused:true});gsap.set('.scene',{opacity:0});"]
    cursor = 0.0
    for index, value in enumerate(durations):
        selector = f"#s{index}"
        if index:
            lines.append(f"tl.set('#s{index-1}',{{opacity:0}},{cursor:.3f});")
        lines.append(f"tl.set('{selector}',{{opacity:1}},{cursor:.3f});")
        if genre == "knowledge":
            lines.append(f"tl.fromTo('{selector} .logic span',{ { 'opacity':0 } },{{opacity:1,duration:.45,stagger:.18}},{cursor+.25:.3f});")
        elif genre == "tutorial":
            lines.append(f"tl.fromTo('{selector} .instruction',{{x:-35,opacity:0}},{{x:0,opacity:1,duration:.6,ease:'power2.out'}},{cursor+.2:.3f});")
        elif genre == "character":
            lines.append(f"tl.fromTo('{selector} .eyes',{{x:-8}},{{x:12,duration:.35,ease:'power1.inOut'}},{cursor+.35:.3f});")
            lines.append(f"tl.fromTo('{selector} .host',{{y:8}},{{y:-4,duration:1.2,ease:'sine.inOut',yoyo:true,repeat:1}},{cursor+.7:.3f});")
            lines.append(f"tl.fromTo('{selector} .arm',{{rotation:-8,transformOrigin:'0% 100%'}},{{rotation:8,duration:.65,ease:'power2.out'}},{cursor+.8:.3f});")
        elif genre == "cartoon":
            lines.append(f"tl.fromTo('{selector} .panel',{{scale:.93,rotation:-1}},{{scale:1,rotation:0,duration:.42,ease:'back.out(1.6)'}},{cursor:.3f});")
            lines.append(f"tl.fromTo('{selector} .impact-word',{{scale:2.2,opacity:0}},{{scale:1,opacity:1,duration:.45,ease:'expo.out'}},{cursor+.55:.3f});")
        else:
            lines.append(f"tl.fromTo('{selector} .stage',{{scale:1.02,opacity:.35}},{{scale:1.08,opacity:.72,duration:{max(1,value-.4):.3f},ease:'none'}},{cursor:.3f});")
            lines.append(f"tl.fromTo('{selector} .doc-card',{{y:22,opacity:0}},{{y:0,opacity:1,duration:.7,ease:'power2.out'}},{cursor+.25:.3f});")
        lines.append(f"tl.fromTo('{selector} h2',{{y:22,opacity:0}},{{y:0,opacity:1,duration:.5,ease:'power2.out'}},{cursor+.15:.3f});")
        if index in (0, 1, 5):
            lines.append(f"tl.fromTo('{selector} .pulse',{{scale:.92,transformOrigin:'50% 50%'}},{{scale:1.06,duration:1.2,yoyo:true,repeat:2,ease:'sine.inOut'}},{cursor+.4:.3f});")
        if index == 1:
            lines.append(f"tl.fromTo('{selector} .ray',{{strokeDasharray:280,strokeDashoffset:280}},{{strokeDashoffset:0,duration:1.2,stagger:.12,ease:'power1.out'}},{cursor+.5:.3f});")
        if index in (2, 3, 4):
            lines.append(f"tl.fromTo('{selector} .fall',{{y:0}},{{y:{120 if index != 4 else 190},rotation:{-8 if index == 2 else 0},duration:{max(1,value*.62):.3f},ease:'power2.in'}},{cursor+max(.8,value*.22):.3f});")
        if index in (1, 3):
            lines.append(f"tl.fromTo('{selector} .crack',{{strokeDasharray:480,strokeDashoffset:480}},{{strokeDashoffset:0,duration:1.1,ease:'power2.out'}},{cursor+.8:.3f});")
        if index == 3:
            lines.append(f"tl.fromTo('{selector} .dust',{{y:0,opacity:0}},{{y:-28,opacity:.85,duration:1.2,ease:'sine.out'}},{cursor+max(1,value*.35):.3f});")
        lines.append(f"tl.fromTo('{selector} .caption',{{opacity:0}},{{opacity:1,duration:.35}},{cursor+.1:.3f});")
        cursor += value
    lines.append(f"tl.set({{}},{{}},{cursor:.3f});window.__timelines['oxygen-{genre}']=tl;")
    return "".join(lines)


def build(output: Path) -> None:
    audio = output / "audio"
    wavs = [audio / f"scene-{index:03}.wav" for index in range(1, len(SCENES) + 1)]
    if not all(path.is_file() for path in wavs):
        write_manifest(output)
        raise SystemExit(f"Audio manifest prepared at {audio / 'narration.json'}; generate local WAV files and run again")
    durations = [duration(path) for path in wavs]
    total = sum(durations)
    if total > 58:
        rate = total / 57.5
        normalized = audio / "normalized"
        normalized.mkdir(exist_ok=True)
        adjusted = []
        for source in wavs:
            target = normalized / source.name
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(source), "-filter:a", f"atempo={rate:.6f}", str(target)], check=True)
            adjusted.append(target)
        wavs = adjusted
        durations = [duration(path) for path in wavs]
        total = sum(durations)
    if total > 60:
        raise ValueError(f"Normalized narration exceeds 60 seconds: {total:.3f}")
    gsap = ROOT / "video-generator/hyperframes-runtime/node_modules/gsap/dist/gsap.min.js"
    receipt = {"scenario": "5초간의 정적", "duration": total, "paid_calls": 0, "voice": "Microsoft Heami Desktop", "formats": []}
    for genre, contract in GENRES.items():
        target = output / f"{contract['number']}-{genre}"
        project = target / "project"
        assets = project / "assets"
        assets.mkdir(parents=True, exist_ok=True)
        shutil.copy2(gsap, assets / "gsap.min.js")
        body = "".join(frame(genre, index, *scene) for index, scene in enumerate(SCENES))
        document = f'''<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>{contract['name']}</title><script src="assets/gsap.min.js"></script><style>{CSS}</style></head><body><main data-composition-id="oxygen-{genre}" data-width="1920" data-height="1080" data-start="0" data-duration="{total:.6f}" data-fps="30">{body}</main><script>{timeline(genre,durations)}</script></body></html>'''
        (project / "index.html").write_text(document, encoding="utf-8")
        (project / "meta.json").write_text(json.dumps({"name": f"oxygen-{genre}", "duration": total, "resolution": {"width": 1920, "height": 1080}, "fps": 30}, ensure_ascii=False), encoding="utf-8")
        design = {"format": genre, "name": contract["name"], "scene_grammar": contract["grammar"], "fixed_frame": False,
                  "scene_functions": [item[0] for item in SCENES], "motion_evidence": ["pulse", "ray draw", "fall", "crack", "dust", "settle"],
                  "human_review_required": True, "scientific_status": "hypothetical_claims_require_fact_review"}
        (target / "design-contract.json").write_text(json.dumps(design, ensure_ascii=False, indent=2), encoding="utf-8")
        receipt["formats"].append({"id": genre, "name": contract["name"], "project": str(project), "design_sha256": hashlib.sha256(json.dumps(design, ensure_ascii=False, sort_keys=True).encode()).hexdigest()})
    (output / "production-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    (output / "audio-concat.txt").write_text("\n".join(f"file '{path.as_posix()}'" for path in wavs) + "\n", encoding="utf-8")
    print(json.dumps({"duration": total, "output": str(output), "formats": list(GENRES)}, ensure_ascii=False))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    build(args.output.resolve())


if __name__ == "__main__":
    main()
