import importlib
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from PIL import Image, ImageDraw
from pydantic import ValidationError
from app.engine.harness_loader import HarnessRegistry
from app.harness_sdk.hybrid import HybridScene, evaluate_hybrid, hybrid_output_schema, hybrid_planning_extension
from app.illustration_assets import illustration_brief, prepare_illustration
from app.rendered_review import file_sha256
from test_hybrid_story import ROOT


def composition_route():
    return json.loads((ROOT / "harnesses/hybrid-story/fixtures/illustrated-transport.json").read_text(encoding="utf-8"))


def make_pack(root):
    Image.new("RGB", (1280,720), "#246a6a").save(root / "plate.png")
    sprite = Image.new("RGBA", (160,80))
    ImageDraw.Draw(sprite).polygon([(10,20),(130,20),(155,40),(130,60),(10,60)], fill="#f87948")
    sprite.save(root / "sprite.png")
    item = {"id":"fictional-coast-launch", "title":"Test", "meaning_limit":"Synthetic test only", "usage_basis":"Authored test",
            "prompt_record":"test", "origin":"generated_illustration", "heading_degrees":0, "safe_rect":[.12,.38,.86,.8],
            **{r:{"file":f,"sha256":file_sha256(root/f)} for r,f in [("background","plate.png"),("subject","sprite.png")]}}
    (root / "catalog.json").write_text(json.dumps({"version":"illustration-packs-0.1","packs":[item]}))
    return item


class IllustratedTransportTests(unittest.TestCase):
    def test_model_schema_requires_nullable_composition_only_in_new_contract(self):
        base = json.loads((ROOT / "video-generator/schemas/scene-plan.schema.json").read_text())
        old = hybrid_output_schema(base, {"hybrid_direction": hybrid_planning_extension()})
        self.assertNotIn("composition", old["$defs"]["HybridScene"]["properties"])
        new = hybrid_output_schema(base, {"hybrid_direction": hybrid_planning_extension("hybrid-scene-0.2")})
        node = new["$defs"]["HybridScene"]
        self.assertEqual(set(node["properties"]), set(node["required"]))
        self.assertNotIn("default", node["properties"]["composition"])

    def test_legacy_route_and_timing_cannot_claim_new_composition(self):
        plan = composition_route()
        HybridScene.model_validate(plan)
        for mutation, message in [(lambda p:p.update(version="hybrid-scene-0.1"), "version_mismatch"),
            (lambda p:p["diagram"]["nodes"][1].update(change_at=.6), "precedes_arrival"),
            (lambda p:p["composition"]["points"][3].update(x=.7), "endpoint_mismatch"),
            (lambda p:p["composition"]["points"][2].update(x=.3), "nonmonotonic")]:
            plan = composition_route(); mutation(plan)
            with self.assertRaisesRegex(ValidationError, message):
                HybridScene.model_validate(plan)

    def test_missing_assets_and_moving_camera_fail_preflight(self):
        scene=SimpleNamespace(id="scene-001", transition="cut", layout={"hybrid":composition_route(),"camera":{"mode":"push"}})
        result=evaluate_hybrid([scene], set(), set())
        self.assertIn("scene-001:illustration_not_registered",result)
        self.assertIn("scene-001:illustrated_transport_requires_fixed_camera",result)

    def test_registry_alpha_hash_paths_and_complete_envelope(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); item=make_pack(root)
            spec=HybridScene.model_validate(composition_route()).composition
            self.assertNotIn("file", illustration_brief(root)[0])
            proof=prepare_illustration(root,spec,root/"prepared.png",(1280,720))
            self.assertEqual(0,proof["image_generation_calls"])
            with self.assertRaisesRegex(ValueError,"aspect_requires"):
                prepare_illustration(root,spec,root/"portrait.png",(720,1280))
            spec.points[1].y=.26
            with self.assertRaisesRegex(ValueError,"safe_envelope"):
                prepare_illustration(root,spec,root/"unsafe.png",(1280,720))
            (root/"sprite.png").write_bytes(b"corrupt")
            with self.assertRaisesRegex(ValueError,"hash_changed"):
                illustration_brief(root)
            make_pack(root)
            Image.new("RGB",(160,80),"orange").save(root/"sprite.png")
            item["subject"]["sha256"]=file_sha256(root/"sprite.png")
            (root/"catalog.json").write_text(json.dumps({"version":"illustration-packs-0.1","packs":[item]}))
            with self.assertRaisesRegex(ValueError,"real_alpha"):
                illustration_brief(root)
            item["subject"]["file"]="../outside.png"
            (root/"catalog.json").write_text(json.dumps({"version":"illustration-packs-0.1","packs":[item]}))
            with self.assertRaisesRegex(ValueError,"outside_registry"):
                illustration_brief(root)

    def test_runtime_rehashes_and_never_uses_plate_zoom_as_transport(self):
        HarnessRegistry(ROOT/"harnesses").load("hybrid-story")
        renderer=importlib.import_module("hybrid_story.hybrid_renderer")
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); make_pack(root)
            route=composition_route()
            proof=prepare_illustration(root,HybridScene.model_validate(route).composition,root/"prepared.png",(1280,720))
            scene=SimpleNamespace(id="scene-001",duration_seconds=8,layout={"hybrid":route,"hybrid_illustration":proof})
            renderer.compile_project([scene],root/"project",SimpleNamespace(width=1280,height=720,fps=24))
            content=(root/"project/index.html").read_text()
            self.assertIn("MotionPathPlugin",content)
            self.assertIn("power2.inOut",content)
            self.assertNotIn(".scene-image',",content)
            (root/"prepared-subject.png").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError,"runtime_hash_mismatch"):
                renderer.compile_project([scene],root/"bad",SimpleNamespace(width=1280,height=720,fps=24))


if __name__ == "__main__":
    unittest.main()
