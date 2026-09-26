from __future__ import annotations

import asyncio
import hashlib
import json
import traceback
import shutil
import uuid
from dataclasses import replace
from pathlib import Path
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import FileResponse

from .config import output_settings, production_settings, settings
from .asset_origin import record_generated_origin
from .layer_decomposition import decompose_scene
from .creative_readiness import evaluate_creative_readiness
from .image_broker import ImageTaskBroker, ImageTaskHandle, ImageTaskSpec
from .image_prompts import AssetImageSubject, canonical_asset_prompt, scene_image_prompt
from .media import validate_audio, validate_image, validate_video
from .motion_style import bind_motion_style
from .engine.artifact_store import ArtifactStore
from .engine.graph_executor import GraphExecutor, LocalLeaseProvider
from .engine.harness_loader import HarnessRegistry, LoadedHarness
from .engine.process_runner import ProcessRunner
from .harness_sdk.context import HarnessContext
from .models import RenderRequest, RunnerResult, Scene, ScenePlan, VoiceSampleRequest, VoiceSettings
from .planner import create_plan, validate_plan
from .plan_compiler import structural_repair_findings
from .prompts import load_prompts
from .providers.elevenlabs import mock_speech
from .providers.voice import create_voice_provider
from .providers.images import generate_image
from .render_pipeline import ProgressiveRenderer
from .scene_contracts import DURATION_POLICIES, build_production_pack, evaluate_quality_gates
from .subtitle_timing import cues_from_alignment
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


async def _harness_operation(harness: LoadedHarness, job_id: str, workspace: Path, operation: str, *, job_settings=None, **metadata):
    context = HarnessContext(
        job_id=job_id, workspace=workspace, settings=job_settings or settings, process=harness_process,
        artifacts=ArtifactStore(workspace), leases=LocalLeaseProvider({"ffmpeg": settings.ffmpeg_task_concurrency, "cpu": 2, "io": 4}),
        metadata={"operation": operation, "config": harness.config, **metadata},
    )
    graph = await harness.instance.build_pipeline(context)
    return context, await GraphExecutor(harness.snapshot).execute(graph, context)


