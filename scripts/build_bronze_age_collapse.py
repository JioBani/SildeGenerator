"""Offline artwork and narrated Astra Motion render for the Bronze Age pilot."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import math
import subprocess
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw

from app.engine.harness_loader import HarnessRegistry
from app.engine.harness_preflight import planning_contract, validate_harness_plan
from app.models import VoiceSettings
from app.providers.microsoft_edge import MicrosoftEdge
from app.tracking import Tracker
from astra_motion.renderer import compile_project

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "bronze-age-collapse-astra-0.7.0"
SCALE = 2
INK = (20, 30, 36)
SEA = (25, 81, 87)
BRONZE = (222, 166, 81)
IVORY = (239, 229, 197)
CORAL = (206, 100, 78)
OLIVE = (106, 123, 92)

SCENES = [
    ("연결된 지중해", "교역과 외교로 이어진 세계",
     "약 삼천이백 년 전, 동지중해의 궁전과 항구는 거대한 교역망으로 이어져 있었습니다.",
     "setup", "route"),
    ("궁전의 시대", "미케네 · 히타이트 · 우가리트",
     "미케네의 궁전과 히타이트 제국, 우가리트의 도시는 서로의 물자와 소식에 의존했죠.",
     "explain", "comparison"),
    ("균열", "여러 지역에서 다른 시기에 위기",
     "기원전 천이백 년 무렵, 여러 지역에서 궁전이 파괴되고 교역로가 끊어졌습니다.",
     "turning_point", "process"),
    ("바다 사람들", "이집트 기록에 남은 이름",
     "이집트 기록에는 바다와 육지로 다가온 집단들, 이른바 바다 사람들이 등장합니다.",
     "evidence", "focus"),
    ("남은 질문", "그들은 누구였을까?",
     "하지만 그들이 누구였고 어디서 왔는지는 지금도 논쟁 중입니다.",
     "question", "diagram"),
    ("겹친 위기", "한 원인으로 설명할 수 없다",
     "가뭄, 전쟁, 내부 갈등과 교역 붕괴가 서로 영향을 주었을 가능성이 제기됩니다.",
     "explanation", "diagram"),
    ("같지 않은 결말", "이집트는 존속했지만 약화",
     "모든 나라가 동시에 멸망한 것은 아닙니다. 이집트는 살아남았지만 국력은 약해졌습니다.",
     "contrast", "split"),
    ("진짜 수수께끼", "연결된 세계의 취약함",
     "수수께끼는 침략자의 정체만이 아닙니다. 연결된 세계가 왜 그토록 취약했는가입니다.",
     "resolution", "route"),
]


def run(*args: str) -> None:
    subprocess.run(args, check=True)


def duration(path: Path) -> float:
    result = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        text=True,
    )
    return float(result.strip())


def p(x: float, y: float) -> tuple[int, int]:
    return round(x * SCALE), round(y * SCALE)


def box(draw: ImageDraw.ImageDraw, xy: tuple[float, float, float, float], fill, outline=None, width=1):
    draw.rounded_rectangle(tuple(round(v * SCALE) for v in xy), radius=14 * SCALE,
                           fill=fill, outline=outline, width=width * SCALE)


def line(draw: ImageDraw.ImageDraw, points, color, width=4, joint="curve"):
    draw.line([p(x, y) for x, y in points], fill=color, width=width * SCALE, joint=joint)


def circle(draw: ImageDraw.ImageDraw, x, y, radius, fill, outline=None, width=3):
    draw.ellipse((*p(x - radius, y - radius), *p(x + radius, y + radius)),
                 fill=fill, outline=outline, width=width * SCALE)


def curve(draw: ImageDraw.ImageDraw, a, b, rise, color, width=4):
    center = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - rise)
    points = []
    for n in range(31):
        t = n / 30
        x = (1 - t) ** 2 * a[0] + 2 * (1 - t) * t * center[0] + t * t * b[0]
        y = (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * center[1] + t * t * b[1]
        points.append((x, y))
    line(draw, points, color, width)


def background(index: int) -> Image.Image:
    image = Image.new("RGB", p(1920, 1080), INK)
    draw = ImageDraw.Draw(image)
    draw.rectangle((*p(950, 0), *p(1920, 1080)), fill=SEA)
    for n in range(10):
        y = 118 + n * 78
        line(draw, [(985, y), (1860, y)], (41, 103, 104), 1)
    for n in range(8):
        x = 1030 + n * 114
        line(draw, [(x, 105), (x, 830)], (41, 103, 104), 1)
    circle(draw, 1450, 472, 340, None, (61, 116, 115), 2)
    circle(draw, 1450, 472, 310, None, (61, 116, 115), 2)
    line(draw, [(1005, 827), (1840, 827)], BRONZE, 3)
    if index in (0, 7):
        network(draw, fractured=index == 7)
    elif index == 1:
        palaces(draw)
    elif index == 2:
        collapse(draw)
    elif index == 3:
        fleet(draw)
    elif index == 4:
        origins(draw)
    elif index == 5:
        pressures(draw)
    elif index == 6:
        survivor(draw)
    return image.resize((1920, 1080), Image.Resampling.LANCZOS)


def network(draw, fractured=False):
    nodes = [(1115, 560), (1270, 350), (1440, 495), (1650, 290), (1735, 625)]
    links = [(0, 1), (1, 2), (2, 3), (2, 4), (0, 2), (3, 4)]
    for a, b in links:
        if fractured and (a, b) in ((1, 2), (2, 3), (2, 4)):
            start, end = nodes[a], nodes[b]
            center = ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2)
            curve(draw, start, center, 32, CORAL, 5)
            curve(draw, (center[0] + 38, center[1] + 16), end, 32, CORAL, 5)
        else:
            curve(draw, nodes[a], nodes[b], 42, BRONZE, 5)
    for n, (x, y) in enumerate(nodes):
        active = not fractured or n in (0, 4)
        circle(draw, x, y, 31, IVORY if active else CORAL, INK, 5)
        circle(draw, x, y, 10, SEA if active else INK)
    for x, y in ((1300, 600), (1550, 652), (1560, 375)):
        circle(draw, x, y, 5, BRONZE)


def palaces(draw):
    for x, top, width in ((1070, 350, 225), (1370, 275, 235), (1650, 380, 178)):
        draw.polygon([p(x, top + 46), p(x + width / 2, top), p(x + width, top + 46)],
                     fill=BRONZE)
        box(draw, (x + 12, top + 56, x + width - 12, 680), IVORY)
        for col in range(3):
            cx = x + 45 + col * (width - 90) / 2
            box(draw, (cx, top + 78, cx + 22, 668), SEA)
        line(draw, [(x - 12, 686), (x + width + 12, 686)], BRONZE, 13)
    for x in (1190, 1490, 1740):
        circle(draw, x, 765, 10, CORAL)


def collapse(draw):
    network(draw, fractured=True)
    for x, y in ((1235, 420), (1510, 365), (1640, 570)):
        line(draw, [(x - 50, y - 50), (x - 5, y - 14), (x - 25, y + 18), (x + 45, y + 60)], CORAL, 9)
    for x in (1260, 1480, 1700):
        draw.polygon([p(x - 46, 720), p(x - 12, 640), p(x + 25, 696), p(x + 45, 720)], fill=(86, 66, 58))


def ship(draw, x, y, scale):
    def q(px, py):
        return p(x + px * scale, y + py * scale)
    draw.polygon([q(-92, 30), q(95, 30), q(56, 70), q(-58, 70)], fill=BRONZE)
    line(draw, [(x - 17 * scale, y + 23 * scale), (x - 17 * scale, y - 120 * scale)], IVORY, 6)
    draw.polygon([q(-12, -112), q(72, -28), q(-12, -28)], fill=IVORY)
    line(draw, [(x - 110 * scale, y + 85 * scale), (x + 105 * scale, y + 85 * scale)], (84, 151, 151), 4)


def fleet(draw):
    ship(draw, 1240, 530, 1.1)
    ship(draw, 1580, 405, 0.85)
    ship(draw, 1745, 625, 0.62)
    curve(draw, (1100, 725), (1790, 720), -78, CORAL, 7)
    for x, y in ((1140, 711), (1430, 785), (1730, 725)):
        circle(draw, x, y, 7, IVORY)


def origins(draw):
    ship(draw, 1450, 485, 1.15)
    for x, y in ((1130, 310), (1740, 260), (1710, 690)):
        circle(draw, x, y, 76, None, BRONZE, 3)
        line(draw, [(x - 35, y), (x + 35, y)], BRONZE, 3)
        line(draw, [(x, y - 35), (x, y + 35)], BRONZE, 3)
        curve(draw, (x, y), (1450, 485), 45, (120, 169, 159), 3)


def pressures(draw):
    ring = [(1230, 335), (1655, 335), (1240, 655), (1670, 665)]
    for n, (x, y) in enumerate(ring):
        circle(draw, x, y, 105, (35, 91, 93), BRONZE if n % 2 else CORAL, 7)
        if n == 0:
            circle(draw, x, y - 12, 32, BRONZE)
            for dx in (-65, -48, 48, 65):
                line(draw, [(x + dx, y - 72), (x + dx * 1.4, y - 95)], BRONZE, 6)
        elif n == 1:
            line(draw, [(x - 55, y - 55), (x + 55, y + 55)], IVORY, 13)
            line(draw, [(x + 55, y - 55), (x - 55, y + 55)], IVORY, 13)
        elif n == 2:
            box(draw, (x - 45, y - 65, x + 45, y + 65), IVORY)
            line(draw, [(x + 10, y - 62), (x - 12, y + 15), (x + 30, y + 63)], CORAL, 11)
        else:
            circle(draw, x - 42, y, 27, None, IVORY, 10)
            circle(draw, x + 42, y, 27, None, IVORY, 10)
            line(draw, [(x - 8, y), (x + 8, y)], CORAL, 9)
    curve(draw, ring[0], ring[1], 60, BRONZE, 5)
    curve(draw, ring[1], ring[3], 20, BRONZE, 5)
    curve(draw, ring[3], ring[2], -50, BRONZE, 5)


def survivor(draw):
    line(draw, [(1440, 155), (1440, 785)], BRONZE, 5)
    draw.polygon([p(1070, 665), p(1160, 535), p(1240, 665)], fill=(98, 73, 63))
    line(draw, [(1040, 695), (1300, 695)], CORAL, 15)
    draw.polygon([p(1550, 430), p(1670, 280), p(1790, 430)], fill=BRONZE)
    box(draw, (1580, 450, 1760, 715), IVORY)
    for x in (1605, 1660, 1715):
        box(draw, (x, 473, x + 20, 705), SEA)
    line(draw, [(1540, 725), (1805, 725)], BRONZE, 14)
    circle(draw, 1670, 240, 23, CORAL)


async def prepare() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    artwork = OUT / "artwork"
    audio = OUT / "audio"
    artwork.mkdir(exist_ok=True)
    audio.mkdir(exist_ok=True)
    voice = VoiceSettings(
        provider="microsoft_edge", model="edge-tts", voice_id="ko-KR-InJoonNeural",
        voice_name="InJoon", rate="+12%", pitch="+0Hz", volume="+0%",
    )
    tracker = Tracker(OUT)
    prepared = []
    for n, (title, takeaway, narration, function, layout) in enumerate(SCENES, 1):
        scene_id = f"scene-{n:03d}"
        picture = artwork / f"{scene_id}.png"
        background(n - 1).save(picture)
        speech = audio / f"{scene_id}.mp3"
        if not speech.exists():
            await MicrosoftEdge(voice).synthesize(
                SimpleNamespace(id=scene_id, narration=narration), speech, tracker,
            )
        prepared.append({
            "id": scene_id, "title": title, "takeaway": takeaway,
            "narration": narration, "function": function, "layout": layout,
            "image_path": str(picture), "audio_path": str(speech),
            "audio_seconds": duration(speech),
        })
    total = sum(row["audio_seconds"] + .3 for row in prepared)
    (OUT / "prepared.json").write_text(
        json.dumps({"harness": "astra-motion@0.7.0", "voice": voice.model_dump(),
                    "scenes": prepared, "planned_duration_seconds": total,
                    "paid_calls": 0, "voice_usage": tracker.usage}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps({"planned_duration_seconds": round(total, 3),
                      "scenes": len(prepared), "voice_calls": len(tracker.usage)}, ensure_ascii=False))


def render() -> None:
    plan = json.loads((OUT / "prepared.json").read_text(encoding="utf-8"))
    if plan["planned_duration_seconds"] > 60.05:
        raise ValueError(f"Narration exceeds one minute: {plan['planned_duration_seconds']:.2f}s")
    harness = HarnessRegistry(ROOT / "harnesses").load("astra-motion")
    contract = planning_contract(harness)
    scenes = []
    for row in plan["scenes"]:
        scenes.append(SimpleNamespace(
            id=row["id"], image_path=row["image_path"], viewer_takeaway=row["takeaway"],
            narration=row["narration"], scene_function=row["function"],
            layout={"mode": row["layout"]}, object_states=[
                {"object_id": "scene-image", "role": "subject", "isolation": "not_needed", "region_hint": None},
            ], motion=[{"object_id": "scene-image", "kind": "camera_push"}],
            transition="crossfade", rhythm="read_then_move_then_hold",
            renderer_requirements={"capabilities": [], "experimental_capabilities": []},
            duration_seconds=row["audio_seconds"] + .3,
        ))
    findings = validate_harness_plan(harness, scenes)
    if findings:
        raise ValueError(f"Motion plan blocked: {findings}")
    project = OUT / "project"
    compile_project(scenes, project, SimpleNamespace(width=1920, height=1080, fps=30))
    cli = Path("/app/hyperframes-runtime/node_modules/.bin/hyperframes")
    silent = OUT / "visual.mp4"
    run(str(cli), "render", f"--output={silent}", "--quality=looks",
        "--workers=1", "--low-memory-mode", "--strict", str(project))
    audio_dir = OUT / "audio"
    concat = audio_dir / "concat.txt"
    parts = []
    for row in plan["scenes"]:
        segment = audio_dir / (row["id"] + ".m4a")
        run("ffmpeg", "-v", "error", "-y", "-i", row["audio_path"], "-af",
            "apad=pad_dur=0.30", "-t", str(row["audio_seconds"] + .3),
            "-c:a", "aac", "-b:a", "160k", str(segment))
        parts.append(segment)
    concat.write_text("\n".join(f"file '{path.as_posix()}'" for path in parts) + "\n", encoding="utf-8")
    combined = OUT / "narration.m4a"
    run("ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
        "-c:a", "aac", "-b:a", "160k", str(combined))
    final = OUT / "bronze-age-collapse.mp4"
    run("ffmpeg", "-v", "error", "-y", "-i", str(silent), "-i", str(combined),
        "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-af",
        "loudnorm=I=-16:TP=-1.5:LRA=11", "-shortest", "-movflags", "+faststart", str(final))
    receipt = {
        "harness_id": "astra-motion", "harness_version": harness.manifest.version,
        "harness_sha256": harness.snapshot.source_sha256,
        "planning_contract": contract, "duration_seconds": duration(final),
        "video_sha256": hashlib.sha256(final.read_bytes()).hexdigest(),
        "paid_calls": 0, "voice_provider": "microsoft_edge",
        "quality_status": "TECHNICAL_PASS_HUMAN_PENDING",
    }
    (OUT / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"video": str(final), "duration_seconds": receipt["duration_seconds"]}, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("prepare", "render"))
    args = parser.parse_args()
    if args.stage == "prepare":
        asyncio.run(prepare())
    else:
        render()
