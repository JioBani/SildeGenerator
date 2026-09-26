"""Isolated revision of the rejected B clip; leaves A and B artifacts untouched."""
from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from actor_assembly_gate import audit
from build_light_pollution_story_ab import ASSETS, EXPERIMENT, GSAP, VOICE, duration, page, render, sha256


def verify() -> dict:
    review = json.loads((EXPERIMENT / "human-review-b-v2.json").read_text(encoding="utf-8"))
    assert sha256(EXPERIMENT / "A/comparison.mp4") == review["baseline_sha256"]
    assert sha256(EXPERIMENT / "B/comparison.mp4") == review["artifact_sha256"]
    audio_hashes = {}
    metadata = {}
    for variant in ("B", "C"):
        video = EXPERIMENT / variant / "comparison.mp4"
        audio_hashes[variant] = subprocess.check_output([
            "ffmpeg", "-v", "error", "-i", str(video), "-map", "0:a:0", "-c:a", "pcm_s16le",
            "-f", "hash", "-hash", "sha256", "-"], text=True).strip()
        probe = json.loads(subprocess.check_output([
            "ffprobe", "-v", "error", "-show_streams", "-of", "json", str(video)], text=True))
        stream = next(s for s in probe["streams"] if s["codec_type"] == "video")
        assert (stream["width"], stream["height"], stream["r_frame_rate"]) == (1920, 1080, "30/1")
        metadata[variant] = {k:stream[k] for k in ("codec_name", "width", "height", "r_frame_rate", "duration", "nb_frames")}
    assert audio_hashes["B"] == audio_hashes["C"]
    assert metadata["B"]["nb_frames"] == metadata["C"]["nb_frames"]
    result = {"technical_checks":"PASS", "originals_preserved":True,
              "decoded_audio_hashes":audio_hashes, "metadata":metadata,
              "candidate_sha256":sha256(EXPERIMENT / "C/comparison.mp4"),
              "human_quality":"PENDING", "comprehension_improvement":"UNPROVEN"}
    assembly_path = EXPERIMENT / "C/assembly-contract.json"
    if assembly_path.is_file():
        assembly = audit(json.loads(assembly_path.read_text(encoding="utf-8")), EXPERIMENT)
        result["asset_assembly"] = {key:value for key,value in assembly.items() if key != "probe_series"}
    else:
        result["asset_assembly"] = {"status":"BLOCKED", "findings":["assembly_contract_missing"]}
    result["delivery_eligible"] = False
    result["overall_status"] = result["asset_assembly"]["status"]
    human_path = EXPERIMENT / "C/human-review.json"
    if human_path.is_file():
        human = json.loads(human_path.read_text(encoding="utf-8"))
        if human.get("video_sha256") != result["candidate_sha256"]:
            result["human_quality"] = "STALE_REVIEW"
        elif human.get("decision") == "REVISE":
            result["human_quality"] = "REVISE"
    (EXPERIMENT / "C/verification.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def candidate_page(seconds: float) -> str:
    html = page("B", seconds).replace("story-b", "story-c")
    html = html.replace('<div class="torso">', '''<svg class="neck-underlay" viewBox="0 0 1920 1080"><path d="M1435 635 L1578 650 L1545 772 L1460 770 L1425 685Z" fill="#b17a55"/></svg><div class="torso">''')
    html = html.replace('<img class="notice" src="assets/person-head-notice.png" alt=""></div>', '''<img class="notice" src="assets/person-head-notice.png" alt=""><img class="squint" src="assets/person-head-squint-v3.png" alt=""><div class="face-light"></div></div>''')
    html = html.replace('</style>', '''
    .head{transform-origin:56px 246px;filter:brightness(.76)}
    .torso,.neck-underlay{filter:brightness(.76)}
    .notice,.squint{clip-path:ellipse(13% 12% at 28% 46%)}
    .squint{opacity:0}
    .face-light{position:absolute;inset:0;opacity:0;background:linear-gradient(90deg,rgba(255,211,142,.32),transparent 65%);mask:url(assets/person-head-neutral.png) center/100% 100% no-repeat}
    .lamp-lit,.room-beam{opacity:0}
    </style>''')
    # Replace the disconnected beam with a visible outdoor source and beam reaching the face.
    html = html.replace('<path d="M465 110V680 M165 395H765"', '''<g fill="#c1d4d4"><circle cx="260" cy="203" r="3"/><circle cx="615" cy="170" r="3"/></g>
    <path d="M535 650V284 Q535 255 567 255H620" fill="none" stroke="#7b9ca6" stroke-width="11"/>
    <path d="M578 248H630L643 274H565Z" fill="#6d8d94"/>
    <path class="lamp-lit" d="M570 274H637L625 286H581Z" fill="#ffe4ab"/>
    <path d="M465 110V680 M165 395H765"''')
    html = html.replace('<path class="light" d="M540 175 L1040 875 L680 900 L185 450Z" fill="url(#beam)"/>', '')
    html = html.replace('</svg><div class="person">', '''<path class="room-beam" d="M599 281L1510 510L1615 840L588 286Z" fill="#f9c67b" fill-opacity=".16"/></svg><div class="person">''')
    start = html.index("tl.to('.light'")
    end = html.index("tl.set({},", start)
    animation = """
    tl.to('.lamp-lit',{opacity:1,duration:.22,ease:'sine.out'},1.5);
    tl.to('.room-beam',{opacity:1,duration:.55,ease:'sine.out'},1.6);
    tl.to('.head,.torso,.neck-underlay',{filter:'brightness(1)',duration:.45,ease:'sine.out'},1.7);
    tl.to('.face-light',{opacity:1,duration:.45,ease:'sine.out'},1.7);
    tl.to('.notice',{opacity:1,duration:.18,ease:'sine.out'},2.2);
    tl.to('.squint',{opacity:1,duration:.16,ease:'sine.inOut'},2.8);
    tl.to('.head',{rotation:1.8,duration:.7,ease:'sine.inOut'},3.05);
    tl.to('.head',{rotation:.7,duration:1.2,ease:'sine.inOut'},4.6);
    tl.to('.squint',{opacity:0,duration:.12,ease:'sine.inOut'},5.0);
    """
    return html[:start] + animation + html[end:]


def build() -> None:
    root = EXPERIMENT / "C"
    project = root / "project"
    target = project / "assets"
    target.mkdir(parents=True, exist_ok=True)
    for asset in ASSETS.glob("*.png"):
        shutil.copy2(asset, target / asset.name)
    shutil.copy2(GSAP, target / GSAP.name)
    seconds = duration(VOICE)
    (project / "index.html").write_text(candidate_page(seconds), encoding="utf-8")
    (project / "meta.json").write_text(json.dumps({"name":"story-c", "duration":seconds,
        "resolution":{"width":1920,"height":1080}, "fps":30}), encoding="utf-8")
    contract = {
        "version":"light-reaction-0.3", "status":"HUMAN_REVIEW_REQUIRED", "production_ready":False,
        "baseline_sha256":sha256(EXPERIMENT / "B/comparison.mp4"),
        "narration_sha256":sha256(VOICE), "duration_seconds":seconds,
        "paid_api_calls":0, "builtin_image_edits":1,
        "events_seconds":{"light_source_on":1.5, "face_illumination":1.7, "notice":2.2,
            "squint":2.8, "head_response":3.05, "settle":4.6, "hold":5.6},
        "contact":{"head_pivot":[1336,566], "hand_stationary":True,
            "neck_coverage":"opaque underlay below torso and head"},
        "asset_sha256":{p.name:sha256(p) for p in target.glob("*.png")},
        "limitations":["Authored experiment, not service pipeline", "Face state crossfade is not a facial rig",
            "Multiple variables changed; no isolated causal attribution", "No curtain action or verified comprehension gain"],
    }
    (root / "revision-contract.json").write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    render("C")
    contract["video_sha256"] = sha256(root / "comparison.mp4")
    contract["html_sha256"] = sha256(project / "index.html")
    (root / "revision-contract.json").write_text(json.dumps(contract, ensure_ascii=False, indent=2), encoding="utf-8")
    verify()


if __name__ == "__main__":
    build()