def _configure_render_harness(harness: LoadedHarness, request: RenderRequest) -> LoadedHarness:
    if request.slide_visual_profile is None:
        return harness
    # Local illustration jobs are still-image slides. Keep the registry's
    # shared defaults intact for older jobs and other classic-slide renders.
    return replace(harness, config={**harness.config, "zoom_strength": 0.0})


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
            await mock_speech(scene, output, tracker, speed=request.voice_settings.speed or .7, record_usage=False)
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
    from .genre_profiles import VERSION, snapshot
    format_id = request.genre_id or ("motion_graphic" if request.harness_id == "astra-motion" else None)
    genre = snapshot(format_id) if format_id else None
    if request.genre_version is not None and request.genre_version != VERSION:
        raise ValueError("Format version mismatch; re-plan with the installed profile")
    image_model = request.image_model or settings.image_generation_model
    try:
        job_settings = output_settings(
            production_settings(settings, request.harness_id, request.motion_style,
                                request.slide_visual_profile, production_job=request.production_job),
            request.aspect_ratio, request.subtitles_enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    image_size = "1024x1536" if request.aspect_ratio == "9:16" else "1536x1024"
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
    genre_path = work / "genre-contract.json"
    # Jobs created before the unified format keep their original retry contract.
    if request.attempt > 1 and genre_path.is_file():
        stored_genre = json.loads(genre_path.read_text(encoding="utf-8"))
        if stored_genre is None and request.genre_id is None:
            genre = None
            format_id = None
    if genre_path.is_file():
        if json.loads(genre_path.read_text(encoding="utf-8")) != genre:
            raise ValueError("Genre changed within an existing job; create a new job")
    elif request.attempt > 1 and genre:
        raise ValueError("Missing genre snapshot for retry")
    else:
        atomic_json(genre_path, genre)
    tracker = Tracker(root, request.attempt)
    prompt_snapshots: list[dict[str, str]] = []
    video_path = output_dir / "video.mp4"
    result_path = root / "result.json"
    prepared: list[asyncio.Task[None]] = []
    plan: ScenePlan | None = None
    harness: LoadedHarness | None = None
    production_pack: dict[str, Any] | None = None
    quality_gate_report: dict[str, Any] | None = None
    director_repairs: dict[str, Any] = {}
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
            harness = _configure_render_harness(harness, request)
        _progress(root, "prompt_loading", 2)
        with tracker.stage("prompt_loading"):
            prompt_values, prompt_snapshots = load_prompts(harness.root / harness.manifest.prompts_dir)
        from .engine.harness_preflight import planning_contract
        harness_planning_contract = planning_contract(harness)
        if request.harness_id == "hybrid-story":
            from .source_media import source_brief
            harness_planning_contract["trusted_source_catalog"] = source_brief(job_settings.source_media_dir)
            from .illustration_assets import illustration_brief
            harness_planning_contract["trusted_illustration_catalog"] = illustration_brief(job_settings.illustration_assets_dir)
        if harness_planning_contract is not None:
            contract_path = work / "harness-planning-contract.json"
            atomic_json(contract_path, {
                "harness_snapshot": harness.snapshot.as_dict(),
                "contract": harness_planning_contract,
            })
            tracker.add_asset(contract_path, "harness_planning_contract",
                              harness_id=request.harness_id, version=harness_planning_contract["version"])

        resume_candidates = (work / "scene-plan.resume.json", work / "scene-plan.final.json", work / "scene-plan.json")
        previous_repair_path = work / "director-repairs.json"
        if request.attempt > 1 and previous_repair_path.is_file():
            previous_repairs = json.loads(previous_repair_path.read_text(encoding="utf-8"))
            if structural_repair_findings(previous_repairs):
                # A retry must not reuse a director plan that the production gate
                # already rejected. Replanning is cheap and happens before assets.
                resume_candidates = ()
        if request.motion_style and job_settings.image_provider == "local_graphic":
            # Old local plans contain fixed-theme artwork. Reusing one would
            # silently recreate the same visuals even after the renderer changes.
            for candidate in resume_candidates:
                if not candidate.is_file():
                    continue
                try:
                    previous = ScenePlan.model_validate_json(candidate.read_text(encoding="utf-8"))
                    if any(not isinstance(scene.layout.get("local_visual"), dict)
                           or scene.layout["local_visual"].get("mode") != "directed"
                           for scene in previous.scenes):
                        resume_candidates = ()
                except (ValueError, OSError):
                    resume_candidates = ()
                break
        resume_path = next((path for path in resume_candidates if request.attempt > 1 and path.is_file()), None)
        _progress(root, "scene_planning", 5)
        with tracker.stage("scene_planning", mode=job_settings.runner_mode, resumed=resume_path is not None):
            if resume_path is not None:
                plan = ScenePlan.model_validate_json(resume_path.read_text(encoding="utf-8"))
                validate_plan(plan, request.scenario)
                if plan.genre_contract != genre:
                    raise ValueError("Resumed plan genre does not match the job")
                repair_path = work / "director-repairs.json"
                if repair_path.is_file():
                    loaded_repairs = json.loads(repair_path.read_text(encoding="utf-8"))
                    if isinstance(loaded_repairs, dict):
                        director_repairs = loaded_repairs
            else:
                plan = await create_plan(
                    request.scenario, prompt_values, job_settings, tracker, work,
                    visual_cues=request.visual_cues,
                    codex_model=request.codex_model,
                    codex_reasoning_effort=request.codex_reasoning_effort,
                    codex_fast_mode=request.codex_fast_mode,
                    continuity_enabled=request.continuity_enabled,
                    image_style=request.image_style,
                    genre_id=format_id,
                    harness_id=request.harness_id,
                    duration_profile=request.duration_profile,
                    harness_planning_contract=harness_planning_contract,
                    motion_style=request.motion_style,
                )
                if request.motion_style is not None:
                    plan = bind_motion_style(plan, request.motion_style, mock=job_settings.runner_mode != "live")
                    if job_settings.image_provider == "local_graphic":
                        from .local_motion import author_directed_local_motion
                        plan = author_directed_local_motion(plan, request.motion_style)
                atomic_json(work / "scene-plan.json", plan.model_dump())
                if tracker.usage:
                    raw_usage = tracker.usage[-1].get("raw_usage") or {}
                    candidate_repairs = raw_usage.get("deterministic_repairs") or {}
                    if isinstance(candidate_repairs, dict):
                        director_repairs = candidate_repairs
                atomic_json(work / "director-repairs.json", director_repairs)

        atomic_json(work / "narrative-blueprint.json", plan.model_dump())
        atomic_json(work / "style-bible.json", plan.style_bible.model_dump())
        if request.motion_style is not None:
            atomic_json(work / "motion-style.json", request.motion_style)
            tracker.add_asset(work / "motion-style.json", "motion_style", style_id=request.motion_style["id"], version=request.motion_style["version"])
        tracker.add_asset(work / "narrative-blueprint.json", "narrative_blueprint", image_style=request.image_style)
        tracker.add_asset(work / "style-bible.json", "style_bible", image_style=request.image_style)

        from .engine.harness_preflight import validate_harness_plan
        creative_findings = validate_harness_plan(harness, plan.scenes)
        if request.harness_id == "hybrid-story":
            from .harness_sdk.hybrid import evaluate_hybrid
            creative_findings += evaluate_hybrid(plan.scenes, {item["id"] for item in harness_planning_contract["trusted_source_catalog"]})
        preflight_findings = structural_repair_findings(director_repairs) + creative_findings
        creative_readiness = None
        if request.harness_id == "astra-motion":
            creative_readiness = evaluate_creative_readiness(plan, harness_id=request.harness_id)
            atomic_json(work / "creative-readiness.json", creative_readiness)
            tracker.add_asset(work / "creative-readiness.json", "creative_readiness",
                              status=creative_readiness["status"])
        production_pack = build_production_pack(
            plan,
            duration_profile=request.duration_profile,
            harness_id=request.harness_id,
            upstream_findings=preflight_findings,
            creative_readiness=creative_readiness,
        )
        atomic_json(work / "scene-production-pack.json", production_pack)
        tracker.add_asset(work / "scene-production-pack.json", "scene_production_pack")
        quality_gate_report = evaluate_quality_gates(production_pack)
        atomic_json(work / "quality-gates.json", quality_gate_report)
        tracker.add_asset(work / "quality-gates.json", "quality_gate_report")
        if production_pack["status"] != "READY_FOR_COMPILATION":
            raise ValueError("장면 계약 사전 검수를 통과하지 못했습니다: " + ", ".join(production_pack["findings"]))

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
                    voice = await voice_provider.synthesize(current, temp, tracker, record_usage=False) if voice_provider else await mock_speech(current, temp, tracker, speed=voice_snapshot.speed or .7, record_usage=False)
                    voice["qc"] = await validate_audio(temp)
                    voice["duration"] = float(voice["qc"]["duration_seconds"])
                    return voice

            voice_handles[scene.id] = await voice_broker.submit(spec, generate_voice)

        bundle = _prompt_bundle(prompt_snapshots)
        asset_by_id = {asset.asset_id: asset for asset in plan.continuity_assets}
        asset_handles: dict[str, ImageTaskHandle] = {}
        active_assets = plan.continuity_assets
        if request.harness_id == "hybrid-story":
            used_asset_ids = {asset_id for scene in plan.scenes if scene.layout["hybrid"]["route"] == "cinematic"
                              for asset_id in [*scene.reference_asset_ids, *scene.present_asset_ids]}
            active_assets = [asset for asset in active_assets if asset.asset_id in used_asset_ids]
        for asset in active_assets:
            compiled = canonical_asset_prompt(asset, prompt_values, plan.style_bible) + f"\n\nOutput composition: {request.aspect_ratio} aspect ratio. Keep the subject inside the safe frame."
            compiled_path = prompt_dir / f"{asset.asset_id}.txt"
            compiled_sha = _write_compiled_prompt(compiled_path, compiled)
            output_path = continuity_dir / f"{asset.asset_id}.png"
            subject = AssetImageSubject(asset.asset_id, compiled)
            task_id = image_broker.task_id(request.job_id, "continuity_asset", asset.asset_id)
            spec = ImageTaskSpec(
                image_task_id=task_id, job_id=request.job_id, task_type="continuity_asset",
                asset_id=asset.asset_id, output_path=output_path, prompt_path=compiled_path,
                prompt_sha256=compiled_sha, provider=job_settings.image_provider,
                model={"mock": "mock-image-v1", "local_graphic": "local-graphics-v1", "local_illustration": "local-illustration-v0.5.0"}.get(job_settings.image_provider, image_model),
                quality="medium", size=image_size, prompt_bundle=bundle,
                image_style=request.image_style,
            )

            async def generate_asset(temp: Path, references: list[Path], attempt: int, *, current=asset, current_subject=subject) -> dict[str, object]:
                with tracker.stage("continuity_asset_generation", asset_id=current.asset_id, broker_attempt=attempt, provider=job_settings.image_provider):
                    return await generate_image(current_subject, temp, prompt_values["image/system.md"], job_settings, tracker, [], stage="continuity_asset_generation", quality="medium", record_usage=False, model=image_model)

            asset_handles[asset.asset_id] = await image_broker.submit(spec, generate_asset)

        scene_handles: dict[str, ImageTaskHandle] = {}
        ordered_scenes = sorted(plan.scenes, key=lambda scene: (scene.cut_role != "keycut", scene.id))
        local_scene_assets = {}
        for scene in ordered_scenes:
            if request.harness_id == "hybrid-story" and scene.layout["hybrid"]["route"] != "cinematic":
                from .hybrid_assets import prepare_local_asset
                local_path = images / f"{scene.id}.png"
                with tracker.stage("local_scene_asset", scene.id, route=scene.layout["hybrid"]["route"]):
                    await asyncio.to_thread(prepare_local_asset, scene, harness, job_settings.source_media_dir, local_path, job_settings)
                local_scene_assets[scene.id] = local_path
                continue
            continuity_ids = list(scene.reference_asset_ids[:8 if scene.cut_role == "keycut" else 7])
            referenced_assets = [asset_by_id[asset_id] for asset_id in continuity_ids]
            dependencies = []
            reference_ids: list[str] = []
            reference_kinds: list[str] = []
            parent_handle = None
            if scene.cut_role != "keycut" and scene.parent_keycut_scene_id not in local_scene_assets:
                parent_handle = scene_handles.get(scene.parent_keycut_scene_id or "")
                if parent_handle is None:
                    raise RuntimeError(f"{scene.sequence_id}의 기준 키컷 작업이 등록되지 않았습니다")
                dependencies.append(parent_handle)
                reference_ids.append(scene.parent_keycut_scene_id or "")
                reference_kinds.append("keycut")
            dependencies.extend(asset_handles[asset_id] for asset_id in continuity_ids)
            reference_ids.extend(continuity_ids)
            reference_kinds.extend("continuity_asset" for _ in continuity_ids)
            compiled = scene_image_prompt(scene, referenced_assets, prompt_values, plan.style_bible) + f"\n\nOutput composition: {request.aspect_ratio} aspect ratio. Keep all important subjects and text within the safe frame."
            compiled_path = prompt_dir / f"{scene.id}.txt"
            compiled_sha = _write_compiled_prompt(compiled_path, compiled)
            output_path = images / f"{scene.id}.png"
            task_type = "keycut" if scene.cut_role == "keycut" else "scene"
            task_id = image_broker.task_id(request.job_id, task_type, scene.id)
            spec = ImageTaskSpec(
                image_task_id=task_id, job_id=request.job_id, task_type=task_type, scene_id=scene.id,
                output_path=output_path, prompt_path=compiled_path, prompt_sha256=compiled_sha,
                provider=job_settings.image_provider,
                model={"mock": "mock-image-v1", "local_graphic": "local-graphics-v1"}.get(job_settings.image_provider, image_model),
                quality="medium", size=image_size,
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
                with tracker.stage("keycut_generation" if current.cut_role == "keycut" else "image_generation", current.id, broker_attempt=attempt, provider=job_settings.image_provider, reference_asset_ids=current_reference_ids, sequence_id=current.sequence_id, image_style=request.image_style):
                    return await generate_image(subject, temp, prompt_values["image/system.md"], job_settings, tracker, references, stage="image_generation", quality="medium", input_fidelity=None, record_usage=False, model=image_model, image_style=request.image_style)

            scene_handles[scene.id] = await image_broker.submit(spec, generate_scene, dependencies)

        total = len(plan.scenes)
        async def prepare_scene(index: int) -> None:
            scene = plan.scenes[index]
            percent = 10 + round(index / max(1, total) * 60)
            _progress(root, "asset_generation", percent, scene.id)
            image_wait = asyncio.sleep(0, result=local_scene_assets[scene.id]) if scene.id in local_scene_assets else scene_handles[scene.id].future
            image_result, voice_result = await asyncio.gather(image_wait, voice_handles[scene.id].future)
            image_path = image_result
            audio_path, voice = voice_result
            if voice_snapshot.provider != "mock" and voice.get("qc", {}).get("silence_detected"):
                raise ValueError(f"{scene.id} 음성이 무음으로 생성되어 영상 렌더 전에 중단했습니다")
            image_info = validate_image(image_path, job_settings)
            scene.image_path = str(image_path)
            origin = scene.layout["asset_provenance"] if scene.id in local_scene_assets else record_generated_origin(
                scene, image_path, provider=job_settings.image_provider, task_id=scene_handles[scene.id].spec.image_task_id)
            if request.harness_id == "astra-motion" and job_settings.layer_decomposition_enabled:
                with tracker.stage("layer_decomposition", scene.id, engine="opencv-grabcut", paid_calls=0):
                    decomposition = await asyncio.to_thread(
                        decompose_scene, scene, image_path, work / "layers" / scene.id,
                    )
                scene.layout = {**(scene.layout or {}), "layer_decomposition": decomposition}
                tracker.add_asset(Path(decomposition["manifest_path"]), "layer_manifest", scene.id,
                                  status=decomposition["status"], paid_calls=0)
                for layer in decomposition["layers"]:
                    if layer.get("technical_ready") and layer.get("rgba_path"):
                        tracker.add_asset(Path(layer["rgba_path"]), "motion_layer", scene.id,
                                          object_id=layer["object_id"], review_status=layer["review_status"])
                if decomposition.get("background_path"):
                    tracker.add_asset(Path(decomposition["background_path"]), "clean_background", scene.id,
                                      review_status="HUMAN_PENDING")
            scene.audio_path = str(audio_path)
            scene.duration_seconds = float(voice["duration"])
            cues = cues_from_alignment(scene.narration, voice.get("alignment"), scene.duration_seconds, max_chars=16 if job_settings.height > job_settings.width else 28)
            if cues:
                scene.layout = {**scene.layout, "subtitle_cues": cues}
            tracker.add_asset(image_path, "scene_image", scene.id, asset_provenance=origin, reference_asset_ids=scene.reference_asset_ids, parent_keycut_scene_id=scene.parent_keycut_scene_id, cut_role=scene.cut_role, sequence_id=scene.sequence_id, image_style=request.image_style, **image_info)
            tracker.add_asset(audio_path, "scene_audio", scene.id, duration_ms=round(scene.duration_seconds * 1000), provider=voice_snapshot.provider, model=voice_snapshot.model, voice_id=voice_snapshot.voice_id, settings_hash=voice_handles[scene.id].spec.settings_hash, qc=voice.get("qc", {}), reused=voice.get("reused", False))
            atomic_json(work / "scene-plan.resume.json", plan.model_dump())

        prepared = [asyncio.create_task(prepare_scene(index), name=f"prepare-{scene.id}") for index, scene in enumerate(plan.scenes)]
        _progress(root, "asset_generation", 10)
        if request.genre_id or request.harness_id in ("astra-motion", "genre-slide", "cinematic-slide", "narrative-slide", "hybrid-story") or request.duration_profile == "single_30m" or request.slide_visual_profile:
            await asyncio.gather(*prepared)
            measured_seconds = sum(scene.duration_seconds for scene in plan.scenes)
            maximum = DURATION_POLICIES[request.duration_profile]["rendered_max_seconds"]
            if measured_seconds > maximum:
                raise ValueError(
                    f"실측 음성 길이가 최대 {maximum}초를 초과했습니다 ({measured_seconds:.2f}초). 렌더 전에 대본이나 음성 속도를 조정해야 합니다."
                )
        if request.slide_visual_profile:
            from hashlib import sha256
            from PIL import Image
            image_records = []
            for scene in plan.scenes:
                path = Path(scene.image_path)
                with Image.open(path) as image:
                    if image.size != (job_settings.width, job_settings.height):
                        raise ValueError(f"{scene.id} local illustration dimensions are invalid")
                image_records.append({"scene_id": scene.id, "sha256": sha256(path.read_bytes()).hexdigest(),
                                      "duration_seconds": scene.duration_seconds})
            if len({item["sha256"] for item in image_records}) != len(image_records):
                raise ValueError("Local illustration scene images contain duplicates")
            manifest_path = work / "slide-visual-manifest.json"
            atomic_json(manifest_path, {"profile": request.slide_visual_profile, "images": image_records})
            tracker.add_asset(manifest_path, "slide_visual_manifest", scene_count=len(image_records),
                              profile_version=request.slide_visual_profile["version"])
        _progress(root, "segment_render", 70)
        with tracker.stage("progressive_video_render", renderer="ffmpeg", fps=settings.fps, configured_concurrency=settings.ffmpeg_task_concurrency, maximum_scenes_per_segment=settings.render_segment_scenes):
            segments = await progressive_renderer.render_ready_segments(request.job_id, plan.scenes, prepared, work, harness, job_settings)

        for asset in active_assets:
            asset_path = await asset_handles[asset.asset_id].future
            image_info = validate_image(asset_path, job_settings)
            tracker.add_asset(asset_path, "continuity_asset", metadata_asset_id=asset.asset_id, category=asset.category, **image_info)

        atomic_json(work / "scene-plan.final.json", plan.model_dump())
        subtitles = work / "subtitles.ass"
        _progress(root, "subtitle_generation", 72)
        with tracker.stage("subtitle_generation", deterministic=True):
            await _harness_operation(harness, request.job_id, work, "subtitles", job_settings=job_settings, task_prefix="final-subtitles", scenes=plan.scenes, output=subtitles)
            tracker.add_asset(subtitles, "subtitles")

        _progress(root, "audio_assembly", 76)
        with tracker.stage("audio_assembly", deterministic=True):
            await _harness_operation(harness, request.job_id, work, "audio_assembly", job_settings=job_settings, task_prefix="audio-assembly", scenes=plan.scenes, work=work)
            narration = work / "narration.m4a"
            tracker.add_asset(narration, "narration_audio")

        _progress(root, "video_render", 80)
        with tracker.stage("video_assembly", renderer="ffmpeg", fps=settings.fps, segment_count=len(segments)):
            await _harness_operation(harness, request.job_id, work, "video_assembly", job_settings=job_settings, task_prefix="video-assembly", segments=segments, audio=narration, output=video_path)

        if request.music_selection.get("mode") != "none":
            from .background_music import mix_music
            _progress(root, "music_mix", 94)
            with tracker.stage("music_mix", engine="ffmpeg", mode=request.music_selection["mode"]):
                music_report = await mix_music(video_path, request.music_selection, job_settings.data_dir,
                                               work, sum(scene.duration_seconds for scene in plan.scenes), harness_process)
                music_report_path = work / "music-report.json"
                atomic_json(music_report_path, music_report)
                tracker.add_asset(music_report_path, "music_report", **music_report)

        _progress(root, "deterministic_validation", 97)
        with tracker.stage("deterministic_validation", engine="ffprobe+pillow"):
            video_info = await validate_video(video_path, job_settings)
            validation_context = HarnessContext(request.job_id, work, job_settings, harness_process, ArtifactStore(work), LocalLeaseProvider())
            harness_validation = await harness.instance.validate_result(validation_context, video_info)
            if not harness_validation.valid:
                raise ValueError(harness_validation.message or "Harness result validation failed")
            from .rendered_review import inspect_for_contract
            picture_review = await asyncio.to_thread(
                inspect_for_contract, video_path, plan.scenes, harness_planning_contract,
                width=job_settings.width, height=job_settings.height, fps=job_settings.fps,
            )
            if picture_review is not None:
                picture_review_path = work / "rendered-observations.json"
                atomic_json(picture_review_path, picture_review)
                tracker.add_asset(picture_review_path, "rendered_observations")
                if picture_review["status"] != "PIXEL_CHECKS_PASS":
                    raise ValueError("완성 영상 화면 검사 실패: " + ", ".join(picture_review["findings"]))
            tracker.add_asset(video_path, "final_video", duration_ms=round(video_info["duration_seconds"] * 1000), width=video_info["width"], height=video_info["height"], video_codec=video_info["video_codec"], audio_codec=video_info["audio_codec"], fps=video_info["fps"], continuity_enabled=request.continuity_enabled, voice_concurrency=settings.voice_task_concurrency)
            quality_gate_report = evaluate_quality_gates(
                production_pack,
                rendered_seconds=float(video_info["duration_seconds"]),
            )
            atomic_json(work / "quality-gates.json", quality_gate_report)
            if quality_gate_report["status"] == "BLOCKED":
                raise ValueError("완성 영상이 길이 검수를 통과하지 못했습니다")

        tracker.usage.extend(await image_broker.usage_events(request.job_id))
        tracker.usage.extend(await voice_broker.usage_events(request.job_id))
        _progress(root, "done", 100)
        result = RunnerResult(success=True, video_path=str(video_path), stages=tracker.stages, usage=tracker.usage, assets=tracker.assets, prompts=prompt_snapshots, narrative_blueprint=plan.model_dump(), harness_snapshot=harness.snapshot.as_dict(), production_pack=production_pack, quality_gate_report=quality_gate_report)
    except Exception as error:
        for task in prepared:
            if not task.done():
                task.cancel()
        if prepared:
            await asyncio.gather(*prepared, return_exceptions=True)
        await asyncio.gather(image_broker.cancel_job(request.job_id), voice_broker.cancel_job(request.job_id), return_exceptions=True)
        _progress(root, "failed", 100, message=str(error)[:500])
        (root / "logs" / "runner-error.log").write_text(traceback.format_exc(), encoding="utf-8")
        result = RunnerResult(success=False, video_path=str(video_path), message=str(error)[:1500], stages=tracker.stages, usage=tracker.usage, assets=tracker.assets, prompts=prompt_snapshots, narrative_blueprint=plan.model_dump() if plan else None, harness_snapshot=harness.snapshot.as_dict() if harness else None, production_pack=production_pack, quality_gate_report=quality_gate_report)
    atomic_json(result_path, result.model_dump())
    return result
