from __future__ import annotations

import asyncio
import hashlib
import json
import traceback
import shutil
import uuid
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI
from fastapi.responses import FileResponse

from .config import settings
from .image_broker import ImageTaskBroker, ImageTaskHandle, ImageTaskSpec
from .image_prompts import AssetImageSubject, canonical_asset_prompt, scene_image_prompt
from .media import apply_audio_speed, validate_audio, validate_image, validate_video
from .engine.artifact_store import ArtifactStore
from .engine.graph_executor import GraphExecutor, LocalLeaseProvider
from .engine.harness_loader import HarnessRegistry, LoadedHarness
from .engine.process_runner import ProcessRunner
from .harness_sdk.context import HarnessContext
from .models import RenderRequest, RunnerResult, Scene, ScenePlan, VoiceSampleRequest, VoiceSettings
from .planner import create_plan, validate_plan
from .prompts import load_prompts
from .providers.elevenlabs import mock_speech
from .providers.voice import create_voice_provider
from .providers.images import generate_image
from .render_pipeline import ProgressiveRenderer
from .tracking import Tracker, atomic_json
from .voice_broker import VoiceTaskBroker, VoiceTaskHandle, VoiceTaskSpec, voice_settings_hash


app = FastAPI(title="Slide Generator Runner", version="0.2.0")
image_broker = ImageTaskBroker(settings)
voice_broker = VoiceTaskBroker(settings)
progressive_renderer = ProgressiveRenderer(settings)
harness_registry = HarnessRegistry(settings.harnesses_dir)
harness_process = ProcessRunner()
active_renders = 0


@app.on_event("startup")
async def start_broker() -> None:
    await image_broker.start()
    await voice_broker.start()
    await progressive_renderer.start()


@app.on_event("shutdown")
async def stop_broker() -> None:
    await image_broker.close()
    await voice_broker.close()
    await progressive_renderer.close()


def _job_root(job_id: str) -> Path:
    jobs_root = (settings.data_dir / "jobs").resolve()
    root = (jobs_root / job_id).resolve()
    if root.parent != jobs_root:
        raise ValueError("invalid job path")
    return root


def _progress(root: Path, step: str, percent: int, scene_id: str | None = None, message: str | None = None) -> None:
    atomic_json(root / "progress.json", {
        "step": step,
        "percent": max(0, min(100, percent)),
        "sceneId": scene_id,
        "message": message,
    })


def _write_compiled_prompt(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def _prompt_bundle(snapshots: list[dict[str, str]]) -> dict[str, object]:
    return {
        "documents": [{"path": item["relative_path"], "sha256": item["sha256"]} for item in snapshots],
    }


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "ok": True,
        "busy": active_renders > 0,
        "activeRenders": active_renders,
        "mode": settings.runner_mode,
        "imageProvider": settings.image_provider,
        "imageConcurrency": settings.image_task_concurrency,
        "voiceConcurrency": settings.voice_task_concurrency,
        "voiceProvider": settings.voice_provider,
        "voiceConfigured": settings.voice_provider in {"mock", "microsoft_edge"} or bool(settings.elevenlabs_api_key),
        "voiceNetworkRequired": settings.voice_provider in {"microsoft_edge", "elevenlabs"},
        "ffmpegConcurrency": settings.ffmpeg_task_concurrency,
        "fps": settings.fps,
        "elevenLabsConfigured": bool(settings.elevenlabs_api_key),
        "harnesses": harness_registry.list(),
    }


@app.get("/harnesses")
async def harnesses() -> list[dict[str, object]]:
    return harness_registry.list()


@app.get("/harnesses/{harness_id}")
async def harness_detail(harness_id: str) -> dict[str, object]:
    loaded = harness_registry.load(harness_id)
    return {**loaded.snapshot.as_dict(), "manifest": loaded.manifest.__dict__, "config": loaded.config, "readme": (loaded.root / "README.md").read_text(encoding="utf-8")}


