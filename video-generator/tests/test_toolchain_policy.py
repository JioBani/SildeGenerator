from app.toolchain_policy import plan_scene_toolchain


def test_stable_default_does_not_start_external_authoring_tools() -> None:
    plan = plan_scene_toolchain({}, selected_harness="classic-slide")
    assert plan["runtime"] == ["classic-slide"]
    assert plan["authoring"] == []
    assert plan["automatic_external_tool_execution"] is False


def test_limited_mesh_selects_gold_authoring_and_geometry_qc() -> None:
    plan = plan_scene_toolchain({
        "experimental_capabilities": [{"capability": "limited_mesh", "contract": {}}],
    }, selected_harness="astra-motion")
    assert plan["runtime"] == ["hyperframes", "gsap"]
    assert plan["authoring"] == ["opentoonz-plastic", "blender-armature"]
    assert plan["quality_control"] == ["astra-mesh-evidence"]
    assert plan["human_review"] is True
