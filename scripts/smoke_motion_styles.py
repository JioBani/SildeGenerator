"""Provider-free A/B render using the same script, timing and mock audio."""
import asyncio
import json

from PIL import Image, ImageDraw

from app.config import settings
from app.engine.process_runner import ProcessRunner
from app.motion_style import bind_motion_style
from app.planner import deterministic_plan
from app.providers.elevenlabs import mock_speech
from app.tracking import Tracker
from astra_motion.renderer import concatenate_audio, render_segment


SCRIPT = (
    "밤의 가로등이 켜지자 창으로 빛이 들어옵니다. "
    "잠들지 못한 사람은 그 빛을 알아차리고 커튼을 닫습니다. "
    "빛이 사라진 방에서 다시 잠을 청합니다."
)


async def run():
    assert settings.runner_mode == settings.image_provider == settings.voice_provider == "mock", "Mock only"
    root = settings.data_dir
    root.mkdir(parents=True, exist_ok=True)
    process = ProcessRunner()
    base = deterministic_plan(SCRIPT, "flat illustrated test context", "editorial_illustration")
    audio_dir = root / "shared-audio"
    audio_dir.mkdir(exist_ok=True)
    tracker = Tracker(root)
    for scene in base.scenes:
        path = audio_dir / f"{scene.id}.mp3"
        voice = await mock_speech(scene, path, tracker, speed=1.0, record_usage=False)
        scene.audio_path = str(path)
        scene.duration_seconds = voice["duration"]
    narration = await concatenate_audio(base.scenes, root, process)
    outputs = []
    for style_id, preset in (("narrative", "editorial_illustration"), ("educational_info", "graphic_explainer")):
        plan = bind_motion_style(base, {"id": style_id, "version": "1.0.0", "imagePreset": preset}, mock=True)
        destination = root / style_id
        destination.mkdir(exist_ok=True)
        for index, scene in enumerate(plan.scenes):
            picture = Image.new("RGB", (settings.width, settings.height), (31, 66 + 12 * index, 75))
            draw = ImageDraw.Draw(picture)
            draw.rectangle((settings.width * .56, settings.height * .13, settings.width * .88, settings.height * .72),
                           fill=(81, 142, 142), outline=(244, 202, 106), width=6)
            draw.ellipse((settings.width * .67, settings.height * .31, settings.width * .78, settings.height * .5),
                         fill=(245, 198, 108))
            image_path = destination / f"{scene.id}.png"
            picture.save(image_path)
            scene.image_path = str(image_path)
        segment = destination / "segment.mp4"
        await render_segment(plan.scenes, segment, settings, {"hyperframes_quality": "looks", "hyperframes_workers": 1}, process)
        video = destination / "animated.mp4"
        await process.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(segment), "-i", str(narration),
                           "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac", "-shortest", str(video)])
        program = json.loads((destination / "segment" / "scene-program.json").read_text(encoding="utf-8"))
        assert video.stat().st_size > 0
        assert all(scene["motion_style_id"] == style_id for scene in program["scenes"])
        outputs.append({"style": style_id, "video": str(video), "bytes": video.stat().st_size,
                        "scenes": len(plan.scenes), "editable_labels": sum(len(scene["visual_labels"]) for scene in program["scenes"]),
                        "program": str(destination / "segment" / "scene-program.json")})
    assert outputs[0]["editable_labels"] == 0 and outputs[1]["editable_labels"] > 0
    (root / "comparison.json").write_text(json.dumps(outputs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(outputs, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(run())
