import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

from PIL import Image
from pydantic import ValidationError
from app.engine.harness_loader import HarnessRegistry
from app.harness_sdk.hybrid import Diagram, HybridScene, evaluate_hybrid, hybrid_output_schema, hybrid_planning_extension
from app.hybrid_assets import prepare_local_asset
from app.rendered_review import file_sha256
from app.source_media import prepare_source, source_brief

ROOT = Path(__file__).resolve().parents[2]


def diagram():
    return {"title": "얼음과 구조", "grammar": "cause_change_result", "comparison_scale_max": None,
        "nodes": [{"id": id, "label": label, "before": before, "after": after, "x": x, "y": .4,
                   "color": color, "reveal_at": 0, "change_at": at, "quantity": None, "unit": None}
                  for id, label, before, after, x, color, at in [
                    ("ice", "얼음", "열린 길", "막힌 길", .2, "#427c91", .15),
                    ("travel", "이동", "진행", "지연", .5, "#d76952", .45),
                    ("rescue", "구조", "접근", "기다림", .8, "#398066", .8)]],
        "edges": [{"source": "ice", "target": "travel", "label": "길 차단", "start_at": .2, "end_at": .4},
                  {"source": "travel", "target": "rescue", "label": "도착 지연", "start_at": .5, "end_at": .75}]}


def route(kind="diagram"):
    return {"version": "hybrid-scene-0.1", "route": kind, "reason": "Explain the declared causal relationship clearly",
            "diagram": diagram() if kind == "diagram" else None, "source_id": "registered" if kind == "source" else None}


class HybridContractTests(unittest.TestCase):
    def test_new_local_routes_reject_silently_ignored_camera(self):
        from test_film_design import design
        for kind in ('diagram','source','cinematic'):
            payload=route(kind)
            payload.update(version='hybrid-scene-0.4',design=design())
            if payload['diagram']:
                for i,node in enumerate(payload['diagram']['nodes']):
                    node['color']=design()['palette']['accents'][i % len(design()['palette']['accents'])]
            for mode in ('hold','push','pull'):
                scene=SimpleNamespace(id='probe',layout={'hybrid':payload,'camera':{'mode':mode}},transition='cut')
                expected=[] if kind=='cinematic' or mode=='hold' else ['probe:local_route_requires_fixed_camera']
                self.assertEqual(expected,evaluate_hybrid([scene]))
        legacy=SimpleNamespace(id='old',layout={'hybrid':route(),'camera':{'mode':'push'}},transition='cut')
        self.assertEqual([],evaluate_hybrid([legacy]))

    def test_cause_before_effect_and_stable_identity(self):
        Diagram.model_validate(diagram())
        bad = diagram()
        bad["nodes"][1]["change_at"] = .3
        with self.assertRaisesRegex(ValidationError, "effect_precedes"):
            Diagram.model_validate(bad)
        bad = diagram()
        bad["nodes"][1]["id"] = "ice"
        with self.assertRaisesRegex(ValidationError, "duplicate"):
            Diagram.model_validate(bad)

    def test_quantities_have_common_scale_and_units(self):
        plan = diagram()
        plan.update(grammar="quantitative_comparison", edges=[], comparison_scale_max=100)
        for node, value in zip(plan["nodes"], [20, 50, 100]):
            node.update(quantity=value, unit="명")
        Diagram.model_validate(plan)
        plan["nodes"][1]["unit"] = "km"
        with self.assertRaisesRegex(ValidationError, "units_mismatch"):
            Diagram.model_validate(plan)

    def test_schema_is_opt_in_and_routes_do_not_substitute(self):
        base = json.loads((ROOT / "video-generator/schemas/scene-plan.schema.json").read_text())
        original = deepcopy(base)
        schema = hybrid_output_schema(base, {"hybrid_direction": hybrid_planning_extension()})
        self.assertEqual(original, base)
        self.assertEqual(base, hybrid_output_schema(base, None))
        self.assertIn("hybrid", schema["$defs"]["scene"]["properties"]["layout"]["required"])
        wrong = route()
        wrong["route"] = "cinematic"
        with self.assertRaises(ValidationError):
            HybridScene.model_validate(wrong)
        scene = SimpleNamespace(id="scene-001", layout={"hybrid": route("source")}, transition="cut")
        self.assertEqual(["scene-001:source_not_registered"], evaluate_hybrid([scene], set()))

    def test_diagram_asset_is_local_and_never_needs_an_image_provider(self):
        loaded = HarnessRegistry(ROOT / "harnesses").load("hybrid-story")
        scene = SimpleNamespace(layout={"hybrid": route()})
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "diagram.png"
            proof = prepare_local_asset(scene, loaded, Path(temp), path, SimpleNamespace(width=1280, height=720))
            self.assertEqual(0, proof["image_generation_calls"])
            with Image.open(path) as image:
                self.assertEqual((1280, 720), image.size)
            self.assertEqual("authored_graphic", scene.layout["asset_origin"])


class SourceRegistryTests(unittest.TestCase):
    def setup_source(self, root):
        image = root / "original.png"
        Image.new("RGB", (128, 72), "red").save(image)
        item = {"id": "registered", "file": "original.png", "sha256": file_sha256(image), "origin": "photograph",
                **{key: "test metadata" for key in ("title", "source_url", "rights_url", "usage_basis", "attribution", "date_label", "meaning_limit")}}
        (root / "catalog.json").write_text(json.dumps({"version": "source-media-0.1", "assets": [item]}))
        return item

    def test_hash_changes_and_unknown_sources_fail_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            self.setup_source(root)
            proof = prepare_source(root, "registered", root / "prepared.png", (256, 144))
            self.assertEqual("trusted_source_registry", proof["prepared_by"])
            self.assertNotIn("file", source_brief(root)[0])
            with self.assertRaisesRegex(ValueError, "not_registered"):
                prepare_source(root, "invented", root / "other.png")
            (root / "original.png").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash_changed"):
                source_brief(root)
            with self.assertRaisesRegex(ValueError, "hash_changed"):
                prepare_source(root, "registered", root / "other.png")

    def test_catalog_cannot_read_outside_its_asset_root(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "registry"
            root.mkdir()
            item = self.setup_source(root)
            item["file"] = "../outside.png"
            Image.new("RGB", (128, 72)).save(root.parent / "outside.png")
            (root / "catalog.json").write_text(json.dumps({"version": "source-media-0.1", "assets": [item]}))
            with self.assertRaisesRegex(ValueError, "outside_registry"):
                prepare_source(root, "registered", root / "other.png")


if __name__ == "__main__":
    unittest.main()