async def _harness_operation(harness: LoadedHarness, job_id: str, workspace: Path, operation: str, **metadata):
    context = HarnessContext(
        job_id=job_id, workspace=workspace, settings=settings, process=harness_process,
        artifacts=ArtifactStore(workspace), leases=LocalLeaseProvider({"ffmpeg": settings.ffmpeg_task_concurrency, "cpu": 2, "io": 4}),
        metadata={"operation": operation, "config": harness.config, **metadata},
    )
    graph = await harness.instance.build_pipeline(context)
    return context, await GraphExecutor(harness.snapshot).execute(graph, context)


@app.post("/voice-sample")
async def voice_sample(request: VoiceSampleRequest, background_tasks: BackgroundTasks):
    sample_root = settings.data_dir / "voice-samples" / str(uuid.uuid4())
    sample_root.mkdir(parents=True, exist_ok=False)
    output = sample_root / "sample.mp3"
    tracker = Tracker(sample_root, 1)
    scene = Scene(id="scene-001", narration=request.text, visual_summary="voice sample", image_prompt="voice sample")
    provider = create_voice_provider(request.voice_settings, settings)
    try:
        if provider:
            await provider.synthesize(scene, output, tracker, record_usage=False)
        else:
            await mock_speech(scene, output, tracker, record_usage=False)
        await validate_audio(output)
    except Exception:
        shutil.rmtree(sample_root, ignore_errors=True)
        raise
    background_tasks.add_task(shutil.rmtree, sample_root, True)
    return FileResponse(output, media_type="audio/mpeg", filename="voice-sample.mp3")


@app.post("/render", response_model=RunnerResult)
async def render(request: RenderRequest) -> RunnerResult:
    global active_renders
    active_renders += 1
    try:
        return await _render(request)
    finally:
        active_renders -= 1


