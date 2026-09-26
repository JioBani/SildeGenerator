"""Render an actual director plan with explicit original stills and local timed voice."""
import argparse
import asyncio
import json
import html
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"video-generator"))
from review_voice_cues import caption_cues, align_quantity_events, align_spatial_events
from app.models import ScenePlan
from app.engine.graph_executor import GraphExecutor, LocalLeaseProvider
from app.engine.harness_loader import HarnessRegistry
from app.engine.harness_preflight import validate_harness_plan
from app.engine.process_runner import ProcessRunner
from app.harness_sdk.artifacts import ArtifactStore
from app.harness_sdk.context import HarnessContext
from app.hybrid_assets import prepare_local_asset
from app.rendered_review import inspect_render, probe_video
from app.tracking import atomic_json, sha256_file


def source_binding(plan,root):
    ids={s.layout['hybrid']['source_id'] for s in plan.scenes if s.layout['hybrid']['route']=='source'}
    if not ids: return None
    if root is None: raise ValueError('source_registry_required_before_voice')
    from app.source_media import read_catalog,verified_source_path
    catalog=read_catalog(root)
    if ids-set(catalog): raise ValueError('requested_source_missing')
    return dict(catalog_sha256=sha256_file(root/'catalog.json'),
        assets={id:sha256_file(verified_source_path(root,catalog[id])) for id in sorted(ids)})


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("plan",type=Path)
    parser.add_argument("assets",type=Path)
    parser.add_argument("output",type=Path)
    parser.add_argument("--prepare-voice",action="store_true")
    parser.add_argument('--source-root',type=Path)
    args=parser.parse_args()
    plan=ScenePlan.model_validate_json(args.plan.read_text(encoding="utf-8"))
    out=args.output.resolve()
    source=source_binding(plan,args.source_root)
    if args.prepare_voice:
        out.mkdir(parents=True,exist_ok=False)
        atomic_json(out/"voice-input.json",[dict(id=s.id,narration=s.narration) for s in plan.scenes])
        atomic_json(out/"input-binding.json",dict(plan_sha256=sha256_file(args.plan),source_binding=source))
        return
    if json.loads((out/"input-binding.json").read_text())["plan_sha256"]!=sha256_file(args.plan):
        raise ValueError("director_plan_changed_after_voice_preparation")
    if json.loads((out/'input-binding.json').read_text()).get('source_binding')!=source:
        raise ValueError('source_registry_changed_after_voice_preparation')
    if json.loads((out/"voice-input.json").read_text(encoding="utf-8"))!=[dict(id=s.id,narration=s.narration) for s in plan.scenes]:
        raise ValueError("voice_script_binding_changed")
    loaded=HarnessRegistry(ROOT/"harnesses").load("hybrid-story")
    settings=SimpleNamespace(width=1280,height=720,fps=24,crossfade_seconds=0,ffmpeg_preset="fast",subtitles_enabled=True)
    config={**loaded.config,"subtitle_size":36,"subtitle_margin_vertical":48,"crossfade_seconds":0}
    work=out/"work"; work.mkdir(exist_ok=False)
    (work/"render-segments").mkdir(); (out/"delivery").mkdir()
    anchors=[]; assets=[]; cursor=0
    for scene in plan.scenes:
        audio=out/f"{scene.id}.wav"
        scene.duration_seconds=float(probe_video(audio)["format"]["duration"])
        scene.audio_path=str(audio)
        words=json.loads(audio.with_suffix(".words.json").read_text(encoding="utf-8"))
        scene.layout["subtitle_cues"]=caption_cues(scene.narration,words,scene.duration_seconds)
        hybrid=scene.layout["hybrid"]
        if hybrid["route"]=="cinematic":
            asset=args.assets.resolve()/f"{scene.id}.png"
            if not asset.is_file(): raise ValueError(f"missing_original_still:{scene.id}")
            scene.image_path=str(asset)
        elif hybrid["route"]=="diagram":
            scene.image_path=str(work/f"{scene.id}-poster.png")
            diagram=hybrid["diagram"]
            align=align_spatial_events if diagram['grammar']=='map_spatial' else align_quantity_events
            for anchor in align(diagram,scene.narration,words,scene.duration_seconds):
                anchors.append(dict(scene_id=scene.id,absolute_seconds=cursor+anchor['seconds'],**anchor))
            prepare_local_asset(scene,loaded,ROOT/"experiments/hybrid-story-v1/source-media",Path(scene.image_path),settings)
        elif hybrid['route']=='source':
            scene.image_path=str(work/f'{scene.id}-source.png')
            prepare_local_asset(scene,loaded,args.source_root,Path(scene.image_path),settings)
        else:
            raise ValueError('unsupported_route')
        assets.append(dict(scene_id=scene.id,route=hybrid["route"],image_sha256=sha256_file(Path(scene.image_path)),
            audio_sha256=sha256_file(audio),start_seconds=cursor,duration_seconds=scene.duration_seconds))
        cursor+=scene.duration_seconds
    if cursor>60: raise ValueError("measured_episode_exceeds_60_seconds")
    findings=validate_harness_plan(loaded,plan.scenes)
    atomic_json(out/"prepared-plan.json",plan.model_dump(mode="json"))
    atomic_json(out/"preflight.json",dict(findings=findings,motion_voice_anchors=anchors,duration_seconds=cursor))
    if findings: raise ValueError(findings)
    async def operation(name,**metadata):
        context=HarnessContext("actual-director-development",out,settings,ProcessRunner(),ArtifactStore(out),LocalLeaseProvider(),
            metadata={"operation":name,"config":config,**metadata})
        await GraphExecutor(loaded.snapshot).execute(await loaded.instance.build_pipeline(context),context)
    segment=work/"render-segments/segment.mp4"
    await operation("render_segment",scenes=plan.scenes,subtitles=work/"captions.ass",output=segment)
    await operation("audio_assembly",scenes=plan.scenes,work=work)
    video=out/"delivery/preview.mp4"
    await operation("video_assembly",segments=[segment],audio=work/"narration.m4a",output=video)
    inspection=inspect_render(video,plan.scenes,width=1280,height=720,fps=24)
    passed=inspection["status"]=="PIXEL_CHECKS_PASS"
    atomic_json(out/"receipt.json",dict(status="DEVELOPMENT_RENDERED" if passed else "REVISE",goal_status="GOAL_NOT_MET",harness=loaded.snapshot.as_dict(),
        plan_sha256=sha256_file(args.plan),video_sha256=sha256_file(video),assets=assets,inspection=inspection,motion_voice_anchors=anchors,
        narration_preserved=True,voice_provider="local Microsoft Heami/SAPI 16kHz word events",human_approval=None,
        paid_api_calls=0,scope="Actual director plan with explicit local artwork, verified registered sources and local voice; not automatic image-provider/service E2E",
        source_binding=source,
        bound_concept_hashes=sorted({s.layout['selected_concept']['sha256'] for s in plan.scenes if s.layout.get('selected_concept')}),
        not_evaluated=["full_independent_film_review","held_out_superiority","actual_viewer_emotion"]))
    (out/"review.html").write_text('<!doctype html><html lang="ko"><meta charset="utf-8"><title>새 대본 제작 시험</title><style>body{margin:32px;background:#f4f7f7;font-family:system-ui}main{max-width:1100px;margin:auto}video{width:100%;background:#172923}h1{font-size:26px}</style><main><h1>'+html.escape(plan.title)+'</h1><video controls preload="metadata" src="delivery/preview.mp4"></video></main></html>',encoding="utf-8")
    print(json.dumps(dict(duration_seconds=cursor,video=str(video),inspection=inspection),ensure_ascii=False),flush=True)
    if not passed: raise SystemExit(1)


if __name__=="__main__": asyncio.run(main())
