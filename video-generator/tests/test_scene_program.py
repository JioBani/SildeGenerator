from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace


MODULE = Path(__file__).parents[2] / "harnesses" / "astra-motion" / "src" / "astra_motion" / "scene_program.py"
SPEC = importlib.util.spec_from_file_location("astra_scene_program", MODULE)
assert SPEC and SPEC.loader
scene_program = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(scene_program)


def test_scene_contract_compiles_to_safe_allowlisted_program() -> None:
    scene = SimpleNamespace(
        id="scene-001", scene_function="compare", layout={"mode": "comparison"}, transition="crossfade",
        rhythm="compare_then_resolve",
        object_states=[
            {"object_id": "main", "role": "subject"},
            {"object_id": "proof", "role": "evidence"},
            {"object_id": "focus", "role": "highlight"},
        ],
        motion=[
            {"object_id": "main", "kind": "camera_push"},
            {"object_id": "proof", "kind": "reveal"},
            {"object_id": "focus", "kind": "emphasize"},
        ],
    )
    program = scene_program.compile_scene_program(scene)
    assert program["layout"] == "comparison"
    assert program["transition"] == "crossfade"
    assert {row["effect"] for row in program["actions"]} >= {"camera_push", "reveal", "emphasize"}


def test_unknown_layout_and_motion_fall_back_without_executing_model_code() -> None:
    scene = SimpleNamespace(
        id="scene-001", scene_function="bad", layout={"mode": "raw_html"}, transition="javascript",
        rhythm="arbitrary", object_states=[{"object_id": "x", "role": "subject"}],
        motion=[{"object_id": "x", "kind": "eval('bad')"}],
    )
    program = scene_program.compile_scene_program(scene)
    assert program["layout"] == "focus"
    assert program["transition"] == "cut"
    assert all("eval" not in row["effect"] for row in program["actions"])


def test_semantic_objects_keep_supported_motion_without_role_aliases() -> None:
    scene = SimpleNamespace(
        id="scene-009", scene_function="resolve", layout={"mode": "route"}, transition="dissolve",
        rhythm="read_then_move_then_hold",
        object_states=[
            {"object_id": "memory-fragments", "role": "새로운 기억"},
            {"object_id": "new-path", "role": "새로운 시간 체감"},
        ],
        motion=[
            {"object_id": "memory-fragments", "kind": "reveal"},
            {"object_id": "new-path", "kind": "state_change"},
        ],
    )

    program = scene_program.compile_scene_program(scene)

    assert program["version"] == "astra-scene-program-1.2"
    assert program["layout"] == "route"
    assert program["transition"] == "crossfade"
    assert program["ignored_motion_count"] == 0
    assert {item["object_id"] for item in program["semantic_objects"]} == {"memory-fragments", "new-path"}
    semantic_actions = [item for item in program["actions"] if item.get("target_type") == "semantic"]
    assert {(item["target"], item["effect"]) for item in semantic_actions} == {
        ("memory-fragments", "reveal"), ("new-path", "state_change"),
    }


def test_approved_decomposition_replaces_generic_overlay_with_real_layer() -> None:
    scene = SimpleNamespace(
        id="scene-001", scene_function="explain", transition="cut", rhythm="read_then_move_then_hold",
        layout={
            "mode": "focus",
            "layer_decomposition": {
                "status": "TECHNICAL_PASS", "production_ready": True,
                "background_path": "/work/background.png",
                "layers": [{
                    "object_id": "person", "rgba_path": "/work/person.png", "technical_ready": True,
                    "bounds": [0.5, 0.2, 0.3, 0.7], "depth_band": "foreground",
                }],
            },
        },
        object_states=[{"object_id": "person", "role": "subject"}],
        motion=[{"object_id": "person", "kind": "reaction"}],
    )

    program = scene_program.compile_scene_program(scene)

    assert program["background_path"] == "/work/background.png"
    assert program["semantic_objects"] == [{
        "object_id": "person", "role": "subject", "variant": "layer-asset",
        "asset_path": "/work/person.png", "bounds": [0.5, 0.2, 0.3, 0.7], "depth_band": "foreground",
    }]
    assert {item["effect"] for item in program["actions"] if item["target"] == "person"} == {"reaction"}
    assert not any(item["target"] == "scene-image" and item["effect"] == "camera_push" for item in program["actions"])


def test_unapproved_decomposition_is_not_used_for_rendering() -> None:
    scene = SimpleNamespace(
        id="scene-001", scene_function="explain", transition="cut", rhythm="read_then_move_then_hold",
        layout={
            "mode": "focus",
            "layer_decomposition": {
                "status": "TECHNICAL_PASS", "production_ready": False,
                "background_path": "/work/background.png",
                "layers": [{
                    "object_id": "person", "rgba_path": "/work/person.png", "technical_ready": True,
                    "bounds": [0.5, 0.2, 0.3, 0.7], "depth_band": "foreground",
                }],
            },
        },
        object_states=[{"object_id": "person", "role": "subject"}],
        motion=[{"object_id": "person", "kind": "reaction"}],
    )

    program = scene_program.compile_scene_program(scene)

    assert program["background_path"] is None
    assert not any(item.get("variant") == "layer-asset" for item in program["semantic_objects"])