async def _render(request: RenderRequest) -> RunnerResult:
    image_model = request.image_model or settings.image_generation_model
    image_broker.resume_job(request.job_id)
    voice_broker.resume_job(request.job_id)
    root = _job_root(request.job_id)
    work = root / "work"
    images = work / "images"
    continuity_dir = work / "continuity-assets"
    prompt_dir = work / "image-prompts"
    audio_dir = work / "audio"
    output_dir = root / "output"
    for directory in (work, images, continuity_dir, prompt_dir, audio_dir, output_dir, root / "logs"):
        directory.mkdir(parents=True, exist_ok=True)
    tracker = Tracker(root, request.attempt)
    prompt_snapshots: list[dict[str, str]] = []
    video_path = output_dir / "video.mp4"
    result_path = root / "result.json"
    prepared: list[asyncio.Task[None]] = []
    plan: ScenePlan | None = None
    harness: LoadedHarness | None = None
    if request.attempt > 1 and result_path.is_file() and video_path.is_file() and video_path.stat().st_size:
        try:
            cached = RunnerResult.model_validate_json(result_path.read_text(encoding="utf-8"))
            if cached.success:
                return cached
        except (ValueError, OSError):
            pass
    try:
        _progress(root, "harness_loading", 1)
        with tracker.stage("harness_loading", harness_id=request.harness_id):
            harness = harness_registry.load(request.harness_id)
            if request.harness_snapshot:
                actual = harness.snapshot.as_dict()
                for key in ("id", "version", "manifest_sha256", "source_sha256", "config_sha256"):
                    if request.harness_snapshot.get(key) != actual.get(key):
                        raise RuntimeError(f"접수된 Harness snapshot과 설치된 코드가 다릅니다: {key}")
        _progress(root, "prompt_loading", 2)
        with tracker.stage("prompt_loading"):
            prompt_values, prompt_snapshots = load_prompts(harness.root / harness.manifest.prompts_dir)

        resume_candidates = (work / "scene-plan.resume.json", work / "scene-plan.final.json", work / "scene-plan.json")
        resume_path = next((path for path in resume_candidates if request.attempt > 1 and path.is_file()), None)
        _progress(root, "scene_planning", 5)
        with tracker.stage("scene_planning", mode=settings.runner_mode, resumed=resume_path is not None):
            if resume_path is not None:
                plan = ScenePlan.model_validate_json(resume_path.read_text(encoding="utf-8"))
                validate_plan(plan, request.scenario)
            else:
                plan = await create_plan(
                    request.scenario, prompt_values, settings, tracker, work,
                    codex_model=request.codex_model,
                    codex_reasoning_effort=request.codex_reasoning_effort,
                    codex_fast_mode=request.codex_fast_mode,
                    continuity_enabled=request.continuity_enabled,
                    image_style=request.image_style,
                )
                atomic_json(work / "scene-plan.json", plan.model_dump())

        atomic_json(work / "narrative-blueprint.json", plan.model_dump())
        atomic_json(work / "style-bible.json", plan.style_bible.model_dump())
        tracker.add_asset(work / "narrative-blueprint.json", "narrative_blueprint", image_style=request.image_style)
        tracker.add_asset(work / "style-bible.json", "style_bible", image_style=request.image_style)

        if not request.continuity_enabled:
            plan = plan.model_copy(update={
                "continuity_assets": [],
                "rejected_borderline_candidates": [],
                "scenes": [scene.model_copy(update={"present_asset_ids": [], "reference_asset_ids": []}) for scene in plan.scenes],
            })
            validate_plan(plan, request.scenario)

        if request.continuity_enabled:
            prompt_snapshots = [item for item in prompt_snapshots if item["relative_path"] != "continuity/disabled.md"]
            if not plan.continuity_assets:
                prompt_snapshots = [item for item in prompt_snapshots if item["relative_path"] not in {"continuity/build-canonical-asset.md", "image/reference-contract.md"}]
        else:
            unused = {"continuity/select-assets.md", "continuity/assign-scene-references.md", "continuity/build-canonical-asset.md", "image/reference-contract.md"}
            prompt_snapshots = [item for item in prompt_snapshots if item["relative_path"] not in unused]
        selected_style_path = f"style/presets/{request.image_style.replace('_', '-')}.md"
        prompt_snapshots = [item for item in prompt_snapshots if not item["relative_path"].startswith("style/presets/") or item["relative_path"] == selected_style_path]

        # Voice work is registered immediately after narration is compiled. It
        # never waits for continuity assets, keycuts, or scene images.
        voice_snapshot = request.voice_settings or VoiceSettings(
            provider=settings.voice_provider if settings.voice_provider in {"mock", "microsoft_edge", "elevenlabs"} else "mock",
            model=settings.elevenlabs_model_id if settings.voice_provider == "elevenlabs" else "edge-tts" if settings.voice_provider == "microsoft_edge" else "mock-silence-v1",
            voice_id=settings.elevenlabs_voice_id if settings.voice_provider == "elevenlabs" else settings.microsoft_edge_voice if settings.voice_provider == "microsoft_edge" else "mock",
            voice_name=settings.elevenlabs_voice_name if settings.voice_provider == "elevenlabs" else settings.microsoft_edge_voice if settings.voice_provider == "microsoft_edge" else "무음 Mock",
            rate=settings.microsoft_edge_rate if settings.voice_provider == "microsoft_edge" else None,
            pitch=settings.microsoft_edge_pitch if settings.voice_provider == "microsoft_edge" else None,
            volume=settings.microsoft_edge_volume if settings.voice_provider == "microsoft_edge" else None,
            stability=settings.elevenlabs_stability if settings.voice_provider == "elevenlabs" else None,
            similarity_boost=settings.elevenlabs_similarity_boost if settings.voice_provider == "elevenlabs" else None,
            speed=settings.elevenlabs_speed if settings.voice_provider == "elevenlabs" else None,
        )
        voice_provider = create_voice_provider(voice_snapshot, settings)
        voice_handles: dict[str, VoiceTaskHandle] = {}
        voice_settings = voice_snapshot.model_dump(exclude_none=True)
        for scene in plan.scenes:
            audio_path = audio_dir / f"{scene.id}.mp3"
            settings_hash = voice_settings_hash(scene.narration, voice_settings)
            spec = VoiceTaskSpec(
                voice_task_id=voice_broker.task_id(request.job_id, scene.id), job_id=request.job_id,
                scene_id=scene.id, output_path=audio_path,
                provider=voice_snapshot.provider,
                model=voice_snapshot.model if voice_snapshot.provider != "microsoft_edge" else voice_snapshot.voice_id,
                settings_hash=settings_hash, settings_snapshot=voice_settings,
                narration_sha256=hashlib.sha256(scene.narration.encode()).hexdigest(),
            )

            async def generate_voice(temp: Path, attempt: int, *, current=scene) -> dict[str, object]:
                with tracker.stage("voice_generation", current.id, provider=voice_snapshot.provider, broker_attempt=attempt):
                    voice = await voice_provider.synthesize(current, temp, tracker, record_usage=False) if voice_provider else await mock_speech(current, temp, tracker, record_usage=False)
                    source_duration = float(voice.get("duration") or 0)
                    await apply_audio_speed(temp, voice_snapshot.playback_speed)
                    voice["qc"] = await validate_audio(temp)
                    voice["duration"] = float(voice["qc"]["duration_seconds"])
                    voice["playback_speed"] = voice_snapshot.playback_speed
                    voice["source_duration"] = source_duration
                    provider_usage = voice.get("provider_usage")
                    if isinstance(provider_usage, dict):
                        provider_usage["audio_duration_ms"] = round(float(voice["duration"]) * 1000)
                        raw_usage = provider_usage.setdefault("raw_usage", {})
                        if isinstance(raw_usage, dict):
                            raw_usage.update({"playback_speed": voice_snapshot.playback_speed, "source_audio_duration_ms": round(source_duration * 1000)})
                    return voice

            voice_handles[scene.id] = await voice_broker.submit(spec, generate_voice)

        bundle = _prompt_bundle(prompt_snapshots)
        asset_by_id = {asset.asset_id: asset for asset in plan.continuity_assets}
        asset_handles: dict[str, ImageTaskHandle] = {}
        for asset in plan.continuity_assets:
            compiled = canonical_asset_prompt(asset, prompt_values, plan.style_bible)
            compiled_path = prompt_dir / f"{asset.asset_id}.txt"
            compiled_sha = _write_compiled_prompt(compiled_path, compiled)
            output_path = continuity_dir / f"{asset.asset_id}.png"
            subject = AssetImageSubject(asset.asset_id, compiled)
            task_id = image_broker.task_id(request.job_id, "continuity_asset", asset.asset_id)
            spec = ImageTaskSpec(
                image_task_id=task_id, job_id=request.job_id, task_type="continuity_asset",
                asset_id=asset.asset_id, output_path=output_path, prompt_path=compiled_path,
                prompt_sha256=compiled_sha, provider=settings.image_provider,
                model=image_model if settings.image_provider != "mock" else "mock-image-v1",
                quality="medium", size="1536x1024", prompt_bundle=bundle,
                image_style=request.image_style,
            )

            async def generate_asset(temp: Path, references: list[Path], attempt: int, *, current=asset, current_subject=subject) -> dict[str, object]:
                with tracker.stage("continuity_asset_generation", asset_id=current.asset_id, broker_attempt=attempt, provider=settings.image_provider):
                    return await generate_image(current_subject, temp, prompt_values["image/system.md"], settings, tracker, [], stage="continuity_asset_generation", quality="medium", record_usage=False, model=image_model)

            asset_handles[asset.asset_id] = await image_broker.submit(spec, generate_asset)

        scene_handles: dict[str, ImageTaskHandle] = {}
        ordered_scenes = sorted(plan.scenes, key=lambda scene: (scene.cut_role != "keycut", scene.id))
        for scene in ordered_scenes:
            continuity_ids = list(scene.reference_asset_ids[:8 if scene.cut_role == "keycut" else 7])
            referenced_assets = [asset_by_id[asset_id] for asset_id in continuity_ids]
            dependencies = []
            reference_ids: list[str] = []
            reference_kinds: list[str] = []
            parent_handle = None
            if scene.cut_role != "keycut":
                parent_handle = scene_handles.get(scene.parent_keycut_scene_id or "")
                if parent_handle is None:
                    raise RuntimeError(f"{scene.sequence_id}의 기준 키컷 작업이 등록되지 않았습니다")
                dependencies.append(parent_handle)
                reference_ids.append(scene.parent_keycut_scene_id or "")
                reference_kinds.append("keycut")
            dependencies.extend(asset_handles[asset_id] for asset_id in continuity_ids)
            reference_ids.extend(continuity_ids)
            reference_kinds.extend("continuity_asset" for _ in continuity_ids)
            compiled = scene_image_prompt(scene, referenced_assets, prompt_values, plan.style_bible)
            compiled_path = prompt_dir / f"{scene.id}.txt"
            compiled_sha = _write_compiled_prompt(compiled_path, compiled)
            output_path = images / f"{scene.id}.png"
            task_type = "keycut" if scene.cut_role == "keycut" else "scene"
            task_id = image_broker.task_id(request.job_id, task_type, scene.id)
            spec = ImageTaskSpec(
                image_task_id=task_id, job_id=request.job_id, task_type=task_type, scene_id=scene.id,
                output_path=output_path, prompt_path=compiled_path, prompt_sha256=compiled_sha,
                provider=settings.image_provider,
                model=image_model if settings.image_provider != "mock" else "mock-image-v1",
                quality="medium", size="1536x1024",
                # ChatGPT OAuth image editing rejects input_fidelity, including for
                # otherwise-supported multi-reference GPT Image 2.5 requests.
                input_fidelity=None,
                reference_asset_ids=reference_ids,
                dependency_task_ids=[handle.spec.image_task_id for handle in dependencies],
                prompt_bundle={**bundle, "sequence_id": scene.sequence_id, "cut_role": scene.cut_role},
                priority=100 if scene.cut_role == "keycut" else 0,
                parent_keycut_task_id=parent_handle.spec.image_task_id if parent_handle else None,
                reference_kinds=reference_kinds,
                image_style=request.image_style,
            )

            async def generate_scene(temp: Path, references: list[Path], attempt: int, *, current=scene, current_prompt=compiled, current_reference_ids=reference_ids) -> dict[str, object]:
                subject = current.model_copy(update={"image_prompt": current_prompt})
                with tracker.stage("keycut_generation" if current.cut_role == "keycut" else "image_generation", current.id, broker_attempt=attempt, provider=settings.image_provider, reference_asset_ids=current_reference_ids, sequence_id=current.sequence_id, image_style=request.image_style):
                    return await generate_image(subject, temp, prompt_values["image/system.md"], settings, tracker, references, stage="image_generation", quality="medium", input_fidelity=None, record_usage=False, model=image_model)

            scene_handles[scene.id] = await image_broker.submit(spec, generate_scene, dependencies)

        total = len(plan.scenes)
        async def prepare_scene(index: int) -> None:
            scene = plan.scenes[index]
            percent = 10 + round(index / max(1, total) * 60)
            _progress(root, "asset_generation", percent, scene.id)
            image_result, voice_result = await asyncio.gather(scene_handles[scene.id].future, voice_handles[scene.id].future)
            image_path = image_result
            audio_path, voice = voice_result
            image_info = validate_image(image_path, settings)
            scene.image_path = str(image_path)
            scene.audio_path = str(audio_path)
            scene.duration_seconds = float(voice["duration"])
            tracker.add_asset(image_path, "scene_image", scene.id, reference_asset_ids=scene.reference_asset_ids, parent_keycut_scene_id=scene.parent_keycut_scene_id, cut_role=scene.cut_role, sequence_id=scene.sequence_id, image_style=request.image_style, **image_info)
            tracker.add_asset(audio_path, "scene_audio", scene.id, duration_ms=round(scene.duration_seconds * 1000), provider=voice_snapshot.provider, model=voice_snapshot.model, voice_id=voice_snapshot.voice_id, settings_hash=voice_handles[scene.id].spec.settings_hash, qc=voice.get("qc", {}), reused=voice.get("reused", False))
            atomic_json(work / "scene-plan.resume.json", plan.model_dump())

        prepared = [asyncio.create_task(prepare_scene(index), name=f"prepare-{scene.id}") for index, scene in enumerate(plan.scenes)]
        _progress(root, "asset_generation", 10)
        with tracker.stage("progressive_video_render", renderer="ffmpeg", fps=settings.fps, configured_concurrency=settings.ffmpeg_task_concurrency, maximum_scenes_per_segment=settings.render_segment_scenes):
            segments = await progressive_renderer.render_ready_segments(request.job_id, plan.scenes, prepared, work, harness)

        for asset in plan.continuity_assets:
            asset_path = await asset_handles[asset.asset_id].future
            image_info = validate_image(asset_path, settings)
            tracker.add_asset(asset_path, "continuity_asset", metadata_asset_id=asset.asset_id, category=asset.category, **image_info)

        atomic_json(work / "scene-plan.final.json", plan.model_dump())
        subtitles = work / "subtitles.ass"
        _progress(root, "subtitle_generation", 72)
        with tracker.stage("subtitle_generation", deterministic=True):
            await _harness_operation(harness, request.job_id, work, "subtitles", task_prefix="final-subtitles", scenes=plan.scenes, output=subtitles)
            tracker.add_asset(subtitles, "subtitles")

        _progress(root, "audio_assembly", 76)
        with tracker.stage("audio_assembly", deterministic=True):
            await _harness_operation(harness, request.job_id, work, "audio_assembly", task_prefix="audio-assembly", scenes=plan.scenes, work=work)
            narration = work / "narration.m4a"
            tracker.add_asset(narration, "narration_audio")

        _progress(root, "video_render", 80)
        with tracker.stage("video_assembly", renderer="ffmpeg", fps=settings.fps, segment_count=len(segments)):
            await _harness_operation(harness, request.job_id, work, "video_assembly", task_prefix="video-assembly", segments=segments, audio=narration, output=video_path)

        _progress(root, "deterministic_validation", 97)
        with tracker.stage("deterministic_validation", engine="ffprobe+pillow"):
            video_info = await validate_video(video_path, settings)
            validation_context = HarnessContext(request.job_id, work, settings, harness_process, ArtifactStore(work), LocalLeaseProvider())
            harness_validation = await harness.instance.validate_result(validation_context, video_info)
            if not harness_validation.valid:
                raise ValueError(harness_validation.message or "Harness result validation failed")
            tracker.add_asset(video_path, "final_video", duration_ms=round(video_info["duration_seconds"] * 1000), width=video_info["width"], height=video_info["height"], video_codec=video_info["video_codec"], audio_codec=video_info["audio_codec"], fps=video_info["fps"], continuity_enabled=request.continuity_enabled, voice_concurrency=settings.voice_task_concurrency)

        tracker.usage.extend(await image_broker.usage_events(request.job_id))
        tracker.usage.extend(await voice_broker.usage_events(request.job_id))
        _progress(root, "done", 100)
        result = RunnerResult(success=True, video_path=str(video_path), stages=tracker.stages, usage=tracker.usage, assets=tracker.assets, prompts=prompt_snapshots, narrative_blueprint=plan.model_dump(), harness_snapshot=harness.snapshot.as_dict())
    except Exception as error:
        for task in prepared:
            if not task.done():
                task.cancel()
        if prepared:
            await asyncio.gather(*prepared, return_exceptions=True)
        await asyncio.gather(image_broker.cancel_job(request.job_id), voice_broker.cancel_job(request.job_id), return_exceptions=True)
        _progress(root, "failed", 100, message=str(error)[:500])
        (root / "logs" / "runner-error.log").write_text(traceback.format_exc(), encoding="utf-8")
        result = RunnerResult(success=False, video_path=str(video_path), message=str(error)[:1500], stages=tracker.stages, usage=tracker.usage, assets=tracker.assets, prompts=prompt_snapshots, narrative_blueprint=plan.model_dump() if plan else None, harness_snapshot=harness.snapshot.as_dict() if harness else None)
    atomic_json(result_path, result.model_dump())
    return result
