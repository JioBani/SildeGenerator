"""Render an actual independent sprite/plate/route, not a proxy infographic."""
import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"video-generator"))
from app.engine.harness_loader import HarnessRegistry
from app.hybrid_assets import prepare_local_asset
from app.rendered_review import file_sha256

p=argparse.ArgumentParser();p.add_argument("output",type=Path);a=p.parse_args()
out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
loaded=HarnessRegistry(ROOT/"harnesses").load("hybrid-story")
settings=SimpleNamespace(width=1280,height=720,fps=24,illustration_assets_dir=ROOT/"experiments/illustrated-transport-v1/assets")
route=json.loads((loaded.root/"fixtures/illustrated-transport.json").read_text(encoding="utf-8"))
scene=SimpleNamespace(id="scene-001",duration_seconds=8,transition="cut",layout={"hybrid":route,"camera":{"mode":"hold"}})
proof=prepare_local_asset(scene,loaded,Path("/unused"),out/"plate.png",settings)
renderer=importlib.import_module("hybrid_story.hybrid_renderer")
project=out/"project";renderer.compile_project([scene],project,settings)
cli="/app/hyperframes-runtime/node_modules/.bin/hyperframes"
video=out/"illustrated-transport.mp4"
subprocess.run([cli,"render",str(project),f"--output={video}","--quality=looks","--workers=1","--low-memory-mode","--strict"],check=True,timeout=900)
subprocess.run([cli,"snapshot",str(project),"--at=0.3,1,3.4,5.9,7.5","--no-end","--describe=false"],check=True,timeout=120)
receipt={"harness":loaded.snapshot.as_dict(),"scene":scene.layout,"duration":8,"voice":None,
         "scope":"Silent authored capability benchmark, not an autonomous full film or human approval",
         "status":"GOAL_NOT_MET","proof":proof,"video_sha256":file_sha256(video),"paid_api_calls":0}
(out/"receipt.json").write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding="utf-8")
print(video)
