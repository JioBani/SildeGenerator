"""Actual narrated renders for three different information tasks, without providers."""
import argparse
import asyncio
import json
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "video-generator"))
from semantic_diagram_fixtures import cases
from review_voice_cues import caption_cues, align_quantity_events, align_spatial_events
from app.engine.graph_executor import GraphExecutor, LocalLeaseProvider
from app.engine.harness_loader import HarnessRegistry
from app.engine.harness_preflight import validate_harness_plan
from app.engine.process_runner import ProcessRunner
from app.harness_sdk.artifacts import ArtifactStore
from app.harness_sdk.context import HarnessContext
from app.hybrid_assets import prepare_local_asset
from app.rendered_review import file_sha256, inspect_render, probe_video


async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("output",type=Path)
    parser.add_argument("--prepare-voice",action="store_true")
    parser.add_argument('--family',choices=['semantic','snapshots','spatial','snapshot_design'],default='semantic')
    args=parser.parse_args()
    selected_cases=cases()
    if args.family=='snapshots':
        from snapshot_pair_fixtures import cases as snapshot_cases
        selected_cases=snapshot_cases()
    elif args.family=='spatial':
        from spatial_map_fixtures import cases as spatial_cases
        selected_cases=spatial_cases()
    elif args.family=='snapshot_design':
        from copy import deepcopy
        from snapshot_pair_fixtures import cases as snapshot_cases
        selected_cases=[]
        for layout in ('columns','rows','dot_tracks'):
            case=deepcopy(snapshot_cases()[0]); case['id']=layout
            case['hybrid']['version']='hybrid-scene-0.6'
            case['hybrid']['design'].update(version='film-design-0.2',snapshot_layout=layout)
            selected_cases.append(case)
    out=args.output.resolve()
    if args.prepare_voice:
        out.mkdir(parents=True,exist_ok=False)
        (out/"voice-input.json").write_text(json.dumps([{"id":f"scene-{i:03d}","narration":c["narration"]} for i,c in enumerate(selected_cases,1)],ensure_ascii=False,indent=2),encoding="utf-8")
        return
    expected=[{'id':f'scene-{i:03d}','narration':c['narration']} for i,c in enumerate(selected_cases,1)]
    if json.loads((out/'voice-input.json').read_text(encoding='utf-8'))!=expected:
        raise ValueError('voice_fixture_binding_changed')
    loaded=HarnessRegistry(ROOT/"harnesses").load("hybrid-story")
    settings=SimpleNamespace(width=1280,height=720,fps=24,crossfade_seconds=0,ffmpeg_preset="fast",subtitles_enabled=True)
    config={**loaded.config,"subtitle_size":36,"subtitle_margin_vertical":48,"crossfade_seconds":0}
    results=[]
    for case_index, case in enumerate(selected_cases,1):
        folder=out/case["id"]
        folder.mkdir(exist_ok=False)
        (folder/"delivery").mkdir()
        work=folder/"work"
        (work/"render-segments").mkdir(parents=True)
        audio=out/f"scene-{case_index:03d}.wav"
        duration=float(probe_video(audio)["format"]["duration"])
        words=json.loads(audio.with_suffix(".words.json").read_text(encoding="utf-8"))
        cues=caption_cues(case["narration"],words,duration)
        motion_anchors=[]
        if case['hybrid']['diagram']['grammar']=='before_after':
            motion_anchors=align_quantity_events(case['hybrid']['diagram'],case['narration'],words,duration)
        elif case['hybrid']['diagram']['grammar']=='map_spatial':
            motion_anchors=align_spatial_events(case['hybrid']['diagram'],case['narration'],words,duration)
        for j,node in enumerate(case["hybrid"]["diagram"]["nodes"]):
            quote=node["source_quote"] or ["자료를 모읍니다","내용을 정리합니다","안내문을 발행합니다"][j]
            position=case["narration"].index(quote)
            word=next(w for w in words if w["start"]<=position<w["start"]+w["length"])
            node["change_at"]=word["seconds"]/duration
            motion_anchors.append(dict(node_id=node["id"],quote=quote,seconds=word["seconds"]))
        nodes=case["hybrid"]["diagram"]["nodes"]
        for j,edge in enumerate(case["hybrid"]["diagram"]["edges"]):
            start,end=nodes[j]["change_at"],nodes[j+1]["change_at"]
            edge.update(start_at=start+(end-start)*.25,end_at=start+(end-start)*.8)
        direction=dict(version="narrative-direction-0.1",mode="observational",subject_id=case["id"],
            subject_description="Explicit example data or procedure",goal="Understand the stated relationship",stakes="Keep quantities and ordering faithful",
            beat="explanation",visible_action="Compare, accumulate or follow the stated steps",state_before="Not yet explained",state_after="Relationship visible",
            new_information=case["narration"],shot_size="wide",viewpoint="observer",focal_target="Editable information objects",
            cut_reason="One self-contained explanation",cause_scene_number=None,choices=[],continuity_note=None,repeat_of_scene_number=None,repeat_reason=None)
        scene=SimpleNamespace(id="scene-001",narration=case["narration"],duration_seconds=duration,audio_path=str(audio),
            image_path=str(work/"poster.png"),transition="cut",layout={"hybrid":case["hybrid"],"direction":direction,"camera":{"mode":"hold"},"subtitle_cues":cues})
        prepare_local_asset(scene,loaded,ROOT/"experiments/hybrid-story-v1/source-media",Path(scene.image_path),settings)
        findings=validate_harness_plan(loaded,[scene])
        if findings: raise ValueError(findings)
        async def operation(name,**metadata):
            context=HarnessContext("semantic-smoke",folder,settings,ProcessRunner(),ArtifactStore(folder),LocalLeaseProvider(),metadata={"operation":name,"config":config,**metadata})
            await GraphExecutor(loaded.snapshot).execute(await loaded.instance.build_pipeline(context),context)
        segment=work/"render-segments/segment.mp4"
        await operation("render_segment",scenes=[scene],subtitles=work/"captions.ass",output=segment)
        await operation("audio_assembly",scenes=[scene],work=work)
        video=folder/"delivery/preview.mp4"
        await operation("video_assembly",segments=[segment],audio=work/"narration.m4a",output=video)
        inspection=inspect_render(video,[scene],width=1280,height=720,fps=24)
        result=dict(id=case["id"],video_sha256=file_sha256(video),audio_sha256=file_sha256(audio),duration_seconds=duration,
            narration=scene.narration,layout=scene.layout,inspection=inspection,motion_voice_anchors=motion_anchors,
            alignment_source="Offline SAPI word events with explicitly fixed 16kHz output")
        results.append(result)
        print(json.dumps({"id":case["id"],"inspection":inspection},ensure_ascii=False),flush=True)
    (out/"receipt.json").write_text(json.dumps(dict(harness=loaded.snapshot.as_dict(),cases=results,
        scope="Three authored input scripts; real local narrated outputs. Not unseen automatic-director transfer or independent semantic approval.",
        paid_api_calls=0,image_generation_calls=0,human_approved=False,goal_status="GOAL_NOT_MET"),ensure_ascii=False,indent=2),encoding="utf-8")
    cards=''.join(f'<section><h2>{c["hybrid"]["diagram"]["title"]}</h2><video controls preload="metadata" src="{c["id"]}/delivery/preview.mp4"></video></section>' for c in selected_cases)
    (out/"review.html").write_text(f'<!doctype html><html lang="ko"><meta charset="utf-8"><title>정보 문법 비교</title><style>body{{margin:32px;background:#f4f7f7;color:#172923;font-family:system-ui}}main{{max-width:1100px;margin:auto}}video{{width:100%;background:#162522}}section{{margin:36px 0}}h1{{font-size:28px}}</style><main><h1>서로 다른 대본 · 서로 다른 정보 표현</h1>{cards}</main></html>',encoding="utf-8")


if __name__=="__main__": asyncio.run(main())
